#!/usr/bin/env python3
"""
强制内存清理脚本

用于处理顽固的GPU内存占用问题。
包括 TensorRT 引擎和其他CUDA内存的强制清理。
"""

import logging
import os
import signal
import subprocess
import time
import torch

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def force_kill_gpu_processes():
    """强制杀死所有GPU相关进程"""
    try:
        # 使用 nvidia-smi 获取GPU进程
        result = subprocess.run(
            ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader,nounits'],
            capture_output=True, text=True
        )

        if result.returncode == 0 and result.stdout.strip():
            logger.info("发现GPU进程:")
            logger.info(result.stdout)

            # 解析进程ID
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 1:
                        try:
                            pid = int(parts[0].strip())
                            process_name = parts[1].strip() if len(parts) > 1 else 'unknown'
                            memory_used = parts[2].strip() if len(parts) > 2 else 'unknown'

                            logger.info(f"强制终止GPU进程: PID={pid}, 名称={process_name}, 内存={memory_used}MB")

                            # 先尝试优雅终止
                            try:
                                os.kill(pid, signal.SIGTERM)
                                time.sleep(2)
                            except ProcessLookupError:
                                logger.info(f"进程 {pid} 已不存在")
                                continue

                            # 检查进程是否还存在
                            try:
                                os.kill(pid, 0)  # 检查进程是否存在
                                # 如果还存在，强制杀死
                                os.kill(pid, signal.SIGKILL)
                                logger.info(f"已强制终止进程 {pid}")
                            except ProcessLookupError:
                                logger.info(f"进程 {pid} 已优雅终止")

                        except (ValueError, ProcessLookupError) as e:
                            logger.warning(f"处理GPU进程时出错: {e}")
        else:
            logger.info("nvidia-smi 未发现GPU计算进程")

    except FileNotFoundError:
        logger.warning("nvidia-smi 命令未找到")
    except Exception as e:
        logger.error(f"获取GPU进程信息时出错: {e}")

def reset_cuda_device():
    """重置CUDA设备"""
    if not torch.cuda.is_available():
        logger.info("CUDA不可用，跳过设备重置")
        return

    try:
        device_count = torch.cuda.device_count()
        logger.info(f"发现 {device_count} 个CUDA设备")

        for device_id in range(device_count):
            try:
                logger.info(f"重置CUDA设备 {device_id}...")

                # 获取设备当前内存状态
                current_device = torch.cuda.device(device_id)
                allocated = torch.cuda.memory_allocated(device_id)
                reserved = torch.cuda.memory_reserved(device_id)

                logger.info(f"设备 {device_id} 当前内存: 已分配 {allocated / 1024**3:.2f}GB, 已保留 {reserved / 1024**3:.2f}GB")

                # 尝试释放内存
                torch.cuda.set_device(device_id)
                torch.cuda.empty_cache()

                # 如果设备有重置功能，尝试重置
                if hasattr(torch.cuda, 'reset'):
                    torch.cuda.reset()
                    logger.info(f"设备 {device_id} 已重置")
                elif hasattr(torch.cuda, 'reset_max_memory_allocated'):
                    torch.cuda.reset_max_memory_allocated(device_id)
                    torch.cuda.reset_max_memory_reserved(device_id)
                    logger.info(f"设备 {device_id} 内存统计已重置")

                # 再次检查内存
                allocated_after = torch.cuda.memory_allocated(device_id)
                reserved_after = torch.cuda.memory_reserved(device_id)

                freed_allocated = (allocated - allocated_after) / 1024**3
                freed_reserved = (reserved - reserved_after) / 1024**3

                logger.info(f"设备 {device_id} 释放后内存: 已分配 {allocated_after / 1024**3:.2f}GB, 已保留 {reserved_after / 1024**3:.2f}GB")
                logger.info(f"设备 {device_id} 释放内存: 已分配 {freed_allocated:.2f}GB, 已保留 {freed_reserved:.2f}GB")

            except Exception as e:
                logger.error(f"重置CUDA设备 {device_id} 时出错: {e}")

        # 最终同步
        torch.cuda.synchronize()
        torch.cuda.empty_cache()

    except Exception as e:
        logger.error(f"重置CUDA设备时出错: {e}")

def clear_tensorrt_engines():
    """清理TensorRT引擎文件"""
    import glob

    engine_paths = [
        "engines",
        "/tmp/engines",
        "/var/tmp/engines",
        os.path.expanduser("~/.cache/torch/engines"),
        "cache/engines"
    ]

    total_engines = 0

    for path in engine_paths:
        if os.path.exists(path):
            logger.info(f"检查TensorRT引擎目录: {path}")
            engine_files = glob.glob(os.path.join(path, "*.engine")) + glob.glob(os.path.join(path, "**/*.engine"), recursive=True)

            if engine_files:
                logger.info(f"发现 {len(engine_files)} 个TensorRT引擎文件在 {path}")

                for engine_file in engine_files:
                    try:
                        file_size = os.path.getsize(engine_file) / 1024**2  # MB
                        logger.info(f"删除TensorRT引擎: {engine_file} ({file_size:.1f}MB)")
                        os.remove(engine_file)
                        total_engines += 1
                    except Exception as e:
                        logger.warning(f"删除TensorRT引擎失败 {engine_file}: {e}")
            else:
                logger.info(f"未发现TensorRT引擎文件在 {path}")

    if total_engines > 0:
        logger.info(f"总共删除了 {total_engines} 个TensorRT引擎文件")
    else:
        logger.info("未发现TensorRT引擎文件需要清理")

