/**
 * XYZ Plot 参数范围解析工具
 * 
 * 支持多种格式的参数值输入：
 * 1. 逗号分隔的值: "1.0, 2.0, 3.0"
 * 2. 范围表达式: "1.0-5.0, 步长1.0" 或 "1.0-5.0:1.0"
 * 3. 混合格式: "1.0, 2.0-4.0:0.5, 5.0"
 */

export interface ParsedValues {
  values: (number | string)[];
  count: number;
  isValid: boolean;
  error?: string;
}

export interface ParameterCombination {
  [key: string]: number | string;
}

export interface GridConfiguration {
  xAxis: { type: string; values: (number | string)[] };
  yAxis: { type: string; values: (number | string)[] };
  zAxis?: { type: string; values: (number | string)[] };
  totalCombinations: number;
  isValid: boolean;
  error?: string;
}

/**
 * 解析参数值字符串
 * 
 * @param valueString - 参数值字符串
 * @param parameterType - 参数类型（用于确定是数值还是字符串）
 * @returns 解析后的值数组
 */
export function parseParameterValues(
  valueString: string,
  parameterType: string = 'numeric'
): ParsedValues {
  if (!valueString || !valueString.trim()) {
    return {
      values: [],
      count: 0,
      isValid: false,
      error: '参数值不能为空'
    };
  }

  const trimmed = valueString.trim();
  const values: (number | string)[] = [];

  try {
    // 分割逗号分隔的部分
    const parts = trimmed.split(',').map(p => p.trim()).filter(p => p);

    for (const part of parts) {
      // 检查是否是范围表达式
      if (isRangeExpression(part)) {
        const rangeValues = parseRangeExpression(part);
        values.push(...rangeValues);
      } else {
        // 单个值
        const value = parseSingleValue(part, parameterType);
        if (value !== null) {
          values.push(value);
        }
      }
    }

    // 去重（保持顺序）
    const uniqueValues = Array.from(new Set(values.map(v => String(v))))
      .map(s => {
        const original = values.find(v => String(v) === s);
        return original !== undefined ? original : s;
      });

    return {
      values: uniqueValues,
      count: uniqueValues.length,
      isValid: uniqueValues.length > 0,
      error: uniqueValues.length === 0 ? '未能解析出有效的参数值' : undefined
    };
  } catch (e) {
    return {
      values: [],
      count: 0,
      isValid: false,
      error: e instanceof Error ? e.message : '解析失败'
    };
  }
}

/**
 * 检查是否是范围表达式
 * 支持格式: "1.0-5.0, 步长1.0" 或 "1.0-5.0:1.0" 或 "1-5"
 */
function isRangeExpression(str: string): boolean {
  // 匹配 "数字-数字" 模式
  return /[\d.]+\s*-\s*[\d.]+/.test(str);
}

/**
 * 解析范围表达式
 * 
 * 支持格式:
 * - "1.0-5.0, 步长1.0"
 * - "1.0-5.0:1.0"
 * - "1-5" (默认步长为1)
 * - "1.0-5.0, step 1.0"
 * - "1.0-5.0 步长 1.0"
 */
function parseRangeExpression(expr: string): number[] {
  // 提取起始值、结束值和步长
  const rangeMatch = expr.match(/([\d.]+)\s*-\s*([\d.]+)/);
  if (!rangeMatch) {
    throw new Error(`无效的范围表达式: ${expr}`);
  }

  const start = parseFloat(rangeMatch[1]);
  const end = parseFloat(rangeMatch[2]);

  if (isNaN(start) || isNaN(end)) {
    throw new Error(`无效的数值: ${expr}`);
  }

  if (start >= end) {
    throw new Error(`起始值必须小于结束值: ${expr}`);
  }

  // 提取步长
  let step = 1;
  
  // 尝试匹配 "步长X" 或 "step X" 或 ":X"
  const stepMatch = expr.match(/(?:步长|step)\s*([\d.]+)/i) || 
                    expr.match(/:([\d.]+)/);
  
  if (stepMatch) {
    step = parseFloat(stepMatch[1]);
    if (isNaN(step) || step <= 0) {
      throw new Error(`无效的步长: ${stepMatch[1]}`);
    }
  } else {
    // 如果没有指定步长，根据范围自动确定
    const range = end - start;
    if (range <= 10) {
      step = 1;
    } else if (range <= 100) {
      step = 10;
    } else {
      step = Math.pow(10, Math.floor(Math.log10(range)) - 1);
    }
  }

  // 生成值数组
  const values: number[] = [];
  let current = start;
  
  // 限制最大生成数量，防止步长过小导致生成过多值
  const maxValues = 100;
  let count = 0;
  
  while (current <= end && count < maxValues) {
    values.push(parseFloat(current.toFixed(10))); // 避免浮点精度问题
    current += step;
    count++;
  }

  if (count >= maxValues) {
    throw new Error(`范围表达式生成的值过多 (>${maxValues})，请增大步长`);
  }

  return values;
}

