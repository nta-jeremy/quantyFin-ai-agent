interface SparklineProps {
  data: number[];
  tone?: string;
  width?: number;
  height?: number;
  withDot?: boolean;
  className?: string;
}

export function Sparkline({ data, tone = 'auto', width = 96, height = 32, withDot = true, className }: SparklineProps) {
  if (!data || !data.length) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);
  const pts = data.map((v, i) => [i * stepX, height - ((v - min) / range) * (height - 4) - 2]);
  const linePath = pts.map((p, i) => (i === 0 ? 'M' : 'L') + p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
  const areaPath = linePath + ` L${width.toFixed(1)},${height} L0,${height} Z`;
  let cls = tone;
  if (tone === 'auto') cls = data[data.length - 1] >= data[0] ? 'up' : 'down';
  const last = pts[pts.length - 1];
  return (
    <svg className={`spark ${cls} ${className || ''}`} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ width, height }}>
      <path className="area" d={areaPath} />
      <path className="line" d={linePath} />
      {withDot && <circle className="dot" cx={last[0]} cy={last[1]} r="2" />}
    </svg>
  );
}
