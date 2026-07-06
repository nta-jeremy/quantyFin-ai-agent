import { TPill, Sentiment, ConfChip } from '@/components/feedback';

interface NewsItemProps {
  n: any;
  onTicker?: (ticker: string) => void;
}

export function NewsItem({ n, onTicker }: NewsItemProps) {
  const hrs = Math.floor(n.minutesAgo / 60);
  const mins = n.minutesAgo % 60;
  const when = hrs ? hrs + 'g ' + mins + 'p' : mins + ' phút';
  return (
    <div className="news-item">
      <div className="when">
        <strong>{when}</strong>
        <span>trước</span>
      </div>
      <div className="body">
        <div className="src">{n.src}</div>
        <p className="title">{n.title}</p>
        <div className="meta">
          <span className="tickers">
            {(n.tickers || []).map((t: string) => <TPill key={t} tone="iris" onClick={onTicker ? () => onTicker(t) : undefined}>{t}</TPill>)}
          </span>
          {n.sector && (<><span className="sep">·</span><span>{n.sector}</span></>)}
          {n.filterStatus === 'filtered' && (<><span className="sep">·</span><span style={{ color: 'var(--fg-3)' }}>Đã lọc · zero-cost</span></>)}
          {n.filterStatus === 'pending' && (<><span className="sep">·</span><span style={{ color: 'var(--gold-deep)' }}>Đang xử lý</span></>)}
        </div>
      </div>
      <div className="end">
        {n.tone != null && <Sentiment tone={n.tone} score={n.sentScore} compact />}
        {n.conf != null && <ConfChip conf={n.conf} pct={n.confPct} />}
      </div>
    </div>
  );
}
