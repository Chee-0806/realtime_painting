#!/usr/bin/env python3
"""
Xformers 内存清理脚本

专门针对使用xformers加速的StreamDiffusion系统的内存清理。
"""

import gc
import logging
import os
import signal
import subprocess
import time
import torch
import psutil

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_xformers_processes():
    """查找使用xformers的Python进程"""
    xformers_processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if proc.info['name'] == 'python':
                cmdline = proc.info['cmdline']
                memory_info = proc.info['memory_info']

                if cmdline and any(keyword in ' '.join(cmdline) for keyword in [
                    'streamdiffusion', 'realtime_painting', 'xformers',
                    'uvicorn', 'fastapi', 'torch', 'cuda'
                ]):
                    process_info = {
                        'pid': proc.info['pid'],
                        'cmdline': ' '.join(cmdline),
                        'rss_gb': memory_info.rss / 1024**3 if memory_info else 0,
                        'vms_gb': memory_info.vms / 1024**3 if memory_info else 0,
                        'has_xformers': any('xformers' in arg for arg in cmdline),
                        'has_streamdiffusion': any('streamdiffusion' in arg for arg in cmdline)
                    }
                    xformers_processes.append(process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return xformers_processes

def terminate_xformers_processes():
    """优雅地终止xformers相关进程"""
    processes = find_xformers_processes()

    if not processes:
        logger.info("未发现xformers相关进程")
        return

    logger.info(f"发现 {len(processes)} 个xformers相关进程:")

    for proc in processes:
        logger.info(f"  PID {proc['pid']}: {proc['cmdline'][:80]}...")
        logger.info(f"    内存: RSS={proc['rss_gb']:.2f}GB, VMS={proc['vms_gb']:.2f}GB")
        logger.info(f"    xformers: {proc['has_xformers']}, streamdiffusion: {proc['has_streamdiffusion']}")

    # 按内存使用排序，先终止大内存进程
    processes.sort(key=lambda x: x['rss_gb'], reverse=True)

    for proc in processes:
        try:
            pid = proc['pid']
            logger.info(f"终止进程 {pid}...")

            # 先发送SIGTERM
            os.kill(pid, signal.SIGTERM)
            time.sleep(3)

            # 检查进程是否还存在
            try:
                os.kill(pid, 0)  # 检查进程是否存在
                # 如果还存在，强制杀死
                os.kill(pid, signal.SIGKILL)
                logger.info(f"进程 {pid} 已被强制终止")
            except ProcessLookupError:
                logger.info(f"进程 {pid} 已优雅终止")

        except (ProcessLookupError, PermissionError) as e:
            logger.warning(f"无法终止进程 {proc['pid']}: {e}")

def clear_xformers_cache():
    """清理xformers相关缓存"""
    cache_paths = [
        "~/.cache/xformers",
        "~/.cache/torch/xformers",
        "./__pycache__",
        "./build",
        "./dist",
        "./xformers.egg-info"
    ]

    total_cleaned = 0

    logger.info("清理xformers缓存...")

    for cache_path in cache_paths:
        expanded_path = os.path.expanduser(cache_path)

        if os.path.exists(expanded_path):
            try:
                # 计算目录大小
                total_size = 0
                file_count = 0

                for root, dirs, files in os.walk(expanded_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            file_count += 1

                if total_size > 0:
                    logger.info(f"删除缓存目录: {expanded_path} ({total_size / 1024**2:.1f}MB, {file_count} 文件)")

                    # 删除整个目录
                    import shutil
                    shutil.rmtree(expanded_path)
                    total_cleaned += total_size

            except Exception as e:
                logger.warning(f"删除缓存目录 {expanded_path} 失败: {e}")
        else:
            logger.debug(f"缓存目录不存在: {expanded_path}")

    if total_cleaned > 0:
        logger.info(f"总共清理了 {total_cleaned / 1024**2:.1f}MB 的xformers缓存")
    else:
        logger.info("未发现xformers缓存需要清理")

def clear_gpu_memory_with_xformers():
    """针对xformers的GPU内存清理"""
    if not torch.cuda.is_available():
        logger.info("CUDA不可用，跳过GPU内存清理")
        return

    try:
        logger.info("开始清理xformers相关的GPU内存...")

        # 获取初始内存状态
        initial_allocated = torch.cuda.memory_allocated()
        initial_reserved = torch.cuda.memory_reserved()

        logger.info(f"初始GPU内存: 已分配 {initial_allocated / 1024**3:.2f}GB, 已保留 {initial_reserved / 1024**3:.2f}GB")

        # 尝试导入并清理xformers相关组件
        try:
            import xformers
            logger.info("检测到xformers，尝试清理...")

            # xformers可能有特定的清理方法
            if hasattr(xformers.ops, 'clear_cache'):
                xformers.ops.clear_cache()
                logger.info("xformers.ops缓存已清理")

        except ImportError:
            logger.info("xformers未安装或不可用")
        except Exception as e:
            logger.warning(f"清理xformers缓存时出错: {e}")

        # 标准CUDA清理
        for i in range(3):
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

            # 强制垃圾回收
            collected = gc.collect()
            if i == 0:
                logger.info(f"垃圾回收释放了 {collected} 个对象")

            time.sleep(0.1)

        # 获取清理后内存状态
        final_allocated = torch.cuda.memory_allocated()
        final_reserved = torch.cuda.memory_reserved()

        freed_allocated = (initial_allocated - final_allocated) / 1024**3
        freed_reserved = (initial_reserved - final_reserved) / 1024**3

        logger.info(f"清理后GPU内存: 已分配 {final_allocated / 1024**3:.2f}GB, 已保留 {final_reserved / 1024**3:.2f}GB")
        logger.info(f"释放GPU内存: 已分配 {freed_allocated:.2f}GB, 已保留 {freed_reserved:.2f}GB")

        # 如果使用多GPU，清理所有设备
        if torch.cuda.device_count() > 1:
            logger.info(f"清理 {torch.cuda.device_count()} 个GPU设备...")
            for device_id in range(torch.cuda.device_count()):
                torch.cuda.set_device(device_id)
                torch.cuda.empty_cache()
                logger.debug(f"GPU设备 {device_id} 已清理")

        # 重置到设备0
        if torch.cuda.device_count() > 0:
            torch.cuda.set_device(0)

    except Exception as e:
        logger.error(f"清理GPU内存时出错: {e}")

def clear_pytorch_memory():
    """深度清理PyTorch内存"""
    try:
        logger.info("深度清理PyTorch内存...")

        # 清理所有已知的PyTorch缓存
        if hasattr(torch, '_C'):
            try:
                torch._C._cuda_clearCublasWorkspaces()
                logger.debug("CUBLAS工作空间已清理")
            except:
                pass

        if hasattr(torch.cuda, 'reset_max_memory_allocated'):
            try:
                torch.cuda.reset_max_memory_allocated()
                torch.cuda.reset_max_memory_reserved()
                logger.debug("PyTorch内存统计已重置")
            except:
                pass

        # 多轮垃圾回收
        for round_num in range(5):
            collected = gc.collect()
            if round_num == 0:
                logger.info(f"第1轮垃圾回收释放了 {collected} 个对象")

            # 清理PyTorch的内部缓存
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

            time.sleep(0.2)

        logger.info("PyTorch深度清理完成")

    except Exception as e:
        logger.error(f"PyTorch深度清理时出错: {e}")

def check_xformers_memory_leak():
    """检查xformers内存泄漏"""
    logger.info("检查xformers内存泄漏...")

    # 检查进程
    processes = find_xformers_processes()
    if processes:
        total_rss = sum(p['rss_gb'] for p in processes)
        total_vms = sum(p['vms_gb'] for p in processes)

        logger.warning(f"发现 {len(processes)} 个xformers相关进程仍在运行:")
        logger.warning(f"  总RSS内存: {total_rss:.2f}GB")
        logger.warning(f"  总VMS内存: {total_vms:.2f}GB")

        for proc in processes:
            logger.warning(f"    PID {proc['pid']}: {proc['rss_gb']:.2f}GB - {proc['cmdline'][:60]}...")

        return True
    else:
        logger.info("未发现xformers相关进程")
        return False

def final_memory_status():
    """报告最终内存状态"""
    logger.info("=== 最终内存状态 ===")

    # GPU内存
    if torch.cuda.is_available():
        try:
            allocated = torch.cuda.memory_allocated()
            reserved = torch.cuda.memory_reserved()
            device_count = torch.cuda.device_count()

            logger.info(f"GPU设备数量: {device_count}")
            for device_id in range(device_count):
                device_allocated = torch.cuda.memory_allocated(device_id)
                device_reserved = torch.cuda.memory_reserved(device_id)
                logger.info(f"  设备 {device_id}: 已分配 {device_allocated / 1024**3:.2f}GB, 已保留 {device_reserved / 1024**3:.2f}GB")

            logger.info(f"总计GPU内存: 已分配 {allocated / 1024**3:.2f}GB, 已保留 {reserved / 1024**3:.2f}GB")

            if allocated > 1024**3:  # 1GB
                logger.warning(f"⚠️  GPU内存仍占用 {allocated / 1024**3:.2f}GB，可能需要重启")
            else:
                logger.info("✅ GPU内存清理成功")

        except Exception as e:
            logger.error(f"获取GPU内存状态时出错: {e}")

    # CPU内存
    try:
        memory = psutil.virtual_memory()
        current_process = psutil.Process()
        process_memory = current_process.memory_info()

        logger.info(f"系统CPU内存: {memory.used / 1024**3:.2f}GB / {memory.total / 1024**3:.2f}GB ({memory.percent:.1f}%)")
        logger.info(f"当前进程内存: RSS {process_memory.rss / 1024**3:.2f}GB, VMS {process_memory.vms / 1024**3:.2f}GB")

        if memory.percent > 80:
            logger.warning(f"⚠️  系统CPU内存使用率较高: {memory.percent:.1f}%")
        else:
            logger.info("✅ CPU内存使用正常")

    except Exception as e:
        logger.error(f"获取CPU内存状态时出错: {e}")

    # nvidia-smi检查
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Memory-Usage' in line or 'python' in line or 'MiB' in line:
                    if 'MiB' in line and '%' in line:
                        logger.info(f"nvidia-smi: {line.strip()}")
    except Exception as e:
        logger.warning(f"运行nvidia-smi时出错: {e}")

def main():
    """主清理流程"""
    logger.info("开始xformers内存清理流程...")

    # 步骤1: 检查内存泄漏
    logger.info("=== 步骤1: 检查xformers内存泄漏 ===")
    has_leak = check_xformers_memory_leak()

    if has_leak:
        # 步骤2: 终止相关进程
        logger.info("=== 步骤2: 终止xformers相关进程 ===")
        terminate_xformers_processes()
        time.sleep(2)

    # 步骤3: 清理xformers缓存
    logger.info("=== 步骤3: 清理xformers缓存 ===")
    clear_xformers_cache()

    # 步骤4: 清理GPU内存
    logger.info("=== 步骤4: 清理GPU内存 ===")
    clear_gpu_memory_with_xformers()

    # 步骤5: 深度清理PyTorch内存
    logger.info("=== 步骤5: 深度清理PyTorch内存 ===")
    clear_pytorch_memory()

    # 步骤6: 最终状态检查
    logger.info("=== 步骤6: 最终状态检查 ===")
    final_memory_status()

    # 步骤7: 再次检查泄漏
    logger.info("=== 步骤7: 再次检查内存泄漏 ===")
    still_has_leak = check_xformers_memory_leak()

    if still_has_leak:
        logger.warning("⚠️  仍检测到内存泄漏，建议:")
        logger.warning("  1. 重启系统")
        logger.warning("  2. 使用: sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia")
        logger.warning("  3. 使用: sudo modprobe nvidia nvidia_modeset nvidia_drm nvidia_uvm")
    else:
        logger.info("✅ xformers内存清理完成！")

if __name__ == "__main__":
    main()