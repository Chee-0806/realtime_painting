# CLIPInterrogatorPanel 组件测试指南

## 测试概述

本文档提供 `CLIPInterrogatorPanel` 组件的完整测试指南，包括功能测试、集成测试和用户体验测试。

## 测试环境准备

### 1. 启动后端服务

确保后端 CLIP 服务正常运行：

```bash
# 启动后端
python -m app.main
```

### 2. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

### 3. 访问示例页面

打开浏览器访问示例页面：
```
http://localhost:5173/
```

---

## 功能测试清单

### ✅ 1. 图像上传功能

#### 1.1 点击上传
- [ ] 点击"点击上传图像"按钮
- [ ] 选择一个有效的图像文件（JPG/PNG）
- [ ] 验证图像预览正确显示
- [ ] 验证图像尺寸自适应（max-h-64）

#### 1.2 文件类型验证
- [ ] 尝试上传非图像文件（如 .txt）
- [ ] 验证显示错误提示："请上传图像文件"
- [ ] 验证上传按钮仍然可用

#### 1.3 文件大小验证
- [ ] 尝试上传超过 10MB 的图像
- [ ] 验证显示错误提示："图像文件过大"
- [ ] 验证上传按钮仍然可用

#### 1.4 更换图像
- [ ] 上传第一张图像
- [ ] 点击"更换"按钮
- [ ] 选择第二张图像
- [ ] 验证图像预览更新为新图像

#### 1.5 清除图像
- [ ] 上传一张图像
- [ ] 点击"清除"按钮
- [ ] 验证图像预览消失
- [ ] 验证显示上传按钮

---

### ✅ 2. 反推模式功能

#### 2.1 快速模式
- [ ] 上传图像
- [ ] 选择"⚡ 快速模式"
- [ ] 点击"🚀 开始反推"
- [ ] 验证显示加载动画
- [ ] 验证反推完成后显示结果
- [ ] 验证 Prompt 内容合理

#### 2.2 经典模式
- [ ] 上传图像
- [ ] 选择"🎯 经典模式"
- [ ] 点击"🚀 开始反推"
- [ ] 验证处理时间较长
- [ ] 验证反推结果更详细

#### 2.3 负面模式
- [ ] 上传图像
- [ ] 选择"🚫 负面Prompt"
- [ ] 点击"🚀 开始反推"
- [ ] 验证生成负面提示词
- [ ] 验证 Negative Prompt 内容合理

#### 2.4 模式切换
- [ ] 在反推过程中尝试切换模式
- [ ] 验证下拉菜单被禁用
- [ ] 等待反推完成
- [ ] 验证可以切换模式

---

### ✅ 3. 结果显示功能

#### 3.1 Prompt 显示
- [ ] 完成反推
- [ ] 验证显示 Prompt 文本框
- [ ] 验证 Prompt 内容可读
- [ ] 验证文本框为只读状态

#### 3.2 Negative Prompt 显示
- [ ] 完成反推
- [ ] 验证显示 Negative Prompt 文本框
- [ ] 验证内容合理
- [ ] 验证文本框为只读状态

#### 3.3 风格标签显示
- [ ] 完成反推
- [ ] 验证显示风格标签（如果有）
- [ ] 验证标签样式正确
- [ ] 验证标签内容合理

#### 3.4 模式标识
- [ ] 完成反推
- [ ] 验证显示当前使用的模式
- [ ] 验证模式图标正确

---

### ✅ 4. 操作功能

#### 4.1 复制 Prompt
- [ ] 完成反推
- [ ] 点击 Prompt 的"📋 复制"按钮
- [ ] 打开文本编辑器粘贴
- [ ] 验证复制的内容正确

#### 4.2 复制 Negative Prompt
- [ ] 完成反推
- [ ] 点击 Negative Prompt 的"📋 复制"按钮
- [ ] 打开文本编辑器粘贴
- [ ] 验证复制的内容正确

#### 4.3 应用 Prompt
- [ ] 完成反推
- [ ] 点击"✓ 应用"按钮
- [ ] 打开浏览器控制台
- [ ] 验证 pipelineValues store 已更新
- [ ] 验证触发 `apply` 事件

#### 4.4 关闭面板
- [ ] 点击右上角"✕"按钮
- [ ] 验证触发 `close` 事件
- [ ] （在集成环境中）验证面板关闭

