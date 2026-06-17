import { Icon, Logo } from '@/components/shared';

interface TopbarProps {
  scenario: string;
  onScenario: (s: string) => void;
  onSearch?: () => void;
  onLogout?: () => void;
  screen?: string;
}

export function Topbar({ scenario, onScenario, onSearch, onLogout, screen: _screen }: TopbarProps) {
  const scenarios = [
    { k: 'up', label: 'Thị trường tăng', cls: 'up' },
    { k: 'down', label: 'Thị trường giảm', cls: 'down' },
    { k: 'volatile', label: 'Biến động mạnh', cls: 'vol' },
    { k: 'crisis', label: 'Khủng hoảng', cls: 'cr' },
  ];
  const cur = scenarios.find((s) => s.k === scenario) || scenarios[0];

  return (
    <header className="top-bar">
      <div className="brand-block" style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
        <Logo />
        <span style={{ width: 1, height: 18, background: 'var(--border)' }} />
        <span className={`scenario-banner ${cur.cls}`}>{cur.label}</span>
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
          <Icon name="search" size={14} />
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
        <button className="btn ghost sm" title="Refresh"><Icon name="refresh" size={14} /></button>
        <button className="btn ghost sm" title="Thông báo" style={{ position: 'relative' }}>
          <Icon name="bell" size={14} />
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
          <button className="btn ghost sm" title="Đăng xuất" onClick={onLogout}><Icon name="logout" size={14} /></button>
        </div>
      </div>
    </header>
  );
}
