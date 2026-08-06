import { useEffect } from 'react';

export interface KeyboardControlHandlers {
  onTogglePlay: () => void;
  onMute: () => void;
  onCaptions: () => void;
  onRestart: () => void;
  onSeekRelative: (deltaMs: number) => void;
  onEscape: () => void;
  enabled?: boolean;
}

export function useKeyboardControls(handlers: KeyboardControlHandlers): void {
  useEffect(() => {
    if (handlers.enabled === false) return;

    const onKey = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target) {
        const tag = target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || target.isContentEditable) {
          return;
        }
      }

      switch (e.key) {
        case ' ':
          e.preventDefault();
          handlers.onTogglePlay();
          break;
        case 'm':
        case 'M':
          handlers.onMute();
          break;
        case 'c':
        case 'C':
          handlers.onCaptions();
          break;
        case 'r':
        case 'R':
          handlers.onRestart();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          handlers.onSeekRelative(-5000);
          break;
        case 'ArrowRight':
          e.preventDefault();
          handlers.onSeekRelative(5000);
          break;
        case 'Escape':
          handlers.onEscape();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [handlers]);
}
