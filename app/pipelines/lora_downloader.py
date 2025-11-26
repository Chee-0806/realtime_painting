"""
LoRA 下载管理器
支持预制LoRA模型的下载、进度跟踪和管理
"""

import asyncio
import logging
import os
import yaml
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib


@dataclass
class LoRAPreset:
    """LoRA预设数据类"""
    id: str
    name: str
    description: str
    mirrors: List[Dict[str, str]]
    filename: str
    size: str
    model_type: str
    compatible_models: List[str]
    tags: List[str]
    preview_image: str = ""


@dataclass
class DownloadTask:
    """下载任务数据类"""
    preset_id: str
    url: str
    filename: str
    total_size: int = 0
    downloaded_size: int = 0
    status: str = "pending"  # pending, downloading, completed, failed, cancelled
    progress: float = 0.0
    speed: float = 0.0  # KB/s
    error_message: str = ""
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class LoRADownloader:
    """LoRA下载管理器"""

    def __init__(self, lora_dir: Optional[Path] = None, presets_file: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.lora_dir = lora_dir or Path(__file__).resolve().parent.parent / "lib" / "StreamDiffusion" / "models" / "LoRA"
        self.presets_file = presets_file or Path(__file__).resolve().parent / "presets.yaml"

        # 确保目录存在
        self.lora_dir.mkdir(parents=True, exist_ok=True)

        # 下载任务管理
        self.download_tasks: Dict[str, DownloadTask] = {}
        self.active_downloads: Dict[str, asyncio.Task] = {}

        # 预设数据
        self.presets: Dict[str, LoRAPreset] = {}
        self.load_presets()

        # 下载统计信息
        self.download_stats_file = self.lora_dir / ".download_stats.json"
        self.stats: Dict[str, Any] = {}
        self.load_stats()

    def load_presets(self):
        """加载LoRA预设配置"""
        try:
            if not self.presets_file.exists():
                self.logger.warning(f"预设文件不存在: {self.presets_file}")
                return

            with open(self.presets_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'presets' not in data:
                self.logger.error("预设文件格式错误")
                return

            for preset_data in data['presets']:
                preset = LoRAPreset(**preset_data)
                self.presets[preset.id] = preset

            self.logger.info(f"加载了 {len(self.presets)} 个LoRA预设")

        except Exception as e:
            self.logger.error(f"加载预设配置失败: {e}")

    def load_stats(self):
        """加载下载统计信息"""
        try:
            if self.download_stats_file.exists():
                import json
                with open(self.download_stats_file, 'r', encoding='utf-8') as f:
                    self.stats = json.load(f)
        except Exception as e:
            self.logger.error(f"加载统计信息失败: {e}")
            self.stats = {}

    def save_stats(self):
        """保存下载统计信息"""
        try:
            import json
            with open(self.download_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"保存统计信息失败: {e}")

    def get_available_presets(self) -> List[LoRAPreset]:
        """获取所有可用的预设"""
        return list(self.presets.values())

    def get_preset_by_id(self, preset_id: str) -> Optional[LoRAPreset]:
        """根据ID获取预设"""
        return self.presets.get(preset_id)

    def is_preset_downloaded(self, preset_id: str) -> bool:
        """检查预设是否已下载"""
        preset = self.get_preset_by_id(preset_id)
        if not preset:
            return False

        file_path = self.lora_dir / preset.filename
        return file_path.exists() and file_path.stat().st_size > 0

    def get_download_task(self, preset_id: str) -> Optional[DownloadTask]:
        """获取下载任务"""
        return self.download_tasks.get(preset_id)

    def get_all_download_tasks(self) -> List[DownloadTask]:
        """获取所有下载任务"""
        return list(self.download_tasks.values())

    async def start_download(self, preset_id: str, mirror_index: int = 0) -> bool:
        """开始下载LoRA"""
        preset = self.get_preset_by_id(preset_id)
        if not preset:
            self.logger.error(f"未找到预设: {preset_id}")
            return False

        if mirror_index >= len(preset.mirrors):
            self.logger.error(f"镜像索引超出范围: {mirror_index}")
            return False

        mirror = preset.mirrors[mirror_index]
        url = mirror['url']

        # 检查是否已在下载
        if preset_id in self.active_downloads:
            self.logger.info(f"预设 {preset_id} 正在下载中")
            return False

        # 检查文件是否已存在
        file_path = self.lora_dir / preset.filename
        if file_path.exists():
            # 验证文件完整性
            if self._verify_file_integrity(file_path):
                self.logger.info(f"预设 {preset_id} 已存在且完整")
                return True
            else:
                self.logger.warning(f"预设 {preset_id} 文件损坏，重新下载")
                file_path.unlink()

        # 创建下载任务
        task = DownloadTask(
            preset_id=preset_id,
            url=url,
            filename=preset.filename
        )
        self.download_tasks[preset_id] = task

        # 启动下载协程
        download_coroutine = self._download_file(task)
        download_task = asyncio.create_task(download_coroutine)
        self.active_downloads[preset_id] = download_task

        self.logger.info(f"开始下载预设 {preset_id} 从镜像 {mirror.get('name', url)}")
        return True

    async def _download_file(self, task: DownloadTask):
        """下载文件的内部实现"""
        try:
            task.status = "downloading"
            file_path = self.lora_dir / task.filename
            temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")

            # 设置超时和连接池
            timeout = aiohttp.ClientTimeout(total=300, connect=30)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)

            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.get(task.url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {response.reason}")

                    task.total_size = int(response.headers.get('content-length', 0))
                    task.status = "downloading"

                    # 记录开始时间用于计算速度
                    start_time = datetime.now()
                    last_update_time = start_time
                    last_downloaded_size = 0

                    async with aiofiles.open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if task.status == "cancelled":
                                return

                            await f.write(chunk)
                            task.downloaded_size += len(chunk)

                            # 更新进度和速度
                            now = datetime.now()
                            time_diff = (now - last_update_time).total_seconds()

                            if time_diff >= 1.0:  # 每秒更新一次速度
                                downloaded_diff = task.downloaded_size - last_downloaded_size
                                task.speed = downloaded_diff / time_diff / 1024  # KB/s
                                last_update_time = now
                                last_downloaded_size = task.downloaded_size

                            # 计算进度
                            if task.total_size > 0:
                                task.progress = (task.downloaded_size / task.total_size) * 100
                            else:
                                task.progress = min(task.downloaded_size / (1024 * 1024), 100)  # 默认按MB估算

                            task.updated_at = now

            # 下载完成，重命名临时文件
            temp_path.rename(file_path)

            # 验证文件完整性
            if self._verify_file_integrity(file_path):
                task.status = "completed"
                task.progress = 100.0
                task.speed = 0.0

                # 更新统计信息
                self._update_download_stats(task)

                self.logger.info(f"预设 {task.preset_id} 下载完成")
            else:
                file_path.unlink()
                raise Exception("文件完整性验证失败")

        except asyncio.CancelledError:
            task.status = "cancelled"
            self.logger.info(f"预设 {task.preset_id} 下载已取消")
        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            self.logger.error(f"下载预设 {task.preset_id} 失败: {e}")

            # 清理临时文件
            temp_path = self.lora_dir / f"{task.filename}.tmp"
            if temp_path.exists():
                temp_path.unlink()
        finally:
            # 清理活动下载任务
            if task.preset_id in self.active_downloads:
                del self.active_downloads[task.preset_id]

    def _verify_file_integrity(self, file_path: Path) -> bool:
        """验证文件完整性"""
        try:
            if not file_path.exists():
                return False

            # 基本大小检查
            if file_path.stat().st_size < 1024:  # 小于1KB认为无效
                return False

            # 简单的文件格式检查
            if file_path.suffix == '.safetensors':
                return self._verify_safetensors(file_path)
            elif file_path.suffix == '.bin':
                return True  # 简单检查.bin文件
            elif file_path.suffix == '.pt':
                return True  # 简单检查.pt文件
            elif file_path.suffix == '.ckpt':
                return True  # 简单检查.ckpt文件

            return True
        except Exception as e:
            self.logger.error(f"验证文件完整性失败 {file_path}: {e}")
            return False

    def _verify_safetensors(self, file_path: Path) -> bool:
        """验证safetensors文件格式"""
        try:
            import struct
            with open(file_path, 'rb') as f:
                # 读取前8字节：头部长度（小端序）
                header_len_bytes = f.read(8)
                if len(header_len_bytes) != 8:
                    return False

                header_len = struct.unpack('<Q', header_len_bytes)[0]

                # 检查头部长度是否合理（不超过文件大小）
                file_size = file_path.stat().st_size
                if header_len <= 0 or header_len > file_size - 8:
                    return False

                # 读取头部数据并验证是否为有效的JSON
                header_data = f.read(header_len)
                if len(header_data) != header_len:
                    return False

                # 验证是否以JSON开头
                if not header_data.startswith(b'{'):
                    return False

                # 尝试解析JSON以验证格式正确性
                try:
                    import json
                    json_str = header_data.decode('utf-8').rstrip('\x00')
                    json.loads(json_str)
                    return True
                except json.JSONDecodeError:
                    return False
        except Exception as e:
            self.logger.error(f"safetensors验证失败 {file_path}: {e}")
            return False

    def _update_download_stats(self, task: DownloadTask):
        """更新下载统计信息"""
        try:
            preset_id = task.preset_id
            file_size = task.downloaded_size

            self.stats[preset_id] = {
                'downloaded_at': datetime.now().isoformat(),
                'file_size': file_size,
                'download_time': (task.updated_at - task.created_at).total_seconds(),
                'average_speed': file_size / max(1, (task.updated_at - task.created_at).total_seconds()) / 1024  # KB/s
            }

            self.save_stats()
        except Exception as e:
            self.logger.error(f"更新下载统计信息失败: {e}")

    async def cancel_download(self, preset_id: str) -> bool:
        """取消下载"""
        if preset_id not in self.download_tasks:
            return False

        task = self.download_tasks[preset_id]

        # 标记为取消
        task.status = "cancelled"

        # 取消异步任务
        if preset_id in self.active_downloads:
            self.active_downloads[preset_id].cancel()
            del self.active_downloads[preset_id]

        # 清理临时文件
        temp_path = self.lora_dir / f"{task.filename}.tmp"
        if temp_path.exists():
            temp_path.unlink()

        self.logger.info(f"已取消下载预设 {preset_id}")
        return True

    def delete_preset_file(self, preset_id: str) -> bool:
        """删除预设文件"""
        preset = self.get_preset_by_id(preset_id)
        if not preset:
            return False

        file_path = self.lora_dir / preset.filename
        if not file_path.exists():
            return True

        try:
            file_path.unlink()

            # 清理统计信息
            if preset_id in self.stats:
                del self.stats[preset_id]
                self.save_stats()

            self.logger.info(f"已删除预设文件 {preset_id}")
            return True
        except Exception as e:
            self.logger.error(f"删除预设文件失败 {preset_id}: {e}")
            return False

    def get_lora_options_with_presets(self) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
        """获取包含预设的LoRA选项（与原有discover_lora_options兼容）"""
        from .lora_utils import discover_lora_options

        # 获取现有的LoRA选项
        existing_options, existing_paths = discover_lora_options()

        # 添加预设选项
        new_options = []
        new_paths = {}

        # 保持原有选项
        for option in existing_options:
            new_options.append(option)

        for key, path in existing_paths.items():
            new_paths[key] = path

        # 添加未下载的预设选项
        for preset in self.presets.values():
            if not self.is_preset_downloaded(preset.id):
                option_value = f"preset:{preset.id}"
                option_label = f"📥 {preset.name} ({preset.size})"

                new_options.append({
                    "label": option_label,
                    "value": option_value
                })
                new_paths[option_value] = f"preset:{preset.id}"

        return new_options, new_paths


# 全局下载管理器实例
_downloader: Optional[LoRADownloader] = None


def get_downloader() -> LoRADownloader:
    """获取全局下载管理器实例"""
    global _downloader
    if _downloader is None:
        _downloader = LoRADownloader()
    return _downloader