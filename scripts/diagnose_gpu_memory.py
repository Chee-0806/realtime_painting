#!/usr/bin/env python3
"""
GPU内存诊断脚本

用于诊断GPU内存占用的原因，特别是PyTorch显示为空但nvidia-smi显示占用的情况。
"""

import subprocess
import os
import logging
import glob
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_kernel_modules():
    """检查加载的内核模块"""
    try:
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        modules = []

        for line in result.stdout.split('\n'):
            if 'nvidia' in line.lower() or 'cuda' in line.lower():
                modules.append(line.strip())

        logger.info("相关内核模块:")
        for module in modules:
            logger.info(f"  {module}")

        return modules

    except Exception as e:
        logger.error(f"检查内核模块时出错: {e}")
        return []

def check_tensorrt_engines():
    """检查TensorRT引擎文件"""
    engine_paths = [
        "engines/",
        "/tmp/engines/",
        "/var/tmp/engines/",
        "~/.cache/torch/engines/",
        "~/.cache/tensorrt/",
        "./cache/",
        ".torch/"
    ]

    total_engines = 0
    total_size = 0

    logger.info("检查TensorRT引擎文件...")

    for path in engine_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            logger.info(f"检查目录: {expanded_path}")

            # 查找.engine文件
            engine_files = []
            for pattern in ["*.engine", "**/*.engine"]:
                engine_files.extend(glob.glob(os.path.join(expanded_path, pattern), recursive=True))

            if engine_files:
                logger.info(f"  发现 {len(engine_files)} 个引擎文件:")
                for engine_file in engine_files:
                    try:
                        file_size = os.path.getsize(engine_file)
                        total_size += file_size
                        total_engines += 1
                        logger.info(f"    {engine_file} ({file_size / 1024**2:.1f}MB)")
                    except Exception as e:
                        logger.warning(f"    无法读取 {engine_file}: {e}")
            else:
                logger.info(f"  未发现引擎文件")
        else:
            logger.info(f"  目录不存在: {expanded_path}")

    logger.info(f"总共发现 {total_engines} 个TensorRT引擎文件，总大小 {total_size / 1024**2:.1f}MB")
    return total_engines, total_size

def check_cuda_contexts():
    """检查CUDA上下文"""
    try:
        # 尝试导入pycuda来检查CUDA上下文
        try:
            import pycuda.driver as cuda
            import pycuda.tools

            cuda.init()
            device_count = cuda.Device.count()

            logger.info(f"CUDA设备数量: {device_count}")

            for device_id in range(device_count):
                device = cuda.Device(device_id)
                context = device.make_context()

                try:
                    # 获取内存信息
                    free_mem, total_mem = context.get_memory()
                    used_mem = total_mem - free_mem

                    logger.info(f"设备 {device_id} ({device.name()}):")
                    logger.info(f"  总内存: {total_mem / 1024**2:.1f}MB")
                    logger.info(f"  已使用: {used_mem / 1024**2:.1f}MB")
                    logger.info(f"  可用: {free_mem / 1024**2:.1f}MB")

                    # 检查上下文信息
                    logger.info(f"  上下文信息:")
                    logger.info(f"    API版本: {context.get_api_version()}")

                finally:
                    context.pop()
                    context.detach()

            return True

        except ImportError:
            logger.warning("pycuda未安装，无法检查CUDA上下文")
            return False

    except Exception as e:
        logger.error(f"检查CUDA上下文时出错: {e}")
        return False