---

### ✅ 5. 错误处理

#### 5.1 无图像错误
- [ ] 不上传图像
- [ ] 直接点击"🚀 开始反推"
- [ ] 验证显示错误提示："请先上传或选择图像"

#### 5.2 网络错误
- [ ] 停止后端服务
- [ ] 上传图像并开始反推
- [ ] 验证显示网络错误提示
- [ ] 验证错误可以关闭

#### 5.3 API 错误
- [ ] 上传无效的图像数据
- [ ] 开始反推
- [ ] 验证显示 API 错误提示
- [ ] 验证显示错误详情

#### 5.4 错误恢复
- [ ] 触发错误
- [ ] 点击错误提示的"✕"按钮
- [ ] 验证错误提示消失
- [ ] 验证可以重新尝试

---

### ✅ 6. Props 功能

#### 6.1 initialImageUrl
- [ ] 设置 `initialImageUrl` prop
- [ ] 验证组件加载时显示图像
- [ ] 验证可以直接开始反推

#### 6.2 showCloseButton
- [ ] 设置 `showCloseButton={false}`
- [ ] 验证不显示关闭按钮
- [ ] 设置 `showCloseButton={true}`
- [ ] 验证显示关闭按钮

#### 6.3 autoApplyPrompt
- [ ] 设置 `autoApplyPrompt={true}`
- [ ] 完成反推
- [ ] 验证自动应用 Prompt
- [ ] 验证触发 `apply` 事件

---

### ✅ 7. 事件系统

#### 7.1 result 事件
- [ ] 监听 `on:result` 事件
- [ ] 完成反推
- [ ] 验证事件被触发
- [ ] 验证事件数据包含：
  - `prompt`
  - `negative_prompt`
  - `flavors`
  - `mode`

#### 7.2 apply 事件
- [ ] 监听 `on:apply` 事件
- [ ] 点击"✓ 应用"按钮
- [ ] 验证事件被触发
- [ ] 验证事件数据正确

#### 7.3 copy 事件
- [ ] 监听 `on:copy` 事件
- [ ] 点击"📋 复制"按钮
- [ ] 验证事件被触发
- [ ] 验证事件数据包含：
  - `type`: 'prompt' 或 'negative_prompt'
  - `text`: 复制的文本

#### 7.4 close 事件
- [ ] 监听 `on:close` 事件
- [ ] 点击关闭按钮
- [ ] 验证事件被触发

---

## 集成测试

### 1. 与主页面集成

```svelte
<!-- 在主页面中使用 -->
<script>
  import CLIPInterrogatorPanel from '$lib/components/CLIPInterrogatorPanel.svelte';
  
  let showCLIP = false;
</script>

<button on:click={() => showCLIP = !showCLIP}>
  CLIP 反推
</button>

{#if showCLIP}
  <CLIPInterrogatorPanel on:close={() => showCLIP = false} />
{/if}
```

测试步骤：
- [ ] 点击"CLIP 反推"按钮
- [ ] 验证面板显示
- [ ] 上传图像并反推
- [ ] 点击"应用"
- [ ] 验证主页面参数更新
- [ ] 点击关闭按钮
- [ ] 验证面板关闭

### 2. 与画板页面集成

测试步骤：
- [ ] 在画板页面绘制图像
- [ ] 点击"分析画布图像"
- [ ] 验证 CLIPInterrogatorPanel 显示
- [ ] 验证画布图像正确传递
- [ ] 完成反推
- [ ] 点击"应用"
- [ ] 验证画板参数更新

### 3. 与生成结果集成

测试步骤：
- [ ] 生成一张图像
- [ ] 点击"分析生成结果"
- [ ] 验证 CLIPInterrogatorPanel 显示
- [ ] 验证生成结果图像正确传递
- [ ] 完成反推
- [ ] 验证结果合理

---

## 性能测试

### 1. 大图像处理

- [ ] 上传 5MB 的图像
- [ ] 验证预览加载速度
- [ ] 验证反推处理时间
- [ ] 验证内存使用正常

### 2. 快速切换

- [ ] 快速上传多张图像
- [ ] 验证组件响应正常
- [ ] 验证没有内存泄漏

### 3. 并发反推

