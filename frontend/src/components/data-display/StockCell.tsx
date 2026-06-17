import { TPill } from '@/components/feedback';

interface StockCellProps {
  s: any;
  onClick?: () => void;
}

export function StockCell({ s, onClick }: StockCellProps) {
  return (
    <button onClick={onClick} style={{
      border: 'none', background: 'transparent', padding: 0, textAlign: 'left',
      display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', minWidth: 0,
    }}>
      <TPill tone="iris" style={{ width: 48, justifyContent: 'center' }}>{s.ticker}</TPill>
      <span style={{ minWidth: 0 }}>
        <span style={{ display: 'block', font: '500 12.5px/1.2 var(--font-body)', color: 'var(--fg-1)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 220 }}>{s.name}</span>
        <span style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>{s.sector} · {s.exchange}</span>
      </span>
    </button>
  );
}
