#!/usr/bin/env python3
"""
内存监控脚本

用于实时监控GPU和CPU内存使用情况。
"""

import psutil
import torch
import time
import subprocess
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_gpu_memory_info():
    """获取GPU内存信息"""
    if not torch.cuda.is_available():
        return {"available": False}

    try:
        device_count = torch.cuda.device_count()
        gpu_info = {"available": True, "devices": []}

        for device_id in range(device_count):
            allocated = torch.cuda.memory_allocated(device_id)
            reserved = torch.cuda.memory_reserved(device_id)
            total = torch.cuda.get_device_properties(device_id).total_memory

            device_info = {
                "device_id": device_id,
                "name": torch.cuda.get_device_name(device_id),
                "total_gb": total / 1024**3,
                "allocated_gb": allocated / 1024**3,
                "reserved_gb": reserved / 1024**3,
                "free_gb": (total - allocated) / 1024**3,
                "utilization_percent": (allocated / total) * 100
            }

            gpu_info["devices"].append(device_info)

        return gpu_info

    except Exception as e:
        logger.error(f"获取GPU信息时出错: {e}")
        return {"available": False, "error": str(e)}

def get_nvidia_smi_info():
    """获取nvidia-smi信息"""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw', '--format=csv,noheader,nounits'],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            nvidia_info = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 8:
                        nvidia_info.append({
                            "index": int(parts[0]),
                            "name": parts[1],
                            "memory_total_mb": int(parts[2]),
                            "memory_used_mb": int(parts[3]),
                            "memory_free_mb": int(parts[4]),
                            "utilization_percent": int(parts[5]),
                            "temperature_c": int(parts[6]),
                            "power_watts": float(parts[7])
                        })
            return nvidia_info
        else:
            return []

    except Exception as e:
        logger.error(f"获取nvidia-smi信息时出错: {e}")
        return []

def get_cpu_memory_info():
    """获取CPU内存信息"""
    try:
        memory = psutil.virtual_memory()
        current_process = psutil.Process()

        # 系统内存
        system_info = {
            "total_gb": memory.total / 1024**3,
            "available_gb": memory.available / 1024**3,
            "used_gb": memory.used / 1024**3,
            "percent": memory.percent
        }

        # 当前进程内存
        process_memory = current_process.memory_info()
        process_info = {
            "rss_gb": process_memory.rss / 1024**3,  # 物理内存
            "vms_gb": process_memory.vms / 1024**3,  # 虚拟内存
            "percent": current_process.memory_percent()
        }

        return {
            "system": system_info,
            "current_process": process_info
        }

    except Exception as e:
        logger.error(f"获取CPU内存信息时出错: {e}")
        return {}