def check_process_handles():
    """检查可能持有GPU句柄的进程"""
    try:
        # 使用lsof检查设备文件
        device_files = [
            "/dev/nvidia0",
            "/dev/nvidiactl",
            "/dev/nvidia-uvm",
            "/dev/nvidia-caps"
        ]

        for device_file in device_files:
            if os.path.exists(device_file):
                try:
                    result = subprocess.run(['lsof', device_file], capture_output=True, text=True)
                    if result.stdout.strip():
                        logger.info(f"设备文件 {device_file} 被以下进程使用:")
                        for line in result.stdout.strip().split('\n'):
                            if line.strip():
                                logger.info(f"  {line}")
                    else:
                        logger.info(f"设备文件 {device_file} 未被使用")
                except FileNotFoundError:
                    logger.warning(f"lsof命令未找到，无法检查 {device_file}")
                except Exception as e:
                    logger.warning(f"检查 {device_file} 时出错: {e}")

    except Exception as e:
        logger.error(f"检查进程句柄时出错: {e}")

def check_nvidia_persistence_mode():
    """检查NVIDIA持久化模式"""
    try:
        result = subprocess.run(['nvidia-smi', '-q', '-d', 'PERSISTENCE_MODE'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Persistence Mode' in line:
                    logger.info(f"持久化模式: {line.strip()}")
        else:
            logger.warning("无法查询持久化模式")
    except Exception as e:
        logger.error(f"检查持久化模式时出错: {e}")

def check_driver_version():
    """检查驱动版本信息"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=driver_version', '--format=csv,noheader,nounits'], capture_output=True, text=True)
        if result.returncode == 0:
            versions = result.stdout.strip().split('\n')
            for i, version in enumerate(versions):
                if version.strip():
                    logger.info(f"GPU {i} 驱动版本: {version.strip()}")
    except Exception as e:
        logger.error(f"检查驱动版本时出错: {e}")

def diagnose_memory_leak():
    """诊断内存泄漏原因"""
    logger.info("开始GPU内存诊断...")

    # 1. 检查驱动版本
    logger.info("=== 驱动版本信息 ===")
    check_driver_version()

    # 2. 检查持久化模式
    logger.info("\n=== 持久化模式 ===")
    check_nvidia_persistence_mode()

    # 3. 检查内核模块
    logger.info("\n=== 内核模块 ===")
    check_kernel_modules()

    # 4. 检查TensorRT引擎
    logger.info("\n=== TensorRT引擎 ===")
    total_engines, total_size = check_tensorrt_engines()

    # 5. 检查CUDA上下文
    logger.info("\n=== CUDA上下文 ===")
    has_cuda_contexts = check_cuda_contexts()

    # 6. 检查进程句柄
    logger.info("\n=== 进程句柄 ===")
    check_process_handles()

    # 7. 分析和建议
    logger.info("\n=== 诊断结果和建议 ===")

    if total_engines > 0:
        logger.info(f"⚠️  发现 {total_engines} 个TensorRT引擎文件 ({total_size / 1024**2:.1f}MB)")
        logger.info("💡 建议:")
        logger.info("   1. TensorRT引擎可能持续占用GPU内存")
        logger.info("   2. 运行: python scripts/force_cleanup.py")
        logger.info("   3. 或者手动删除引擎文件")

    if not has_cuda_contexts:
        logger.info("✅ 无活跃的CUDA上下文")
    else:
        logger.info("⚠️  存在活跃的CUDA上下文")

    # 运行最终的nvidia-smi检查
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("\n=== 当前nvidia-smi状态 ===")
            # 提取关键信息
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Memory-Usage' in line or 'python' in line or 'MiB' in line:
                    logger.info(f"  {line}")

                # 查找GPU进程
                if 'Processes:' in line:
                    # 获取接下来的几行
                    process_lines = []
                    for i in range(lines.index(line) + 1, len(lines)):
                        if lines[i].strip():
                            process_lines.append(lines[i].strip())
                        else:
                            break

                    if process_lines:
                        logger.info("  GPU进程:")
                        for process_line in process_lines:
                            logger.info(f"    {process_line}")
                    else:
                        logger.info("  无GPU进程显示")
                        logger.info("  ⚠️  这可能是TensorRT引擎或其他驱动级别的内存占用")

    except Exception as e:
        logger.error(f"最终nvidia-smi检查失败: {e}")

    logger.info("\n诊断完成!")

if __name__ == "__main__":
    diagnose_memory_leak()