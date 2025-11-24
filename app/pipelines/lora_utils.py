from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple

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

    options: List[Dict[str, str]] = [_build_option_entry("Disable", "none")]
    path_map: Dict[str, str] = {"none": ""}

    if not LORA_DIR.exists():
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

    return options, path_map
