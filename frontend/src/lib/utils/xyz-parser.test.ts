/**
 * XYZ Parser 单元测试
 * 
 * 测试参数范围解析功能
 */

import { describe, it, expect } from 'vitest';
import {
  parseParameterValues,
  validateGridConfiguration,
  calculateParameterCombinations,
  getExampleValues,
  formatParameterValues
} from './xyz-parser';

describe('parseParameterValues', () => {
  it('应该解析逗号分隔的数值', () => {
    const result = parseParameterValues('1, 2, 3, 4', 'numeric');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([1, 2, 3, 4]);
    expect(result.count).toBe(4);
  });

  it('应该解析带小数的数值', () => {
    const result = parseParameterValues('1.0, 2.5, 3.7', 'cfg_scale');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([1.0, 2.5, 3.7]);
  });

  it('应该解析范围表达式（冒号格式）', () => {
    const result = parseParameterValues('1.0-5.0:1.0', 'numeric');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([1.0, 2.0, 3.0, 4.0, 5.0]);
    expect(result.count).toBe(5);
  });

  it('应该解析范围表达式（步长格式）', () => {
    const result = parseParameterValues('1-5, 步长1', 'numeric');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([1, 2, 3, 4, 5]);
  });

  it('应该解析范围表达式（step格式）', () => {
    const result = parseParameterValues('1-5, step 2', 'numeric');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([1, 3, 5]);
  });

  it('应该解析混合格式', () => {
    const result = parseParameterValues('1, 2-4:1, 5', 'numeric');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([1, 2, 3, 4, 5]);
  });

  it('应该解析小数范围', () => {
    const result = parseParameterValues('5.0-10.0:2.5', 'cfg_scale');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([5.0, 7.5, 10.0]);
  });

  it('应该处理空字符串', () => {
    const result = parseParameterValues('', 'numeric');
    expect(result.isValid).toBe(false);
    expect(result.error).toBeDefined();
  });

  it('应该处理无效的范围表达式', () => {
    const result = parseParameterValues('5-1:1', 'numeric'); // 起始值大于结束值
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('起始值必须小于结束值');
  });

  it('应该去除重复值', () => {
    const result = parseParameterValues('1, 2, 2, 3, 3, 3', 'numeric');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([1, 2, 3]);
    expect(result.count).toBe(3);
  });

  it('应该解析字符串类型参数', () => {
    const result = parseParameterValues('euler, euler_a, dpm++', 'sampler');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual(['euler', 'euler_a', 'dpm++']);
  });

  it('应该处理带空格的输入', () => {
    const result = parseParameterValues('  1 ,  2  , 3  ', 'numeric');
    expect(result.isValid).toBe(true);
    expect(result.values).toEqual([1, 2, 3]);
  });

  it('应该限制范围表达式生成的值数量', () => {
    const result = parseParameterValues('1-1000:0.1', 'numeric');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('值过多');
  });
});

describe('validateGridConfiguration', () => {
  it('应该验证有效的配置', () => {
    const result = validateGridConfiguration('1, 2, 3', '4, 5, 6');
    expect(result.isValid).toBe(true);
    expect(result.totalCombinations).toBe(9);
  });

  it('应该验证带Z轴的配置', () => {
    const result = validateGridConfiguration('1, 2', '3, 4', '5, 6');
    expect(result.isValid).toBe(true);
    expect(result.totalCombinations).toBe(8);
  });

  it('应该拒绝超过限制的配置', () => {
    const result = validateGridConfiguration(
      '1-20:1',
      '1-20:1',
      null,
      100
    );
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('超过限制');
  });

  it('应该拒绝组合数太少的配置', () => {
    const result = validateGridConfiguration('1', '2');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('至少2个');
  });

  it('应该拒绝无效的X轴', () => {
    const result = validateGridConfiguration('', '1, 2, 3');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('X轴');
  });

  it('应该拒绝无效的Y轴', () => {
    const result = validateGridConfiguration('1, 2, 3', '');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('Y轴');
  });

  it('应该拒绝无效的Z轴', () => {
    const result = validateGridConfiguration('1, 2', '3, 4', '');
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('Z轴');
  });
});

describe('calculateParameterCombinations', () => {
  it('应该计算2D网格的所有组合', () => {
    const config = {
      xAxis: { type: 'steps', values: [10, 20] },
      yAxis: { type: 'cfg_scale', values: [5.0, 7.5] },
      totalCombinations: 4,
      isValid: true
    };

    const combinations = calculateParameterCombinations(config);
    expect(combinations).toHaveLength(4);
    expect(combinations).toEqual([
      { steps: 10, cfg_scale: 5.0 },
      { steps: 20, cfg_scale: 5.0 },
      { steps: 10, cfg_scale: 7.5 },
      { steps: 20, cfg_scale: 7.5 }
    ]);
  });

  it('应该计算3D网格的所有组合', () => {
    const config = {
      xAxis: { type: 'steps', values: [10, 20] },
      yAxis: { type: 'cfg_scale', values: [5.0, 7.5] },
      zAxis: { type: 'seed', values: [42, 123] },
      totalCombinations: 8,
      isValid: true
    };

    const combinations = calculateParameterCombinations(config);
    expect(combinations).toHaveLength(8);
    expect(combinations[0]).toEqual({ steps: 10, cfg_scale: 5.0, seed: 42 });
    expect(combinations[7]).toEqual({ steps: 20, cfg_scale: 7.5, seed: 123 });
  });
});

describe('getExampleValues', () => {
  it('应该返回steps的示例', () => {
    const example = getExampleValues('steps');
    expect(example).toBe('20, 30, 40, 50');
  });

  it('应该返回cfg_scale的示例', () => {
    const example = getExampleValues('cfg_scale');
    expect(example).toBe('5.0-10.0:2.5');
  });

  it('应该返回未知类型的默认示例', () => {
    const example = getExampleValues('unknown');
    expect(example).toBe('1, 2, 3');
  });
});

describe('formatParameterValues', () => {
  it('应该格式化数值数组', () => {
    const formatted = formatParameterValues([1, 2, 3]);
    expect(formatted).toBe('1, 2, 3');
  });

  it('应该格式化字符串数组', () => {
    const formatted = formatParameterValues(['euler', 'euler_a']);
    expect(formatted).toBe('euler, euler_a');
  });

  it('应该格式化混合数组', () => {
    const formatted = formatParameterValues([1.5, 'test', 3]);
    expect(formatted).toBe('1.5, test, 3');
  });
});
