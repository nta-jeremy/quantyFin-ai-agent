interface SentimentProps {
  tone: 'pos' | 'neg' | 'neu';
  score?: number;
  compact?: boolean;
}

export function Sentiment({ tone, score, compact }: SentimentProps) {
  const label = tone === 'pos' ? 'Tích cực' : tone === 'neg' ? 'Tiêu cực' : 'Trung tính';
  return (
    <span className={`sent ${tone}`}>
      {label}
      {!compact && score != null && (
        <span style={{ marginLeft: 4, fontVariantNumeric: 'tabular-nums', opacity: 0.8 }}>
          {score > 0 ? '+' : ''}{score.toFixed(2)}
        </span>
      )}
    </span>
  );
}
