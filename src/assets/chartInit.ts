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
  if (_done.has(id)) return;
  // Wrap fn so any call path (IntersectionObserver or triggerChart) marks
  // the chart done and prevents a second render race.
  const guarded = () => {
    if (_done.has(id)) return;   // already rendered by another call path
    _done.add(id);
    _registry.delete(id);
    fn();
  };
  _registry.set(id, guarded);
}

export function triggerChart(id: string): void {
  const fn = _registry.get(id);
  if (fn) fn(); // guarded wrapper handles _done tracking
}

export function triggerAll(): void {
  _registry.forEach(fn => fn()); // guarded wrappers handle dedup
  _registry.clear();
}