def find_python_processes():
    """查找Python进程"""
    python_processes = []

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            if proc.info['name'] == 'python':
                cmdline = proc.info['cmdline']
                memory_info = proc.info['memory_info']

                process_info = {
                    "pid": proc.info['pid'],
                    "cmdline": ' '.join(cmdline) if cmdline else '',
                    "rss_gb": memory_info.rss / 1024**3 if memory_info else 0,
                    "vms_gb": memory_info.vms / 1024**3 if memory_info else 0,
                    "cpu_percent": proc.info['cpu_percent'] if proc.info['cpu_percent'] else 0
                }

                # 标记相关进程
                if cmdline and any(keyword in ' '.join(cmdline) for keyword in [
                    'streamdiffusion', 'realtime_painting', 'uvicorn', 'fastapi'
                ]):
                    process_info["relevant"] = True
                else:
                    process_info["relevant"] = False

                python_processes.append(process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return python_processes

def format_memory_info():
    """格式化内存信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # GPU信息
    gpu_info = get_gpu_memory_info()
    nvidia_info = get_nvidia_smi_info()

    # CPU信息
    cpu_info = get_cpu_memory_info()
    python_processes = find_python_processes()

    # 打印报告
    print(f"\n{'='*80}")
    print(f"内存监控报告 - {timestamp}")
    print(f"{'='*80}")

    # GPU部分
    print(f"\n🎮 GPU 内存状态:")
    if gpu_info.get("available"):
        for device in gpu_info["devices"]:
            print(f"  设备 {device['device_id']}: {device['name']}")
            print(f"    总内存: {device['total_gb']:.2f}GB")
            print(f"    已分配: {device['allocated_gb']:.2f}GB ({device['utilization_percent']:.1f}%)")
            print(f"    已保留: {device['reserved_gb']:.2f}GB")
            print(f"    可用: {device['free_gb']:.2f}GB")

    # nvidia-smi信息
    if nvidia_info:
        print(f"\n📊 nvidia-smi 详细信息:")
        for gpu in nvidia_info:
            print(f"  GPU {gpu['index']}: {gpu['name']}")
            print(f"    内存: {gpu['memory_used_mb']}/{gpu['memory_total_mb']}MB ({gpu['memory_used_mb']/gpu['memory_total_mb']*100:.1f}%)")
            print(f"    利用率: {gpu['utilization_percent']}%")
            print(f"    温度: {gpu['temperature_c']}°C")
            print(f"    功耗: {gpu['power_watts']:.1f}W")

    # CPU部分
    print(f"\n💻 CPU 内存状态:")
    if cpu_info.get("system"):
        system = cpu_info["system"]
        print(f"  系统总内存: {system['total_gb']:.2f}GB")
        print(f"  已使用: {system['used_gb']:.2f}GB ({system['percent']:.1f}%)")
        print(f"  可用: {system['available_gb']:.2f}GB")

    if cpu_info.get("current_process"):
        process = cpu_info["current_process"]
        print(f"  当前进程内存:")
        print(f"    物理内存(RSS): {process['rss_gb']:.2f}GB ({process['percent']:.1f}%)")
        print(f"    虚拟内存(VMS): {process['vms_gb']:.2f}GB")

    # Python进程
    relevant_processes = [p for p in python_processes if p.get("relevant")]
    other_processes = [p for p in python_processes if not p.get("relevant")]

    print(f"\n🐍 Python 进程:")
    if relevant_processes:
        print(f"  相关进程 ({len(relevant_processes)}):")
        for proc in relevant_processes:
            print(f"    PID {proc['pid']}: {proc['rss_gb']:.2f}GB, {proc['cpu_percent']:.1f}% CPU")
            print(f"      {proc['cmdline'][:80]}...")

    if other_processes:
        print(f"  其他Python进程 ({len(other_processes)}):")
        for proc in other_processes[:5]:  # 只显示前5个
            print(f"    PID {proc['pid']}: {proc['rss_gb']:.2f}GB")
        if len(other_processes) > 5:
            print(f"    ... 还有 {len(other_processes) - 5} 个进程")

    # 内存使用建议
    print(f"\n💡 内存使用分析:")

    # GPU内存分析
    if gpu_info.get("available"):
        total_gpu_allocated = sum(device["allocated_gb"] for device in gpu_info["devices"])
        total_gpu_reserved = sum(device["reserved_gb"] for device in gpu_info["devices"])

        if total_gpu_allocated > 10:
            print(f"  ⚠️  GPU内存使用较高 ({total_gpu_allocated:.1f}GB)，建议检查是否有内存泄漏")
        elif total_gpu_allocated > 5:
            print(f"  🔶 GPU内存使用中等 ({total_gpu_allocated:.1f}GB)")
        else:
            print(f"  ✅ GPU内存使用正常 ({total_gpu_allocated:.1f}GB)")

        if total_gpu_reserved > total_gpu_allocated * 1.2:
            print(f"  ⚠️  GPU保留内存较多 ({total_gpu_reserved:.1f}GB)，建议运行 torch.cuda.empty_cache()")

    # CPU内存分析
    if cpu_info.get("system") and cpu_info["system"]["percent"] > 80:
        print(f"  ⚠️  系统CPU内存使用率较高 ({cpu_info['system']['percent']:.1f}%)")
    elif cpu_info.get("current_process") and cpu_info["current_process"]["rss_gb"] > 2:
        print(f"  ⚠️  当前进程CPU内存使用较高 ({cpu_info['current_process']['rss_gb']:.1f}GB)")

    # 进程分析
    total_python_memory = sum(p["rss_gb"] for p in relevant_processes)
    if total_python_memory > 8:
        print(f"  ⚠️  Python相关进程总内存使用较高 ({total_python_memory:.1f}GB)")

def monitor_continuous(interval_seconds=10, max_iterations=60):
    """持续监控"""
    print(f"开始持续监控，每 {interval_seconds} 秒更新一次，最多 {max_iterations} 次")
    print("按 Ctrl+C 停止监控")

    try:
        for i in range(max_iterations):
            format_memory_info()
            if i < max_iterations - 1:  # 最后一次不需要等待
                time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n监控已停止")

def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        max_iter = int(sys.argv[3]) if len(sys.argv) > 3 else 60
        monitor_continuous(interval, max_iter)
    else:
        format_memory_info()

if __name__ == "__main__":
    main()