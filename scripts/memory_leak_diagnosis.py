#!/usr/bin/env python3
"""
内存和显存泄漏诊断脚本
用于分析系统中进程、内存和GPU资源的使用情况，找出潜在的资源泄漏问题
"""

import os
import sys
import time
import subprocess
import psutil
import logging
from typing import Dict, List, Optional
import json

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResourceLeakDetector:
    """资源泄漏检测器"""

    def __init__(self):
        self.process_snapshots = []
        self.gpu_snapshots = []

    def get_process_info(self) -> Dict:
        """获取当前进程信息"""
        try:
            # 获取Python进程信息
            python_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
                try:
                    if 'python' in proc.info['name'].lower():
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent'],
                            'memory_rss': proc.info['memory_info'].rss / 1024 / 1024,  # MB
                            'memory_vms': proc.info['memory_info'].vms / 1024 / 1024,  # MB
                            'cmdline': ' '.join(proc.cmdline()) if proc.cmdline() else 'N/A'
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # 获取系统总内存信息
            memory = psutil.virtual_memory()

            return {
                'timestamp': time.time(),
                'python_processes': python_processes,
                'system_memory': {
                    'total': memory.total / 1024 / 1024 / 1024,  # GB
                    'available': memory.available / 1024 / 1024 / 1024,  # GB
                    'used': memory.used / 1024 / 1024 / 1024,  # GB
                    'percent': memory.percent
                }
            }
        except Exception as e:
            logger.error(f"获取进程信息失败: {e}")
            return {}

    def get_gpu_info(self) -> Dict:
        """获取GPU信息"""
        try:
            # 使用nvidia-smi获取GPU信息
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, check=True
            )

            gpu_info = {}
            for i, line in enumerate(result.stdout.strip().split('\n')):
                if line.strip():
                    parts = [p.strip() for p in line.split(',')]
                    gpu_info[f'gpu_{i}'] = {
                        'name': parts[0],
                        'memory_total': int(parts[1]),  # MB
                        'memory_used': int(parts[2]),  # MB
                        'memory_free': int(parts[3]),  # MB
                        'utilization': int(parts[4]),  # %
                        'temperature': int(parts[5])  # °C
                    }

            # 获取进程信息
            try:
                result_processes = subprocess.run(
                    ['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                     '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, check=True
                )

                processes = []
                for line in result_processes.stdout.strip().split('\n'):
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        processes.append({
                            'pid': int(parts[0]),
                            'process_name': parts[1],
                            'used_memory': int(parts[2])  # MB
                        })

                gpu_info['processes'] = processes
            except subprocess.CalledProcessError:
                gpu_info['processes'] = []

            return {
                'timestamp': time.time(),
                'gpu_info': gpu_info
            }
        except subprocess.CalledProcessError as e:
            logger.warning(f"获取GPU信息失败: {e}")
            return {}
        except FileNotFoundError:
            logger.warning("nvidia-smi 命令未找到，可能没有NVIDIA GPU")
            return {}

    def analyze_python_multiprocessing(self) -> Dict:
        """分析Python多进程情况"""
        try:
            # 查找multiprocessing相关的进程
            result = subprocess.run(
                ['ps', 'aux'], capture_output=True, text=True
            )

            multiprocessing_processes = []
            for line in result.stdout.split('\n'):
                if 'multiprocessing' in line or 'spawn_main' in line or 'resource_tracker' in line:
                    parts = line.split()
                    if len(parts) >= 11:
                        multiprocessing_processes.append({
                            'user': parts[0],
                            'pid': parts[1],
                            'cpu': parts[2],
                            'mem': parts[3],
                            'command': ' '.join(parts[10:])
                        })

            return {
                'multiprocessing_processes': multiprocessing_processes,
                'total_count': len(multiprocessing_processes)
            }
        except Exception as e:
            logger.error(f"分析多进程失败: {e}")
            return {}

    def detect_leak_patterns(self) -> Dict:
        """检测泄漏模式"""
        leak_analysis = {
            'potential_leaks': [],
            'warnings': [],
            'recommendations': []
        }

        # 分析多进程情况
        mp_analysis = self.analyze_python_multiprocessing()
        if mp_analysis.get('total_count', 0) > 10:
            leak_analysis['warnings'].append(f"检测到大量多进程: {mp_analysis['total_count']} 个")
            leak_analysis['recommendations'].append("检查是否有未正确清理的multiprocessing进程")

        # 分析Python进程内存使用
        process_info = self.get_process_info()
        for proc in process_info.get('python_processes', []):
            if proc['memory_rss'] > 2000:  # 超过2GB
                leak_analysis['potential_leaks'].append(
                    f"高内存进程: PID {proc['pid']} ({proc['name']}) - {proc['memory_rss']:.1f}MB"
                )

        # 分析GPU显存使用
        gpu_info = self.get_gpu_info()
        for gpu_key, gpu_data in gpu_info.get('gpu_info', {}).items():
            if gpu_key.startswith('gpu_'):
                memory_usage_percent = (gpu_data['memory_used'] / gpu_data['memory_total']) * 100
                if memory_usage_percent > 80:
                    leak_analysis['warnings'].append(
                        f"GPU {gpu_key} 显存使用率过高: {memory_usage_percent:.1f}%"
                    )

                # 检查是否有僵尸GPU进程
                gpu_processes = gpu_info.get('processes', [])
                if len(gpu_processes) == 0 and gpu_data['memory_used'] > 1000:  # 没有进程但显存被占用
                    leak_analysis['potential_leaks'].append(
                        f"GPU {gpu_key} 可能有显存泄漏: {gpu_data['memory_used']}MB 被占用但没有活跃进程"
                    )

        return leak_analysis

    def generate_report(self) -> str:
        """生成诊断报告"""
        report_lines = [
            "=" * 80,
            "内存和显存泄漏诊断报告",
            f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            ""
        ]

        # 进程信息
        process_info = self.get_process_info()
        report_lines.extend([
            "📊 系统进程信息",
            "-" * 40,
            f"系统内存使用: {process_info.get('system_memory', {}).get('used', 0):.1f}GB / {process_info.get('system_memory', {}).get('total', 0):.1f}GB ({process_info.get('system_memory', {}).get('percent', 0):.1f}%)",
            f"Python进程数量: {len(process_info.get('python_processes', []))}",
            ""
        ])

        # 高内存进程
        high_memory_processes = [p for p in process_info.get('python_processes', []) if p['memory_rss'] > 1000]
        if high_memory_processes:
            report_lines.extend([
                "🔴 高内存使用进程 (>1GB):",
                "-" * 40
            ])
            for proc in high_memory_processes[:5]:  # 只显示前5个
                report_lines.append(f"  PID {proc['pid']:>8}: {proc['memory_rss']:.1f}MB ({proc['memory_percent']:.1f}%) - {proc['cmdline'][:80]}")
            report_lines.append("")

        # GPU信息
        gpu_info = self.get_gpu_info()
        if gpu_info.get('gpu_info'):
            report_lines.extend([
                "🎮 GPU信息",
                "-" * 40
            ])
            for gpu_key, gpu_data in gpu_info.get('gpu_info', {}).items():
                if gpu_key.startswith('gpu_'):
                    memory_usage_percent = (gpu_data['memory_used'] / gpu_data['memory_total']) * 100
                    report_lines.extend([
                        f"  {gpu_key.upper()}: {gpu_data['name']}",
                        f"    显存: {gpu_data['memory_used']}MB / {gpu_data['memory_total']}MB ({memory_usage_percent:.1f}%)",
                        f"    利用率: {gpu_data['utilization']}%, 温度: {gpu_data['temperature']}°C"
                    ])

            gpu_processes = gpu_info.get('processes', [])
            if gpu_processes:
                report_lines.extend([
                    "",
                    "  GPU进程:",
                ])
                for proc in gpu_processes:
                    report_lines.append(f"    PID {proc['pid']}: {proc['process_name']} ({proc['used_memory']}MB)")
            report_lines.append("")

        # 多进程分析
        mp_analysis = self.analyze_python_multiprocessing()
        if mp_analysis.get('total_count', 0) > 0:
            report_lines.extend([
                "🔄 多进程分析",
                "-" * 40,
                f"Multiprocessing进程总数: {mp_analysis['total_count']}",
                ""
            ])

            if mp_analysis.get('multiprocessing_processes'):
                report_lines.extend(["进程详情:"])
                for proc in mp_analysis['multiprocessing_processes'][:10]:  # 只显示前10个
                    report_lines.append(f"  {proc['pid']:>8} {proc['cpu']:>5}% {proc['mem']:>5}% {proc['command'][:60]}")
                report_lines.append("")

        # 泄漏检测
        leak_analysis = self.detect_leak_patterns()
        report_lines.extend([
            "🚨 泄漏检测分析",
            "-" * 40
        ])

        if leak_analysis['potential_leaks']:
            report_lines.extend([
                "⚠️  潜在泄漏:",
                *[f"  - {leak}" for leak in leak_analysis['potential_leaks']],
                ""
            ])

        if leak_analysis['warnings']:
            report_lines.extend([
                "⚡ 警告:",
                *[f"  - {warning}" for warning in leak_analysis['warnings']],
                ""
            ])

        if leak_analysis['recommendations']:
            report_lines.extend([
                "💡 建议:",
                *[f"  - {rec}" for rec in leak_analysis['recommendations']],
                ""
            ])

        # 修复建议
        report_lines.extend([
            "🔧 修复建议",
            "-" * 40,
            "1. 检查Python应用中的资源清理逻辑",
            "2. 确保所有GPU模型和tensor在使用后被正确释放",
            "3. 检查multiprocessing进程是否正确join()和terminate()",
            "4. 考虑使用torch.cuda.empty_cache()定期清理GPU缓存",
            "5. 监控长时间运行应用的内存增长趋势",
            ""
        ])

        return "\n".join(report_lines)

    def save_report(self, filename: str = None) -> str:
        """保存报告到文件"""
        if filename is None:
            filename = f"/tmp/memory_leak_report_{int(time.time())}.txt"

        report = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"诊断报告已保存到: {filename}")
        return filename

def main():
    """主函数"""
    logger.info("开始内存和显存泄漏诊断...")

    detector = ResourceLeakDetector()

    # 生成并保存报告
    report_file = detector.save_report()

    # 打印报告到控制台
    report_content = detector.generate_report()
    print(report_content)

    logger.info("诊断完成")

if __name__ == "__main__":
    main()