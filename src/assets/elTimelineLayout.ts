/**
 * Label packer for the Extended Look chapter timeline.
 *
 * Pins stay on the true timestamp. Labels may shift left/right and drop
 * to extra rows so nearby long names (e.g. "6-Star Wanted Level") do not
 * collide. Width includes the timestamp suffix — the previous packer
 * measured the entity name only and then fell back to row 0, which is
 * what produced the overlaps.
 */

export type ElEvent = { t: number; entity: string; type?: string };

export type ElPlacement = {
  t: number;
  entity: string;
  type: string;
  pinX: number;
  labelX: number;
  labelW: number;
  row: number;
  text: string;
};

export const EL_LAYOUT = {
  charW: 6.1,       // 9px monospace, conservative
  pad: 12,          // gap between two labels on the same row
  rowH: 20,         // vertical pitch — was 16, too tight
  labelPadTop: 10,
  axisH: 16,
  maxShift: 96,     // how far a label may slide from its pin
  shiftStep: 12,
} as const;

export function formatTs(t: number): string {
  return `${Math.floor(t / 60)}:${String(Math.round(t) % 60).padStart(2, "0")}`;
}

export function labelText(entity: string, t: number): string {
  const shortName = entity.length > 28 ? `${entity.slice(0, 26)}…` : entity;
  return `${shortName} (${formatTs(t)})`;
}

export function estimateLabelWidth(text: string): number {
  return Math.ceil(text.length * EL_LAYOUT.charW + 8);
}

function fits(row: { left: number; right: number }[], left: number, right: number, pad: number): boolean {
  return row.every((b) => right + pad <= b.left || left - pad >= b.right);
}

export function layoutSectionLabels(
  events: ElEvent[],
  tStart: number,
  tEnd: number,
  plotW: number,
): { placements: ElPlacement[]; rowCount: number; labelAreaH: number } {
  const sorted = [...events].filter((e) => e.t >= tStart && e.t < tEnd).sort((a, b) => a.t - b.t);
  const dur = Math.max(1, tEnd - tStart);
  const xOf = (t: number) => ((t - tStart) / dur) * plotW;

  const rows: { left: number; right: number }[][] = [[]];
  const placements: ElPlacement[] = [];
  const { pad, maxShift, shiftStep } = EL_LAYOUT;

  for (const ev of sorted) {
    const pinX = xOf(ev.t);
    const text = labelText(ev.entity, ev.t);
    const w = estimateLabelWidth(text);

    const xCandidates: number[] = [];
    const preferRight = pinX + 4;
    const preferLeft = pinX - 4 - w;
    xCandidates.push(preferRight, preferLeft);
    for (let d = shiftStep; d <= maxShift; d += shiftStep) {
      xCandidates.push(preferRight + d, preferRight - d, preferLeft + d, preferLeft - d);
    }

    let placed: { row: number; left: number } | null = null;

    const tryPlace = (rowIdx: number): boolean => {
      for (const raw of xCandidates) {
        const left = Math.max(0, Math.min(raw, Math.max(0, plotW - w)));
        const right = left + w;
        if (fits(rows[rowIdx], left, right, pad)) {
          placed = { row: rowIdx, left };
          return true;
        }
      }
      return false;
    };

    for (let r = 0; r < rows.length; r++) {
      if (tryPlace(r)) break;
    }
    if (!placed) {
      rows.push([]);
      tryPlace(rows.length - 1);
    }
    if (!placed) {
      // Last resort: new row, clamp to pin (still no shared-row collision)
      const left = Math.max(0, Math.min(pinX + 4, Math.max(0, plotW - w)));
      rows.push([]);
      placed = { row: rows.length - 1, left };
    }

    const { row, left } = placed;
    const right = left + w;
    rows[row].push({ left, right });
    placements.push({
      t: ev.t,
      entity: ev.entity,
      type: ev.type ?? "",
      pinX,
      labelX: left,
      labelW: w,
      row,
      text,
    });
  }

  const rowCount = Math.max(1, rows.length);
  const labelAreaH = EL_LAYOUT.labelPadTop + rowCount * EL_LAYOUT.rowH + 4;
  return { placements, rowCount, labelAreaH };
}

