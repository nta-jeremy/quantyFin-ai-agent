import { Icon } from '@/components/shared';

interface SideRailProps {
  active: string;
  onNav: (s: string) => void;
  alertCount?: number;
}

export function SideRail({ active, onNav, alertCount }: SideRailProps) {
  const nav = [
    { k: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
    { k: 'kg', label: 'Knowledge Graph', icon: 'graph' },
    { k: 'stock', label: 'Cổ phiếu', icon: 'stock' },
    { k: 'news', label: 'Tin tức', icon: 'news' },
    { k: 'chat', label: 'AI Chat', icon: 'chat' },
    { k: 'alerts', label: 'Cảnh báo', icon: 'bell', badge: alertCount },
    { k: 'jobs', label: 'Pipeline & Jobs', icon: 'pipe' },
    { k: 'crawler', label: 'Giám sát Crawler', icon: 'server' },
    { k: 'ai-health', label: 'AI Pipeline Health', icon: 'bolt' },
    { k: 'settings', label: 'Cài đặt', icon: 'cog' },
  ];

  return (
    <aside className="side-rail">
      <div style={{ padding: '14px 12px 6px', font: '700 10px/1 var(--font-mono)', letterSpacing: '0.18em', color: 'var(--fg-3)', textTransform: 'uppercase' }}>
        Workspace
      </div>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: 1, padding: '0 8px' }}>
        {nav.map((n) => (
          <button
            key={n.k}
            className="nav-link"
            data-active={active === n.k ? 'true' : undefined}
            onClick={() => onNav(n.k)}
            style={{
              display: 'grid', gridTemplateColumns: '16px 1fr auto',
              alignItems: 'center', gap: 10,
              padding: '8px 12px',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              font: '500 13px/1 var(--font-body)',
              cursor: 'pointer', textAlign: 'left',
              position: 'relative',
            }}
          >
            <Icon name={n.icon} size={15} />
            <span>{n.label}</span>
            {n.badge ? (
              <span style={{
                font: '700 10px/1 var(--font-mono)', padding: '3px 5px',
                background: 'var(--gap)', color: '#fff', borderRadius: 9,
                minWidth: 16, textAlign: 'center',
              }}>{n.badge}</span>
            ) : null}
          </button>
        ))}
      </nav>
      <div style={{ marginTop: 'auto', padding: 12, borderTop: '1px solid var(--border-light)' }}>
        <div style={{
          background: 'var(--iris-tint)', borderRadius: 'var(--radius-sm)', padding: 12,
          border: '1px solid rgba(124,108,245,.18)',
        }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, font: '700 10px/1 var(--font-mono)', color: 'var(--iris-deep)', letterSpacing: '0.12em' }}>
            <Icon name="sparkle" size={12} /> AI ANALYST
          </div>
          <p style={{ margin: '6px 0 8px', font: '12.5px/1.45 var(--font-body)', color: 'var(--fg-1)' }}>
            Phiên hôm nay có 3 tín hiệu đáng chú ý trong watchlist của bạn.
          </p>
          <button className="btn iris sm" style={{ width: '100%', justifyContent: 'center' }}>Xem briefing</button>
        </div>
      </div>
    </aside>
  );
}
