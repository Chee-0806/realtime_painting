<script lang="ts">
  import { getPipelineValues, pipelineValues } from '$lib/store';

  // 提示词模板定义
  export const promptTemplates = [
    {
      id: 'branch_flowers',
      name: '🌸 线条→树枝花朵',
      description: '将简单线条转换为带花朵的树枝',
      prompt: 'flowering tree branch, cherry blossoms, detailed bark texture, natural curves, blooming flowers, delicate petals, botanical illustration, high quality, artistic style',
      negative_prompt: 'straight line, geometric, abstract, blurry, low quality, distorted, deformed, bad anatomy, poorly drawn, watermark, signature, text',
      recommended_params: {
        denoise: 0.45,
        cfg_scale: 2.8,
        steps: 3
      }
    },
    {
      id: 'portrait_photo',
      name: '📸 人像摄影',
      description: '高质量人像照片效果',
      prompt: 'portrait photography, detailed face, professional lighting, high resolution, sharp focus, natural skin texture, cinematic lighting, masterpiece',
      negative_prompt: 'blurry, low quality, distorted, deformed, bad anatomy, extra limbs, disfigured, poorly drawn, watermark, signature',
      recommended_params: {
        denoise: 0.3,
        cfg_scale: 2.0,
        steps: 2
      }
    },
    {
      id: 'landscape_art',
      name: '🏔️ 风景绘画',
      description: '艺术风景画效果',
      prompt: 'beautiful landscape, cinematic lighting, detailed environment, atmospheric, high quality, professional photography, artistic style, vibrant colors',
      negative_prompt: 'blurry, low quality, distorted, oversaturated, poorly drawn, amateur, watermark',
      recommended_params: {
        denoise: 0.4,
        cfg_scale: 2.5,
        steps: 3
      }
    },
    {
      id: 'anime_style',
      name: '🎌 动漫风格',
      description: '日式动漫插画风格',
      prompt: 'anime style, manga art, clean lines, vibrant colors, detailed shading, professional illustration, high quality anime artwork',
      negative_prompt: 'realistic, photo, 3d render, blurry, low quality, distorted, bad anatomy',
      recommended_params: {
        denoise: 0.5,
        cfg_scale: 3.0,
        steps: 4
      }
    },
    {
      id: 'abstract_art',
      name: '🎨 抽象艺术',
      description: '现代抽象艺术风格',
      prompt: 'abstract art, vibrant colors, flowing shapes, contemporary, gallery quality, artistic composition, modern art style',
      negative_prompt: 'realistic, photorealistic, blurry, low quality, amateur, childish, simple shapes',
      recommended_params: {
        denoise: 0.6,
        cfg_scale: 3.5,
        steps: 4
      }
    },
    {
      id: 'sketch_line_art',
      name: '✏️ 素描线稿',
      description: '精细素描线条艺术',
      prompt: 'line art, clean lines, detailed drawing, sketch, professional illustration, black and white, high contrast, artistic lines',
      negative_prompt: 'colorful, blurry, low quality, messy lines, amateur drawing, photorealistic',
      recommended_params: {
        denoise: 0.2,
        cfg_scale: 2.0,
        steps: 2
      }
    }
  ];

  // 应用模板
  function applyTemplate(template: typeof promptTemplates[0]) {
    const currentValues = getPipelineValues();

    // 应用提示词
    pipelineValues.set({
      ...currentValues,
      prompt: template.prompt,
      negative_prompt: template.negative_prompt,
      // 应用推荐参数（如果用户没有自定义的话）
      denoise: template.recommended_params.denoise,
      cfg_scale: template.recommended_params.cfg_scale,
      steps: template.recommended_params.steps
    });

    // 触发自定义事件通知父组件
    const event = new CustomEvent('templateApplied', {
      detail: {
        template: template,
        message: `已应用 "${template.name}" 模板`
      }
    });
    document.dispatchEvent(event);
  }

  // 导出函数供父组件使用
  export { applyTemplate };
</script>

<div class="bg-surface/50 p-4 rounded-xl border border-border">
  <div class="flex items-center justify-between mb-3">
    <h4 class="text-sm font-semibold text-text-primary flex items-center gap-2">
      <span>🎯</span>
      <span>提示词模板</span>
    </h4>
    <div class="text-xs text-text-tertiary">
      快速应用专业配置
    </div>
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
    {#each promptTemplates as template}
      <button
        on:click={() => applyTemplate(template)}
        class="group p-3 bg-surface hover:bg-primary/10 border border-border hover:border-primary/30 rounded-lg transition-all duration-200 text-left"
        title={template.description}
      >
        <div class="flex items-center justify-between mb-1">
          <span class="text-sm font-medium text-text-primary group-hover:text-primary">
            {template.name}
          </span>
          <span class="text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity">
            ✓ 应用
          </span>
        </div>
        <p class="text-xs text-text-secondary line-clamp-2">
          {template.description}
        </p>
        <div class="mt-2 flex gap-1">
          {#if template.recommended_params.denoise}
            <span class="text-xs px-1.5 py-0.5 bg-surface-elevated rounded text-text-tertiary">
              δ{template.recommended_params.denoise}
            </span>
          {/if}
          {#if template.recommended_params.cfg_scale}
            <span class="text-xs px-1.5 py-0.5 bg-surface-elevated rounded text-text-tertiary">
              cfg{template.recommended_params.cfg_scale}
            </span>
          {/if}
          {#if template.recommended_params.steps}
            <span class="text-xs px-1.5 py-0.5 bg-surface-elevated rounded text-text-tertiary">
              {template.recommended_params.steps}步
            </span>
          {/if}
        </div>
      </button>
    {/each}
  </div>

  <div class="mt-3 p-2 bg-surface-elevated/50 rounded-lg border border-border">
    <p class="text-xs text-text-tertiary text-center">
      💡 <strong>使用提示：</strong>点击模板快速应用专业配置，包含优化的提示词和推荐参数
    </p>
  </div>
</div>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>