export type BilateralPlacement = ElPlacement & { side: "above" | "below" };

/** First two words — the summary discovery chart label. */
export function shortEntityName(entity: string): string {
  return entity.split(/\s+/).slice(0, 2).join(" ");
}

/**
 * Pack labels onto several rows above and below a single strip.
 * Used by the all-releases discovery summary so the 52-entity Extended Look
 * row can stack instead of colliding on two fixed heights.
 */
export function layoutBilateralLabels(
  events: ElEvent[],
  plotW: number,
  durationSec: number,
): { placements: BilateralPlacement[]; aboveRows: number; belowRows: number } {
  const sorted = [...events].sort((a, b) => a.t - b.t);
  const dur = Math.max(1, durationSec);
  const xOf = (t: number) => (t / dur) * plotW;
  const above: { left: number; right: number }[][] = [[]];
  const below: { left: number; right: number }[][] = [[]];
  const placements: BilateralPlacement[] = [];
  const { pad, maxShift, shiftStep } = EL_LAYOUT;

  const sidesOf = (preferAbove: boolean): ("above" | "below")[] =>
    preferAbove ? ["above", "below"] : ["below", "above"];

  for (let i = 0; i < sorted.length; i++) {
    const ev = sorted[i];
    const pinX = xOf(ev.t);
    const text = shortEntityName(ev.entity);
    const w = estimateLabelWidth(text);

    const xCandidates: number[] = [];
    const preferRight = pinX - w / 2;
    const preferLeft = pinX - w;
    const preferFlush = pinX;
    xCandidates.push(preferRight, preferFlush, preferLeft);
    for (let d = shiftStep; d <= maxShift; d += shiftStep) {
      xCandidates.push(preferRight + d, preferRight - d, preferFlush + d, preferLeft - d);
    }

    let placed: { side: "above" | "below"; row: number; left: number } | null = null;

    const trySide = (side: "above" | "below"): boolean => {
      const rows = side === "above" ? above : below;
      const tryPlace = (rowIdx: number): boolean => {
        for (const raw of xCandidates) {
          const left = Math.max(0, Math.min(raw, Math.max(0, plotW - w)));
          const right = left + w;
          if (fits(rows[rowIdx], left, right, pad)) {
            placed = { side, row: rowIdx, left };
            return true;
          }
        }
        return false;
      };
      for (let r = 0; r < rows.length; r++) {
        if (tryPlace(r)) return true;
      }
      return false;
    };

    for (const side of sidesOf(i % 2 === 0)) {
      if (trySide(side)) break;
    }
    if (!placed) {
      const side: "above" | "below" = above.length <= below.length ? "above" : "below";
      const rows = side === "above" ? above : below;
      rows.push([]);
      trySide(side);
      if (!placed) {
        const left = Math.max(0, Math.min(pinX - w / 2, Math.max(0, plotW - w)));
        placed = { side, row: rows.length - 1, left };
      }
    }

    const { side, row, left } = placed;
    const rows = side === "above" ? above : below;
    rows[row].push({ left, right: left + w });
    placements.push({
      t: ev.t,
      entity: ev.entity,
      type: ev.type ?? "",
      pinX,
      labelX: left,
      labelW: w,
      row,
      text,
      side,
    });
  }

  return {
    placements,
    aboveRows: Math.max(1, above.length),
    belowRows: Math.max(1, below.length),
  };
}

/** Count same-row bounding-box overlaps. 0 means the packer succeeded. */
export function countOverlaps(placements: ElPlacement[], pad = EL_LAYOUT.pad): number {
  let n = 0;
  for (let i = 0; i < placements.length; i++) {
    for (let j = i + 1; j < placements.length; j++) {
      const a = placements[i];
      const b = placements[j];
      if (a.row !== b.row) continue;
      const aR = a.labelX + a.labelW;
      const bR = b.labelX + b.labelW;
      if (!(aR + pad <= b.labelX || bR + pad <= a.labelX)) n++;
    }
  }
  return n;
}
