export enum PipelineMode {
  IMAGE = 'image',
  VIDEO = 'video',
}

export interface Field {
  default: any;
  title: string;
  id: string;
  field?: 'textarea' | 'range' | 'select' | 'number';
  type?: string;
  min?: number;
  max?: number;
  values?: Array<{ value: string; label: string }>;
}

export type Fields = Record<string, Field>;

export interface PipelineInfo {
  title?: string;
  name?: string;
  description?: string;
  input_mode?: {
    default: PipelineMode;
  };
  page_content?: string;
}

