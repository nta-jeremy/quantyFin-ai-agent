// @ts-nocheck
/* QuantyFin · Shared UI components */

const { useState, useEffect, useRef, useMemo, useLayoutEffect } = React;

// ════════ ICONS ════════
const ICONS = {
  dashboard: 'M3 13h8V3H3v10zM13 21h8V11h-8v10zM3 21h8v-6H3v6zM13 3v6h8V3h-8z',
  graph: 'M5 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6zm14 0a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM12 14a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM7 8l4 4M17 8l-4 4',
  stock: 'M3 3v18h18M7 14l4-4 4 4 6-6',
  news: 'M4 4h13v16H4zM7 8h7M7 12h7M7 16h5M17 8h3v10a2 2 0 0 1-2 2',
  chat: 'M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z',
  bell: 'M18 16v-5a6 6 0 0 0-12 0v5l-2 2v1h16v-1zM10 21a2 2 0 0 0 4 0',
  pipe: 'M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6zM10 7h4M10 17h4M7 10v4M17 10v4',
  cog: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm9 5l-2-1 1-2-2-2-2 1-1-2h-3l-1 2-2-1-2 2 1 2-2 1v3l2 1-1 2 2 2 2-1 1 2h3l1-2 2 1 2-2-1-2 2-1z',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zm5.5 12L21 21',
  ext:    'M14 3h7v7M10 14L21 3M19 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6',
  filter: 'M4 4h16l-6 8v6l-4 2v-8z',
  refresh: 'M3 12a9 9 0 0 1 15.5-6.36L21 8M21 4v4h-4M21 12a9 9 0 0 1-15.5 6.36L3 16M3 20v-4h4',
  plus: 'M12 5v14M5 12h14',
  caret: 'M6 9l6 6 6-6',
  caretR: 'M9 6l6 6-6 6',
  check: 'M5 12l5 5L20 7',
  x: 'M6 6l12 12M6 18L18 6',
  send: 'M22 2L11 13M22 2l-7 20-4-9-9-4z',
  bolt: 'M13 2L3 14h7l-1 8 10-12h-7z',
  shield: 'M12 2L4 5v6c0 5 3.5 9.4 8 11 4.5-1.6 8-6 8-11V5z',
  doc: 'M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9zM14 3v6h6',
  fire: 'M12 22c4 0 8-3 8-8 0-5-4-7-4-12 0 0-4 4-4 8 0-2-2-3-2-3s-6 4-6 9 4 6 8 6z',
  trend: 'M3 17l6-6 4 4 8-8M14 7h7v7',
  trendDown: 'M3 7l6 6 4-4 8 8M14 17h7v-7',
  globe: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18',
  zap: 'M13 2L3 14h7l-1 8 10-12h-7z',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1',
  logout: 'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9',
  copy: 'M16 3H8a2 2 0 0 0-2 2v10h2V5h8zM20 7H12a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z',
  database: 'M12 3c-4.4 0-8 1.3-8 3v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6c0-1.7-3.6-3-8-3zM4 6c0 1.7 3.6 3 8 3s8-1.3 8-3M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3',
  link: 'M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1',
  sparkle: 'M12 2l2 6 6 2-6 2-2 6-2-6-6-2 6-2zM19 14l1 3 3 1-3 1-1 3-1-3-3-1 3-1z',
  more: 'M5 12h.01M12 12h.01M19 12h.01',
  arrowR: 'M5 12h14M13 5l7 7-7 7',
  alert: 'M12 9v4M12 17h.01M10.3 3.86L1.82 18a2 2 0 0 0 1.72 3h16.92a2 2 0 0 0 1.72-3L13.71 3.86a2 2 0 0 0-3.42 0z',
  download: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3',
  key: 'M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4',
  mail: 'M4 6h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2zM22 8l-10 7L2 8',
  clock: 'M12 6v6l4 2M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z',
  lock: 'M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4',
  server: 'M3 4h18v6H3zM3 14h18v6H3zM7 7h.01M7 17h.01M11 7h6M11 17h6',
  upload: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12',
  rotate: 'M21 2v6h-6M3 12a9 9 0 0 1 15-6.7L21 8M3 22v-6h6M21 12a9 9 0 0 1-15 6.7L3 16',
  webhook: 'M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 1 1 2 16h.5M14 7a4 4 0 1 1 8 0 4 4 0 0 1-8 0zM10.46 6.46a4 4 0 1 0-5.92 5.39M14.5 17.5l-2.5-4.33',
  trash: 'M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14zM10 11v6M14 11v6',
  eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  eyeOff: 'M17.94 17.94A10.1 10.1 0 0 1 12 19c-6.5 0-10-7-10-7a16.7 16.7 0 0 1 4.06-5.06M9.9 4.24A9.1 9.1 0 0 1 12 4c6.5 0 10 7 10 7a16.7 16.7 0 0 1-1.51 2.36M1 1l22 22M14.12 14.12A3 3 0 1 1 9.88 9.88',
  edit: 'M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z',
};

