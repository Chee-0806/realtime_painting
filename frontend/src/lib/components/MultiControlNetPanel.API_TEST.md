# MultiControlNetPanel API集成测试指南

## 概述

本文档说明如何测试MultiControlNetPanel组件与后端多ControlNet API的集成。

## API端点

### 获取可用的ControlNet类型

**端点**: `GET /api/controlnet/types`

**响应**:
```json
{
  "success": true,
  "types": ["canny", "depth", "pose", "scribble", "lineart", "normal", "semantic"]
}
```

### 多ControlNet生成

**端点**: `POST /api/controlnet/multi`

**请求体**:
```json
{
  "prompt": "a beautiful landscape",
  "negative_prompt": "ugly, blurry",
  "controlnet_configs": [
    {
      "type": "canny",
      "image": "data:image/png;base64,...",
      "weight": 1.0
    },
    {
      "type": "depth",
      "image": "data:image/png;base64,...",
      "weight": 0.8
    }
  ],
  "num_inference_steps": 20,
  "guidance_scale": 7.5,
  "height": 512,
  "width": 512,
  "seed": null
}
```

**响应**:
```json
{
  "success": true,
  "image": "data:image/png;base64,..."
}
```

## 测试步骤

### 1. 准备测试环境

确保后端服务正在运行：
```bash
cd /path/to/streamdiffusion-mvp
python -m app.main
```

确保前端开发服务器正在运行：
```bash
cd frontend
npm run dev
```

### 2. 测试组件初始化

1. 打开浏览器访问示例页面
2. 检查MultiControlNetPanel组件是否正确渲染
3. 验证"添加ControlNet"按钮是否可用
4. 检查控制台是否有ControlNet类型加载日志

**预期结果**:
- 组件正常显示
- 控制台显示: `✅ 成功获取X个ControlNet类型: [...]`

### 3. 测试添加ControlNet

1. 点击"添加ControlNet"按钮
2. 验证新的ControlNet配置项是否出现
3. 检查类型下拉菜单是否包含所有可用类型
4. 尝试添加多个ControlNet（最多3个）

**预期结果**:
- 每次点击都会添加新的ControlNet配置项
- 达到3个后按钮变为禁用状态
- 显示"已达到最大数量（3个）"提示

### 4. 测试图像上传

1. 为每个ControlNet上传控制图像
2. 验证图像预览是否正确显示
3. 检查图像是否正确转换为Base64格式

**预期结果**:
- 图像上传后立即显示预览
- 控制台显示图像数据信息

### 5. 测试参数配置

1. 调整每个ControlNet的权重滑块
2. 修改引导范围（guidanceStart和guidanceEnd）
3. 验证参数值是否正确更新

**预期结果**:
- 滑块值实时更新
- 参数值在合理范围内（0.0-2.0）

### 6. 测试API调用

#### 方法1：使用示例页面

1. 打开MultiControlNetPanel.example.svelte示例页面
2. 添加至少一个ControlNet并上传图像
3. 点击"开始生成"按钮
4. 观察控制台日志和网络请求

**预期结果**:
- 控制台显示: `🚀 发送多ControlNet生成请求: {...}`
- 网络面板显示POST请求到`/api/controlnet/multi`
- 请求体包含正确的参数
- 生成成功后显示: `✅ 多ControlNet生成成功`
- 结果图像正确显示

#### 方法2：使用浏览器控制台

```javascript
// 在浏览器控制台中执行
const testMultiControlNet = async () => {
  const response = await fetch('/api/controlnet/multi', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: 'a beautiful landscape',
      negative_prompt: 'ugly, blurry',
      controlnet_configs: [
        {
          type: 'canny',
          image: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
          weight: 1.0
        }
      ],
      num_inference_steps: 20,
      guidance_scale: 7.5,
      height: 512,
      width: 512
    })
  });
  
  const result = await response.json();
  console.log('API响应:', result);
  return result;
};

testMultiControlNet();
```

### 7. 测试错误处理

#### 测试场景1：没有添加ControlNet

1. 不添加任何ControlNet
2. 尝试调用generate方法

**预期结果**:
- 返回错误: `请至少添加一个ControlNet并上传图像`
- 不发送API请求

#### 测试场景2：ControlNet没有上传图像

1. 添加ControlNet但不上传图像
2. 尝试生成

**预期结果**:
- 验证失败: `请为所有ControlNet上传图像`
- 显示错误提示

