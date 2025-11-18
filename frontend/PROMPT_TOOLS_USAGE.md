# PromptTools 使用指南

## 功能概述

PromptTools 是一个集成在 Prompt 输入框下方的工具栏，提供三大核心功能：
1. **模板选择** - 快速应用预设的风格模板
2. **历史记录** - 自动保存和加载历史 Prompt
3. **通配符** - 插入随机变量，增加生成多样性

## 使用方法

### 1. 模板选择 📝

**步骤**:
1. 在 Prompt 输入框下方点击 "📝 模板" 按钮
2. 从弹出的面板中选择一个模板
3. 模板内容会自动添加到你的 Prompt 中

**可用模板**:
- **写实风格**: 适合生成照片级真实图像
- **动漫风格**: 适合生成动漫插画
- **油画风格**: 适合生成古典艺术风格
- **赛博朋克**: 适合生成未来科幻风格
- **水彩画**: 适合生成柔和的水彩效果

**示例**:
```
原始 Prompt: "a beautiful landscape"
选择"写实风格"后: "a beautiful landscape, photorealistic, highly detailed, 8k uhd, professional photography"
```

### 2. 历史记录 📜

**自动保存**:
- 每次修改 Prompt 后，系统会自动保存到历史记录
- 最多保存 20 条记录
- 历史记录会持久化保存，刷新页面不会丢失

**使用历史**:
1. 点击 "📜 历史 (数量)" 按钮
2. 从列表中选择之前使用过的 Prompt
3. 点击即可加载到输入框

**管理历史**:
- 点击"清除"按钮可以删除所有历史记录
- 相同的 Prompt 不会重复保存
- 新记录会显示在列表顶部

### 3. 通配符 🎲

**什么是通配符**:
通配符使用 `{选项1|选项2|选项3}` 格式，在生成图像时会随机选择一个选项。

**可用通配符**:
- **随机颜色**: `{red|blue|green|yellow|purple|orange}`
- **随机时间**: `{morning|afternoon|evening|night}`
- **随机天气**: `{sunny|cloudy|rainy|snowy|foggy}`
- **随机情绪**: `{happy|sad|angry|peaceful|excited}`

**使用方法**:
1. 点击 "🎲 通配符" 按钮
2. 选择要插入的通配符类型
3. 通配符会添加到 Prompt 末尾

**示例**:
```
Prompt: "a {red|blue|green} car in {morning|evening} light"

可能的生成结果:
- "a red car in morning light"
- "a blue car in evening light"
- "a green car in morning light"
等等...
```

## 高级技巧

### 组合使用

你可以同时使用模板、历史记录和通配符：

```
1. 从历史记录加载: "a beautiful landscape"
2. 添加模板: "a beautiful landscape, photorealistic, highly detailed, 8k uhd"
3. 插入通配符: "a beautiful landscape, photorealistic, highly detailed, 8k uhd, {morning|evening} light"
```

### 自定义通配符

虽然界面提供了预设通配符，你也可以手动输入自定义通配符：

```
"a {cat|dog|bird} sitting on a {chair|table|floor}"
```

### 批量生成

使用通配符可以轻松生成多样化的图像：

```
"a {red|blue|green|yellow} {car|bike|boat} in {sunny|rainy} weather"
```

这个 Prompt 可以生成 4×3×2 = 24 种不同的组合！

## 快捷操作

- **展开/折叠面板**: 点击按钮即可切换
- **关闭面板**: 点击面板右上角的 ✕ 按钮
- **快速加载**: 直接点击历史记录项即可加载

## 注意事项

1. **历史记录限制**: 最多保存 20 条，超过后会自动删除最旧的记录
2. **去重机制**: 相同的 Prompt 不会重复保存
3. **持久化**: 历史记录保存在浏览器本地，清除浏览器数据会丢失
4. **通配符格式**: 必须使用 `{选项1|选项2}` 格式，用竖线分隔选项

## 常见问题

**Q: 历史记录在哪里保存？**
A: 保存在浏览器的 LocalStorage 中，key 为 'prompt_history'

**Q: 可以添加自己的模板吗？**
A: 当前版本不支持，但你可以使用历史记录功能保存常用的 Prompt

**Q: 通配符在什么时候被替换？**
A: 在后端生成图像时，系统会自动随机选择一个选项

**Q: 可以嵌套使用通配符吗？**
A: 不建议，可能导致解析错误

**Q: 历史记录会同步到其他设备吗？**
A: 不会，历史记录只保存在当前浏览器中

## 反馈和建议

如果你有任何建议或发现问题，欢迎反馈！

---

**版本**: 1.0
**更新时间**: 2025-11-14
