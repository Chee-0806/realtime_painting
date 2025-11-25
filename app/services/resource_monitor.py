"""
资源监控和管理服务
用于监控GPU内存、multiprocessing进程，并提供自动清理功能
"""

import os
import signal
import time
import logging
import threading
import asyncio
import psutil
import subprocess
from typing import Dict, List, Optional, Set
from contextlib import contextmanager

import torch


class ResourceMonitor:
    """资源监控器"""

    def __init__(self, check_interval: int = 60, auto_cleanup: bool = False):
        self.check_interval = check_interval
        self.auto_cleanup = auto_cleanup
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._tracked_pids: Set[int] = set()

        # 资源阈值配置
        self.gpu_memory_threshold_gb = 20.0  # GPU内存超过20GB时触发清理
        self.multiprocessing_threshold = 10  # multiprocessing进程数超过10时触发清理
        self.system_memory_threshold_percent = 85.0  # 系统内存使用率超过85%时触发清理

    def start_monitoring(self):
        """启动资源监控"""
        if self._running:
            self.logger.warning("资源监控已在运行中")
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        self.logger.info(f"资源监控已启动，检查间隔: {self.check_interval}秒")

    def stop_monitoring(self):
        """停止资源监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("资源监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                self._check_resources()
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"资源监控过程中发生错误: {e}")
                time.sleep(self.check_interval)

    def _check_resources(self):
        """检查资源使用情况"""
        # 检查GPU内存
        if torch.cuda.is_available():
            gpu_info = self._get_gpu_info()
            if gpu_info:
                memory_usage_percent = (gpu_info['used'] / gpu_info['total']) * 100
                memory_usage_gb = gpu_info['used'] / 1024

                self.logger.debug(f"GPU内存使用: {memory_usage_gb:.2f}GB ({memory_usage_percent:.1f}%)")

                if memory_usage_gb > self.gpu_memory_threshold_gb:
                    self.logger.warning(f"GPU内存使用过高: {memory_usage_gb:.2f}GB > {self.gpu_memory_threshold_gb}GB")
                    if self.auto_cleanup:
                        self._cleanup_gpu_memory()

        # 检查multiprocessing进程
        mp_processes = self._find_multiprocessing_processes()
        mp_count = len(mp_processes)

        if mp_count > 0:
            self.logger.debug(f"发现 {mp_count} 个multiprocessing进程")

        if mp_count > self.multiprocessing_threshold:
            self.logger.warning(f"multiprocessing进程数过多: {mp_count} > {self.multiprocessing_threshold}")
            if self.auto_cleanup:
                self._cleanup_orphaned_processes(mp_processes)

        # 检查系统内存
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        if memory_percent > self.system_memory_threshold_percent:
            self.logger.warning(f"系统内存使用率过高: {memory_percent:.1f}% > {self.system_memory_threshold_percent}%")
            if self.auto_cleanup:
                self._cleanup_system_memory()

    def _get_gpu_info(self) -> Optional[Dict]:
        """获取GPU信息"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.total,memory.used,memory.free',
                 '--format=csv,noheader,nounits'],
                capture_output=True, text=True, check=True
            )

            if result.returncode == 0 and result.stdout.strip():
                total, used, free = map(int, result.stdout.strip().split(', '))
                return {
                    'total': total,  # MB
                    'used': used,     # MB
                    'free': free,     # MB
                }
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

        return None

    def _find_multiprocessing_processes(self) -> List[Dict]:
        """查找multiprocessing进程"""
        mp_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'ppid']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('multiprocessing' in str(arg) for arg in cmdline):
                    mp_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': ' '.join(cmdline),
                        'create_time': proc.info['create_time'],
                        'ppid': proc.info['ppid'],
                        'process_obj': proc
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return mp_processes

    def _cleanup_gpu_memory(self):
        """清理GPU内存"""
        try:
            self.logger.info("开始清理GPU内存...")

            # 获取清理前的状态
            if torch.cuda.is_available():
                before_allocated = torch.cuda.memory_allocated()
                before_reserved = torch.cuda.memory_reserved()

                # 多次清理
                for i in range(5):
                    import gc
                    gc.collect()
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()

                # 获取清理后的状态
                after_allocated = torch.cuda.memory_allocated()
                after_reserved = torch.cuda.memory_reserved()

                freed_allocated = (before_allocated - after_allocated) / 1024**3
                freed_reserved = (before_reserved - after_reserved) / 1024**3

                self.logger.info(f"GPU内存清理完成: 已分配释放 {freed_allocated:.2f}GB, 已保留释放 {freed_reserved:.2f}GB")
                self.logger.info(f"当前GPU内存: 已分配 {after_allocated / 1024**3:.2f}GB, 已保留 {after_reserved / 1024**3:.2f}GB")

        except Exception as e:
            self.logger.error(f"清理GPU内存时出错: {e}")

    def _cleanup_orphaned_processes(self, mp_processes: List[Dict]):
        """清理孤立的multiprocessing进程"""
        try:
            self.logger.info("开始清理孤立的multiprocessing进程...")

            cleaned_count = 0
            for proc_info in mp_processes:
                pid = proc_info['pid']
                ppid = proc_info['ppid']

                # 检查是否是孤立进程（父进程为1或不存在）
                try:
                    parent = psutil.Process(ppid)
                    if parent.pid == 1:  # init进程
                        is_orphaned = True
                        reason = "父进程为init"
                    else:
                        is_orphaned = False
                        reason = "父进程存在"
                except psutil.NoSuchProcess:
                    is_orphaned = True
                    reason = "父进程不存在"

                if is_orphaned:
                    self.logger.info(f"发现孤立进程: PID {pid}, 原因: {reason}")
                    self.logger.debug(f"进程详情: {proc_info['cmdline']}")

                    # 尝试优雅终止
                    try:
                        proc_obj = proc_info['process_obj']
                        memory_info = proc_obj.memory_info()
                        memory_mb = memory_info.rss / 1024 / 1024

                        self.logger.info(f"终止孤立进程: PID {pid}, 内存使用: {memory_mb:.1f}MB")
                        proc_obj.terminate()

                        # 等待进程结束
                        try:
                            proc_obj.wait(timeout=3)
                            cleaned_count += 1
                            self.logger.info(f"进程 {pid} 已优雅终止")
                        except psutil.TimeoutExpired:
                            # 强制杀死
                            proc_obj.kill()
                            cleaned_count += 1
                            self.logger.warning(f"进程 {pid} 已强制终止")

                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        self.logger.warning(f"无法处理进程 {pid}: {e}")

            self.logger.info(f"multiprocessing进程清理完成，共处理 {cleaned_count} 个孤立进程")

        except Exception as e:
            self.logger.error(f"清理multiprocessing进程时出错: {e}")

    def _cleanup_system_memory(self):
        """清理系统内存"""
        try:
            self.logger.info("开始清理系统内存...")

            # Python垃圾回收
            import gc
            collected = gc.collect()
            self.logger.info(f"Python垃圾回收释放了 {collected} 个对象")

            # 清理GPU内存
            if torch.cuda.is_available():
                self._cleanup_gpu_memory()

            # 获取清理后的内存状态
            memory = psutil.virtual_memory()
            self.logger.info(f"系统内存清理后: {memory.percent:.1f}% 使用 ({memory.used / 1024**3:.1f}GB / {memory.total / 1024**3:.1f}GB)")

        except Exception as e:
            self.logger.error(f"清理系统内存时出错: {e}")

    def get_resource_status(self) -> Dict:
        """获取当前资源状态"""
        status = {
            'timestamp': time.time(),
            'gpu': None,
            'multiprocessing': {},
            'system_memory': {}
        }

        # GPU状态
        if torch.cuda.is_available():
            gpu_info = self._get_gpu_info()
            if gpu_info:
                status['gpu'] = {
                    'memory_total_mb': gpu_info['total'],
                    'memory_used_mb': gpu_info['used'],
                    'memory_free_mb': gpu_info['free'],
                    'memory_usage_percent': (gpu_info['used'] / gpu_info['total']) * 100,
                    'memory_usage_gb': gpu_info['used'] / 1024
                }

        # multiprocessing状态
        mp_processes = self._find_multiprocessing_processes()
        status['multiprocessing'] = {
            'total_count': len(mp_processes),
            'orphaned_count': len([p for p in mp_processes if p['ppid'] == 1]),
            'processes': [
                {
                    'pid': p['pid'],
                    'ppid': p['ppid'],
                    'cmdline': p['cmdline']
                } for p in mp_processes[:10]  # 只返回前10个
            ]
        }

        # 系统内存状态
        memory = psutil.virtual_memory()
        status['system_memory'] = {
            'total_gb': memory.total / 1024**3,
            'used_gb': memory.used / 1024**3,
            'available_gb': memory.available / 1024**3,
            'usage_percent': memory.percent
        }

        return status

    def track_pid(self, pid: int):
        """跟踪一个进程ID，用于后续清理"""
        self._tracked_pids.add(pid)
        self.logger.debug(f"开始跟踪进程: PID {pid}")

    def untrack_pid(self, pid: int):
        """取消跟踪进程ID"""
        self._tracked_pids.discard(pid)
        self.logger.debug(f"停止跟踪进程: PID {pid}")

    def cleanup_tracked_processes(self):
        """清理所有被跟踪的进程"""
        if not self._tracked_pids:
            return

        self.logger.info(f"清理 {len(self._tracked_pids)} 个被跟踪的进程...")

        for pid in list(self._tracked_pids):
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    self.logger.info(f"终止跟踪进程: PID {pid}")
                    proc.terminate()
                    proc.wait(timeout=3)
                self.untrack_pid(pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                try:
                    proc.kill()
                    self.untrack_pid(pid)
                except:
                    pass
                self.untrack_pid(pid)


# 全局资源监控器实例
_resource_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """获取全局资源监控器实例"""
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor()
    return _resource_monitor


def start_resource_monitoring(check_interval: int = 60, auto_cleanup: bool = True):
    """启动全局资源监控"""
    monitor = get_resource_monitor()
    monitor.check_interval = check_interval
    monitor.auto_cleanup = auto_cleanup
    monitor.start_monitoring()
    return monitor


def stop_resource_monitoring():
    """停止全局资源监控"""
    monitor = get_resource_monitor()
    monitor.stop_monitoring()


@contextmanager
def managed_resource_cleanup():
    """上下文管理器，确保资源清理"""
    monitor = get_resource_monitor()
    try:
        yield monitor
    finally:
        # 清理被跟踪的进程
        monitor.cleanup_tracked_processes()
        # 最终清理
        monitor._cleanup_gpu_memory()
        monitor._cleanup_system_memory()