#### 测试场景3：API错误

1. 停止后端服务
2. 尝试生成图像

**预期结果**:
- 显示网络错误提示
- 错误处理器显示详细错误信息和建议

#### 测试场景4：超过最大数量

1. 尝试添加超过3个ControlNet

**预期结果**:
- 按钮变为禁用
- 显示"已达到最大数量"提示

### 8. 测试加载状态

1. 开始生成图像
2. 观察加载状态显示

**预期结果**:
- 显示加载动画
- 显示"正在生成..."文本
- 生成按钮变为禁用状态

### 9. 测试多ControlNet组合

测试不同的ControlNet组合：

#### 组合1：Canny + Depth
```javascript
{
  controlnet_configs: [
    { type: 'canny', image: '...', weight: 1.0 },
    { type: 'depth', image: '...', weight: 0.8 }
  ]
}
```

#### 组合2：Pose + Scribble + Lineart
```javascript
{
  controlnet_configs: [
    { type: 'pose', image: '...', weight: 1.0 },
    { type: 'scribble', image: '...', weight: 0.7 },
    { type: 'lineart', image: '...', weight: 0.5 }
  ]
}
```

**预期结果**:
- 所有组合都能正常工作
- 生成的图像反映多个ControlNet的影响

## 性能测试

### 测试生成时间

1. 记录单个ControlNet的生成时间
2. 记录2个ControlNet的生成时间
3. 记录3个ControlNet的生成时间

**预期结果**:
- 生成时间随ControlNet数量增加而增加
- 但增加幅度应该是合理的（不是线性增长）

### 测试内存使用

1. 打开浏览器开发者工具的Performance面板
2. 开始录制
3. 执行多次生成
4. 停止录制并分析内存使用

**预期结果**:
- 内存使用稳定，没有明显泄漏
- 图像数据正确释放

## 调试技巧

### 查看网络请求

1. 打开浏览器开发者工具
2. 切换到Network面板
3. 筛选XHR/Fetch请求
4. 查看`/api/controlnet/multi`请求的详细信息

### 查看控制台日志

关键日志信息：
- `✅ 成功获取X个ControlNet类型`
- `🚀 发送多ControlNet生成请求`
- `✅ 多ControlNet生成成功`
- `❌ 多ControlNet生成失败`

### 查看后端日志

后端关键日志：
- `加载ControlNet模型: ...`
- `✓ ControlNet模型已加载: ...`
- `使用MultiControlNetModel支持X个ControlNet`
- `Multi-ControlNet生成失败: ...`

## 常见问题

### Q1: ControlNet类型列表为空

**原因**: 后端API未正确返回类型列表

**解决方案**:
1. 检查后端服务是否正常运行
2. 检查`/api/controlnet/types`端点是否可访问
3. 查看后端日志是否有错误

### Q2: 图像上传后无法生成

**原因**: 图像格式不正确或Base64编码问题

**解决方案**:
1. 确保图像是PNG或JPEG格式
2. 检查Base64编码是否包含正确的前缀
3. 验证图像大小是否合理（建议512x512）

### Q3: 生成速度很慢

**原因**: 多个ControlNet增加了计算负担

**解决方案**:
1. 减少ControlNet数量
2. 降低推理步数
3. 使用更小的图像尺寸
4. 检查GPU显存是否充足

### Q4: 某些ControlNet类型不可用

**原因**: 对应的ControlNet模型未加载

**解决方案**:
1. 检查后端日志中的模型加载信息
2. 确保模型ID正确
3. 检查网络连接（首次使用需要下载模型）
4. 尝试使用其他ControlNet类型（如canny、depth、pose）

## 验收标准

✅ 所有测试步骤都通过
✅ 错误处理正确且用户友好
✅ 加载状态正确显示
✅ API请求和响应格式正确
✅ 生成的图像质量符合预期
✅ 性能表现良好
✅ 没有内存泄漏
✅ 控制台没有错误日志

## 总结

MultiControlNetPanel组件已成功集成后端多ControlNet API，支持：
- ✅ 动态添加/删除ControlNet（最多3个）
- ✅ 图像上传和预览
- ✅ 参数配置（类型、权重、引导范围）
- ✅ API调用和结果处理
- ✅ 完善的错误处理
- ✅ 加载状态显示

下一步可以将此组件集成到主页面和画板页面中。
