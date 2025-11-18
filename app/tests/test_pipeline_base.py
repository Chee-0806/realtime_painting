"""
测试 Pipeline 抽象层

验证 BasePipeline 和 PipelineFactory 的基本功能。
"""

import pytest
import torch
from PIL import Image
from pydantic import Field

from app.pipelines.base import BasePipeline, PipelineFactory


class MockPipeline(BasePipeline):
    """用于测试的 Mock Pipeline"""
    
    class InputParams(BasePipeline.InputParams):
        """扩展的输入参数"""
        guidance_scale: float = Field(
            default=7.5,
            title="Guidance Scale",
            ge=1.0,
            le=20.0
        )
    
    def __init__(self, config: dict, device: torch.device, dtype: torch.dtype):
        self.config = config
        self.device = device
        self.dtype = dtype
        self.prepared = False
    
    def predict(self, params: InputParams) -> Image.Image:
        """返回一个简单的测试图像"""
        return Image.new("RGB", (512, 512), color="red")
    
    def prepare(self, prompt: str, **kwargs):
        """标记为已准备"""
        self.prepared = True
    
    @classmethod
    def get_info(cls) -> BasePipeline.Info:
        """返回 Pipeline 信息"""
        return BasePipeline.Info(
            name="mock",
            input_mode="image",
            page_content="<h1>Mock Pipeline</h1>"
        )
    
    @classmethod
    def get_input_params_schema(cls) -> dict:
        """返回参数 schema"""
        return cls.InputParams.model_json_schema()


def test_base_pipeline_info_model():
    """测试 Info 数据模型"""
    info = BasePipeline.Info(
        name="test",
        input_mode="image",
        page_content="<h1>Test</h1>"
    )
    
    assert info.name == "test"
    assert info.input_mode == "image"
    assert info.page_content == "<h1>Test</h1>"


def test_base_pipeline_input_params_model():
    """测试 InputParams 数据模型"""
    params = BasePipeline.InputParams(prompt="a beautiful landscape")
    
    assert params.prompt == "a beautiful landscape"


def test_mock_pipeline_creation():
    """测试 Mock Pipeline 的创建"""
    config = {"model_id": "test-model"}
    device = torch.device("cpu")
    dtype = torch.float32
    
    pipeline = MockPipeline(config, device, dtype)
    
    assert pipeline.config == config
    assert pipeline.device == device
    assert pipeline.dtype == dtype
    assert not pipeline.prepared


def test_mock_pipeline_prepare():
    """测试 Pipeline 的 prepare 方法"""
    pipeline = MockPipeline({}, torch.device("cpu"), torch.float32)
    
    assert not pipeline.prepared
    pipeline.prepare("test prompt")
    assert pipeline.prepared


def test_mock_pipeline_predict():
    """测试 Pipeline 的 predict 方法"""
    pipeline = MockPipeline({}, torch.device("cpu"), torch.float32)
    params = MockPipeline.InputParams(prompt="test", guidance_scale=8.0)
    
    image = pipeline.predict(params)
    
    assert isinstance(image, Image.Image)
    assert image.size == (512, 512)


def test_mock_pipeline_get_info():
    """测试 Pipeline 的 get_info 方法"""
    info = MockPipeline.get_info()
    
    assert info.name == "mock"
    assert info.input_mode == "image"
    assert info.page_content == "<h1>Mock Pipeline</h1>"


def test_mock_pipeline_get_input_params_schema():
    """测试 Pipeline 的 get_input_params_schema 方法"""
    schema = MockPipeline.get_input_params_schema()
    
    assert "properties" in schema
    assert "prompt" in schema["properties"]
    assert "guidance_scale" in schema["properties"]


def test_pipeline_factory_list_available():
    """测试 PipelineFactory 列出可用 Pipeline"""
    available = PipelineFactory.list_available_pipelines()
    
    # 应该是一个列表（可能为空，因为还没有实现具体的 Pipeline）
    assert isinstance(available, list)


def test_pipeline_factory_import_error():
    """测试 PipelineFactory 导入不存在的 Pipeline"""
    with pytest.raises(ImportError) as exc_info:
        PipelineFactory.create_pipeline(
            "nonexistent",
            {},
            torch.device("cpu"),
            torch.float32
        )
    
    assert "Failed to import pipeline 'nonexistent'" in str(exc_info.value)


def test_extended_input_params():
    """测试扩展的 InputParams"""
    params = MockPipeline.InputParams(
        prompt="test prompt",
        guidance_scale=10.0
    )
    
    assert params.prompt == "test prompt"
    assert params.guidance_scale == 10.0


def test_input_params_validation():
    """测试 InputParams 的验证"""
    # guidance_scale 应该在 1.0 到 20.0 之间
    with pytest.raises(Exception):  # Pydantic 会抛出验证错误
        MockPipeline.InputParams(
            prompt="test",
            guidance_scale=25.0  # 超出范围
        )
