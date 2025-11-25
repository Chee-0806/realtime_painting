"""ControlNet API 模块

提供 ControlNet 相关的 API 端点，包括获取支持的 ControlNet 类型信息。
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/controlnet", tags=["controlnet"])

# 支持的 ControlNet 类型
SUPPORTED_CONTROLNET_TYPES = [
    "canny",        # Canny 边缘检测
    "depth",        # 深度图
    "pose",         # 人体姿态
    "scribble",     # 素描
    "lineart",      # 线稿
    "normal",       # 法线图
    "semantic",     # 语义分割
    "mlsd",         # 直线检测
    "hed",          # HED 边缘检测
    "openpose",     # OpenPose 姿态
    "tile",         # 分块重采样
    "inpaint",      # 修复
]

# 定义请求和响应模型
class ControlNetTypeResponse(BaseModel):
    success: bool
    types: List[str]
    message: Optional[str] = None


class ControlNetInfoResponse(BaseModel):
    success: bool
    type: str
    info: Dict[str, Any]


@router.get("/types", response_model=ControlNetTypeResponse)
async def get_controlnet_types():
    """
    获取支持的 ControlNet 类型列表

    Returns:
        包含支持类型的响应
    """
    try:
        logger.info("获取 ControlNet 类型列表")

        return ControlNetTypeResponse(
            success=True,
            types=SUPPORTED_CONTROLNET_TYPES,
            message=f"共支持 {len(SUPPORTED_CONTROLNET_TYPES)} 种 ControlNet 类型"
        )

    except Exception as e:
        logger.error(f"获取 ControlNet 类型失败: {e}")
        return ControlNetTypeResponse(
            success=False,
            types=SUPPORTED_CONTROLNET_TYPES,  # 返回默认类型
            message=f"获取类型失败: {str(e)}"
        )


@router.get("/info/{controlnet_type}", response_model=ControlNetInfoResponse)
async def get_controlnet_info(controlnet_type: str):
    """
    获取特定 ControlNet 类型的详细信息

    Args:
        controlnet_type: ControlNet 类型

    Returns:
        ControlNet 类型的详细信息
    """
    if controlnet_type not in SUPPORTED_CONTROLNET_TYPES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"不支持的 ControlNet 类型: {controlnet_type}"
        )

    # 定义各种 ControlNet 的信息
    controlnet_info = {
        "canny": {
            "name": "Canny 边缘检测",
            "description": "检测图像中的边缘线条，适合控制图像的轮廓结构",
            "model": "lllyasviel/sd-controlnet-canny",
            "parameters": ["low_threshold", "high_threshold"],
            "recommended_weight": 1.0
        },
        "depth": {
            "name": "深度图",
            "description": "控制图像的深度和空间关系",
            "model": "lllyasviel/sd-controlnet-depth",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "pose": {
            "name": "人体姿态",
            "description": "检测和控制人体姿态，适合人物图像",
            "model": "lllyasviel/sd-controlnet-openpose",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "scribble": {
            "name": "素描",
            "description": "基于手绘草图生成图像",
            "model": "lllyasviel/sd-controlnet-scribble",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "lineart": {
            "name": "线稿",
            "description": "控制图像的线条结构",
            "model": "lllyasviel/sd-controlnet-lineart",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "normal": {
            "name": "法线图",
            "description": "控制图像的表面法线信息",
            "model": "lllyasviel/sd-controlnet-normal",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "semantic": {
            "name": "语义分割",
            "description": "基于语义分割控制图像区域",
            "model": "lllyasviel/sd-controlnet-seg",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "mlsd": {
            "name": "直线检测",
            "description": "检测图像中的直线结构",
            "model": "lllyasviel/sd-controlnet-mlsd",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "hed": {
            "name": "HED 边缘检测",
            "description": "更柔软的边缘检测方法",
            "model": "lllyasviel/sd-controlnet-hed",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "openpose": {
            "name": "OpenPose 姿态",
            "description": "详细的身体和手部姿态检测",
            "model": "lllyasviel/sd-controlnet-openpose",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "tile": {
            "name": "分块重采样",
            "description": "用于提高图像分辨率和质量",
            "model": "lllyasviel/sd-controlnet-tile",
            "parameters": [],
            "recommended_weight": 1.0
        },
        "inpaint": {
            "name": "图像修复",
            "description": "用于图像修复和局部重绘",
            "model": "lllyasviel/sd-controlnet-inpaint",
            "parameters": [],
            "recommended_weight": 1.0
        }
    }

    info = controlnet_info.get(controlnet_type, {
        "name": controlnet_type,
        "description": "ControlNet 控制模型",
        "model": f"lllyasviel/sd-controlnet-{controlnet_type}",
        "parameters": [],
        "recommended_weight": 1.0
    })

    return {
        "success": True,
        "type": controlnet_type,
        "info": info
    }