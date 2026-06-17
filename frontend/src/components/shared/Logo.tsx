interface LogoProps {
  variant?: 'light' | 'dark';
  className?: string;
}

export function Logo({ variant = 'light', className }: LogoProps) {
  return (
    <div className={className} style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <span className="qf-mark">Q</span>
      <span className="qf-wordmark" style={variant === 'dark' ? { color: '#fff' } : undefined}>
        Quanty<span className="accent">Fin</span>
      </span>
    </div>
  );
}
