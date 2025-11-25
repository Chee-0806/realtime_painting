#!/usr/bin/env python3
"""
强制Xformers内存清理脚本

绕过自检测，强制清理xformers相关内存。
"""

import gc
import logging
import os
import signal
import subprocess
import time
import torch
import psutil
import sys

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_current_pid():
    """获取当前进程ID"""
    return os.getpid()

def find_other_xformers_processes():
    """查找其他xformers相关进程"""
    current_pid = get_current_pid()
    other_processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            if proc.info['pid'] == current_pid:
                continue  # 跳过当前进程

            if proc.info['name'] == 'python':
                cmdline = proc.info['cmdline']
                memory_info = proc.info['memory_info']

                if cmdline and any(keyword in ' '.join(cmdline) for keyword in [
                    'streamdiffusion', 'realtime_painting', 'uvicorn', 'fastapi'
                ]):
                    process_info = {
                        'pid': proc.info['pid'],
                        'cmdline': ' '.join(cmdline) if cmdline else '',
                        'rss_gb': memory_info.rss / 1024**3 if memory_info else 0,
                        'vms_gb': memory_info.vms / 1024**3 if memory_info else 0,
                        'cpu_percent': proc.info['cpu_percent'] if proc.info['cpu_percent'] else 0
                    }
                    other_processes.append(process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return other_processes

def force_terminate_processes():
    """强制终止其他相关进程"""
    processes = find_other_xformers_processes()

    if not processes:
        logger.info("未发现其他xformers相关进程")
        return 0

    logger.info(f"发现 {len(processes)} 个其他xformers相关进程，准备强制终止:")

    total_freed = 0
    for proc in processes:
        logger.info(f"  PID {proc['pid']}: {proc['rss_gb']:.2f}GB - {proc['cmdline'][:80]}...")

        try:
            # 直接发送SIGKILL，强制终止
            os.kill(proc['pid'], signal.SIGKILL)
            total_freed += proc['rss_gb']
            logger.info(f"    ✓ 已强制终止，释放 {proc['rss_gb']:.2f}GB")
            time.sleep(1)  # 等待进程完全结束
        except (ProcessLookupError, PermissionError) as e:
            logger.warning(f"    ✗ 无法终止 PID {proc['pid']}: {e}")

    return total_freed

def aggressive_gpu_cleanup():
    """激进式GPU内存清理"""
    if not torch.cuda.is_available():
        logger.info("CUDA不可用，跳过GPU内存清理")
        return 0

    try:
        logger.info("开始激进式GPU内存清理...")

        device_count = torch.cuda.device_count()
        total_freed = 0

        for device_id in range(device_count):
            logger.info(f"清理设备 {device_id}...")

            # 获取清理前状态
            torch.cuda.set_device(device_id)
            before_allocated = torch.cuda.memory_allocated(device_id)
            before_reserved = torch.cuda.memory_reserved(device_id)

            logger.info(f"  清理前: 已分配 {before_allocated / 1024**3:.2f}GB, 已保留 {before_reserved / 1024**3:.2f}GB")

            # 激进清理策略
            for round_num in range(5):
                # 1. 空缓存
                torch.cuda.empty_cache()

                # 2. 同步
                torch.cuda.synchronize()

                # 3. 垃圾回收
                collected = gc.collect()

                # 4. 再次空缓存
                torch.cuda.empty_cache()

                if round_num == 0:
                    logger.info(f"    第1轮清理: 回收 {collected} 个对象")

                time.sleep(0.1)

            # 获取清理后状态
            after_allocated = torch.cuda.memory_allocated(device_id)
            after_reserved = torch.cuda.memory_reserved(device_id)

            freed_allocated = (before_allocated - after_allocated) / 1024**3
            freed_reserved = (before_reserved - after_reserved) / 1024**3

            total_freed += freed_allocated

            logger.info(f"  清理后: 已分配 {after_allocated / 1024**3:.2f}GB, 已保留 {after_reserved / 1024**3:.2f}GB")
            logger.info(f"  释放: 已分配 {freed_allocated:.2f}GB, 已保留 {freed_reserved:.2f}GB")

        # 重置到设备0
        if device_count > 0:
            torch.cuda.set_device(0)

        # 最终全局清理
        for i in range(3):
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            gc.collect()
            time.sleep(0.1)

        logger.info(f"激进GPU清理完成，总计释放 {total_freed:.2f}GB")
        return total_freed

    except Exception as e:
        logger.error(f"激进GPU清理时出错: {e}")
        return 0

def aggressive_cpu_cleanup():
    """激进式CPU内存清理"""
    try:
        logger.info("开始激进式CPU内存清理...")

        # 获取当前进程
        current_process = psutil.Process()
        before_memory = current_process.memory_info()

        logger.info(f"清理前: RSS {before_memory.rss / 1024**3:.2f}GB, VMS {before_memory.vms / 1024**3:.2f}GB")

        # 多轮激进垃圾回收
        total_collected = 0
        for round_num in range(10):
            collected = gc.collect()
            total_collected += collected

            if round_num == 0:
                logger.info(f"第1轮: 回收 {collected} 个对象")
            elif round_num % 3 == 0:
                logger.info(f"第{round_num+1}轮: 回收 {collected} 个对象")

            # 清理特定模块缓存
            if round_num == 5:
                try:
                    # 清理torch相关模块
                    if hasattr(torch, '_C'):
                        del torch._C
                    if hasattr(torch, 'storage'):
                        del torch.storage
                except:
                    pass

            time.sleep(0.1)

        # 获取清理后内存
        after_memory = current_process.memory_info()
        freed_rss = (before_memory.rss - after_memory.rss) / 1024**3
        freed_vms = (before_memory.vms - after_memory.vms) / 1024**3

        logger.info(f"清理后: RSS {after_memory.rss / 1024**3:.2f}GB, VMS {after_memory.vms / 1024**3:.2f}GB")
        logger.info(f"释放: RSS {freed_rss:.2f}GB, VMS {freed_vms:.2f}GB")
        logger.info(f"总计回收 {total_collected} 个对象")

        return freed_rss

    except Exception as e:
        logger.error(f"激进CPU清理时出错: {e}")
        return 0

def clear_system_caches():
    """清理系统级缓存"""
    try:
        logger.info("清理系统级缓存...")

        # 清理Python模块缓存
        import sys
        if hasattr(sys, 'modules'):
            modules_to_remove = []
            for module_name in sys.modules:
                if any(name in module_name.lower() for name in [
                    'streamdiffusion', 'xformers', 'diffusers', 'transformers'
                ]):
                    modules_to_remove.append(module_name)

            for module_name in modules_to_remove:
                try:
                    del sys.modules[module_name]
                except:
                    pass

            logger.info(f"清理了 {len(modules_to_remove)} 个Python模块缓存")

        # 清理目录缓存
        cache_dirs = [
            "./__pycache__",
            "./build",
            "./dist",
            "./.pytest_cache",
            "./temp",
            "./tmp"
        ]

        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                try:
                    import shutil
                    shutil.rmtree(cache_dir)
                    logger.info(f"删除缓存目录: {cache_dir}")
                except Exception as e:
                    logger.warning(f"无法删除 {cache_dir}: {e}")

    except Exception as e:
        logger.error(f"清理系统缓存时出错: {e}")

def check_gpu_status():
    """检查GPU状态"""
    logger.info("=== GPU状态检查 ===")

    try:
        # PyTorch状态
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            logger.info(f"PyTorch: {device_count} 个CUDA设备")

            for device_id in range(device_count):
                allocated = torch.cuda.memory_allocated(device_id)
                reserved = torch.cuda.memory_reserved(device_id)
                logger.info(f"  设备 {device_id}: 已分配 {allocated / 1024**3:.3f}GB, 已保留 {reserved / 1024**3:.3f}GB")
        else:
            logger.info("PyTorch: CUDA不可用")

        # nvidia-smi状态
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Memory-Usage' in line or 'MiB' in line:
                        logger.info(f"nvidia-smi: {line.strip()}")
                    if 'Processes:' in line:
                        # 检查是否有进程行
                        process_lines = []
                        for i in range(lines.index(line) + 1, len(lines)):
                            if lines[i].strip():
                                process_lines.append(lines[i].strip())
                            else:
                                break
                        if process_lines:
                            logger.info("GPU进程:")
                            for process_line in process_lines:
                                logger.info(f"  {process_line}")
                        else:
                            logger.info("无GPU进程显示")
            else:
                logger.warning("nvidia-smi执行失败")
        except Exception as e:
            logger.error(f"执行nvidia-smi时出错: {e}")

    except Exception as e:
        logger.error(f"检查GPU状态时出错: {e}")

def main():
    """主清理流程"""
    logger.info("开始强制Xformers内存清理...")

    # 步骤1: 强制终止其他进程
    logger.info("=== 步骤1: 强制终止其他进程 ===")
    process_freed = force_terminate_processes()

    # 步骤2: 激进GPU清理
    logger.info("=== 步骤2: 激进GPU内存清理 ===")
    gpu_freed = aggressive_gpu_cleanup()

    # 步骤3: 激进CPU清理
    logger.info("=== 步骤3: 激进CPU内存清理 ===")
    cpu_freed = aggressive_cpu_cleanup()

    # 步骤4: 清理系统缓存
    logger.info("=== 步骤4: 清理系统缓存 ===")
    clear_system_caches()

    # 步骤5: 最终状态检查
    logger.info("=== 步骤5: 最终状态检查 ===")
    check_gpu_status()

    # 总结
    logger.info("=== 清理总结 ===")
    logger.info(f"进程内存释放: {process_freed:.2f}GB")
    logger.info(f"GPU内存释放: {gpu_freed:.2f}GB")
    logger.info(f"CPU内存释放: {cpu_freed:.2f}GB")

    if gpu_freed < 0.1:  # 如果释放少于100MB
        logger.warning("⚠️ GPU内存释放较少，可能需要:")
        logger.warning("  1. 重启系统")
        logger.warning("  2. 运行: sudo rmmod nvidia_uvm nvidia_drm nvidia_modeset nvidia")
        logger.warning("  3. 运行: sudo modprobe nvidia nvidia_modeset nvidia_drm nvidia_uvm")
    else:
        logger.info("✅ 内存清理成功！")

if __name__ == "__main__":
    main()