- [ ] 在反推过程中尝试再次反推
- [ ] 验证按钮被禁用
- [ ] 验证不会发起重复请求

---

## 用户体验测试

### 1. 加载状态

- [ ] 开始反推
- [ ] 验证显示加载动画
- [ ] 验证按钮文本变为"正在分析图像..."
- [ ] 验证按钮被禁用

### 2. 响应式设计

- [ ] 在桌面浏览器测试
- [ ] 在平板设备测试
- [ ] 在手机设备测试
- [ ] 验证布局适配正常

### 3. 可访问性

- [ ] 使用键盘导航
- [ ] 验证所有按钮可以通过 Tab 键访问
- [ ] 验证 Enter 键可以触发操作
- [ ] 使用屏幕阅读器测试

---

## 浏览器兼容性测试

### Chrome
- [ ] 版本 90+
- [ ] 所有功能正常

### Firefox
- [ ] 版本 88+
- [ ] 所有功能正常

### Safari
- [ ] 版本 14+
- [ ] 所有功能正常

### Edge
- [ ] 版本 90+
- [ ] 所有功能正常

---

## 已知问题

### 问题 1: 大图像预览可能较慢
- **影响**: 上传大图像时预览加载较慢
- **解决方案**: 使用 `max-h-64` 限制预览高度
- **状态**: 已优化

### 问题 2: 经典模式处理时间长
- **影响**: 经典模式可能需要 10-30 秒
- **解决方案**: 显示加载动画和提示
- **状态**: 正常行为

---

## 测试报告模板

```markdown
## CLIPInterrogatorPanel 测试报告

**测试日期**: YYYY-MM-DD
**测试人员**: [姓名]
**测试环境**: 
- 浏览器: Chrome 120
- 操作系统: macOS 14
- 后端版本: v1.0.0

### 测试结果

| 测试项 | 状态 | 备注 |
|--------|------|------|
| 图像上传 | ✅ 通过 | |
| 反推模式 | ✅ 通过 | |
| 结果显示 | ✅ 通过 | |
| 操作功能 | ✅ 通过 | |
| 错误处理 | ✅ 通过 | |
| Props 功能 | ✅ 通过 | |
| 事件系统 | ✅ 通过 | |

### 发现的问题

1. [问题描述]
   - 严重程度: 高/中/低
   - 复现步骤: ...
   - 预期结果: ...
   - 实际结果: ...

### 建议

1. [改进建议]

### 总结

[测试总结]
```

---

## 自动化测试（可选）

### 单元测试示例

```typescript
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import CLIPInterrogatorPanel from './CLIPInterrogatorPanel.svelte';

describe('CLIPInterrogatorPanel', () => {
  it('should render upload button initially', () => {
    const { getByText } = render(CLIPInterrogatorPanel);
    expect(getByText('点击上传图像')).toBeInTheDocument();
  });
  
  it('should show image preview after upload', async () => {
    const { getByLabelText, getByAltText } = render(CLIPInterrogatorPanel);
    const input = getByLabelText('上传图像') as HTMLInputElement;
    
    const file = new File(['test'], 'test.png', { type: 'image/png' });
    await fireEvent.change(input, { target: { files: [file] } });
    
    await waitFor(() => {
      expect(getByAltText('预览图像')).toBeInTheDocument();
    });
  });
  
  it('should trigger result event on successful interrogation', async () => {
    const handleResult = jest.fn();
    const { component, getByText } = render(CLIPInterrogatorPanel);
    
    component.$on('result', handleResult);
    
    // Mock API response
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          success: true,
          prompt: 'test prompt',
          negative_prompt: 'test negative',
          flavors: ['test'],
          mode: 'fast'
        })
      })
    ) as jest.Mock;
    
    // Upload image and start interrogation
    // ...
    
    await waitFor(() => {
      expect(handleResult).toHaveBeenCalled();
    });
  });
});
```

---

## 测试完成标准

所有测试项目必须通过才能认为组件测试完成：

- ✅ 所有功能测试通过
- ✅ 所有集成测试通过
- ✅ 性能测试达标
- ✅ 用户体验良好
- ✅ 浏览器兼容性确认
- ✅ 无严重 bug

---

**最后更新**: 2025-11-17
**文档版本**: 1.0.0
