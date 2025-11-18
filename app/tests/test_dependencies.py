"""依赖检查系统单元测试"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from app.core.dependencies import DependencyChecker, VersionInfo, DependencyCheckResult


class TestDependencyChecker(unittest.TestCase):
    """测试 DependencyChecker 类"""
    
    def test_check_python_version_compatible(self):
        """测试 Python 版本检查 - 兼容版本"""
        checker = DependencyChecker()
        
        # Mock Python 3.10
        with patch.object(sys, 'version_info', (3, 10, 0, 'final', 0)):
            result = checker.check_python_version()
            
            self.assertTrue(result)
            self.assertIn("python", checker.version_info)
            self.assertTrue(checker.version_info["python"].compatible)
            self.assertEqual(checker.version_info["python"].current, "3.10.0")
    
    def test_check_python_version_incompatible(self):
        """测试 Python 版本检查 - 不兼容版本"""
        checker = DependencyChecker()
        
        # Mock Python 3.9
        with patch.object(sys, 'version_info', (3, 9, 6, 'final', 0)):
            result = checker.check_python_version()
            
            self.assertFalse(result)
            self.assertIn("python", checker.version_info)
            self.assertFalse(checker.version_info["python"].compatible)
            self.assertEqual(checker.version_info["python"].current, "3.9.6")
    
    def test_check_pytorch_cuda_not_installed(self):
        """测试 PyTorch 未安装的情况"""
        checker = DependencyChecker()
        
        with patch.dict('sys.modules', {'torch': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'torch'")):
                result = checker.check_pytorch_cuda()
                
                self.assertFalse(result)
                self.assertIn("torch", checker.version_info)
                self.assertFalse(checker.version_info["torch"].compatible)
                self.assertIsNone(checker.version_info["torch"].current)
    
    def test_check_pytorch_cuda_compatible(self):
        """测试 PyTorch 和 CUDA 兼容"""
        checker = DependencyChecker()
        
        # Mock torch module
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = True
        mock_torch.version.cuda = "12.1"
        
        with patch.dict('sys.modules', {'torch': mock_torch}):
            result = checker.check_pytorch_cuda()
            
            self.assertTrue(result)
            self.assertTrue(checker.version_info["torch"].compatible)
            self.assertTrue(checker.version_info["cuda"].compatible)
    
    def test_check_pytorch_cuda_no_cuda(self):
        """测试 CUDA 不可用的情况"""
        checker = DependencyChecker()
        
        # Mock torch module without CUDA
        mock_torch = MagicMock()
        mock_torch.__version__ = "2.1.0"
        mock_torch.cuda.is_available.return_value = False
        mock_torch.version.cuda = None
        
        with patch.dict('sys.modules', {'torch': mock_torch}):
            result = checker.check_pytorch_cuda()
            
            self.assertFalse(result)
            self.assertFalse(checker.version_info["cuda"].compatible)
    
    def test_check_xformers_not_installed(self):
        """测试 xformers 未安装"""
        checker = DependencyChecker()
        
        with patch.dict('sys.modules', {'xformers': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'xformers'")):
                success, message = checker.check_xformers()
                
                self.assertFalse(success)
                self.assertIn("未安装", message)
                self.assertIn("xformers", checker.version_info)
                self.assertFalse(checker.version_info["xformers"].compatible)
    
    def test_check_xformers_compatible(self):
        """测试 xformers 兼容版本"""
        checker = DependencyChecker()
        
        # Mock xformers module
        mock_xformers = MagicMock()
        mock_xformers.__version__ = "0.0.22"
        
        mock_ops = MagicMock()
        mock_ops.memory_efficient_attention = MagicMock()
        
        with patch.dict('sys.modules', {
            'xformers': mock_xformers,
            'xformers.ops': mock_ops
        }):
            success, message = checker.check_xformers()
            
            self.assertTrue(success)
            self.assertIn("可用", message)
            self.assertTrue(checker.version_info["xformers"].compatible)
    
    def test_check_tensorrt_not_installed(self):
        """测试 TensorRT 未安装"""
        checker = DependencyChecker()
        
        with patch.dict('sys.modules', {'tensorrt': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'tensorrt'")):
                success, message = checker.check_tensorrt()
                
                self.assertFalse(success)
                self.assertIn("缺少依赖", message)
                self.assertIn("tensorrt", message)
    
    def test_check_tensorrt_compatible(self):
        """测试 TensorRT 所有依赖都兼容"""
        checker = DependencyChecker()
        
        # Mock all TensorRT dependencies
        mock_tensorrt = MagicMock()
        mock_tensorrt.__version__ = "9.0.1"
        
        mock_cuda = MagicMock()
        mock_cuda.__version__ = "12.0.0"
        
        mock_onnx = MagicMock()
        mock_onnx.__version__ = "1.15.0"
        
        mock_onnxruntime = MagicMock()
        mock_onnxruntime.__version__ = "1.16.3"
        
        mock_protobuf = MagicMock()
        mock_protobuf.__version__ = "3.20.2"
        
        mock_polygraphy = MagicMock()
        mock_polygraphy.__version__ = "0.47.0"
        
        with patch.dict('sys.modules', {
            'tensorrt': mock_tensorrt,
            'cuda': mock_cuda,
            'onnx': mock_onnx,
            'onnxruntime': mock_onnxruntime,
            'google.protobuf': mock_protobuf,
            'polygraphy': mock_polygraphy
        }):
            success, message = checker.check_tensorrt()
            
            self.assertTrue(success)
            self.assertIn("通过", message)
    
    def test_check_all_none_acceleration(self):
        """测试 check_all 方法 - 无加速"""
        checker = DependencyChecker()
        
        # Mock compatible Python and PyTorch
        with patch.object(sys, 'version_info', (3, 10, 0, 'final', 0)):
            mock_torch = MagicMock()
            mock_torch.__version__ = "2.1.0"
            mock_torch.cuda.is_available.return_value = True
            mock_torch.version.cuda = "12.1"
            
            with patch.dict('sys.modules', {'torch': mock_torch}):
                result = checker.check_all("none")
                
                self.assertIsInstance(result, DependencyCheckResult)
                self.assertTrue(result.passed)
                self.assertEqual(len(result.errors), 0)
    
    def test_check_all_xformers_acceleration(self):
        """测试 check_all 方法 - xformers 加速"""
        checker = DependencyChecker()
        
        # Mock compatible environment
        with patch.object(sys, 'version_info', (3, 10, 0, 'final', 0)):
            mock_torch = MagicMock()
            mock_torch.__version__ = "2.1.0"
            mock_torch.cuda.is_available.return_value = True
            mock_torch.version.cuda = "12.1"
            
            mock_xformers = MagicMock()
            mock_xformers.__version__ = "0.0.22"
            
            mock_ops = MagicMock()
            mock_ops.memory_efficient_attention = MagicMock()
            
            with patch.dict('sys.modules', {
                'torch': mock_torch,
                'xformers': mock_xformers,
                'xformers.ops': mock_ops
            }):
                result = checker.check_all("xformers")
                
                self.assertIsInstance(result, DependencyCheckResult)
                self.assertTrue(result.passed)
                self.assertEqual(len(result.errors), 0)
    
    def test_get_recommended_versions_none(self):
        """测试获取推荐版本 - 无加速"""
        checker = DependencyChecker()
        versions = checker.get_recommended_versions("none")
        
        self.assertIn("python", versions)
        self.assertIn("torch", versions)
        self.assertIn("cuda", versions)
        self.assertNotIn("xformers", versions)
        self.assertNotIn("tensorrt", versions)
    
    def test_get_recommended_versions_xformers(self):
        """测试获取推荐版本 - xformers"""
        checker = DependencyChecker()
        versions = checker.get_recommended_versions("xformers")
        
        self.assertIn("python", versions)
        self.assertIn("torch", versions)
        self.assertIn("cuda", versions)
        self.assertIn("xformers", versions)
        self.assertNotIn("tensorrt", versions)
    
    def test_get_recommended_versions_tensorrt(self):
        """测试获取推荐版本 - TensorRT"""
        checker = DependencyChecker()
        versions = checker.get_recommended_versions("tensorrt")
        
        self.assertIn("python", versions)
        self.assertIn("torch", versions)
        self.assertIn("cuda", versions)
        self.assertIn("tensorrt", versions)
        self.assertIn("onnx", versions)
        self.assertIn("onnxruntime", versions)
        self.assertIn("protobuf", versions)


class TestVersionInfo(unittest.TestCase):
    """测试 VersionInfo 数据类"""
    
    def test_version_info_creation(self):
        """测试创建 VersionInfo"""
        info = VersionInfo(
            name="Test",
            current="1.0.0",
            required="1.0.0+",
            compatible=True
        )
        
        self.assertEqual(info.name, "Test")
        self.assertEqual(info.current, "1.0.0")
        self.assertEqual(info.required, "1.0.0+")
        self.assertTrue(info.compatible)
        self.assertIsNone(info.error_message)
    
    def test_version_info_with_error(self):
        """测试带错误消息的 VersionInfo"""
        info = VersionInfo(
            name="Test",
            current=None,
            required="1.0.0+",
            compatible=False,
            error_message="Not installed"
        )
        
        self.assertFalse(info.compatible)
        self.assertEqual(info.error_message, "Not installed")


class TestDependencyCheckResult(unittest.TestCase):
    """测试 DependencyCheckResult 数据类"""
    
    def test_result_creation(self):
        """测试创建 DependencyCheckResult"""
        result = DependencyCheckResult(
            passed=True,
            errors=[],
            warnings=[],
            version_info={}
        )
        
        self.assertTrue(result.passed)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
        self.assertEqual(len(result.version_info), 0)
    
    def test_result_with_errors(self):
        """测试带错误的结果"""
        result = DependencyCheckResult(
            passed=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            version_info={}
        )
        
        self.assertFalse(result.passed)
        self.assertEqual(len(result.errors), 2)
        self.assertEqual(len(result.warnings), 1)


if __name__ == '__main__':
    unittest.main()