/**
 * 解析单个值
 */
function parseSingleValue(
  str: string,
  parameterType: string
): number | string | null {
  if (parameterType === 'numeric' || 
      parameterType === 'steps' || 
      parameterType === 'cfg_scale' ||
      parameterType === 'denoising_strength' ||
      parameterType === 'seed' ||
      parameterType === 'width' ||
      parameterType === 'height') {
    const num = parseFloat(str);
    return isNaN(num) ? null : num;
  }
  
  // 字符串类型（如采样器、调度器名称）
  return str;
}

/**
 * 计算参数组合
 * 
 * @param config - 网格配置
 * @returns 所有参数组合
 */
export function calculateParameterCombinations(
  config: GridConfiguration
): ParameterCombination[] {
  const combinations: ParameterCombination[] = [];

  const xValues = config.xAxis.values;
  const yValues = config.yAxis.values;
  const zValues = config.zAxis?.values || [null];

  for (const zValue of zValues) {
    for (const yValue of yValues) {
      for (const xValue of xValues) {
        const combination: ParameterCombination = {
          [config.xAxis.type]: xValue,
          [config.yAxis.type]: yValue
        };

        if (config.zAxis && zValue !== null) {
          combination[config.zAxis.type] = zValue;
        }

        combinations.push(combination);
      }
    }
  }

  return combinations;
}

/**
 * 验证网格配置
 * 
 * @param xAxisValues - X轴值字符串
 * @param yAxisValues - Y轴值字符串
 * @param zAxisValues - Z轴值字符串（可选）
 * @param maxCombinations - 最大组合数限制
 * @returns 验证结果
 */
export function validateGridConfiguration(
  xAxisValues: string,
  yAxisValues: string,
  zAxisValues: string | null = null,
  maxCombinations: number = 100
): { isValid: boolean; error?: string; totalCombinations: number } {
  // 解析X轴
  const xParsed = parseParameterValues(xAxisValues);
  if (!xParsed.isValid) {
    return {
      isValid: false,
      error: `X轴: ${xParsed.error}`,
      totalCombinations: 0
    };
  }

  // 解析Y轴
  const yParsed = parseParameterValues(yAxisValues);
  if (!yParsed.isValid) {
    return {
      isValid: false,
      error: `Y轴: ${yParsed.error}`,
      totalCombinations: 0
    };
  }

  // 解析Z轴（如果有）
  let zParsed: ParsedValues | null = null;
  if (zAxisValues && zAxisValues.trim()) {
    zParsed = parseParameterValues(zAxisValues);
    if (!zParsed.isValid) {
      return {
        isValid: false,
        error: `Z轴: ${zParsed.error}`,
        totalCombinations: 0
      };
    }
  }

  // 计算总组合数
  const totalCombinations = xParsed.count * yParsed.count * (zParsed?.count || 1);

  // 检查是否超过限制
  if (totalCombinations > maxCombinations) {
    return {
      isValid: false,
      error: `生成数量 (${totalCombinations}) 超过限制 (${maxCombinations})`,
      totalCombinations
    };
  }

  // 检查最小数量
  if (totalCombinations < 2) {
    return {
      isValid: false,
      error: 'XYZ Plot需要至少2个参数组合',
      totalCombinations
    };
  }

  return {
    isValid: true,
    totalCombinations
  };
}

/**
 * 格式化参数值数组为字符串
 * 
 * @param values - 参数值数组
 * @returns 格式化的字符串
 */
export function formatParameterValues(values: (number | string)[]): string {
  return values.map(v => String(v)).join(', ');
}

/**
 * 生成示例值字符串
 * 
 * @param parameterType - 参数类型
 * @returns 示例字符串
 */
export function getExampleValues(parameterType: string): string {
  const examples: Record<string, string> = {
    steps: '20, 30, 40, 50',
    cfg_scale: '5.0-10.0:2.5',
    denoising_strength: '0.5-0.9, 步长0.1',
    seed: '42, 123, 456',
    sampler: 'euler, euler_a, dpm++',
    scheduler: 'normal, karras, exponential',
    width: '512, 768, 1024',
    height: '512, 768, 1024'
  };

  return examples[parameterType] || '1, 2, 3';
}
