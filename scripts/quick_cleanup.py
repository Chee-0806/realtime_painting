#!/usr/bin/env python3
"""
快速清理脚本 - 清理multiprocessing孤儿进程和GPU内存
"""

import logging
import sys
import time

try:
    import torch
except ImportError:
    torch = None

try:
    import psutil
except ImportError:
    psutil = None
    print("警告: psutil未安装，无法清理进程")
    sys.exit(1)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_multiprocessing_processes():
    """清理multiprocessing孤儿进程"""
    if not psutil:
        return 0

    cleaned_count = 0
    current_pid = psutil.Process().pid

    logger.info(f"当前进程PID: {current_pid}")

    # 查找所有multiprocessing相关进程
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'ppid', 'status']):
        try:
            cmdline = proc.info.get('cmdline', [])
            if cmdline and any('multiprocessing' in str(arg) for arg in cmdline):
                pid = proc.info['pid']
                ppid = proc.info['ppid']
                status = proc.info['status']

                # 检查是否是孤儿进程（父进程不存在或为1）
                is_orphaned = False
                try:
                    if ppid == 1:
                        is_orphaned = True
                        reason = "父进程为init"
                    else:
                        parent = psutil.Process(ppid)
                        if not parent.is_running():
                            is_orphaned = True
                            reason = "父进程已死"
                except psutil.NoSuchProcess:
                    is_orphaned = True
                    reason = "父进程不存在"

                if is_orphaned or True:  # 暂时清理所有multiprocessing进程
                    memory_info = proc.memory_info() if hasattr(proc, 'memory_info') else None
                    memory_mb = memory_info.rss / 1024 / 1024 if memory_info else 0

                    logger.info(f"发现multiprocessing进程: PID {pid}, PPID {ppid}, "
                              f"状态: {status}, 内存: {memory_mb:.1f}MB, 孤儿: {is_orphaned}")

                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                        cleaned_count += 1
                        logger.info(f"✓ 进程 {pid} 已优雅终止")
                    except psutil.TimeoutExpired:
                        proc.kill()
                        cleaned_count += 1
                        logger.warning(f"✓ 进程 {pid} 已强制终止")
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        logger.warning(f"✗ 无法处理进程 {pid}: {e}")

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return cleaned_count

def cleanup_gpu_memory():
    """清理GPU内存"""
    if not torch or not torch.cuda.is_available():
        logger.info("CUDA不可用，跳过GPU内存清理")
        return

    try:
        # 获取清理前状态
        before_allocated = torch.cuda.memory_allocated()
        before_reserved = torch.cuda.memory_reserved()

        logger.info(f"清理前GPU内存: 已分配 {before_allocated / 1024**3:.2f}GB, "
                   f"已保留 {before_reserved / 1024**3:.2f}GB")

        # 多轮清理
        import gc
        for i in range(5):
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            time.sleep(0.1)

        # 获取清理后状态
        after_allocated = torch.cuda.memory_allocated()
        after_reserved = torch.cuda.memory_reserved()

        freed_allocated = (before_allocated - after_allocated) / 1024**3
        freed_reserved = (before_reserved - after_reserved) / 1024**3

        logger.info(f"清理后GPU内存: 已分配 {after_allocated / 1024**3:.2f}GB, "
                   f"已保留 {after_reserved / 1024**3:.2f}GB")
        logger.info(f"释放内存: 已分配 {freed_allocated:.2f}GB, "
                   f"已保留 {freed_reserved:.2f}GB")

    except Exception as e:
        logger.error(f"GPU内存清理失败: {e}")

def main():
    logger.info("🧹 开始快速清理...")

    # 清理multiprocessing进程
    logger.info("📋 查找并清理multiprocessing孤儿进程...")
    cleaned_processes = cleanup_multiprocessing_processes()
    logger.info(f"✅ 清理了 {cleaned_processes} 个multiprocessing进程")

    # 清理GPU内存
    logger.info("🎮 清理GPU内存...")
    cleanup_gpu_memory()

    # 显示最终状态
    logger.info("📊 最终资源状态:")
    if torch and torch.cuda.is_available():
        final_allocated = torch.cuda.memory_allocated() / 1024**3
        final_reserved = torch.cuda.memory_reserved() / 1024**3
        logger.info(f"   GPU内存: 已分配 {final_allocated:.2f}GB, 已保留 {final_reserved:.2f}GB")

    memory = psutil.virtual_memory()
    logger.info(f"   系统内存: {memory.percent:.1f}% 使用 ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")

    logger.info("🎉 快速清理完成！")

if __name__ == "__main__":
    main()