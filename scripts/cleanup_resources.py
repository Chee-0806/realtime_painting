#!/usr/bin/env python3
"""
资源清理脚本
用于清理Python应用中可能存在的内存和显存泄漏
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import logging
from typing import List, Optional
import gc

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResourceCleaner:
    """资源清理器"""

    def __init__(self):
        self.killed_processes = []
        self.cleanup_stats = {
            'killed_processes': 0,
            'freed_memory_mb': 0,
            'cleaned_gpu_memory_mb': 0
        }

    def find_orphaned_multiprocessing_processes(self) -> List[psutil.Process]:
        """查找孤立的multiprocessing进程"""
        orphaned_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('multiprocessing' in str(arg) for arg in cmdline):
                    # 检查是否是孤立的resource_tracker或spawn_main进程
                    if any('resource_tracker' in str(arg) or 'spawn_main' in str(arg) for arg in cmdline):
                        # 检查父进程是否存在
                        try:
                            parent = proc.parent()
                            if parent is None or not parent.is_running():
                                orphaned_processes.append(proc)
                                logger.info(f"发现孤立multiprocessing进程: PID {proc.pid}, 命令: {' '.join(cmdline)}")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            orphaned_processes.append(proc)
                            logger.info(f"无法访问父进程，标记为孤立: PID {proc.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return orphaned_processes

    def kill_process_tree(self, pid: int) -> bool:
        """杀死进程及其子进程树"""
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            # 先杀死子进程
            for child in children:
                try:
                    child.terminate()
                    child.wait(timeout=3)
                    logger.info(f"已终止子进程: PID {child.pid}")
                except psutil.NoSuchProcess:
                    pass
                except psutil.TimeoutExpired:
                    try:
                        child.kill()
                        logger.info(f"强制杀死子进程: PID {child.pid}")
                    except psutil.NoSuchProcess:
                        pass

            # 再杀死父进程
            parent.terminate()
            try:
                parent.wait(timeout=3)
                logger.info(f"已终止主进程: PID {pid}")
            except psutil.TimeoutExpired:
                parent.kill()
                logger.info(f"强制杀死主进程: PID {pid}")

            self.killed_processes.append(pid)
            self.cleanup_stats['killed_processes'] += 1
            return True

        except psutil.NoSuchProcess:
            logger.warning(f"进程 {pid} 已不存在")
            return False
        except psutil.AccessDenied:
            logger.error(f"没有权限杀死进程 {pid}")
            return False

    def clean_python_multiprocessing(self) -> int:
        """清理孤立的Python多进程"""
        logger.info("开始清理孤立的multiprocessing进程...")

        orphaned = self.find_orphaned_multiprocessing_processes()
        cleaned_count = 0

        for proc in orphaned:
            if self.kill_process_tree(proc.pid):
                cleaned_count += 1
                # 获取进程内存使用情况
                try:
                    memory_info = proc.memory_info()
                    freed_memory = memory_info.rss / 1024 / 1024  # MB
                    self.cleanup_stats['freed_memory_mb'] += freed_memory
                    logger.info(f"释放内存: {freed_memory:.1f}MB")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        logger.info(f"清理完成，共处理 {cleaned_count} 个孤立进程")
        return cleaned_count

    def clean_gpu_memory(self) -> bool:
        """清理GPU显存"""
        try:
            import torch

            if not torch.cuda.is_available():
                logger.info("没有检测到CUDA设备，跳过GPU清理")
                return False

            # 获取清理前的显存状态
            before_allocated = torch.cuda.memory_allocated()
            before_reserved = torch.cuda.memory_reserved()

            logger.info(f"清理前GPU显存: 已分配 {before_allocated / 1024**3:.2f}GB, 已保留 {before_reserved / 1024**3:.2f}GB")

            # 执行多次清理
            for i in range(3):
                gc.collect()  # Python垃圾回收
                torch.cuda.empty_cache()  # 清空CUDA缓存
                torch.cuda.synchronize()  # 同步所有CUDA操作
                time.sleep(0.1)  # 短暂等待

            # 获取清理后的显存状态
            after_allocated = torch.cuda.memory_allocated()
            after_reserved = torch.cuda.memory_reserved()

            freed_allocated = (before_allocated - after_allocated) / 1024**2  # MB
            freed_reserved = (before_reserved - after_reserved) / 1024**2  # MB

            self.cleanup_stats['cleaned_gpu_memory_mb'] = max(freed_allocated, freed_reserved)

            logger.info(f"清理后GPU显存: 已分配 {after_allocated / 1024**3:.2f}GB, 已保留 {after_reserved / 1024**3:.2f}GB")
            logger.info(f"释放显存: {max(freed_allocated, freed_reserved):.1f}MB")

            return True

        except ImportError:
            logger.warning("PyTorch未安装，跳过GPU清理")
            return False
        except Exception as e:
            logger.error(f"清理GPU显存时出错: {e}")
            return False

    def clean_zombie_gpu_processes(self) -> int:
        """清理僵尸GPU进程"""
        try:
            # 使用nvidia-smi查找GPU进程
            result = subprocess.run(
                ['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader'],
                capture_output=True, text=True
            )

            if result.returncode != 0:
                logger.warning("无法获取GPU进程信息")
                return 0

            gpu_processes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid = int(parts[0].strip())
                        process_name = parts[1].strip()
                        gpu_processes.append({'pid': pid, 'name': process_name})

            cleaned_count = 0
            for gpu_proc in gpu_processes:
                try:
                    # 检查进程是否还存在
                    proc = psutil.Process(gpu_proc['pid'])
                    if not proc.is_running():
                        logger.info(f"发现僵尸GPU进程记录: PID {gpu_proc['pid']} ({gpu_proc['name']})")
                        # 这里我们无法直接清理nvidia-smi中的记录，只能记录
                        cleaned_count += 1
                except psutil.NoSuchProcess:
                    logger.info(f"GPU进程 {gpu_proc['pid']} 已不存在")
                    cleaned_count += 1
                except psutil.AccessDenied:
                    logger.warning(f"无权限访问进程 {gpu_proc['pid']}")

            return cleaned_count

        except FileNotFoundError:
            logger.warning("nvidia-smi命令未找到")
            return 0
        except Exception as e:
            logger.error(f"清理僵尸GPU进程时出错: {e}")
            return 0

    def force_cleanup_with_xformers(self) -> bool:
        """使用xformers强制清理"""
        try:
            # 检查是否已存在force_xformers_cleanup.py脚本
            cleanup_script = "/root/realtime_painting/scripts/force_xformers_cleanup.py"
            if os.path.exists(cleanup_script):
                logger.info("运行xformers强制清理脚本...")
                result = subprocess.run(
                    [sys.executable, cleanup_script],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    logger.info("xformers强制清理完成")
                    logger.info(f"输出: {result.stdout}")
                    return True
                else:
                    logger.error(f"xformers强制清理失败: {result.stderr}")
                    return False
            else:
                logger.info("未找到xformers清理脚本，跳过")
                return False

        except Exception as e:
            logger.error(f"运行xformers清理脚本时出错: {e}")
            return False

    def run_full_cleanup(self) -> dict:
        """执行完整的资源清理"""
        logger.info("开始执行完整资源清理...")
        start_time = time.time()

        # 1. 清理孤立的多进程
        multiprocessing_cleaned = self.clean_python_multiprocessing()

        # 2. 清理GPU显存
        gpu_cleaned = self.clean_gpu_memory()

        # 3. 清理僵尸GPU进程
        zombie_gpu_cleaned = self.clean_zombie_gpu_processes()

        # 4. 强制xformers清理
        xformers_cleaned = self.force_cleanup_with_xformers()

        # 5. 最终垃圾回收
        final_gc = gc.collect()

        end_time = time.time()
        duration = end_time - start_time

        # 生成清理报告
        cleanup_report = {
            'duration_seconds': duration,
            'multiprocessing_cleaned': multiprocessing_cleaned,
            'gpu_memory_cleaned': gpu_cleaned,
            'zombie_gpu_cleaned': zombie_gpu_cleaned,
            'xformers_cleaned': xformers_cleaned,
            'final_gc_objects': final_gc,
            'stats': self.cleanup_stats,
            'killed_process_pids': self.killed_processes
        }

        logger.info(f"资源清理完成，耗时 {duration:.2f} 秒")
        logger.info(f"清理统计: {cleanup_report}")

        return cleanup_report

    def print_cleanup_report(self, report: dict):
        """打印清理报告"""
        print("\n" + "="*60)
        print("🧹 资源清理报告")
        print("="*60)
        print(f"⏱️  清理耗时: {report['duration_seconds']:.2f} 秒")
        print(f"🔄 多进程清理: {report['multiprocessing_cleaned']} 个")
        print(f"🎮 GPU显存清理: {'成功' if report['gpu_memory_cleaned'] else '失败'}")
        print(f"💀 僵尸GPU进程: {report['zombie_gpu_cleaned']} 个")
        print(f"🔧 Xformers清理: {'成功' if report['xformers_cleaned'] else '跳过'}")
        print(f"🗑️  最终垃圾回收: {report['final_gc_objects']} 个对象")

        if report['stats']['killed_processes'] > 0:
            print(f"\n💀 已终止进程:")
            for pid in report['killed_process_pids']:
                print(f"   - PID {pid}")

        if report['stats']['freed_memory_mb'] > 0:
            print(f"\n💾 释放内存: {report['stats']['freed_memory_mb']:.1f} MB")

        if report['stats']['cleaned_gpu_memory_mb'] > 0:
            print(f"🎮 释放GPU显存: {report['stats']['cleaned_gpu_memory_mb']:.1f} MB")

        print("\n✅ 清理完成!")
        print("="*60)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="资源清理工具")
    parser.add_argument("--dry-run", action="store_true", help="只检查不执行清理")
    parser.add_argument("--multiprocessing-only", action="store_true", help="只清理多进程")
    parser.add_argument("--gpu-only", action="store_true", help="只清理GPU")
    parser.add_argument("--force", action="store_true", help="强制执行清理")

    args = parser.parse_args()

    cleaner = ResourceCleaner()

    if args.dry_run:
        logger.info("干运行模式，只检查不清理")
        orphaned = cleaner.find_orphaned_multiprocessing_processes()
        logger.info(f"发现 {len(orphaned)} 个孤立multiprocessing进程")
        return

    if args.multiprocessing_only:
        count = cleaner.clean_python_multiprocessing()
        logger.info(f"多进程清理完成，处理了 {count} 个进程")
        return

    if args.gpu_only:
        success = cleaner.clean_gpu_memory()
        logger.info(f"GPU清理完成: {'成功' if success else '失败'}")
        return

    # 执行完整清理
    report = cleaner.run_full_cleanup()
    cleaner.print_cleanup_report(report)

if __name__ == "__main__":
    main()