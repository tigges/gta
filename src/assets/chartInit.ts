/**
 * chartInit.ts
 * Shared chart initialisation registry.
 *
 * Chart components call registerChart(id, fn) to enrol their init function.
 * ChartPreviewCard calls triggerChart(id) when a card is expanded, ensuring
 * charts that were hidden at viewport-entry time are initialised with the
 * correct (now non-zero) clientWidth.
 */

const _registry = new Map<string, () => void>();
const _done     = new Set<string>();

export function registerChart(id: string, fn: () => void): void {
  if (!_done.has(id)) _registry.set(id, fn);
}

export function triggerChart(id: string): void {
  const fn = _registry.get(id);
  if (fn) {
    fn();
    _done.add(id);
    _registry.delete(id);
  }
}

export function triggerAll(): void {
  _registry.forEach((fn, id) => {
    fn();
    _done.add(id);
  });
  _registry.clear();
}
