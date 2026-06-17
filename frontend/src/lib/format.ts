export function fmt(n: number | null | undefined, d = 2): string {
  return n == null ? '—' : Number(n).toLocaleString('vi-VN', { minimumFractionDigits: d, maximumFractionDigits: d });
}

export function fmtInt(n: number | null | undefined): string {
  return n == null ? '—' : Number(n).toLocaleString('vi-VN');
}

export function fmtPct(n: number | null | undefined, d = 2): string {
  return n == null ? '—' : (n >= 0 ? '+' : '') + Number(n).toFixed(d) + '%';
}

export function fmtKbig(n: number): string {
  if (n >= 1e9) return (n / 1e9).toFixed(2) + ' tỷ';
  if (n >= 1e6) return (n / 1e6).toFixed(2) + ' triệu';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + ' nghìn';
  return n + '';
}
