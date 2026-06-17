interface ConfChipProps {
  conf: 'high' | 'med' | 'low';
  pct?: number;
}

export function ConfChip({ conf, pct }: ConfChipProps) {
  const colorMap = { high: '#10b981', med: '#f59e0b', low: '#ef4444' };
  const label = conf === 'high' ? 'Cao' : conf === 'med' ? 'TB' : 'Thấp';
  return (
    <span className="ai-conf" style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      font: '600 10.5px/1 var(--font-mono)',
      letterSpacing: '0.06em',
      padding: '3px 6px 3px 5px',
      borderRadius: 4,
      background: 'var(--iris-tint)',
      color: 'var(--iris-deep)',
      textTransform: 'uppercase',
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: colorMap[conf] }} />
      AI · {pct ? pct + '%' : label}
    </span>
  );
}
