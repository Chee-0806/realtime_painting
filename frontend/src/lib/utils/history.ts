// Placeholder for history utility
// TODO: Implement full history management

export interface HistoryState {
  type: 'canvas' | 'parameter';
  data: any;
  timestamp: number;
}

export class HistoryManager<T = HistoryState> {
  private history: T[] = [];
  private currentIndex = -1;
  private maxSize: number;

  constructor(maxSize: number = 20) {
    this.maxSize = maxSize;
  }

  push(state: T) {
    // Remove any states after current index
    this.history = this.history.slice(0, this.currentIndex + 1);
    
    // Add new state
    this.history.push(state);
    
    // Limit history size
    if (this.history.length > this.maxSize) {
      this.history.shift();
    } else {
      this.currentIndex++;
    }
  }

  undo(): T | null {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      return this.history[this.currentIndex];
    }
    return null;
  }

  redo(): T | null {
    if (this.currentIndex < this.history.length - 1) {
      this.currentIndex++;
      return this.history[this.currentIndex];
    }
    return null;
  }

  canUndo(): boolean {
    return this.currentIndex > 0;
  }

  canRedo(): boolean {
    return this.currentIndex < this.history.length - 1;
  }

  getCurrent(): T | null {
    if (this.currentIndex >= 0 && this.currentIndex < this.history.length) {
      return this.history[this.currentIndex];
    }
    return null;
  }

  getInfo() {
    return {
      canUndo: this.canUndo(),
      canRedo: this.canRedo(),
      currentIndex: this.currentIndex,
      historyLength: this.history.length
    };
  }

  clear() {
    this.history = [];
    this.currentIndex = -1;
  }
}
