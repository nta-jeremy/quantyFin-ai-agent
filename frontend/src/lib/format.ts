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

export function fmtRelativeTime(input: string | number | Date, now: Date = new Date()): string {
  const then = input instanceof Date ? input : new Date(input);
  const ms = then.getTime();
  if (Number.isNaN(ms)) return '—';
  const diffSec = Math.round((now.getTime() - ms) / 1000);
  if (diffSec < 60) return 'Vừa xong';
  const diffMin = Math.round(diffSec / 60);
  if (diffMin < 60) return `${diffMin} phút trước`;
  const diffHour = Math.round(diffMin / 60);
  if (diffHour < 24) return `${diffHour} giờ trước`;
  const diffDay = Math.round(diffHour / 24);
  return `${diffDay} ngày trước`;
}