function Icon({ k, size = 16, stroke = 1.75, style }) {
  const d = ICONS[k];
  if (!d) return null;
  return (
    <span className="ico" style={{ width: size, height: size, ...style }}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
        <path d={d} />
      </svg>
    </span>
  );
}

// ════════ LOGO ════════
function Logo({ variant = 'light' }) {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <span className="qf-mark">Q</span>
      <span className="qf-wordmark" style={variant === 'dark' ? { color: '#fff' } : null}>
        Quanty<span className="accent">Fin</span>
      </span>
    </div>
  );
}

// ════════ TICKER PILL ════════
function TPill({ children, tone, onClick, style }) {
  return (
    <span className={'t-pill ' + (tone || '')} style={style} onClick={onClick} role={onClick ? 'button' : null}>
      {children}
    </span>
  );
}

// ════════ SENTIMENT CHIP ════════
function Sentiment({ tone, score, compact }) {
  const label = tone === 'pos' ? 'Tích cực' : tone === 'neg' ? 'Tiêu cực' : 'Trung tính';
  return (
    <span className={'sent ' + tone}>
      {label}
      {!compact && score != null && (
        <span style={{ marginLeft: 4, fontVariantNumeric: 'tabular-nums', opacity: .8 }}>
          {score > 0 ? '+' : ''}{score.toFixed(2)}
        </span>
      )}
    </span>
  );
}

// ════════ AI CONFIDENCE CHIP ════════
function ConfChip({ conf, pct }) {
  const colorMap = { high: '#10b981', med: '#f59e0b', low: '#ef4444' };
  const label = conf === 'high' ? 'Cao' : conf === 'med' ? 'TB' : 'Thấp';
  return (
    <span className="ai-conf" style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      font: '600 10.5px/1 var(--font-mono)',
      letterSpacing: '0.06em',
      padding: '3px 6px 3px 5px',
      borderRadius: 4,
      background: 'var(--iris-tint)',
      color: 'var(--iris-deep)',
      textTransform: 'uppercase',
    }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: colorMap[conf] }} />
      AI · {pct ? pct + '%' : label}
    </span>
  );
}

// ════════ SPARKLINE ════════
function Sparkline({ data, tone = 'auto', width = 96, height = 32, withDot = true }) {
  if (!data || !data.length) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const stepX = width / (data.length - 1);
  const pts = data.map((v, i) => [i * stepX, height - ((v - min) / range) * (height - 4) - 2]);
  const linePath = pts.map((p, i) => (i === 0 ? 'M' : 'L') + p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
  const areaPath = linePath + ` L${width.toFixed(1)},${height} L0,${height} Z`;
  let cls = tone;
  if (tone === 'auto') cls = data[data.length - 1] >= data[0] ? 'up' : 'down';
  const last = pts[pts.length - 1];
  return (
    <svg className={'spark ' + cls} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ width, height }}>
      <path className="area" d={areaPath} />
      <path className="line" d={linePath} />
      {withDot && <circle className="dot" cx={last[0]} cy={last[1]} r="2" />}
    </svg>
  );
}

// ════════ KPI CARD ════════
function KpiCard({ label, value, valueClass, delta, deltaTone, sub, spark, sparkTone }) {
  return (
    <div className="kpi-card">
      <div className="label">{label}</div>
      <div className="row">
        <span className={'value ' + (valueClass || '')}>{value}</span>
        {delta != null && (
          <span className={'delta ' + (deltaTone === 'up' ? 'dir-up' : deltaTone === 'down' ? 'dir-down' : 'dir-flat')}>
            {delta}
          </span>
        )}
      </div>
      {sub && <div className="sub">{sub}</div>}
      {spark && <div style={{ marginTop: 6 }}><Sparkline data={spark} tone={sparkTone || 'auto'} width={220} height={32} /></div>}
    </div>
  );
}

