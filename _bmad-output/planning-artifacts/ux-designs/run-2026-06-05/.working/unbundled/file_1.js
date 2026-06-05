// @ts-nocheck
/* QuantyFin · Settings screen — comprehensive
   Exposes window.QFSettings
*/

const { useState: zuseState, useMemo: zuseMemo } = React;

// ════════ NAV ════════
const SET_NAV = [
  { group: 'AI · Dữ liệu', items: [
    { k: 'llm',     label: 'LLM Gateway',       icon: 'sparkle', sub: 'Routing + budget' },
    { k: 'sources', label: 'Nguồn dữ liệu',     icon: 'database', sub: '8 nguồn · 6 RSS' },
    { k: 'kg',      label: 'Knowledge Graph',   icon: 'graph',    sub: 'Neo4j · embeddings' },
  ]},
  { group: 'Phân phối', items: [
    { k: 'alerts',  label: 'Cảnh báo & Webhooks', icon: 'bell',    sub: '6 rule · 3 kênh' },
  ]},
  { group: 'Quản trị', items: [
    { k: 'access',    label: 'Truy cập & API',  icon: 'shield',   sub: '12 thành viên · 4 key' },
    { k: 'workspace', label: 'Workspace',       icon: 'cog',      sub: 'Brand · vùng · lưu trữ' },
  ]},
];

// shared field row
function Field({ label, hint, children, span }) {
  return (
    <div className="set-field" style={span ? { gridColumn: 'span 2' } : null}>
      <div className="set-field-l">
        <div className="set-field-label">{label}</div>
        {hint && <div className="set-field-hint">{hint}</div>}
      </div>
      <div className="set-field-r">{children}</div>
    </div>
  );
}

function Toggle({ checked, onChange, label, disabled = false }) {
  return (
    <label className="qf-toggle" aria-label={label || undefined} data-on={checked ? 'true' : 'false'}>
      <input
        type="checkbox"
        checked={!!checked}
        disabled={disabled}
        onChange={(e) => onChange && onChange(e.target.checked)}
      />
      <span className="qf-toggle-track" aria-hidden="true">
        <span className="qf-toggle-thumb" />
      </span>
    </label>
  );
}

function StatusDot({ ok = true, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, font: '500 12px/1 var(--font-body)', color: ok ? 'var(--mint-deep)' : 'var(--gap)' }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: ok ? 'var(--mint)' : 'var(--gap)', boxShadow: ok ? '0 0 0 3px rgba(16,185,129,.18)' : '0 0 0 3px rgba(239,68,68,.16)' }} />
      {label}
    </span>
  );
}

function Stepper({ value, onChange, min = 0, max = 99, unit }) {
  return (
    <div className="set-stepper">
      <button type="button" onClick={() => onChange(Math.max(min, value - 1))}>−</button>
      <span className="v"><span className="n">{value}</span>{unit && <span className="u">{unit}</span>}</span>
      <button type="button" onClick={() => onChange(Math.min(max, value + 1))}>+</button>
    </div>
  );
}

