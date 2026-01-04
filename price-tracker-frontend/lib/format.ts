export function formatCompactNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  if (!Number.isFinite(value)) return 'N/A';
  const abs = Math.abs(value);
  const fmt = (n: number, suffix: string) => `${n.toFixed(2).replace(/\.00$/, '')}${suffix}`;
  if (abs >= 1e12) return fmt(value / 1e12, 'T');
  if (abs >= 1e9) return fmt(value / 1e9, 'B');
  if (abs >= 1e6) return fmt(value / 1e6, 'M');
  if (abs >= 1e3) return fmt(value / 1e3, 'K');
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
}

export function formatCompactUsd(value: number | null | undefined): string {
  return formatCompactNumber(value);
}

export function formatPercent(num: number | null | undefined, digits: number = 2): string {
  if (num === null || num === undefined) return 'N/A';
  if (!Number.isFinite(num)) return 'N/A';
  return `${Number(num).toFixed(digits)}%`;
}

export function formatTonnes(num: number | null | undefined, digits: number = 3): string {
  if (num === null || num === undefined) return 'N/A';
  if (!Number.isFinite(num)) return 'N/A';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: digits }).format(num);
}
