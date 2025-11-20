type KeyConfig = {
  key: string;
  shift?: boolean;
  ctrl?: boolean;
  alt?: boolean;
  meta?: boolean;
};

type KeyboardHandler = (event: KeyboardEvent) => boolean | void;

class KeyboardManager {
  private handlers: Map<string, KeyboardHandler[]> = new Map();

  register(config: KeyConfig, handler: KeyboardHandler): () => void {
    const key = this.getKeyString(config);
    
    if (!this.handlers.has(key)) {
      this.handlers.set(key, []);
      this.setupListener(key);
    }
    
    const handlers = this.handlers.get(key)!;
    handlers.push(handler);
    
    // 返回注销函数
    return () => {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
      if (handlers.length === 0) {
        this.handlers.delete(key);
      }
    };
  }

  private getKeyString(config: KeyConfig): string {
    const parts: string[] = [];
    if (config.ctrl) parts.push('ctrl');
    if (config.alt) parts.push('alt');
    if (config.shift) parts.push('shift');
    if (config.meta) parts.push('meta');
    parts.push(config.key.toLowerCase());
    return parts.join('+');
  }

  private setupListener(key: string): void {
    if (typeof window === 'undefined') return;
    
    const handleKeyDown = (event: KeyboardEvent) => {
      const config = this.parseKeyString(key);
      if (this.matches(event, config)) {
        const handlers = this.handlers.get(key);
        if (handlers) {
          for (const handler of handlers) {
            const result = handler(event);
            if (result === false) {
              event.preventDefault();
              event.stopPropagation();
            }
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
  }

  private parseKeyString(key: string): KeyConfig {
    const parts = key.split('+');
    const config: KeyConfig = { key: '' };
    
    for (const part of parts) {
      switch (part.toLowerCase()) {
        case 'ctrl':
          config.ctrl = true;
          break;
        case 'alt':
          config.alt = true;
          break;
        case 'shift':
          config.shift = true;
          break;
        case 'meta':
          config.meta = true;
          break;
        default:
          config.key = part;
      }
    }
    
    return config;
  }

  private matches(event: KeyboardEvent, config: KeyConfig): boolean {
    if (event.key.toLowerCase() !== config.key.toLowerCase()) {
      return false;
    }
    
    if (config.ctrl !== undefined && event.ctrlKey !== config.ctrl) {
      return false;
    }
    
    if (config.alt !== undefined && event.altKey !== config.alt) {
      return false;
    }
    
    if (config.shift !== undefined && event.shiftKey !== config.shift) {
      return false;
    }
    
    if (config.meta !== undefined && event.metaKey !== config.meta) {
      return false;
    }
    
    return true;
  }
}

export const keyboardManager = new KeyboardManager();

