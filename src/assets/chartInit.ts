/**
 * chartInit.ts
 * Shared chart initialisation registry.
 *
 * Chart components call registerChart(id, fn) to enrol their init function.
 * ChartPreviewCard calls triggerChart(id) when a card is expanded, ensuring
 * charts that were hidden at viewport-entry time are initialised with the
 * correct (now non-zero) clientWidth.
 *
 * Registry is stored on `window` rather than module scope so it survives
 * any Astro/Vite chunk-splitting that might produce multiple module instances.
 */

declare global {
  interface Window {
    __chartReg?: Map<string, () => void>;
    __chartDone?: Set<string>;
  }
}

function reg(): Map<string, () => void> {
  return (window.__chartReg ??= new Map());
}
function done(): Set<string> {
  return (window.__chartDone ??= new Set());
}

export function registerChart(id: string, fn: () => void): void {
  if (done().has(id)) return;
  const guarded = () => {
    if (done().has(id)) return;
    done().add(id);
    reg().delete(id);
    fn();
  };
  reg().set(id, guarded);
}

export function triggerChart(id: string): void {
  const fn = reg().get(id);
  if (fn) fn();
}

export function triggerAll(): void {
  reg().forEach(fn => fn());
  reg().clear();
}
