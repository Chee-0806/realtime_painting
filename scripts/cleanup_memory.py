#!/usr/bin/env python3
"""
内存清理脚本

用于清理 StreamDiffusion 相关的 GPU 和 CPU 内存。
在服务停止后运行此脚本来释放被占用的内存。
"""

import gc
import logging
import os
import psutil
import signal
import time
import torch

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_python_processes():
    """查找与项目相关的Python进程"""
    current_pid = os.getpid()
    python_processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if proc.info['name'] == 'python' and proc.info['pid'] != current_pid:
                cmdline = proc.info['cmdline']
                if cmdline and any(keyword in ' '.join(cmdline) for keyword in [
                    'streamdiffusion', 'realtime_painting', 'uvicorn', 'fastapi'
                ]):
                    python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return python_processes

def terminate_process_gracefully(proc, timeout=10):
    """优雅地终止进程"""
    try:
        pid = proc.info['pid']
        logger.info(f"尝试优雅终止进程 {pid}...")

        # 发送 SIGTERM 信号
        proc.terminate()

        # 等待进程结束
        try:
            proc.wait(timeout=timeout)
            logger.info(f"进程 {pid} 已优雅终止")
            return True
        except psutil.TimeoutExpired:
            logger.warning(f"进程 {pid} 未在 {timeout} 秒内终止，强制杀死")
            proc.kill()
            proc.wait(timeout=5)
            logger.info(f"进程 {pid} 已被强制终止")
            return True

    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.error(f"无法终止进程 {proc.info['pid']}: {e}")
        return False

def clear_gpu_memory():
    """清理 GPU 内存"""
    if not torch.cuda.is_available():
        logger.info("未检测到 CUDA，跳过 GPU 内存清理")
        return

    try:
        logger.info("开始清理 GPU 内存...")

        # 获取初始内存状态
        initial_memory = torch.cuda.memory_allocated()
        initial_reserved = torch.cuda.memory_reserved()
        logger.info(f"初始 GPU 内存: 已分配 {initial_memory / 1024**3:.2f}GB, 已保留 {initial_reserved / 1024**3:.2f}GB")

        # 清理所有 GPU 缓存
        torch.cuda.empty_cache()
        torch.cuda.synchronize()

        # 强制垃圾回收
        gc.collect()

        # 再次清理
        torch.cuda.empty_cache()

        # 获取清理后内存状态
        final_memory = torch.cuda.memory_allocated()
        final_reserved = torch.cuda.memory_reserved()

        logger.info(f"清理后 GPU 内存: 已分配 {final_memory / 1024**3:.2f}GB, 已保留 {final_reserved / 1024**3:.2f}GB")
        logger.info(f"释放内存: 已分配 {(initial_memory - final_memory) / 1024**3:.2f}GB, 已保留 {(initial_reserved - final_reserved) / 1024**3:.2f}GB")

    except Exception as e:
        logger.error(f"清理 GPU 内存时出错: {e}")

def clear_cpu_memory():
    """清理 CPU 内存"""
    try:
        logger.info("开始清理 CPU 内存...")

        # 获取当前进程
        current_process = psutil.Process()

        # 获取清理前内存状态
        memory_before = current_process.memory_info()
        logger.info(f"清理前 CPU 内存: RSS {memory_before.rss / 1024**3:.2f}GB, VMS {memory_before.vms / 1024**3:.2f}GB")

        # 强制垃圾回收
        collected = gc.collect()
        logger.info(f"垃圾回收释放了 {collected} 个对象")

        # 多次垃圾回收以确保彻底清理
        for i in range(3):
            gc.collect()
            time.sleep(0.1)

        # 获取清理后内存状态
        memory_after = current_process.memory_info()
        logger.info(f"清理后 CPU 内存: RSS {memory_after.rss / 1024**3:.2f}GB, VMS {memory_after.vms / 1024**3:.2f}GB")

        freed_memory = (memory_before.rss - memory_after.rss) / 1024**3
        if freed_memory > 0:
            logger.info(f"释放 CPU 内存: {freed_memory:.2f}GB")
        else:
            logger.info("CPU 内存没有明显变化")

    except Exception as e:
        logger.error(f"清理 CPU 内存时出错: {e}")

def kill_zombie_processes():
    """杀死僵尸进程"""
    logger.info("检查并杀死相关进程...")

    processes = find_python_processes()
    if not processes:
        logger.info("未发现相关进程")
        return

    logger.info(f"发现 {len(processes)} 个相关进程")

    for proc in processes:
        cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else 'Unknown'
        logger.info(f"发现进程 {proc.info['pid']}: {cmdline}")

        if not terminate_process_gracefully(proc):
            logger.warning(f"无法终止进程 {proc.info['pid']}")

def main():
    """主函数"""
    logger.info("开始内存清理流程...")

    # 1. 首先尝试优雅地终止相关进程
    kill_zombie_processes()

    # 等待一段时间让进程完全关闭
    time.sleep(2)

    # 2. 清理 GPU 内存
    clear_gpu_memory()

    # 3. 清理 CPU 内存
    clear_cpu_memory()

    # 4. 最终检查
    if torch.cuda.is_available():
        final_gpu_memory = torch.cuda.memory_allocated()
        final_gpu_reserved = torch.cuda.memory_reserved()
        logger.info(f"最终 GPU 内存状态: 已分配 {final_gpu_memory / 1024**3:.2f}GB, 已保留 {final_gpu_reserved / 1024**3:.2f}GB")

    logger.info("内存清理流程完成")

if __name__ == "__main__":
    main()