// ════════ NEWS ITEM ════════
function NewsItem({ n, onTicker }) {
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
            {n.tickers.map((t) => <TPill key={t} tone="iris" onClick={() => onTicker && onTicker(t)}>{t}</TPill>)}
          </span>
          <span className="sep">·</span>
          <span>{n.sector}</span>
          {n.filterStatus === 'filtered' && (<><span className="sep">·</span><span style={{ color: 'var(--fg-3)' }}>Đã lọc · zero-cost</span></>)}
          {n.filterStatus === 'pending' && (<><span className="sep">·</span><span style={{ color: 'var(--gold-deep)' }}>Đang xử lý</span></>)}
        </div>
      </div>
      <div className="end">
        <Sentiment tone={n.tone} score={n.sentScore} compact />
        <ConfChip conf={n.conf} pct={n.confPct} />
      </div>
    </div>
  );
}

// ════════ ALERT ROW ════════
function AlertRow({ a, onTicker }) {
  const sevClass = a.sev === 'high' ? 'high' : a.sev === 'med' ? 'med' : 'info';
  const iconK = a.sev === 'high' ? 'alert' : a.sev === 'med' ? 'bell' : 'zap';
  return (
    <div className={'alert-row ' + sevClass}>
      <div className="sev"><Icon k={iconK} size={14} /></div>
      <div className="body">
        <p className="t">{a.t}</p>
        <div className="m">
          <span>{a.m}</span>
          {a.tickers && a.tickers.length > 0 && <span className="sep">·</span>}
          {a.tickers && a.tickers.map((t) => <TPill key={t} tone="iris" onClick={() => onTicker && onTicker(t)}>{t}</TPill>)}
        </div>
      </div>
      <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>{a.when}</div>
    </div>
  );
}

// ════════ TOPBAR ════════
function Topbar({ scenario, onScenario, onSearch, onLogout, screen }) {
  const scenarios = [
    { k: 'up',       label: 'Thị trường tăng',  cls: 'up'   },
    { k: 'down',     label: 'Thị trường giảm',  cls: 'down' },
    { k: 'volatile', label: 'Biến động mạnh',   cls: 'vol'  },
    { k: 'crisis',   label: 'Khủng hoảng',      cls: 'cr'   },
  ];
  const cur = scenarios.find((s) => s.k === scenario) || scenarios[0];
  return (
    <header className="top-bar">
      <div className="brand-block" style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <Logo />
        <span style={{ width: 1, height: 18, background: 'var(--border)' }} />
        <span className={'scenario-banner ' + cur.cls}>{cur.label}</span>
      </div>
      <div className="top-bar__search" style={{ flex: 1, maxWidth: 520, margin: '0 24px', position: 'relative' }}>
        <input
          placeholder="Tìm mã, công ty, sự kiện, hoặc hỏi AI…"
          style={{
            width: '100%', height: 36, padding: '0 12px 0 36px',
            background: 'var(--bg)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-sm)',
            font: '13px/1 var(--font-body)', color: 'var(--fg-1)',
            outline: 'none',
          }}
          onClick={onSearch}
          readOnly
        />
        <span style={{ position: 'absolute', left: 11, top: '50%', transform: 'translateY(-50%)', color: 'var(--fg-3)' }}>
          <Icon k="search" size={14} />
        </span>
        <span style={{
          position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
          font: '600 10px/1 var(--font-mono)', letterSpacing: '0.08em',
          padding: '3px 6px', border: '1px solid var(--border)', borderRadius: 4,
          color: 'var(--fg-3)', background: 'var(--bg-muted)',
        }}>⌘K</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <select
          value={scenario}
          onChange={(e) => onScenario(e.target.value)}
          style={{
            height: 32, padding: '0 8px', borderRadius: 'var(--radius-sm)',
            border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--fg-2)',
            font: '500 12px/1 var(--font-body)', cursor: 'pointer',
          }}
        >
          {scenarios.map((s) => <option key={s.k} value={s.k}>Kịch bản · {s.label}</option>)}
        </select>
        <button className="btn ghost sm" title="Refresh"><Icon k="refresh" size={14} /></button>
        <button className="btn ghost sm" title="Thông báo" style={{ position: 'relative' }}>
          <Icon k="bell" size={14} />
          <span style={{ position: 'absolute', top: 4, right: 6, width: 6, height: 6, borderRadius: '50%', background: 'var(--gap)' }} />
        </button>
        <span style={{ width: 1, height: 20, background: 'var(--border)' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            width: 28, height: 28, borderRadius: '50%',
            background: 'var(--brand-tint)', color: 'var(--brand)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            font: '700 11px/1 var(--font-body)',
          }}>HN</span>
          <button className="btn ghost sm" title="Đăng xuất" onClick={onLogout}><Icon k="logout" size={14} /></button>
        </div>
      </div>
    </header>
  );
}

