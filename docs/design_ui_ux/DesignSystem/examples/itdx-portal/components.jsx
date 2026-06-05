// QuantyFin ITDX EA Portal — UI Kit (React + Inline JSX)
// All components in one file for clarity. Loaded by index.html via Babel.

const { useState, useEffect, useRef } = React;

// ── Header ──────────────────────────────────────────────
function Header({ active, onNav }) {
  const items = [
    { id: 'dashboard', label: 'Tổng quan' },
    { id: 'mindmap', label: 'Bản đồ EA' },
    { id: 'health', label: 'Sức khoẻ' },
    { id: 'roadmap', label: 'Lộ trình' },
  ];
  return (
    <header className="hdr">
      <div className="logo">
        <div className="logo-mark">Y</div>
        <div className="logo-name">QuantyFin <span>ID</span></div>
      </div>
      <div className="hdr-sep" />
      <nav className="hdr-nav">
        {items.map(it => (
          <a key={it.id} className={active === it.id ? 'active' : ''} onClick={() => onNav(it.id)}>{it.label}</a>
        ))}
      </nav>
      <div className="hdr-right">
        <span className="hdr-tag">TOGAF Governance</span>
        <span className="hdr-updated">Cập nhật T5/2026</span>
      </div>
    </header>
  );
}

// ── Status Tag ──────────────────────────────────────────
function StatusTag({ status, size = 'sm' }) {
  const cls = `tag tag-${status.toLowerCase()} ${size === 'lg' ? 'tag-lg' : ''}`;
  return <span className={cls}>{status}</span>;
}

// ── Domain Badge ────────────────────────────────────────
const DOMAIN_COLORS = {
  A: '#2a2b86', B: '#c2185b', C: '#1565c0', D: '#00897b',
  E: '#d84315', F: '#6a1b9a', G: '#455a64', H: '#ef6c00', I: '#2e7d32',
};
function DomainBadge({ letter, size = 28 }) {
  return (
    <div className="dom-badge" style={{ width: size, height: size, background: DOMAIN_COLORS[letter] || 'var(--brand)', fontSize: size * 0.46 }}>
      {letter}
    </div>
  );
}

// ── KPI Card ────────────────────────────────────────────
function KpiCard({ label, value, suffix, trend, accent = 'brand' }) {
  const accentColor = accent === 'live' ? 'var(--live)' : accent === 'gap' ? 'var(--gap)' : accent === 'plan' ? 'var(--plan)' : 'var(--brand)';
  const trendCls = trend?.startsWith('+') || trend?.startsWith('↗') ? 'up' : trend?.startsWith('-') || trend?.startsWith('↘') ? 'down' : 'flat';
  return (
    <div className="kpi-card" style={{ '--accent': accentColor }}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-num">{value}{suffix && <span className="kpi-suffix">{suffix}</span>}</div>
      {trend && <div className={`kpi-trend ${trendCls}`}>{trend}</div>}
    </div>
  );
}

// ── Domain / Capability Card ────────────────────────────
function DomainCard({ letter, title, subtitle, status, platform, maturity, onClick }) {
  return (
    <div className="dom-card" onClick={onClick}>
      <DomainBadge letter={letter} />
      <div className="dom-body">
        <div className="dom-title">{title}</div>
        <div className="dom-sub">{subtitle}</div>
        <div className="dom-row">
          <StatusTag status={status} />
          {platform && <span className="platform-chip">{platform}</span>}
        </div>
        {maturity != null && (
          <div className="bar"><i style={{ width: `${maturity * 20}%`, background: status === 'LIVE' ? 'var(--live)' : status === 'GAP' ? 'var(--gap)' : 'var(--brand)' }} /></div>
        )}
      </div>
    </div>
  );
}

// ── Side Panel (drill-down) ─────────────────────────────
function SidePanel({ open, onClose, item }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  return (
    <>
      <div className={`backdrop ${open ? 'open' : ''}`} onClick={onClose} />
      <aside className={`panel ${open ? 'open' : ''}`} role="dialog" aria-modal="true">
        {item && (
          <>
            <div className="panel-hdr">
              <div className="panel-eyebrow">{item.platform || 'TOGAF'} · Domain {item.letter}</div>
              <h2 className="panel-title">{item.title}</h2>
              <button className="panel-close" onClick={onClose} aria-label="Close">×</button>
            </div>
            <div className="panel-body">
              <p className="panel-desc">{item.desc}</p>

              <div className="panel-section">
                <div className="panel-label">Trạng thái</div>
                <StatusTag status={item.status} size="lg" />
              </div>

              <div className="panel-section">
                <div className="panel-label">Owner / Squad</div>
                <span className="owner-chip">{item.owner}</span>
              </div>

              <div className="panel-section">
                <div className="panel-label">Hệ thống liên quan</div>
                <ul className="sys-list">
                  {(item.systems || []).map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>

              <div className="panel-section">
                <div className="panel-label">Maturity (CMMI)</div>
                <div className="bar tall"><i style={{ width: `${(item.maturity || 0) * 20}%` }} /></div>
                <div className="caption">{item.maturity?.toFixed(1)} / 5.0</div>
              </div>
            </div>
          </>
        )}
      </aside>
    </>
  );
}

// ── Filter Pills ────────────────────────────────────────
function FilterPills({ active, onChange }) {
  const pills = ['ALL', 'LIVE', 'BUILD', 'GAP', 'PLAN'];
  return (
    <div className="filter-pills">
      {pills.map(p => (
        <button key={p} className={`pill ${active === p ? 'active' : ''}`} onClick={() => onChange(p)}>{p}</button>
      ))}
    </div>
  );
}

// ── Section Header ──────────────────────────────────────
function SectionHeader({ eyebrow, title, sub }) {
  return (
    <div className="section-head">
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h2 className="section-title">{title}</h2>
      {sub && <p className="section-sub">{sub}</p>}
    </div>
  );
}

// ── Insight Callout (the "kết luận" pattern) ────────────
function Insight({ children }) {
  return (
    <div className="insight">
      <div className="insight-mark" />
      <p>{children}</p>
    </div>
  );
}

// Export all components to window for use in index.html
Object.assign(window, {
  Header, StatusTag, DomainBadge, KpiCard, DomainCard, SidePanel, FilterPills, SectionHeader, Insight,
});