def clear_cache_directories():
    """清理各种缓存目录"""
    import shutil

    cache_dirs = [
        "~/.cache/huggingface",
        "~/.cache/torch",
        "~/.cache/transformers",
        "./cache",
        "./__pycache__",
        "./.pytest_cache"
    ]

    for cache_dir in cache_dirs:
        cache_path = os.path.expanduser(cache_dir)
        if os.path.exists(cache_path):
            try:
                # 只清理特定的大文件，不删除整个缓存目录
                total_size = 0
                for root, dirs, files in os.walk(cache_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if file.endswith(('.bin', '.safetensors', '.engine', '.pt', '.pth')):
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            # 只删除大于100MB的模型文件
                            if file_size > 100 * 1024 * 1024:  # 100MB
                                logger.info(f"删除大缓存文件: {file_path} ({file_size / 1024**2:.1f}MB)")
                                os.remove(file_path)

                if total_size > 0:
                    logger.info(f"缓存目录 {cache_dir} 清理了 {total_size / 1024**2:.1f}MB 的大文件")

            except Exception as e:
                logger.warning(f"清理缓存目录 {cache_dir} 时出错: {e}")

def restart_cuda_subsystem():
    """尝试重启CUDA子系统（需要管理员权限）"""
    try:
        logger.info("尝试重载CUDA内核模块...")

        # 这些命令需要管理员权限
        commands = [
            "sudo rmmod nvidia_uvm",
            "sudo rmmod nvidia_drm",
            "sudo rmmod nvidia_modeset",
            "sudo rmmod nvidia",
            "sudo modprobe nvidia",
            "sudo modprobe nvidia_modeset",
            "sudo modprobe nvidia_drm",
            "sudo modprobe nvidia_uvm"
        ]

        for cmd in commands:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"执行成功: {cmd}")
                else:
                    logger.warning(f"执行失败: {cmd} - {result.stderr}")
            except Exception as e:
                logger.warning(f"无法执行 {cmd}: {e}")

        # 等待GPU重新初始化
        time.sleep(5)

        # 检查GPU是否可用
        if torch.cuda.is_available():
            logger.info("CUDA子系统重启成功")
        else:
            logger.error("CUDA子系统重启失败")

    except Exception as e:
        logger.error(f"重启CUDA子系统时出错: {e}")

def main():
    """主函数"""
    logger.info("开始强制内存清理流程...")

    # 1. 强制杀死GPU进程
    logger.info("=== 步骤 1: 强制杀死GPU进程 ===")
    force_kill_gpu_processes()

    # 2. 重置CUDA设备
    logger.info("=== 步骤 2: 重置CUDA设备 ===")
    reset_cuda_device()

    # 3. 清理TensorRT引擎
    logger.info("=== 步骤 3: 清理TensorRT引擎 ===")
    clear_tensorrt_engines()

    # 4. 清理缓存目录
    logger.info("=== 步骤 4: 清理缓存目录 ===")
    clear_cache_directories()

    # 5. 最终垃圾回收
    logger.info("=== 步骤 5: 最终垃圾回收 ===")
    import gc
    for i in range(3):
        collected = gc.collect()
        logger.info(f"垃圾回收 {i+1}: 释放了 {collected} 个对象")
        time.sleep(0.1)

    # 6. 最终CUDA清理
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        logger.info("最终CUDA清理完成")

    # 7. 检查最终状态
    logger.info("=== 最终状态检查 ===")

    # 检查GPU内存
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        total_allocated = 0
        total_reserved = 0

        for device_id in range(device_count):
            allocated = torch.cuda.memory_allocated(device_id)
            reserved = torch.cuda.memory_reserved(device_id)
            total_allocated += allocated
            total_reserved += reserved

            logger.info(f"设备 {device_id}: 已分配 {allocated / 1024**3:.2f}GB, 已保留 {reserved / 1024**3:.2f}GB")

        logger.info(f"总计GPU内存: 已分配 {total_allocated / 1024**3:.2f}GB, 已保留 {total_reserved / 1024**3:.2f}GB")

    # 运行nvidia-smi检查
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("nvidia-smi 状态:")
            # 提取内存使用行
            lines = result.stdout.split('\n')
            for line in lines:
                if 'MiB' in line and ('Memory-Usage' in line or 'python' in line):
                    logger.info(line)
    except Exception as e:
        logger.warning(f"运行nvidia-smi时出错: {e}")

    logger.info("强制内存清理流程完成")

if __name__ == "__main__":
    main()