// ════════ SIDE RAIL ════════
function SideRail({ active, onNav, alertCount }) {
  const nav = [
    { k: 'dashboard', label: 'Dashboard',       icon: 'dashboard' },
    { k: 'kg',        label: 'Knowledge Graph', icon: 'graph' },
    { k: 'stock',     label: 'Cổ phiếu',        icon: 'stock' },
    { k: 'news',      label: 'Tin tức',         icon: 'news' },
    { k: 'chat',      label: 'AI Chat',         icon: 'chat' },
    { k: 'alerts',    label: 'Cảnh báo',        icon: 'bell', badge: alertCount },
    { k: 'jobs',      label: 'Pipeline & Jobs', icon: 'pipe' },
    { k: 'settings',  label: 'Cài đặt',         icon: 'cog' },
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
            data-active={active === n.k}
            onClick={() => onNav(n.k)}
            style={{
              display: 'grid', gridTemplateColumns: '16px 1fr auto',
              alignItems: 'center', gap: 10,
              padding: '8px 12px',
              border: 'none', background: 'transparent',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--fg-2)',
              font: '500 13px/1 var(--font-body)',
              cursor: 'pointer', textAlign: 'left',
              position: 'relative',
            }}
          >
            <Icon k={n.icon} size={15} />
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
            <Icon k="sparkle" size={12} /> AI ANALYST
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

// ════════ PAGE HEAD ════════
function PageHead({ eyebrow, title, sub, actions }) {
  return (
    <div className="qf-pagehead">
      <div>
        {eyebrow && (
          <div style={{ font: '700 10.5px/1 var(--font-mono)', color: 'var(--iris-deep)', letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 6, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <Icon k="sparkle" size={11} /> {eyebrow}
          </div>
        )}
        <h1>{title}</h1>
        {sub && <div className="sub">{sub}</div>}
      </div>
      {actions && <div className="actions">{actions}</div>}
    </div>
  );
}

// ════════ CARD / SECTION ════════
function Section({ title, meta, actions, flush, children, ai, style }) {
  return (
    <div className={'qf-card' + (flush ? ' flush' : '')} style={style}>
      {(title || meta || actions) && (
        <div className="qf-card-head">
          <div>
            {title && (
              <h3 className="qf-card-title">
                {ai && <span className="ai-spark"><Icon k="sparkle" size={12} /></span>}
                {title}
              </h3>
            )}
            {meta && <div className="qf-card-meta" style={{ marginTop: 4 }}>{meta}</div>}
          </div>
          {actions && <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>{actions}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

// ════════ TEXT INPUT (form-aware) ════════
function TextInput({ label, value, onChange, placeholder, mono }) {
  return (
    <label className="qf-input">
      {label && <span>{label}</span>}
      <input
        value={value || ''}
        onChange={(e) => onChange && onChange(e.target.value)}
        placeholder={placeholder}
        style={mono ? { fontFamily: 'var(--font-mono)', fontSize: 12.5 } : null}
      />
    </label>
  );
}

// ════════ FILTER BAR (segments) ════════
function Segment({ value, onChange, options }) {
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

// ════════ STOCK CELL FOR TABLE ════════
function StockCell({ s, onClick }) {
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

// ════════ FORMAT ════════
function fmt(n, d = 2) { return n == null ? '—' : Number(n).toLocaleString('vi-VN', { minimumFractionDigits: d, maximumFractionDigits: d }); }
function fmtInt(n) { return n == null ? '—' : Number(n).toLocaleString('vi-VN'); }
function fmtPct(n, d = 2) { return (n >= 0 ? '+' : '') + Number(n).toFixed(d) + '%'; }
function fmtKbig(n) {
  if (n >= 1e9) return (n / 1e9).toFixed(2) + ' tỷ';
  if (n >= 1e6) return (n / 1e6).toFixed(2) + ' triệu';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + ' nghìn';
  return n + '';
}

Object.assign(window, {
  Icon, Logo, TPill, Sentiment, ConfChip, Sparkline, KpiCard,
  NewsItem, AlertRow, Topbar, SideRail, PageHead, Section,
  TextInput, Segment, StockCell, fmt, fmtInt, fmtPct, fmtKbig,
});