function SecretField({ value, masked = true, onCopy }) {
  const [shown, setShown] = zuseState(!masked);
  return (
    <div className="set-secret">
      <code>{shown ? value : value.replace(/[a-z0-9]/gi, '•').replace(/\.+$/, '')}</code>
      <button type="button" title={shown ? 'Ẩn' : 'Hiện'} onClick={() => setShown(!shown)}>
        <Icon k={shown ? 'eyeOff' : 'eye'} size={13} />
      </button>
      <button type="button" title="Sao chép" onClick={onCopy}><Icon k="copy" size={13} /></button>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// SECTION · LLM GATEWAY
// ════════════════════════════════════════════════════════════════════
function SecLLM() {
  const [primary, setPrimary] = zuseState('sonnet');
  const [budget, setBudget] = zuseState(120000);
  const [cache, setCache] = zuseState(true);
  const [retry, setRetry] = zuseState(2);

  const dailySpend = (budget * 0.000003 * 0.62 + 1.84).toFixed(2);
  const monthSpend = (Number(dailySpend) * 30).toFixed(0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* usage KPI */}
      <div className="qf-grid qf-grid-4">
        <KpiCard label="Tokens · 24h" value={fmtInt(74820)} delta="+8%" deltaTone="up" sub="62% của budget" />
        <KpiCard label="Chi phí · 24h" value={`$${dailySpend}`} valueClass="iris" sub={`Ước tính tháng: $${monthSpend}`} />
        <KpiCard label="Yêu cầu · 24h" value={fmtInt(1842)} sub="cache hit 41%" />
        <KpiCard label="p95 latency" value="2.4s" sub="↓ 0.3s so với tuần trước" />
      </div>

      <Section title="Model routing" meta="Tự động chọn model theo task để cân bằng chi phí · chất lượng">
        <div>
          <div style={{ font: 'var(--type-label)', color: 'var(--fg-2)', marginBottom: 8 }}>Model chính cho analyst</div>
          <div className="set-model-grid">
            {[
              { k: 'haiku',  vendor: 'Anthropic', name: 'Claude Haiku 3.5',  desc: 'Tốc độ cao · phân loại nhanh', price: '$0.25 / 1M', tps: '180 tok/s' },
              { k: 'sonnet', vendor: 'Anthropic', name: 'Claude Sonnet 4',   desc: 'Phân tích sâu · lập luận đa bước', price: '$3.00 / 1M', tps: '95 tok/s', rec: true },
              { k: 'gpt4o',  vendor: 'OpenAI',    name: 'GPT-4o',            desc: 'Đa mục đích · multimodal',         price: '$2.50 / 1M', tps: '110 tok/s' },
              { k: 'gemini', vendor: 'Google',    name: 'Gemini 1.5 Pro',    desc: 'Long context · phân tích báo cáo', price: '$1.25 / 1M', tps: '85 tok/s' },
            ].map((m) => (
              <button key={m.k} onClick={() => setPrimary(m.k)} className="set-model-card" data-active={primary === m.k}>
                <div className="head">
                  <span className="v">{m.vendor}</span>
                  {m.rec && <span className="rec">Đề xuất</span>}
                  {primary === m.k && <Icon k="check" size={13} style={{ color: 'var(--iris)', marginLeft: 'auto' }} />}
                </div>
                <div className="n">{m.name}</div>
                <div className="d">{m.desc}</div>
                <div className="m"><span>{m.price}</span><span>·</span><span>{m.tps}</span></div>
              </button>
            ))}
          </div>
        </div>

        <div className="divider" />

        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', font: 'var(--type-label)', color: 'var(--fg-2)', marginBottom: 8 }}>
            <span>Token budget · ngày</span>
            <strong style={{ color: 'var(--fg-1)', font: '600 13px var(--font-mono)' }}>{fmtInt(budget)} tokens</strong>
          </div>
          <input type="range" min="20000" max="500000" step="10000" value={budget} onChange={(e) => setBudget(+e.target.value)} className="set-range" />
          <div style={{ display: 'flex', justifyContent: 'space-between', font: 'var(--type-caption)', color: 'var(--fg-3)' }}>
            <span>20K</span><span>500K</span>
          </div>
          <div className="set-callout iris">
            <Icon k="sparkle" size={13} />
            <div>
              Ước tính chi phí: <strong>${(budget * 0.000003).toFixed(2)} / ngày</strong> với Sonnet 4.
              Fallback tự động sang <strong>Haiku</strong> khi đạt 80% budget · gửi cảnh báo Telegram khi đạt 95%.
            </div>
          </div>
        </div>

        <div className="divider" />

        <div style={{ font: 'var(--type-label)', color: 'var(--fg-2)', marginBottom: 8 }}>Routing per task</div>
        <table className="dt set-route-table">
          <thead>
            <tr><th>Task</th><th>Model</th><th>Max tokens</th><th>Temperature</th><th>Fallback</th><th>Trạng thái</th></tr>
          </thead>
          <tbody>
            {[
              { n: 'Headline extractor', m: 'Haiku 3.5',    t: '512',  temp: '0.0', fb: 'GPT-4o-mini', ok: true },
              { n: 'Sentiment scorer',   m: 'GPT-4o-mini',  t: '256',  temp: '0.0', fb: 'Haiku 3.5',   ok: true },
              { n: 'Analyst Q&A',        m: 'Sonnet 4',     t: '4096', temp: '0.4', fb: 'Gemini 1.5', ok: true },
              { n: 'Daily briefing',     m: 'Sonnet 4',     t: '8192', temp: '0.3', fb: 'GPT-4o',     ok: true },
              { n: 'KG entity extract',  m: 'Haiku 3.5',    t: '1024', temp: '0.0', fb: 'GPT-4o-mini', ok: true },
              { n: 'Embedding',          m: 'text-emb-3-l', t: '—',    temp: '—',   fb: 'BGE-M3',     ok: false },
            ].map((r) => (
              <tr key={r.n}>
                <td><span style={{ font: '500 13px var(--font-body)', color: 'var(--fg-1)' }}>{r.n}</span></td>
                <td><TPill tone="iris">{r.m}</TPill></td>
                <td className="num tabular" style={{ font: '500 12px var(--font-mono)' }}>{r.t}</td>
                <td className="num tabular" style={{ font: '500 12px var(--font-mono)' }}>{r.temp}</td>
                <td><span style={{ font: 'var(--type-mono-sm)', color: 'var(--fg-3)' }}>{r.fb}</span></td>
                <td><StatusDot ok={r.ok} label={r.ok ? 'Hoạt động' : 'Suy giảm'} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="API keys · nhà cung cấp" meta="Mọi key được mã hóa AES-256 · không hiển thị nguyên trong UI">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {[
            { vendor: 'Anthropic', label: 'PROD · primary',    key: 'sk-ant-api03-7Hk2Ld...x9Q', rpm: '4000', last: '2 phút trước', ok: true },
            { vendor: 'OpenAI',    label: 'PROD · backup',     key: 'sk-proj-abQ8y...Lmn',       rpm: '3500', last: '14 phút trước', ok: true },
            { vendor: 'Google',    label: 'PROD · long-ctx',   key: 'AIzaSyA...kxQ',             rpm: '600',  last: '3 giờ trước', ok: true },
            { vendor: 'OpenRouter',label: 'DEV · sandbox',     key: 'sk-or-v1-...8a',            rpm: '60',   last: 'Hôm qua', ok: false },
          ].map((k) => (
            <div key={k.label} className="set-key-row">
              <div className="vendor">
                <span className="logo">{k.vendor[0]}</span>
                <div>
                  <div className="n">{k.vendor}</div>
                  <div className="l">{k.label}</div>
                </div>
              </div>
              <SecretField value={k.key} />
              <div className="meta">
                <span>{k.rpm} <em>RPM</em></span>
                <span className="sep">·</span>
                <span>Lần cuối {k.last}</span>
              </div>
              <StatusDot ok={k.ok} label={k.ok ? 'Hoạt động' : 'Đã hết hạn'} />
              <div className="act">
                <button className="btn ghost sm" title="Xoay key"><Icon k="rotate" size={12} /></button>
                <button className="btn ghost sm" title="Xóa"><Icon k="trash" size={12} /></button>
              </div>
            </div>
          ))}
          <button className="btn sm" style={{ alignSelf: 'flex-start' }}><Icon k="plus" size={12} /> Thêm provider</button>
        </div>
      </Section>

      <Section title="Hiệu suất & độ tin cậy" meta="Retry · cache · timeout">
        <div className="set-fields">
          <Field label="Retry tối đa" hint="Tự retry với exponential backoff khi gặp 429 / 5xx">
            <Stepper value={retry} onChange={setRetry} min={0} max={6} unit="lần" />
          </Field>
          <Field label="Timeout mỗi request" hint="Vượt timeout sẽ rơi vào fallback">
            <Stepper value={60} onChange={() => {}} min={5} max={300} unit="giây" />
          </Field>
          <Field label="Prompt cache" hint="Tái sử dụng prefix của system prompt · giảm 60% chi phí Sonnet">
            <Toggle checked={cache} onChange={setCache} label="Prompt cache" />
          </Field>
          <Field label="Hard cost cap" hint="Khi đạt mức này trong ngày, hệ thống chỉ phục vụ task ưu tiên thấp">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input className="set-input mono" defaultValue="$50.00" style={{ width: 110 }} />
              <span style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>/ ngày</span>
            </div>
          </Field>
        </div>
      </Section>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// SECTION · NGUỒN DỮ LIỆU
// ════════════════════════════════════════════════════════════════════
function SecSources() {
  const srcs = [
    { fav: 'C', name: 'CafeF',     url: 'cafef.vn/rss',           tier: 'RSS',        per: 'Mỗi 5 phút',  total: 184, ok: true,  filt: 62 },
    { fav: 'V', name: 'Vietstock', url: 'vietstock.vn/rss',       tier: 'RSS',        per: 'Mỗi 5 phút',  total: 142, ok: true,  filt: 55 },
    { fav: 'V', name: 'VnEconomy', url: 'vneconomy.vn',           tier: 'Search',     per: 'Mỗi 10 phút', total:  96, ok: true,  filt: 48 },
    { fav: 'T', name: 'Tuổi Trẻ',  url: 'tuoitre.vn/kinh-doanh',  tier: 'Playwright', per: 'Mỗi 30 phút', total:  48, ok: true,  filt: 71 },
    { fav: 'N', name: 'NDH',       url: 'ndh.vn',                 tier: 'RSS',        per: 'Mỗi 5 phút',  total:  68, ok: true,  filt: 58 },
    { fav: 'Đ', name: 'ĐTCK',      url: 'tinnhanhchungkhoan.vn',  tier: 'Search',     per: 'Mỗi 10 phút', total:  84, ok: true,  filt: 64 },
    { fav: 'F', name: 'FireAnt',   url: 'fireant.vn',             tier: 'Playwright', per: 'Mỗi 30 phút', total:  21, ok: false, filt: 42 },
    { fav: 'X', name: 'X · finance', url: 'x.com/lists/vn-fin',   tier: 'API',        per: 'Mỗi 2 phút',  total: 312, ok: true,  filt: 84 },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="qf-grid qf-grid-4">
        <KpiCard label="Nguồn đang theo dõi" value="8" sub="6 RSS · 2 Search · 2 Playwright" />
        <KpiCard label="Tin / 24h" value={fmtInt(955)} delta="+12%" deltaTone="up" />
        <KpiCard label="Zero-cost filter" value="62%" valueClass="iris" sub="Lọc trước khi gọi LLM" />
        <KpiCard label="Tỷ lệ thành công" value="98.4%" sub="1 nguồn đang lỗi: FireAnt" />
      </div>

      <Section title="Danh sách nguồn" meta="Mỗi nguồn có lịch riêng · zero-cost filter chạy ngay sau crawl"
        actions={<><button className="btn ghost sm"><Icon k="filter" size={12} /> Lọc</button><button className="btn sm primary"><Icon k="plus" size={12} /> Thêm nguồn</button></>}>
        <div className="set-source-list">
          {srcs.map((s) => (
            <div key={s.name} className="set-source-row">
              <span className="fav">{s.fav}</span>
              <div className="info">
                <div className="name-row">
                  <span className="name">{s.name}</span>
                  <span className="trace-pill" style={{ background: 'var(--bg)' }}>{s.tier}</span>
                </div>
                <div className="url">{s.url}</div>
              </div>
              <div className="schedule">
                <Icon k="clock" size={12} />
                <span>{s.per}</span>
              </div>
              <div className="metric">
                <strong>{s.total}</strong>
                <span>tin · 24h</span>
              </div>
              <div className="metric">
                <strong style={{ color: 'var(--iris-deep)' }}>{s.filt}%</strong>
                <span>lọc</span>
              </div>
              <StatusDot ok={s.ok} label={s.ok ? 'Đang chạy' : 'Lỗi DNS'} />
              <div className="act">
                <Toggle checked={s.ok} onChange={() => {}} label="Bật/tắt" />
                <button className="btn ghost sm" title="Chạy ngay"><Icon k="refresh" size={12} /></button>
                <button className="btn ghost sm" title="Sửa"><Icon k="edit" size={12} /></button>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <div className="qf-grid qf-grid-2-1">
        <Section title="Zero-cost filter" meta="Lọc tin trước khi gửi LLM · tiết kiệm token" ai>
          <div className="set-callout iris" style={{ marginBottom: 12 }}>
            <Icon k="sparkle" size={13} />
            <div>Đã loại <strong>591 tin</strong> trong 24h · ước tính tiết kiệm <strong>$8.40</strong>.</div>
          </div>
          <div style={{ font: 'var(--type-label)', color: 'var(--fg-2)', marginBottom: 8 }}>Rule đang áp dụng</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {[
              { r: 'Tiêu đề ≥ 4 từ khóa watchlist', hit: 41, ok: true },
              { r: 'Loại tin "tuyển dụng", "khuyến mại"',   hit: 28, ok: true },
              { r: 'Nguồn trong allowlist ngành',           hit: 18, ok: true },
              { r: 'Phát hiện click-bait (regex)',          hit: 13, ok: true },
              { r: 'TF-IDF tương đồng tin đã có > 0.85',   hit:  7, ok: false },
            ].map((rule) => (
              <div key={rule.r} className="set-rule-row">
                <Toggle checked={rule.ok} onChange={() => {}} label="" />
                <div className="t">{rule.r}</div>
                <span className="m">{rule.hit}% lọc</span>
                <button className="btn ghost sm"><Icon k="edit" size={11} /></button>
              </div>
            ))}
          </div>
          <button className="btn sm" style={{ marginTop: 10 }}><Icon k="plus" size={12} /> Thêm rule</button>
        </Section>

        <Section title="Crawler global" meta="Cấu hình áp cho mọi nguồn">
          <div className="set-fields cmp">
            <Field label="Concurrency" hint="Số request đồng thời">
              <Stepper value={8} onChange={() => {}} min={1} max={32} unit="req" />
            </Field>
            <Field label="Timeout" hint="Bỏ qua sau">
              <Stepper value={20} onChange={() => {}} min={5} max={120} unit="giây" />
            </Field>
            <Field label="User-Agent" hint="Xoay UA mỗi lần crawl">
              <Toggle checked={true} onChange={() => {}} label="Rotate UA" />
            </Field>
            <Field label="Proxy pool" hint="6 IP · auto rotate">
              <Toggle checked={true} onChange={() => {}} label="Proxy" />
            </Field>
            <Field label="Tuân thủ robots.txt" hint="Tôn trọng disallow">
              <Toggle checked={true} onChange={() => {}} label="robots" />
            </Field>
            <Field label="Giữ raw HTML" hint="14 ngày · để re-extract">
              <Toggle checked={false} onChange={() => {}} label="Lưu HTML" />
            </Field>
          </div>
        </Section>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// SECTION · KNOWLEDGE GRAPH
// ════════════════════════════════════════════════════════════════════
function SecKG() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="qf-grid qf-grid-4">
        <KpiCard label="Thực thể" value={fmtInt(2840)} sub="+184 trong 7 ngày" />
        <KpiCard label="Quan hệ" value={fmtInt(11203)} sub="ø bậc = 7.9" />
        <KpiCard label="Conf · TB" value="78%" valueClass="iris" sub="Ngưỡng tự động: 65%" />
        <KpiCard label="Lần cuối refresh" value="14:30:22" sub="cron · 30 phút" />
      </div>

      <Section title="Kết nối graph database" meta="Neo4j · Aura cloud">
        <div className="set-fields">
          <Field label="Endpoint" hint="bolt+s:// hoặc neo4j+s://">
            <input className="set-input mono" defaultValue="neo4j+s://quantyfin.databases.neo4j.io" />
          </Field>
          <Field label="Database" hint="Tên database">
            <input className="set-input mono" defaultValue="quantyfin-prod" />
          </Field>
          <Field label="Username">
            <input className="set-input mono" defaultValue="neo4j" />
          </Field>
          <Field label="Password" hint="Mã hóa AES-256 trong vault">
            <SecretField value="Bx7K2pLm9Q.aR8nT" />
          </Field>
          <Field label="SSL · TLS" hint="Bắt buộc cho production">
            <Toggle checked={true} onChange={() => {}} />
          </Field>
          <Field label="Tình trạng kết nối" hint="Auto-ping mỗi 60s">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <StatusDot ok={true} label="Kết nối ổn · 24ms RTT" />
              <button className="btn ghost sm"><Icon k="refresh" size={12} /> Test</button>
            </div>
          </Field>
        </div>
      </Section>

      <Section title="Loại thực thể" meta="Phân loại + nguồn trích xuất + quy tắc đặt tên">
        <table className="dt set-route-table">
          <thead>
            <tr><th>Loại</th><th className="num">Đếm</th><th>Trích xuất</th><th>Ngưỡng conf</th><th>Auto-link</th><th>Trạng thái</th></tr>
          </thead>
          <tbody>
            {[
              { type: 'Event',  color: '#FCAF16', n: 142,  src: 'News NER + KG analyst', th: '70%', auto: true },
              { type: 'Sector', color: '#7C6CF5', n: 9,    src: 'Static taxonomy',       th: '—',   auto: false },
              { type: 'Stock',  color: '#2A2B86', n: 230,  src: 'HOSE · HNX · UPCOM',    th: '—',   auto: false },
              { type: 'Leader', color: '#10b981', n: 412,  src: 'Bố cáo + NER',          th: '80%', auto: true },
              { type: 'Macro',  color: '#f59e0b', n: 38,   src: 'NHNN + GSO + Reuters',  th: '75%', auto: true },
              { type: 'Company',color: '#a78bfa', n: 2009, src: 'BCTC + KG',             th: '70%', auto: true },
            ].map((t) => (
              <tr key={t.type}>
                <td>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 10, height: 10, borderRadius: '50%', background: t.color }} />
                    <span style={{ font: '600 13px var(--font-body)' }}>{t.type}</span>
                  </span>
                </td>
                <td className="num tabular" style={{ font: '600 13px var(--font-mono)' }}>{fmtInt(t.n)}</td>
                <td><span style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>{t.src}</span></td>
                <td className="num tabular" style={{ font: '500 12px var(--font-mono)', color: 'var(--iris-deep)' }}>{t.th}</td>
                <td><Toggle checked={t.auto} onChange={() => {}} /></td>
                <td><StatusDot ok={true} label="Hoạt động" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <div className="qf-grid qf-grid-2-1">
        <Section title="Loại quan hệ · trọng số" meta="Trọng số quyết định độ lan tỏa khi giải thích path">
          <div className="set-edge-list">
            {[
              { e: 'IMPACTS_POS', w: 1.00, dir: 'positive', n: 1284 },
              { e: 'IMPACTS_NEG', w: 1.00, dir: 'negative', n:  892 },
              { e: 'BELONGS_TO',  w: 0.40, dir: 'neutral',  n: 2009 },
              { e: 'CORRELATES',  w: 0.60, dir: 'neutral',  n: 4218 },
              { e: 'SUPPLIES',    w: 0.75, dir: 'neutral',  n:  514 },
              { e: 'MANAGES',     w: 0.85, dir: 'positive', n:  412 },
              { e: 'INFLUENCES',  w: 0.55, dir: 'neutral',  n:  893 },
              { e: 'AMPLIFIES',   w: 1.20, dir: 'negative', n:  142 },
            ].map((e) => (
              <div key={e.e} className="set-edge-row">
                <span className="lbl" style={{ font: '600 11.5px var(--font-mono)' }}>{e.e}</span>
                <div className="bar">
                  <div className="fill" style={{ width: `${(e.w/1.2)*100}%`, background: e.dir === 'positive' ? 'var(--mint)' : e.dir === 'negative' ? 'var(--gap)' : 'var(--iris)' }} />
                </div>
                <span className="w tabular" style={{ font: '600 12px var(--font-mono)' }}>{e.w.toFixed(2)}</span>
                <span className="n">{fmtInt(e.n)}</span>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Vector embeddings" meta="Cho semantic search + clustering" ai>
          <div className="set-fields cmp">
            <Field label="Model" hint="OpenAI text-embedding-3-large">
              <select className="set-input"><option>text-embedding-3-large</option><option>BGE-M3 (local)</option><option>Cohere embed-v3</option></select>
            </Field>
            <Field label="Số chiều">
              <Stepper value={1536} onChange={() => {}} min={256} max={3072} unit="dim" />
            </Field>
            <Field label="Vector store" hint="Qdrant cluster">
              <input className="set-input mono" defaultValue="qdrant://qf-vec.internal:6333" />
            </Field>
            <Field label="Cập nhật khi…" hint="Trigger reembed">
              <select className="set-input"><option>Thực thể thay đổi tên</option><option>Có thông tin mới</option><option>Thủ công</option></select>
            </Field>
          </div>
          <div className="divider" />
          <div className="set-callout">
            <Icon k="server" size={13} />
            <div>Index hiện có <strong>2,840</strong> vector · <strong>4.18 GB</strong> · upsert/giây trung bình <strong>32</strong>.</div>
          </div>
        </Section>
      </div>

      <Section title="Lịch refresh" meta="Cron jobs cập nhật KG">
        <div className="set-cron">
          {[
            { name: 'Daily entity sweep',  cron: '0 1 * * *',    next: '01:00 ngày mai', last: 'OK · 02:14', dur: '6m 12s' },
            { name: 'Hourly news → KG',    cron: '0 * * * *',    next: '15:00 hôm nay', last: 'OK · 14:00', dur: '1m 42s' },
            { name: 'Edge weight recalc',  cron: '0 0 * * 0',    next: 'CN tuần này',   last: 'OK · 24/05', dur: '18m' },
            { name: 'Vector reindex',      cron: '0 3 * * *',    next: '03:00 ngày mai', last: 'OK · 03:00', dur: '11m 03s' },
            { name: 'Macro feed merge',    cron: '*/30 * * * *', next: 'Trong 8 phút',  last: 'OK · 14:30', dur: '52s' },
          ].map((c) => (
            <div key={c.name} className="set-cron-row">
              <div>
                <div className="n">{c.name}</div>
                <code className="c">{c.cron}</code>
              </div>
              <div className="next"><span className="l">Lần tới</span><strong>{c.next}</strong></div>
              <div className="next"><span className="l">Lần cuối</span><strong>{c.last}</strong></div>
              <div className="next"><span className="l">Thời gian</span><strong>{c.dur}</strong></div>
              <Toggle checked={true} onChange={() => {}} />
              <button className="btn ghost sm" title="Chạy"><Icon k="refresh" size={12} /></button>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// SECTION · ALERTS & WEBHOOKS
// ════════════════════════════════════════════════════════════════════
function SecAlerts() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Section title="Kênh phân phối" meta="Cấu hình các kênh nhận cảnh báo"
        actions={<button className="btn sm primary"><Icon k="plus" size={12} /> Thêm kênh</button>}>
        <div className="set-channel-list">
          {[
            { type: 'telegram', name: '@quantyfin_team',  desc: 'Kênh nhóm · 12 thành viên',          status: 'connected', last: '3 phút trước', sent: 184 },
            { type: 'telegram', name: '@hungnguyen_pa',   desc: 'Cá nhân · ưu tiên cao',              status: 'connected', last: '12 phút trước', sent: 42 },
            { type: 'email',    name: 'alerts@quantyfin.vn', desc: 'Daily digest 07:00 + critical',    status: 'connected', last: '7 giờ trước',  sent: 24 },
            { type: 'slack',    name: '#qf-signals',      desc: 'Slack workspace · YODY',             status: 'connected', last: '1 giờ trước',  sent: 88 },
            { type: 'webhook',  name: 'https://hooks.qf.../briefing', desc: 'POST · n8n workflow',     status: 'pending',   last: '—',           sent: 0 },
            { type: 'webhook',  name: 'https://hooks.qf.../audit',    desc: 'Audit log mirror',        status: 'error',     last: 'Hôm qua',     sent: 0 },
          ].map((c) => {
            const meta = { telegram: { icon: 'chat', color: '#0088cc' }, email: { icon: 'mail', color: '#7c6cf5' }, slack: { icon: 'chat', color: '#4a154b' }, webhook: { icon: 'webhook', color: '#10b981' } }[c.type];
            const status = c.status === 'connected' ? { ok: true, label: 'Đã kết nối' } : c.status === 'pending' ? { ok: true, label: 'Chờ xác thực' } : { ok: false, label: 'Lỗi gửi · 5xx' };
            return (
              <div key={c.name} className="set-channel-row">
                <span className="ico" style={{ background: meta.color + '22', color: meta.color }}>
                  <Icon k={meta.icon} size={15} />
                </span>
                <div className="info">
                  <div className="n">{c.name}</div>
                  <div className="d">{c.desc}</div>
                </div>
                <div className="metric">
                  <strong>{c.sent}</strong>
                  <span>gửi · 24h</span>
                </div>
                <div className="metric">
                  <span>Lần cuối</span>
                  <strong>{c.last}</strong>
                </div>
                <StatusDot ok={status.ok} label={status.label} />
                <div className="act">
                  <button className="btn ghost sm" title="Test"><Icon k="send" size={12} /></button>
                  <button className="btn ghost sm" title="Sửa"><Icon k="edit" size={12} /></button>
                  <button className="btn ghost sm" title="Xóa"><Icon k="trash" size={12} /></button>
                </div>
              </div>
            );
          })}
        </div>
      </Section>

      <div className="qf-grid qf-grid-2-1">
        <Section title="Routing theo mức độ" meta="Mỗi mức nghiêm trọng đi qua các kênh khác nhau">
          <table className="dt set-route-table">
            <thead><tr><th>Mức</th><th>Telegram team</th><th>Telegram cá nhân</th><th>Email</th><th>Slack</th><th>Webhook</th></tr></thead>
            <tbody>
              {[
                { sev: 'Critical', color: 'var(--gap)',     vals: [true, true,  true,  true,  true] },
                { sev: 'High',     color: 'var(--gold-deep)', vals: [true, true,  false, true,  true] },
                { sev: 'Medium',   color: 'var(--gold)',    vals: [true, false, false, true,  false] },
                { sev: 'Info',     color: 'var(--iris)',    vals: [false,false, true,  false, false] },
                { sev: 'Digest',   color: 'var(--fg-3)',    vals: [false,false, true,  false, false] },
              ].map((r) => (
                <tr key={r.sev}>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8, font: '600 12.5px var(--font-body)' }}>
                      <span style={{ width: 8, height: 8, borderRadius: '50%', background: r.color }} />
                      {r.sev}
                    </span>
                  </td>
                  {r.vals.map((v, i) => (
                    <td key={i} style={{ textAlign: 'center' }}><Toggle checked={v} onChange={() => {}} label="" /></td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        <Section title="Quy tắc gửi" meta="Tránh spam · giờ yên tĩnh">
          <div className="set-fields cmp">
            <Field label="Throttle / kênh" hint="Tối đa mỗi 5 phút">
              <Stepper value={6} onChange={() => {}} min={1} max={60} unit="tin" />
            </Field>
            <Field label="Dedup window" hint="Gộp tin trùng lặp">
              <Stepper value={15} onChange={() => {}} min={0} max={120} unit="phút" />
            </Field>
            <Field label="Giờ yên tĩnh" hint="Chỉ critical mới gửi">
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, font: '500 12.5px var(--font-mono)' }}>
                <input className="set-input mono" defaultValue="22:00" style={{ width: 70 }} />
                <span style={{ color: 'var(--fg-3)' }}>→</span>
                <input className="set-input mono" defaultValue="06:30" style={{ width: 70 }} />
              </div>
            </Field>
            <Field label="Cuối tuần" hint="Tắt non-critical T7 · CN">
              <Toggle checked={true} onChange={() => {}} />
            </Field>
            <Field label="Retry khi fail" hint="Backoff 1m · 5m · 15m">
              <Toggle checked={true} onChange={() => {}} />
            </Field>
            <Field label="Audit signature" hint="Ký HMAC mỗi webhook">
              <Toggle checked={true} onChange={() => {}} />
            </Field>
          </div>
        </Section>
      </div>

      <Section title="Mẫu tin · message templates" meta="Hỗ trợ biến {{ticker}} · {{price}} · {{conf}}"
        actions={<button className="btn ghost sm"><Icon k="plus" size={12} /> Thêm mẫu</button>}>
        <div className="set-template-list">
          {[
            { name: 'Price target hit',  channel: 'Telegram', body: '🎯 {{ticker}} chạm mục tiêu {{target}} ({{change}}). Volume {{vol_mult}}× TB.' },
            { name: 'Volume spike',      channel: 'Telegram', body: '⚡ {{ticker}} · KL gấp {{mult}}× trong {{window}}p. Giá {{change}}.' },
            { name: 'Daily briefing',    channel: 'Email',    body: 'Tổng quan ngày {{date}} — {{n_news}} tin · {{n_alerts}} cảnh báo · AI conf {{conf}}.' },
            { name: 'AI insight',        channel: 'Slack',    body: ':sparkles: {{title}} — AI conf {{conf}}. KG path: {{path}}. Trace: {{trace}}.' },
          ].map((t) => (
            <div key={t.name} className="set-template-row">
              <div className="h">
                <span className="n">{t.name}</span>
                <span className="trace-pill">{t.channel}</span>
              </div>
              <code className="b">{t.body}</code>
              <div className="a">
                <button className="btn ghost sm"><Icon k="edit" size={12} /></button>
                <button className="btn ghost sm"><Icon k="copy" size={12} /></button>
              </div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// SECTION · TRUY CẬP & API
// ════════════════════════════════════════════════════════════════════
function SecAccess() {
  const members = [
    { name: 'Nguyễn Quang Hùng', email: 'hungnguyen@quantyfin.vn', role: 'Owner',    avatar: 'HN', tone: 'iris',  last: 'Đang online' },
    { name: 'Trần Mỹ Linh',      email: 'linh.tm@quantyfin.vn',   role: 'Analyst',  avatar: 'LT', tone: 'iris',  last: '2 giờ trước' },
    { name: 'Phạm Đức Minh',     email: 'minh.pd@quantyfin.vn',   role: 'Analyst',  avatar: 'MP', tone: 'mint',  last: '14 phút trước' },
    { name: 'Lê Hoàng Anh',      email: 'anh.lh@quantyfin.vn',    role: 'Trader',   avatar: 'AL', tone: 'gold',  last: 'Hôm qua' },
    { name: 'Vũ Thanh Tâm',      email: 'tam.vt@quantyfin.vn',    role: 'Viewer',   avatar: 'TV', tone: 'mint',  last: '3 ngày trước' },
    { name: 'Đỗ Khánh Linh',     email: 'linh.dk@quantyfin.vn',   role: 'Admin',    avatar: 'KL', tone: 'rose',  last: 'Đang online' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="qf-grid qf-grid-4">
        <KpiCard label="Thành viên" value="12" sub="4 admin · 6 analyst · 2 viewer" />
        <KpiCard label="API key đang hoạt động" value="4" sub="2 prod · 2 dev" />
        <KpiCard label="Phiên đăng nhập" value="18" sub="trong 24h qua" />
        <KpiCard label="SSO · SAML" value="Bật" valueClass="iris" sub="Workspace SSO · Google" />
      </div>

      <Section title="Thành viên" meta={`${members.length} người · phân theo role`}
        actions={<><button className="btn ghost sm"><Icon k="download" size={12} /> Xuất CSV</button><button className="btn sm primary"><Icon k="plus" size={12} /> Mời thành viên</button></>}>
        <table className="dt set-member-table">
          <thead>
            <tr>
              <th>Người dùng</th><th>Role</th><th>Watchlist</th><th>API call · 7d</th><th>Hoạt động cuối</th><th></th>
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.email}>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className={'avatar ' + m.tone}>{m.avatar}</span>
                    <div>
                      <div style={{ font: '500 13px var(--font-body)', color: 'var(--fg-1)' }}>{m.name}</div>
                      <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>{m.email}</div>
                    </div>
                  </div>
                </td>
                <td><span className={'role-pill ' + m.role.toLowerCase()}>{m.role}</span></td>
                <td style={{ font: '500 12px var(--font-mono)', color: 'var(--fg-2)' }}>{Math.floor(Math.random()*12)+4} mã</td>
                <td className="num tabular" style={{ font: '500 12.5px var(--font-mono)' }}>{fmtInt(Math.floor(Math.random()*4000)+200)}</td>
                <td style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>{m.last}</td>
                <td>
                  <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                    <button className="btn ghost sm"><Icon k="edit" size={12} /></button>
                    <button className="btn ghost sm"><Icon k="more" size={12} /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <div className="qf-grid qf-grid-2-1">
        <Section title="Ma trận quyền" meta="Role × capability">
          <table className="dt set-role-matrix">
            <thead><tr><th>Capability</th><th>Owner</th><th>Admin</th><th>Analyst</th><th>Trader</th><th>Viewer</th></tr></thead>
            <tbody>
              {[
                { c: 'Xem dashboard & dữ liệu',         vals: [true,true,true,true,true] },
                { c: 'Đặt cảnh báo & rule riêng',       vals: [true,true,true,true,false] },
                { c: 'Sửa Knowledge Graph',             vals: [true,true,true,false,false] },
                { c: 'Cấu hình LLM / model routing',    vals: [true,true,false,false,false] },
                { c: 'Quản lý API keys',                vals: [true,true,false,false,false] },
                { c: 'Mời / xóa thành viên',            vals: [true,true,false,false,false] },
                { c: 'Xuất dữ liệu thô',                vals: [true,true,true,false,false] },
                { c: 'Xóa / khóa workspace',            vals: [true,false,false,false,false] },
              ].map((r) => (
                <tr key={r.c}>
                  <td style={{ font: '500 12.5px var(--font-body)' }}>{r.c}</td>
                  {r.vals.map((v, i) => (
                    <td key={i} style={{ textAlign: 'center' }}>
                      {v ? <Icon k="check" size={13} style={{ color: 'var(--mint-deep)' }} /> : <span style={{ color: 'var(--fg-3)' }}>—</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        <Section title="Xác thực" meta="SSO · MFA · device trust">
          <div className="set-fields cmp">
            <Field label="SSO · SAML" hint="Workspace SSO qua Google">
              <Toggle checked={true} onChange={() => {}} />
            </Field>
            <Field label="MFA bắt buộc" hint="TOTP hoặc passkey">
              <Toggle checked={true} onChange={() => {}} />
            </Field>
            <Field label="Phiên đăng nhập" hint="Tự đăng xuất">
              <Stepper value={14} onChange={() => {}} min={1} max={90} unit="ngày" />
            </Field>
            <Field label="IP allow list" hint="Chỉ truy cập từ IP trong list">
              <Toggle checked={false} onChange={() => {}} />
            </Field>
            <Field label="Audit log retention" hint="Lưu sự kiện đăng nhập + thay đổi">
              <Stepper value={365} onChange={() => {}} min={30} max={730} unit="ngày" />
            </Field>
          </div>
        </Section>
      </div>

      <Section title="API keys của workspace" meta="Key dùng cho integration ngoài · không phải LLM provider key"
        actions={<button className="btn sm primary"><Icon k="key" size={12} /> Tạo key mới</button>}>
        <div className="set-apikey-list">
          {[
            { name: 'n8n · briefing flow',  key: 'qf_live_7Hk2Ld...x9Q', scope: 'read:news, write:alerts', owner: 'Nguyễn Q. Hùng',  created: '12/05/2026', last: '14 phút trước', uses: 4218, ok: true },
            { name: 'Power BI · finance',   key: 'qf_live_Mn3pq...Lvc', scope: 'read:all',                owner: 'Trần M. Linh',     created: '02/03/2026', last: '2 giờ trước',  uses: 1280, ok: true },
            { name: 'iOS app · mobile',     key: 'qf_live_8aQy2...Wnk', scope: 'read:dashboard',          owner: 'Lê H. Anh',        created: '24/04/2026', last: '7 phút trước', uses:  894, ok: true },
            { name: 'Audit · SIEM',         key: 'qf_test_pKx4n...Bd2', scope: 'read:audit_log',          owner: 'Đỗ K. Linh',       created: 'Hôm nay',     last: '—',           uses:    0, ok: false },
          ].map((k) => (
            <div key={k.name} className="set-apikey-row">
              <div className="h">
                <Icon k="key" size={14} style={{ color: 'var(--iris)' }} />
                <span className="n">{k.name}</span>
                {!k.ok && <span className="role-pill viewer">Chưa kích hoạt</span>}
              </div>
              <SecretField value={k.key} />
              <div className="scope">{k.scope.split(',').map((s) => <span key={s} className="trace-pill" style={{ background:'var(--bg-muted)' }}>{s.trim()}</span>)}</div>
              <div className="m">
                <div><span>Sở hữu</span><strong>{k.owner}</strong></div>
                <div><span>Tạo</span><strong>{k.created}</strong></div>
                <div><span>Lần cuối</span><strong>{k.last}</strong></div>
                <div><span>Số lượt</span><strong className="tabular">{fmtInt(k.uses)}</strong></div>
              </div>
              <div className="a">
                <button className="btn ghost sm"><Icon k="rotate" size={12} /> Xoay</button>
                <button className="btn ghost sm"><Icon k="trash" size={12} /></button>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Audit log gần nhất" meta="Hành động quan trọng trong 24 giờ qua"
        actions={<button className="btn ghost sm"><Icon k="ext" size={12} /> Xem toàn bộ</button>}>
        <div className="set-audit-list">
          {[
            { who: 'hungnguyen@', what: 'Cập nhật routing strategy', tgt: 'task: Analyst Q&A → Sonnet 4', ip: '113.161.42.18', when: '14:30:08' },
            { who: 'linh.tm@',    what: 'Tạo API key',                tgt: 'n8n · briefing flow',         ip: '171.231.18.92', when: '14:18:42' },
            { who: 'minh.pd@',    what: 'Thêm rule cảnh báo',         tgt: 'rule#142 · VHM volume',       ip: '113.161.42.20', when: '13:48:14' },
            { who: 'anh.lh@',     what: 'Đăng nhập (SSO)',            tgt: '—',                            ip: '14.232.84.11',  when: '13:12:08' },
            { who: 'hungnguyen@', what: 'Xoay key Anthropic prod',    tgt: 'provider: anthropic',         ip: '113.161.42.18', when: '12:30:00' },
            { who: 'system',      what: 'Auto-retry webhook fail',    tgt: 'audit · SIEM (3 lần)',         ip: '—',              when: '11:14:30' },
          ].map((r, i) => (
            <div key={i} className="set-audit-row">
              <span className="t">{r.when}</span>
              <span className="w" style={{ font: 'var(--type-mono-sm)' }}>{r.who}</span>
              <span className="a">{r.what}</span>
              <span className="g" style={{ color: 'var(--fg-3)' }}>{r.tgt}</span>
              <span className="ip" style={{ font: 'var(--type-mono-sm)', color: 'var(--fg-3)' }}>{r.ip}</span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// SECTION · WORKSPACE
// ════════════════════════════════════════════════════════════════════
function SecWorkspace() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Section title="Hồ sơ workspace" meta="Thông tin chung · vùng và ngôn ngữ">
        <div className="set-fields">
          <Field label="Tên workspace" hint="Hiển thị trong UI và email">
            <input className="set-input" defaultValue="QuantyFin Production" />
          </Field>
          <Field label="Slug · subdomain" hint="quantyfin-prod.quantyfin.app">
            <input className="set-input mono" defaultValue="quantyfin-prod" />
          </Field>
          <Field label="Ngôn ngữ chính">
            <select className="set-input"><option>Tiếng Việt</option><option>English</option></select>
          </Field>
          <Field label="Múi giờ">
            <select className="set-input"><option>GMT+7 · Asia/Ho_Chi_Minh</option><option>GMT+0 · UTC</option><option>GMT+8 · Asia/Singapore</option></select>
          </Field>
          <Field label="Giờ giao dịch · phiên VN" hint="HOSE · HNX · UPCOM">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, font: '500 12.5px var(--font-mono)' }}>
              <input className="set-input mono" defaultValue="09:00" style={{ width: 80 }} />
              <span style={{ color: 'var(--fg-3)' }}>→</span>
              <input className="set-input mono" defaultValue="14:45" style={{ width: 80 }} />
            </div>
          </Field>
          <Field label="Định dạng số · tiền tệ" hint="1.234.567,89 ₫ · vi-VN">
            <select className="set-input"><option>vi-VN · ₫ (đồng)</option><option>en-US · $</option></select>
          </Field>
        </div>
      </Section>

      <div className="qf-grid qf-grid-2-1">
        <Section title="Thương hiệu" meta="Logo, màu nhấn và favicon">
          <div className="set-brand">
            <div className="logo-slot">
              <div className="qf-mark" style={{ width: 56, height: 56, font: '800 26px/1 var(--font-brand)' }}>Q</div>
              <div>
                <div style={{ font: '600 13px var(--font-body)' }}>Logo</div>
                <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>SVG hoặc PNG · tối thiểu 256×256</div>
                <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
                  <button className="btn ghost sm"><Icon k="upload" size={12} /> Tải lên</button>
                  <button className="btn ghost sm"><Icon k="trash" size={12} /></button>
                </div>
              </div>
            </div>
            <div className="divider" />
            <Field label="Màu nhấn workspace">
              <div className="set-colors">
                {['#2A2B86', '#7C6CF5', '#10b981', '#f59e0b', '#ef4444', '#0ea5e9'].map((c) => (
                  <button key={c} className="swatch" style={{ background: c }} data-active={c === '#2A2B86'} />
                ))}
              </div>
            </Field>
            <Field label="Theme mặc định" hint="Người dùng có thể đổi sau">
              <Segment value="light" onChange={() => {}} options={[
                { k: 'light', label: 'Sáng' },
                { k: 'dark',  label: 'Tối' },
                { k: 'auto',  label: 'Theo hệ thống' },
              ]} />
            </Field>
            <Field label="Watermark trong export" hint="In dấu workspace lên PDF / PNG">
              <Toggle checked={true} onChange={() => {}} />
            </Field>
          </div>
        </Section>

        <Section title="Sử dụng · billing" meta="Tháng 6 · 2026" ai>
          <div className="set-usage-card">
            <div className="head">
              <div>
                <div className="l">Hóa đơn dự kiến</div>
                <div className="v">$284.<span className="dec">12</span></div>
                <div className="d">Ước tính cuối tháng: <strong>$486</strong></div>
              </div>
              <span className="plan-pill">Plan · Pro</span>
            </div>
            <div className="bars">
              <div className="row">
                <div className="lbl">LLM tokens</div>
                <div className="bar"><div className="fill" style={{ width: '62%', background: 'var(--iris)' }} /></div>
                <div className="val tabular">$184 / $300</div>
              </div>
              <div className="row">
                <div className="lbl">Crawl + Playwright</div>
                <div className="bar"><div className="fill" style={{ width: '38%', background: 'var(--mint)' }} /></div>
                <div className="val tabular">$48 / $120</div>
              </div>
              <div className="row">
                <div className="lbl">Lưu trữ · KG + Vector</div>
                <div className="bar"><div className="fill" style={{ width: '54%', background: 'var(--gold)' }} /></div>
                <div className="val tabular">$32 / $60</div>
              </div>
              <div className="row">
                <div className="lbl">Telegram + email</div>
                <div className="bar"><div className="fill" style={{ width: '12%', background: 'var(--rose)' }} /></div>
                <div className="val tabular">$20 / $50</div>
              </div>
            </div>
            <div className="divider" />
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn sm primary"><Icon k="ext" size={12} /> Mở portal billing</button>
              <button className="btn ghost sm"><Icon k="download" size={12} /> Xuất hóa đơn</button>
            </div>
          </div>
        </Section>
      </div>

      <Section title="Lưu trữ & dữ liệu" meta="Quy định retention và backup">
        <div className="set-fields">
          <Field label="Giữ raw news" hint="Nguyên văn HTML đã crawl">
            <Stepper value={30} onChange={() => {}} min={1} max={365} unit="ngày" />
          </Field>
          <Field label="Giữ phân tích AI" hint="Output của LLM analyst">
            <Stepper value={180} onChange={() => {}} min={30} max={730} unit="ngày" />
          </Field>
          <Field label="Giữ alerts đã gửi" hint="Lịch sử cảnh báo">
            <Stepper value={90} onChange={() => {}} min={7} max={365} unit="ngày" />
          </Field>
          <Field label="Backup tự động" hint="Daily snapshot KG + cấu hình">
            <Toggle checked={true} onChange={() => {}} />
          </Field>
          <Field label="Vùng lưu trữ" hint="Tuân thủ NQ 13/2023 · dữ liệu cá nhân VN">
            <select className="set-input"><option>Việt Nam · VNG Cloud (HCM)</option><option>Singapore · AWS</option></select>
          </Field>
          <Field label="Mã hóa at-rest" hint="AES-256 cho cả KG và vector">
            <Toggle checked={true} onChange={() => {}} />
          </Field>
        </div>
      </Section>

      <Section title="Tùy chỉnh trải nghiệm" meta="Áp dụng cho mọi thành viên · từng người có thể override">
        <div className="set-fields">
          <Field label="Confidence chip mặc định" hint="Hiển thị badge AI · % tin cậy">
            <Toggle checked={true} onChange={() => {}} />
          </Field>
          <Field label="Hiển thị citation" hint="Số nguồn + link gốc trong mọi AI output">
            <Toggle checked={true} onChange={() => {}} />
          </Field>
          <Field label="Tự refresh dashboard" hint="Cập nhật mỗi 30 giây">
            <Toggle checked={true} onChange={() => {}} />
          </Field>
          <Field label="Compact density" hint="Hàng bảng nhỏ hơn · cho màn hình lớn">
            <Toggle checked={false} onChange={() => {}} />
          </Field>
          <Field label="Phím tắt ⌘K" hint="Mở search / AI chat từ mọi màn hình">
            <Toggle checked={true} onChange={() => {}} />
          </Field>
          <Field label="Logo trong sidebar" hint="Hiển thị tên workspace dưới logo">
            <Toggle checked={true} onChange={() => {}} />
          </Field>
        </div>
      </Section>

      <Section title="Khu vực nguy hiểm" meta="Hành động không hoàn tác">
        <div className="set-danger">
          {[
            { t: 'Xuất toàn bộ dữ liệu', d: 'JSON + Parquet · gửi link tải về email. Khoảng 4.2 GB.', cta: 'Yêu cầu export', kind: 'ghost' },
            { t: 'Reset Knowledge Graph', d: 'Xóa toàn bộ entity tự sinh · giữ taxonomy gốc. Không hoàn tác.', cta: 'Reset KG', kind: 'warn' },
            { t: 'Xóa workspace', d: 'Vĩnh viễn xóa workspace, dữ liệu, billing. 30 ngày grace period.', cta: 'Xóa workspace', kind: 'danger' },
          ].map((d) => (
            <div key={d.t} className={'set-danger-row ' + d.kind}>
              <div>
                <div className="t">{d.t}</div>
                <div className="d">{d.d}</div>
              </div>
              <button className={'btn sm ' + (d.kind === 'danger' ? 'danger' : d.kind === 'warn' ? '' : 'ghost')}>{d.cta}</button>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// ROOT
// ════════════════════════════════════════════════════════════════════
function QFSettingsScreen() {
  const [active, setActive] = zuseState('llm');
  const [dirty, setDirty] = zuseState(false);

  // visually flicker dirty when user clicks any toggle/stepper (mock)
  React.useEffect(() => {
    const root = document.querySelector('.set-pane');
    if (!root) return;
    const fn = () => setDirty(true);
    root.addEventListener('click', fn);
    return () => root.removeEventListener('click', fn);
  }, [active]);

  React.useEffect(() => { setDirty(false); }, [active]);

  const flat = SET_NAV.flatMap(g => g.items);
  const cur = flat.find(n => n.k === active) || flat[0];

  let body = null;
  if      (active === 'llm')       body = <SecLLM />;
  else if (active === 'sources')   body = <SecSources />;
  else if (active === 'kg')        body = <SecKG />;
  else if (active === 'alerts')    body = <SecAlerts />;
  else if (active === 'access')    body = <SecAccess />;
  else if (active === 'workspace') body = <SecWorkspace />;

  return (
    <main className="page">
      <PageHead
        eyebrow="Settings"
        title="Cấu hình hệ thống"
        sub={<><span>Workspace · QuantyFin Production</span><span className="sep">·</span><span>Version 0.4.2-rc</span><span className="sep">·</span><span>Cập nhật lần cuối bởi <strong style={{color:'var(--fg-2)'}}>@hungnguyen</strong> · 12 phút trước</span></>}
        actions={<>
          {dirty && <span className="set-dirty"><span className="dt"/>Có thay đổi chưa lưu</span>}
          <button className="btn ghost" onClick={() => setDirty(false)}>Hủy</button>
          <button className="btn primary" onClick={() => setDirty(false)}><Icon k="check" size={14} /> Lưu thay đổi</button>
        </>}
      />
      <div className="qf-page">
        <div className="set-shell">
          {/* LEFT NAV */}
          <aside className="set-nav">
            <div className="set-nav-search">
              <Icon k="search" size={13} />
              <input placeholder="Tìm trong cài đặt…" />
            </div>
            {SET_NAV.map((g) => (
              <div key={g.group} className="set-nav-group">
                <div className="set-nav-grp-label">{g.group}</div>
                {g.items.map((s) => (
                  <button key={s.k} className={'set-nav-item' + (active === s.k ? ' is-active' : '')} data-active={active === s.k ? 'true' : 'false'} onClick={() => setActive(s.k)}>
                    <span className="ico"><Icon k={s.icon} size={15} /></span>
                    <span className="t">
                      <span className="l">{s.label}</span>
                      <span className="s">{s.sub}</span>
                    </span>
                    <Icon k="caretR" size={11} />
                  </button>
                ))}
              </div>
            ))}
            <div className="set-nav-footer">
              <span><Icon k="shield" size={11} /> SOC 2 · ISO 27001</span>
              <span><Icon k="ext" size={11} /> Tài liệu API</span>
            </div>
          </aside>

          {/* RIGHT PANE */}
          <div className="set-pane">
            <div className="set-pane-head">
              <div>
                <div className="eyebrow"><Icon k={cur.icon} size={12} /> Cài đặt · {cur.label}</div>
                <h2>{cur.label}</h2>
                <div className="sub">{cur.sub}</div>
              </div>
            </div>
            {body}
          </div>
        </div>
      </div>
    </main>
  );
}

window.QFSettings = QFSettingsScreen;
