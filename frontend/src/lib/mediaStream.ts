import { writable } from 'svelte/store';

export interface FrameStore {
  blob: Blob | null;
  timestamp: number;
}

export const onFrameChangeStore = writable<FrameStore>({
  blob: null,
  timestamp: 0,
});

export const mediaStreamActions = {
  updateFrame(blob: Blob): void {
    onFrameChangeStore.set({
      blob,
      timestamp: Date.now(),
    });
  },
  
  clearFrame(): void {
    onFrameChangeStore.set({
      blob: null,
      timestamp: 0,
    });
  },
};

