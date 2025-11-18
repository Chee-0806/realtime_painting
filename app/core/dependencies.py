"""依赖兼容性检查系统

在系统启动时检查关键依赖的版本兼容性，确保环境满足运行要求。
严格验证加速方式的可用性，不进行降级。

验证需求：
- 需求 12.1: 检查 Python、PyTorch、CUDA 版本
- 需求 12.2: 验证 TensorRT 版本与 StreamDiffusion 的兼容性
- 需求 12.3: 验证 xformers 版本与 PyTorch 版本的兼容性
- 需求 12.6: 记录所有关键依赖的版本信息
- 需求 12.7: 依赖检查失败时终止启动
"""

import sys
import logging
from typing import Literal, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VersionInfo:
    """版本信息"""
    name: str
    current: Optional[str]
    required: str
    compatible: bool
    error_message: Optional[str] = None


@dataclass
class DependencyCheckResult:
    """依赖检查结果"""
    passed: bool
    errors: list[str]
    warnings: list[str]
    version_info: dict[str, VersionInfo]


class DependencyChecker:
    """依赖兼容性检查器
    
    检查系统依赖的版本兼容性，包括：
    - Python 版本
    - PyTorch 和 CUDA 版本
    - xformers 可用性（如果需要）
    - TensorRT 依赖（如果需要）
    
    特点：
    - 严格验证，不降级
    - 提供详细的错误信息和推荐版本
    - 记录所有关键依赖的版本信息
    """
    
    # 推荐版本
    RECOMMENDED_VERSIONS = {
        "python": "3.10+",
        "torch": "2.0.0+",
        "cuda": "11.8+ or 12.1+",
        "xformers": "0.0.22+",
        "tensorrt": "9.0.0+",
        "onnx": "1.15.0",
        "onnxruntime": "1.16.3",
        "protobuf": "3.20.2",
    }
    
    def __init__(self):
        """初始化依赖检查器"""
        self.version_info: dict[str, VersionInfo] = {}
    
    def check_all(
        self, 
        acceleration: Literal["xformers", "tensorrt", "none"]
    ) -> DependencyCheckResult:
        """检查所有依赖
        
        Args:
            acceleration: 加速方式
            
        Returns:
            依赖检查结果
        """
        errors = []
        warnings = []
        
        # 1. 检查 Python 版本
        logger.info("检查 Python 版本...")
        if not self.check_python_version():
            errors.append(
                f"Python 版本不兼容。"
                f"当前: {self.version_info['python'].current}, "
                f"要求: {self.RECOMMENDED_VERSIONS['python']}"
            )
        
        # 2. 检查 PyTorch 和 CUDA
        logger.info("检查 PyTorch 和 CUDA...")
        if not self.check_pytorch_cuda():
            errors.append(
                f"PyTorch 或 CUDA 版本不兼容。"
                f"PyTorch: {self.version_info.get('torch', VersionInfo('torch', None, '', False)).current}, "
                f"CUDA: {self.version_info.get('cuda', VersionInfo('cuda', None, '', False)).current}"
            )
        
        # 3. 根据加速方式检查特定依赖
        if acceleration == "xformers":
            logger.info("检查 xformers...")
            success, message = self.check_xformers()
            if not success:
                errors.append(
                    f"xformers 加速方式初始化失败: {message}\n"
                    f"推荐版本: {self.RECOMMENDED_VERSIONS['xformers']}\n"
                    f"安装命令: pip install xformers>={self.RECOMMENDED_VERSIONS['xformers']}"
                )
        
        elif acceleration == "tensorrt":
            logger.info("检查 TensorRT 依赖...")
            success, message = self.check_tensorrt()
            if not success:
                errors.append(
                    f"TensorRT 加速方式初始化失败: {message}\n"
                    f"推荐版本:\n"
                    f"  - tensorrt: {self.RECOMMENDED_VERSIONS['tensorrt']}\n"
                    f"  - onnx: {self.RECOMMENDED_VERSIONS['onnx']}\n"
                    f"  - onnxruntime: {self.RECOMMENDED_VERSIONS['onnxruntime']}\n"
                    f"  - protobuf: {self.RECOMMENDED_VERSIONS['protobuf']}\n"
                    f"安装命令: pip install -r requirements-tensorrt.txt"
                )
        
        # 4. 记录版本信息
        if not errors:
            logger.info("依赖检查通过")
            self._log_version_info()
        
        passed = len(errors) == 0
        
        return DependencyCheckResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            version_info=self.version_info
        )
    
    def check_python_version(self) -> bool:
        """检查 Python 版本 >= 3.10
        
        Returns:
            是否兼容
        """
        version = sys.version_info
        # 处理 tuple 和 sys.version_info 两种情况
        if isinstance(version, tuple):
            major, minor, micro = version[0], version[1], version[2]
        else:
            major, minor, micro = version.major, version.minor, version.micro
        
        current_version = f"{major}.{minor}.{micro}"
        
        # Python 3.10+
        compatible = major == 3 and minor >= 10
        
        self.version_info["python"] = VersionInfo(
            name="Python",
            current=current_version,
            required=self.RECOMMENDED_VERSIONS["python"],
            compatible=compatible,
            error_message=None if compatible else "需要 Python 3.10 或更高版本"
        )
        
        return compatible
    
    def check_pytorch_cuda(self) -> bool:
        """检查 PyTorch 和 CUDA 版本兼容性
        
        Returns:
            是否兼容
        """
        try:
            import torch
            
            torch_version = torch.__version__
            cuda_available = torch.cuda.is_available()
            cuda_version = torch.version.cuda if cuda_available else None
            
            # 检查 PyTorch 版本 >= 2.0.0
            torch_major = int(torch_version.split('.')[0])
            torch_compatible = torch_major >= 2
            
            self.version_info["torch"] = VersionInfo(
                name="PyTorch",
                current=torch_version,
                required=self.RECOMMENDED_VERSIONS["torch"],
                compatible=torch_compatible,
                error_message=None if torch_compatible else "需要 PyTorch 2.0.0 或更高版本"
            )
            
            # 检查 CUDA
            if not cuda_available:
                self.version_info["cuda"] = VersionInfo(
                    name="CUDA",
                    current=None,
                    required=self.RECOMMENDED_VERSIONS["cuda"],
                    compatible=False,
                    error_message="CUDA 不可用，需要 NVIDIA GPU 和 CUDA 支持"
                )
                return False
            
            # CUDA 版本检查（11.8+ 或 12.1+）
            cuda_major = int(cuda_version.split('.')[0]) if cuda_version else 0
            cuda_minor = int(cuda_version.split('.')[1]) if cuda_version and '.' in cuda_version else 0
            
            cuda_compatible = (
                (cuda_major == 11 and cuda_minor >= 8) or
                (cuda_major >= 12)
            )
            
            self.version_info["cuda"] = VersionInfo(
                name="CUDA",
                current=cuda_version,
                required=self.RECOMMENDED_VERSIONS["cuda"],
                compatible=cuda_compatible,
                error_message=None if cuda_compatible else "需要 CUDA 11.8+ 或 12.1+"
            )
            
            return torch_compatible and cuda_compatible
            
        except ImportError as e:
            self.version_info["torch"] = VersionInfo(
                name="PyTorch",
                current=None,
                required=self.RECOMMENDED_VERSIONS["torch"],
                compatible=False,
                error_message=f"PyTorch 未安装: {e}"
            )
            return False
        except Exception as e:
            logger.error(f"检查 PyTorch/CUDA 时出错: {e}")
            return False
    
    def check_xformers(self) -> tuple[bool, str]:
        """检查 xformers 是否可用
        
        Returns:
            (是否可用, 错误消息)
        """
        try:
            import xformers
            
            xformers_version = xformers.__version__
            
            # 检查版本 >= 0.0.22
            version_parts = xformers_version.split('.')
            if len(version_parts) >= 3:
                major = int(version_parts[0])
                minor = int(version_parts[1])
                patch = int(version_parts[2].split('+')[0])  # 处理 0.0.22+cu118 这样的版本
                
                compatible = (major > 0) or (major == 0 and minor > 0) or (major == 0 and minor == 0 and patch >= 22)
            else:
                compatible = False
            
            self.version_info["xformers"] = VersionInfo(
                name="xformers",
                current=xformers_version,
                required=self.RECOMMENDED_VERSIONS["xformers"],
                compatible=compatible,
                error_message=None if compatible else f"xformers 版本过低: {xformers_version}"
            )
            
            if not compatible:
                return False, f"xformers 版本过低: {xformers_version}，需要 {self.RECOMMENDED_VERSIONS['xformers']}"
            
            # 尝试导入核心功能
            try:
                from xformers.ops import memory_efficient_attention
                return True, "xformers 可用"
            except ImportError as e:
                return False, f"xformers 导入失败: {e}"
                
        except ImportError:
            self.version_info["xformers"] = VersionInfo(
                name="xformers",
                current=None,
                required=self.RECOMMENDED_VERSIONS["xformers"],
                compatible=False,
                error_message="xformers 未安装"
            )
            return False, "xformers 未安装"
        except Exception as e:
            return False, f"检查 xformers 时出错: {e}"
    
    def check_tensorrt(self) -> tuple[bool, str]:
        """检查 TensorRT 依赖
        
        检查以下依赖：
        - tensorrt >= 9.0.0
        - cuda-python
        - onnx == 1.15.0
        - onnxruntime == 1.16.3
        - protobuf == 3.20.2
        - polygraphy
        
        Returns:
            (是否可用, 错误消息)
        """
        missing_deps = []
        version_mismatches = []
        
        # 1. 检查 tensorrt
        try:
            import tensorrt as trt
            
            trt_version = trt.__version__
            version_parts = trt_version.split('.')
            major = int(version_parts[0])
            
            compatible = major >= 9
            
            self.version_info["tensorrt"] = VersionInfo(
                name="TensorRT",
                current=trt_version,
                required=self.RECOMMENDED_VERSIONS["tensorrt"],
                compatible=compatible,
                error_message=None if compatible else f"TensorRT 版本过低: {trt_version}"
            )
            
            if not compatible:
                version_mismatches.append(
                    f"TensorRT 版本过低: {trt_version}，需要 {self.RECOMMENDED_VERSIONS['tensorrt']}"
                )
                
        except ImportError:
            missing_deps.append("tensorrt")
            self.version_info["tensorrt"] = VersionInfo(
                name="TensorRT",
                current=None,
                required=self.RECOMMENDED_VERSIONS["tensorrt"],
                compatible=False,
                error_message="TensorRT 未安装"
            )
        
        # 2. 检查 cuda-python
        try:
            import cuda
            cuda_python_version = getattr(cuda, "__version__", "unknown")
            self.version_info["cuda-python"] = VersionInfo(
                name="cuda-python",
                current=cuda_python_version,
                required="12.0.0+",
                compatible=True
            )
        except ImportError:
            missing_deps.append("cuda-python")
            self.version_info["cuda-python"] = VersionInfo(
                name="cuda-python",
                current=None,
                required="12.0.0+",
                compatible=False,
                error_message="cuda-python 未安装"
            )
        
        # 3. 检查 onnx
        try:
            import onnx
            
            onnx_version = onnx.__version__
            expected_version = self.RECOMMENDED_VERSIONS["onnx"]
            
            compatible = onnx_version.startswith(expected_version)
            
            self.version_info["onnx"] = VersionInfo(
                name="ONNX",
                current=onnx_version,
                required=expected_version,
                compatible=compatible,
                error_message=None if compatible else f"ONNX 版本不匹配: {onnx_version}"
            )
            
            if not compatible:
                version_mismatches.append(
                    f"ONNX 版本不匹配: {onnx_version}，需要 {expected_version}"
                )
                
        except ImportError:
            missing_deps.append("onnx")
            self.version_info["onnx"] = VersionInfo(
                name="ONNX",
                current=None,
                required=self.RECOMMENDED_VERSIONS["onnx"],
                compatible=False,
                error_message="ONNX 未安装"
            )
        
        # 4. 检查 onnxruntime
        try:
            import onnxruntime
            
            ort_version = onnxruntime.__version__
            expected_version = self.RECOMMENDED_VERSIONS["onnxruntime"]
            
            compatible = ort_version.startswith(expected_version)
            
            self.version_info["onnxruntime"] = VersionInfo(
                name="ONNX Runtime",
                current=ort_version,
                required=expected_version,
                compatible=compatible,
                error_message=None if compatible else f"ONNX Runtime 版本不匹配: {ort_version}"
            )
            
            if not compatible:
                version_mismatches.append(
                    f"ONNX Runtime 版本不匹配: {ort_version}，需要 {expected_version}"
                )
                
        except ImportError:
            missing_deps.append("onnxruntime")
            self.version_info["onnxruntime"] = VersionInfo(
                name="ONNX Runtime",
                current=None,
                required=self.RECOMMENDED_VERSIONS["onnxruntime"],
                compatible=False,
                error_message="ONNX Runtime 未安装"
            )
        
        # 5. 检查 protobuf
        try:
            import google.protobuf as protobuf_module
            
            protobuf_version = protobuf_module.__version__
            expected_version = self.RECOMMENDED_VERSIONS["protobuf"]
            
            compatible = protobuf_version.startswith(expected_version)
            
            self.version_info["protobuf"] = VersionInfo(
                name="Protobuf",
                current=protobuf_version,
                required=expected_version,
                compatible=compatible,
                error_message=None if compatible else f"Protobuf 版本不匹配: {protobuf_version}"
            )
            
            if not compatible:
                version_mismatches.append(
                    f"Protobuf 版本不匹配: {protobuf_version}，需要 {expected_version}"
                )
                
        except ImportError:
            missing_deps.append("protobuf")
            self.version_info["protobuf"] = VersionInfo(
                name="Protobuf",
                current=None,
                required=self.RECOMMENDED_VERSIONS["protobuf"],
                compatible=False,
                error_message="Protobuf 未安装"
            )
        
        # 6. 检查 polygraphy
        try:
            import polygraphy
            polygraphy_version = getattr(polygraphy, "__version__", "unknown")
            self.version_info["polygraphy"] = VersionInfo(
                name="Polygraphy",
                current=polygraphy_version,
                required="0.47.0+",
                compatible=True
            )
        except ImportError:
            missing_deps.append("polygraphy")
            self.version_info["polygraphy"] = VersionInfo(
                name="Polygraphy",
                current=None,
                required="0.47.0+",
                compatible=False,
                error_message="Polygraphy 未安装"
            )
        
        # 生成错误消息
        if missing_deps or version_mismatches:
            error_parts = []
            
            if missing_deps:
                error_parts.append(f"缺少依赖: {', '.join(missing_deps)}")
            
            if version_mismatches:
                error_parts.append("版本不匹配:\n  - " + "\n  - ".join(version_mismatches))
            
            return False, "\n".join(error_parts)
        
        return True, "TensorRT 依赖检查通过"
    
    def get_recommended_versions(
        self, 
        acceleration: Literal["xformers", "tensorrt", "none"]
    ) -> dict[str, str]:
        """返回推荐的依赖版本
        
        Args:
            acceleration: 加速方式
            
        Returns:
            推荐版本字典
        """
        base_versions = {
            "python": self.RECOMMENDED_VERSIONS["python"],
            "torch": self.RECOMMENDED_VERSIONS["torch"],
            "cuda": self.RECOMMENDED_VERSIONS["cuda"],
        }
        
        if acceleration == "xformers":
            base_versions["xformers"] = self.RECOMMENDED_VERSIONS["xformers"]
        elif acceleration == "tensorrt":
            base_versions.update({
                "tensorrt": self.RECOMMENDED_VERSIONS["tensorrt"],
                "onnx": self.RECOMMENDED_VERSIONS["onnx"],
                "onnxruntime": self.RECOMMENDED_VERSIONS["onnxruntime"],
                "protobuf": self.RECOMMENDED_VERSIONS["protobuf"],
            })
        
        return base_versions
    
    def _log_version_info(self):
        """记录所有关键依赖的版本信息"""
        logger.info("=" * 60)
        logger.info("依赖版本信息:")
        logger.info("=" * 60)
        
        for name, info in self.version_info.items():
            status = "✓" if info.compatible else "✗"
            current = info.current or "未安装"
            logger.info(f"{status} {info.name}: {current} (要求: {info.required})")
        
        logger.info("=" * 60)
