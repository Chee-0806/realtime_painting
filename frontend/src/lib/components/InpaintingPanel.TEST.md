# InpaintingPanel 测试指南

## 快速测试步骤

### 1. 集成到测试页面

在 `frontend/src/routes/tools/+page.svelte` 中添加：

```svelte
<script lang="ts">
  import InpaintingPanel from '$lib/components/InpaintingPanel.svelte';
</script>

<div class="container mx-auto p-6">
  <h1 class="text-2xl font-bold mb-6">工具测试页面</h1>
  
  <div class="card">
    <InpaintingPanel />
  </div>
</div>
```

### 2. 启动开发服务器

```bash
cd frontend
npm run dev
```

访问: http://localhost:5173/tools

### 3. 功能测试清单

#### ✅ 图像上传测试

- [ ] 点击"选择图像"按钮
- [ ] 选择一个PNG/JPG图像文件
- [ ] 验证图像正确显示在Canvas上
- [ ] 验证图像自动缩放到合适大小
- [ ] 尝试上传非图像文件，验证错误提示

#### ✅ 蒙版绘制测试

- [ ] 选择画笔工具
- [ ] 在图像上绘制，验证红色蒙版显示
- [ ] 调整画笔大小，验证画笔变化
- [ ] 调整画笔硬度，验证边缘效果
- [ ] 切换到橡皮擦工具
- [ ] 擦除部分蒙版，验证擦除效果
- [ ] 点击"清除"按钮，验证蒙版完全清除

#### ✅ 参数配置测试

- [ ] 输入Prompt文本
- [ ] 输入Negative Prompt文本
- [ ] 调整重绘强度滑块，验证数值显示
- [ ] 调整引导强度滑块，验证数值显示
- [ ] 调整生成步数滑块，验证数值显示

#### ✅ 生成功能测试

**前提：需要后端API支持**

- [ ] 不输入Prompt点击"开始重绘"，验证错误提示
- [ ] 输入Prompt后点击"开始重绘"
- [ ] 验证按钮显示"生成中..."和加载动画
- [ ] 等待生成完成
- [ ] 验证结果图像正确显示
- [ ] 点击"下载"按钮，验证图像下载

#### ✅ 错误处理测试

- [ ] 在未上传图像时点击"开始重绘"，验证错误提示
- [ ] 在未输入Prompt时点击"开始重绘"，验证错误提示
- [ ] 模拟网络错误（断开网络），验证错误提示
- [ ] 验证错误提示包含建议信息

#### ✅ 重置功能测试

- [ ] 完成一次完整的Inpainting流程
- [ ] 点击"重置"按钮
- [ ] 验证所有状态清除：
  - 图像清除
  - 蒙版清除
  - Prompt清除
  - 结果清除
  - 错误清除

### 4. UI/UX测试

#### 视觉测试

- [ ] 验证组件在不同屏幕尺寸下的显示
- [ ] 验证按钮hover效果
- [ ] 验证禁用状态样式
- [ ] 验证加载状态动画
- [ ] 验证错误提示样式
- [ ] 验证成功状态样式

#### 交互测试

- [ ] 验证鼠标绘制流畅度
- [ ] 验证滑块拖动响应
- [ ] 验证按钮点击反馈
- [ ] 验证文本输入体验

### 5. 性能测试

- [ ] 上传大图像（>2MB），验证加载时间
- [ ] 连续绘制蒙版，验证Canvas性能
- [ ] 多次生成，验证内存使用
- [ ] 检查浏览器控制台是否有错误或警告

### 6. 兼容性测试

#### 浏览器测试

- [ ] Chrome/Edge (推荐)
- [ ] Firefox
- [ ] Safari

#### 图像格式测试

- [ ] PNG
- [ ] JPG/JPEG
- [ ] WebP
- [ ] GIF (静态)

## Mock API测试

如果后端API尚未实现，可以使用Mock数据测试：

### 方法1: 修改组件使用Mock数据

在 `performInpainting()` 函数中临时添加：

```typescript
async function performInpainting() {
  // ... 验证代码 ...
  
  loading = true;
  clearError();
  
  // Mock响应（用于测试）
  await new Promise(resolve => setTimeout(resolve, 2000)); // 模拟2秒延迟
  
  resultImage = sourceImage; // 使用源图像作为结果
  showResult = true;
  loading = false;
  return;
  
  // 实际API调用代码...
}
```

### 方法2: 使用Mock Service Worker

创建 `frontend/src/mocks/handlers.ts`:

```typescript
import { rest } from 'msw';

export const handlers = [
  rest.post('/api/inpaint', async (req, res, ctx) => {
    const body = await req.json();
    
    // 模拟处理延迟
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    return res(
      ctx.status(200),
      ctx.json({
        success: true,
        image: body.image, // 返回原图作为测试
        message: 'Inpainting完成（Mock）'
      })
    );
  })
];
```

## 测试结果记录

### 测试环境

- 浏览器: ___________
- 操作系统: ___________
- 日期: ___________

### 测试结果

| 测试项 | 状态 | 备注 |
|--------|------|------|
| 图像上传 | ⬜ 通过 / ⬜ 失败 | |
| 蒙版绘制 | ⬜ 通过 / ⬜ 失败 | |
| 画笔工具 | ⬜ 通过 / ⬜ 失败 | |
| 参数配置 | ⬜ 通过 / ⬜ 失败 | |
| 生成功能 | ⬜ 通过 / ⬜ 失败 | |
| 错误处理 | ⬜ 通过 / ⬜ 失败 | |
| 重置功能 | ⬜ 通过 / ⬜ 失败 | |
| UI/UX | ⬜ 通过 / ⬜ 失败 | |
| 性能 | ⬜ 通过 / ⬜ 失败 | |

### 发现的问题

1. ___________
2. ___________
3. ___________

### 改进建议

1. ___________
2. ___________
3. ___________

## 自动化测试（未来）

可以使用以下工具编写自动化测试：

- **单元测试**: Vitest + @testing-library/svelte
- **E2E测试**: Playwright
- **视觉回归测试**: Percy 或 Chromatic

示例单元测试：

```typescript
import { render, fireEvent } from '@testing-library/svelte';
import InpaintingPanel from './InpaintingPanel.svelte';

describe('InpaintingPanel', () => {
  it('should render upload button', () => {
    const { getByText } = render(InpaintingPanel);
    expect(getByText('选择图像')).toBeInTheDocument();
  });
  
  it('should show error when generating without prompt', async () => {
    const { getByText } = render(InpaintingPanel);
    // 模拟上传图像
    // ...
    const button = getByText('开始重绘');
    await fireEvent.click(button);
    // 验证错误提示
  });
});
```

## 验收标准

组件通过测试的标准：

✅ 所有核心功能正常工作
✅ 错误处理完善，提示清晰
✅ UI响应流畅，无明显卡顿
✅ 无控制台错误或警告
✅ 符合设计规范和用户体验要求
✅ 代码质量良好，无明显bug

## 下一步

测试通过后：

1. 集成到主页面或工具页面
2. 连接实际的后端API
3. 进行用户验收测试
4. 收集反馈并优化
