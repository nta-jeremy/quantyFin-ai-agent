interface SegmentProps {
  value: string;
  onChange: (v: string) => void;
  options: { k: string; label: string; count?: number }[];
}

export function Segment({ value, onChange, options }: SegmentProps) {
  return (
    <div className="grp">
      {options.map((o) => (
        <button key={o.k} className="seg" data-active={value === o.k} onClick={() => onChange(o.k)}>
          <span className="seg-label">{o.label}</span>{o.count != null && <span className="seg-count">{o.count}</span>}
        </button>
      ))}
    </div>
  );
}
