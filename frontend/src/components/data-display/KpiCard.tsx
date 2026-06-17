import { Sparkline } from './Sparkline';

interface KpiCardProps {
  label: string;
  value: string | number;
  valueClass?: string;
  delta?: string;
  deltaTone?: 'up' | 'down' | 'flat';
  sub?: string;
  spark?: number[];
  sparkTone?: string;
}

export function KpiCard({ label, value, valueClass, delta, deltaTone, sub, spark, sparkTone }: KpiCardProps) {
  return (
    <div className="kpi-card">
      <div className="label">{label}</div>
      <div className="row">
        <span className={`value ${valueClass || ''}`}>{value}</span>
        {delta != null && (
          <span className={`delta ${deltaTone === 'up' ? 'dir-up' : deltaTone === 'down' ? 'dir-down' : 'dir-flat'}`}>
            {delta}
          </span>
        )}
      </div>
      {sub && <div className="sub">{sub}</div>}
      {spark && <div style={{ marginTop: 6 }}><Sparkline data={spark} tone={sparkTone || 'auto'} width={220} height={32} /></div>}
    </div>
  );
}
