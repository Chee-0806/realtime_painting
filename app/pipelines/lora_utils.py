from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

LORA_DIR = (
    Path(__file__).resolve().parent.parent
    / "lib"
    / "StreamDiffusion"
    / "models"
    / "LoRA"
)

_SUPPORTED_SUFFIXES = {".safetensors", ".pt", ".bin", ".ckpt"}


def _build_option_entry(label: str, value: str) -> Dict[str, str]:
    return {"label": label, "value": value}


@lru_cache(maxsize=1)
def discover_lora_options() -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """Return dropdown options plus selection->path mapping.

    The mapping dictionary always contains the "none" option which disables
    additional LoRA weights.
    """
    logger = logging.getLogger(__name__)

    options: List[Dict[str, str]] = [_build_option_entry("禁用", "none")]
    path_map: Dict[str, str] = {"none": ""}

    if not LORA_DIR.exists():
        logger.warning(f"LoRA目录不存在: {LORA_DIR}")
        return options, path_map

    seen_values: Dict[str, int] = {}
    for file in sorted(LORA_DIR.glob("**/*")):
        if not file.is_file() or file.suffix.lower() not in _SUPPORTED_SUFFIXES:
            continue

        base_value = file.stem
        if base_value in seen_values:
            seen_values[base_value] += 1
            option_value = f"{base_value}-{seen_values[base_value]}"
        else:
            seen_values[base_value] = 0
            option_value = base_value

        options.append(_build_option_entry(file.stem, option_value))
        path_map[option_value] = str(file)

    logger.info(f"发现 {len(options)-1} 个本地LoRA文件")
    return options, path_map


def get_lora_options_with_presets() -> Tuple[List[Dict[str, str]], Dict[str, str]]:
    """获取包含预制LoRA的选项列表"""
    logger = logging.getLogger(__name__)

    try:
        from .lora_downloader import get_downloader
        downloader = get_downloader()
        return downloader.get_lora_options_with_presets()
    except ImportError as e:
        logger.warning(f"无法加载LoRA下载器，使用本地选项: {e}")
        return discover_lora_options()
    except Exception as e:
        logger.error(f"获取预制LoRA选项失败: {e}")
        return discover_lora_options()


def resolve_lora_path(lora_selection: str) -> Optional[str]:
    """解析LoRA选择到实际文件路径"""
    if not lora_selection or lora_selection == "none":
        return None

    # 预设LoRA
    if lora_selection.startswith("preset:"):
        preset_id = lora_selection[7:]  # 移除 "preset:" 前缀

        try:
            from .lora_downloader import get_downloader
            downloader = get_downloader()

            # 检查是否已下载
            if downloader.is_preset_downloaded(preset_id):
                preset = downloader.get_preset_by_id(preset_id)
                if preset:
                    lora_dir = downloader.lora_dir
                    return str(lora_dir / preset.filename)
            else:
                # 如果未下载，返回None或触发下载
                logger = logging.getLogger(__name__)
                logger.warning(f"预设LoRA {preset_id} 尚未下载")
                return None

        except ImportError:
            pass
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"解析预设LoRA路径失败: {e}")
            return None

    # 本地LoRA
    if LORA_DIR.exists():
        for file in sorted(LORA_DIR.glob("**/*")):
            if file.is_file() and file.suffix.lower() in _SUPPORTED_SUFFIXES:
                if file.stem == lora_selection or str(file) == lora_selection:
                    return str(file)

    return None
