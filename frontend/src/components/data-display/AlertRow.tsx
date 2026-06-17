import { Icon } from '@/components/shared';
import { TPill } from '@/components/feedback';

interface AlertRowProps {
  a: any;
  onTicker?: (ticker: string) => void;
}

export function AlertRow({ a, onTicker }: AlertRowProps) {
  const sevClass = a.sev === 'high' ? 'high' : a.sev === 'med' ? 'med' : 'info';
  const iconK = a.sev === 'high' ? 'alert' : a.sev === 'med' ? 'bell' : 'zap';
  return (
    <div className={`alert-row ${sevClass}`}>
      <div className="sev"><Icon name={iconK} size={14} /></div>
      <div className="body">
        <p className="t">{a.t}</p>
        <div className="m">
          <span>{a.m}</span>
          {a.tickers && a.tickers.length > 0 && <span className="sep">·</span>}
          {a.tickers && a.tickers.map((t: string) => <TPill key={t} tone="iris" onClick={onTicker ? () => onTicker(t) : undefined}>{t}</TPill>)}
        </div>
      </div>
      <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>{a.when}</div>
    </div>
  );
}
