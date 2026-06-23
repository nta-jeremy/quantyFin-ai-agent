import { Icon } from '@/components/shared';
import { TPill } from '@/components/feedback';

interface AlertRowProps {
  a: any;
  onTicker?: (ticker: string) => void;
  onDismiss?: () => void;
  onClick?: () => void;
}

export function AlertRow({ a, onTicker, onDismiss, onClick }: AlertRowProps) {
  const sevClass = a.sev === 'high' ? 'high' : a.sev === 'med' ? 'med' : 'info';
  const iconK = a.sev === 'high' ? 'alert' : a.sev === 'med' ? 'bell' : 'zap';
  return (
    <div
      className={`alert-row ${sevClass}`}
      onClick={onClick}
      style={onClick ? { cursor: 'pointer' } : undefined}
    >
      <div className="sev"><Icon name={iconK} size={14} /></div>
      <div className="body">
        <p className="t">{a.t}</p>
        <div className="m">
          <span>{a.m}</span>
          {a.tickers && a.tickers.length > 0 && <span className="sep">·</span>}
          {a.tickers && a.tickers.map((t: string) => (
            <TPill
              key={t}
              tone="iris"
              onClick={onTicker ? (e: React.MouseEvent) => {
                e.stopPropagation();
                onTicker(t);
              } : undefined}
            >
              {t}
            </TPill>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>{a.when}</span>
        {onDismiss && (
          <button
            type="button"
            className="btn ghost sm"
            style={{
              padding: 4,
              minWidth: 0,
              width: 24,
              height: 24,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: 'none',
              background: 'transparent',
              color: 'var(--fg-3)',
              cursor: 'pointer'
            }}
            onClick={(e) => {
              e.stopPropagation();
              onDismiss();
            }}
            aria-label="Dismiss alert"
          >
            <Icon k="x" size={13} />
          </button>
        )}
      </div>
    </div>
  );
}
