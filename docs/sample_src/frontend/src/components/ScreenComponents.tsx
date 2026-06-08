import React, { useState, useMemo, useEffect, useRef } from 'react';
import {
  Icon,
  Logo,
  TPill,
  Sentiment,
  ConfChip,
  Sparkline,
  KpiCard,
  NewsItem,
  AlertRow,
  PageHead,
  Section,
  TextInput,
  Segment,
  StockCell,
  fmt,
  fmtInt,
  fmtPct,
  fmtKbig,
} from './SharedUI';
import { KGViewer } from './KGViewer';
import { Settings } from './Settings';
import {
  WATCHLIST,
  KG_NODES,
  KG_EDGES,
} from '../lib/mockData';
import type {
  Stock,
  NewsItemData,
  DashboardData,
} from '../lib/mockData';

// ════════════════════════════════════════════════════════════════════
// DASHBOARD
// ════════════════════════════════════════════════════════════════════
interface ScreenDashboardProps {
  data: DashboardData;
  onNav: (screen: string) => void;
  onTicker: (ticker: string) => void;
  scenario: string;
}

export function ScreenDashboard({ data, onNav, onTicker, scenario }: ScreenDashboardProps) {
  const { stocks, news, alerts, indices, macros } = data;
  const vni = indices[0];
  const watch = WATCHLIST.map((t) => stocks.find((s) => s.ticker === t)).filter((s): s is Stock => !!s);

  // top movers
  const sorted = [...stocks].sort((a, b) => b.changePct - a.changePct);
  const gainers = sorted.slice(0, 4);
  const losers = sorted.slice(-4).reverse();

  // sector aggregates
  const sectors = useMemo(() => {
    const map: Record<string, { sector: string; n: number; pct: number; posN: number }> = {};
    stocks.forEach((s) => {
      if (!map[s.sector]) map[s.sector] = { sector: s.sector, n: 0, pct: 0, posN: 0 };
      map[s.sector].n += 1;
      map[s.sector].pct += s.changePct;
      if (s.sentiment === 'pos') map[s.sector].posN += 1;
    });
    return Object.values(map)
      .map((x) => ({ ...x, avg: x.pct / x.n }))
      .sort((a, b) => b.avg - a.avg);
  }, [stocks]);

  return (
    <main className="page">
      <PageHead
        eyebrow="Market briefing"
        title={`Phiên ngày ${new Date().toLocaleDateString('vi-VN')}`}
        sub={
          <>
            <span>Cập nhật 14:32:18</span>
            <span className="sep">·</span>
            <span>Tự động làm mới 30s</span>
            <span className="sep">·</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--mint)' }} />
              Live
            </span>
          </>
        }
        actions={
          <>
            <button className="btn ghost">
              <Icon k="download" size={14} /> Xuất briefing
            </button>
            <button className="btn primary" onClick={() => onNav('chat')}>
              <Icon k="sparkle" size={14} /> Hỏi AI
            </button>
          </>
        }
      />
      <div className="qf-page">
        {/* ROW 1 · 4 KPI cards */}
        <div className="qf-grid qf-grid-4" style={{ marginBottom: 16 }}>
          {indices.map((ix) => {
            const up = ix.changePct >= 0;
            return (
              <KpiCard
                key={ix.name}
                label={ix.name}
                value={fmt(ix.value, 2)}
                valueClass=""
                delta={fmtPct(ix.changePct)}
                deltaTone={up ? 'up' : 'down'}
                sub={`${up ? '+' : ''}${fmt(ix.change)} điểm · phiên hôm nay`}
                spark={ix.series}
                sparkTone={up ? 'up' : 'down'}
              />
            );
          })}
        </div>

        {/* ROW 2 · main chart + AI briefing */}
        <div className="qf-grid qf-grid-2-1" style={{ marginBottom: 16 }}>
          <Section
            title="VN-Index · phiên hôm nay"
            meta="Khung 5 phút · 09:00 → 14:32"
            actions={
              <>
                <Segment
                  value="d"
                  onChange={() => {}}
                  options={[
                    { k: 'i', label: '1P' },
                    { k: 'd', label: '1N' },
                    { k: 'w', label: '1T' },
                    { k: 'm', label: '1Th' },
                    { k: 'y', label: '1N' },
                  ]}
                />
              </>
            }
          >
            <DashboardChart series={vni.series} up={vni.changePct >= 0} />
          </Section>

          <Section
            ai
            title="AI Briefing"
            meta="Tổng hợp tự động · 14:30"
            actions={<ConfChip conf="high" pct={92} />}
          >
            <BriefingBody scenario={scenario} stocks={stocks} gainers={gainers} losers={losers} />
          </Section>
        </div>

        {/* ROW 3 · watchlist + alerts */}
        <div className="qf-grid qf-grid-2-1" style={{ marginBottom: 16 }}>
          <Section
            flush
            title="Watchlist của tôi"
            actions={
              <>
                <button className="btn ghost sm">
                  <Icon k="filter" size={13} /> Lọc
                </button>
                <button className="btn sm">
                  <Icon k="plus" size={13} /> Thêm mã
                </button>
              </>
            }
          >
            <WatchlistTable rows={watch} onTicker={onTicker} />
          </Section>

          <Section
            flush
            title="Cảnh báo gần nhất"
            actions={
              <button className="btn ghost sm" onClick={() => onNav('alerts')}>
                Xem tất cả <Icon k="caretR" size={12} />
              </button>
            }
          >
            <div className="scroll" style={{ maxHeight: 380 }}>
              {alerts.map((a) => (
                <AlertRow key={a.id} a={a} onTicker={onTicker} />
              ))}
            </div>
          </Section>
        </div>

        {/* ROW 4 · heatstrip + sector + news */}
        <div className="qf-grid qf-grid-2-1" style={{ marginBottom: 16 }}>
          <Section
            title="Heatmap · biến động intraday"
            meta="30 mã có vốn hóa lớn nhất · tô màu theo % thay đổi"
            actions={
              <>
                <span style={{ font: '11px var(--font-mono)', color: 'var(--fg-3)' }}>−5%</span>
                <span
                  style={{
                    width: 80,
                    height: 8,
                    borderRadius: 4,
                    background:
                      'linear-gradient(90deg, #ef4444 0%, #1c1e3a 50%, #10b981 100%)',
                  }}
                />
                <span style={{ font: '11px var(--font-mono)', color: 'var(--fg-3)' }}>+5%</span>
              </>
            }
          >
            <HeatStrip stocks={stocks} onTicker={onTicker} />
          </Section>

          <Section title="Hiệu suất ngành" meta="Trung bình % thay đổi">
            <SectorList sectors={sectors} />
          </Section>
        </div>

        {/* ROW 5 · news + macros */}
        <div className="qf-grid qf-grid-2-1">
          <Section
            flush
            title="Dòng tin mới"
            meta={`${news.length} tin trong 24 giờ qua`}
            actions={
              <button className="btn ghost sm" onClick={() => onNav('news')}>
                Xem tất cả <Icon k="caretR" size={12} />
              </button>
            }
          >
            <div className="scroll" style={{ maxHeight: 460 }}>
              {news.slice(0, 8).map((n) => (
                <NewsItem key={n.id} n={n} onTicker={onTicker} />
              ))}
            </div>
          </Section>
          <Section title="Bối cảnh vĩ mô" meta="Sự kiện ảnh hưởng nhiều ngành" ai>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {macros.slice(0, 5).map((m) => (
                <div
                  key={m.id}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'auto 1fr',
                    gap: 10,
                    padding: '10px 12px',
                    background:
                      m.impact === 'pos'
                        ? 'var(--mint-tint)'
                        : m.impact === 'neg'
                        ? 'var(--gap-bg)'
                        : 'var(--bg-muted)',
                    borderRadius: 'var(--radius-sm)',
                  }}
                >
                  <span
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: 6,
                      background: 'var(--bg)',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color:
                        m.impact === 'pos'
                          ? 'var(--mint-deep)'
                          : m.impact === 'neg'
                          ? 'var(--gap)'
                          : 'var(--fg-3)',
                    }}
                  >
                    <Icon
                      k={m.impact === 'pos' ? 'trend' : m.impact === 'neg' ? 'trendDown' : 'globe'}
                      size={13}
                    />
                  </span>
                  <div>
                    <p
                      style={{
                        margin: 0,
                        font: '500 12.5px/1.4 var(--font-body)',
                        color: 'var(--fg-1)',
                      }}
                    >
                      {m.title}
                    </p>
                    <div style={{ marginTop: 4, font: 'var(--type-caption)', color: 'var(--fg-3)' }}>
                      {m.sector}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Section>
        </div>
      </div>
    </main>
  );
}

// AI briefing body (scenario-aware copy)
interface BriefingBodyProps {
  scenario: string;
  stocks: Stock[];
  gainers: Stock[];
  losers: Stock[];
}

function BriefingBody({ scenario, gainers }: BriefingBodyProps) {
  let copy: React.ReactNode;
  if (scenario === 'up') {
    copy = (
      <>
        <p>
          <strong>Thị trường tăng đồng thuận.</strong> 6 trên 9 ngành đóng cửa trong sắc xanh, dẫn
          dắt bởi Công nghệ và Ngân hàng. Khối ngoại tiếp tục mua ròng phiên thứ 8 liên tiếp.
        </p>
        <p>
          Tín hiệu quan trọng: <strong>{gainers[0]?.ticker || 'FPT'}</strong> vượt đỉnh lịch sử với
          khối lượng gấp 2.4× trung bình 20 phiên. Sentiment tích cực được xác nhận qua 14 tin có
          lợi trong 24 giờ.
        </p>
        <p>
          Cần theo dõi: nhóm Thép có dấu hiệu phân hóa, dòng tiền yếu hơn xu hướng chung — khả năng
          điều chỉnh kỹ thuật.
        </p>
      </>
    );
  } else if (scenario === 'down') {
    copy = (
      <>
        <p>
          <strong>Áp lực bán mở rộng.</strong> CPI tháng 5 vượt mục tiêu kiểm soát đã kích hoạt lo
          ngại về thắt chặt tiền tệ. NHNN buộc phải bán dự trữ ngoại hối để ổn định tỷ giá.
        </p>
        <p>
          Ngành chịu áp lực mạnh: <strong>Bất động sản</strong> (−2.8%) và{' '}
          <strong>Chứng khoán</strong> (−2.1%). NVL giảm sàn với khối lượng đột biến gấp 3.2×.
        </p>
        <p>
          Đề xuất theo dõi: VCB và GAS có sentiment trung tính, có thể là vùng phòng thủ nếu áp lực
          vĩ mô tiếp tục.
        </p>
      </>
    );
  } else if (scenario === 'crisis') {
    copy = (
      <>
        <p>
          <strong>Cảnh báo hệ thống.</strong> Dữ liệu việc làm Mỹ kém kích hoạt làn sóng bán tháo
          toàn cầu, S&P 500 giảm 3.8%. KG phát hiện chuỗi rủi ro 3 hops: ngoại tệ rút → ngân hàng →
          bất động sản → chứng khoán.
        </p>
        <p>
          UBCKNN đã cảnh báo 12 mã có dấu hiệu thao túng giá. Khối ngoại bán ròng vượt 1.4 nghìn tỷ
          trong 60 phút — đột biến σ &gt; 2.5.
        </p>
        <p>
          Khuyến nghị: giảm tỷ trọng các mã trong chuỗi lây lan (<strong>VHM, SSI, TCB</strong>).
          Theo dõi sát động thái can thiệp của NHNN.
        </p>
      </>
    );
  } else {
    copy = (
      <>
        <p>
          <strong>Phân hóa, chờ tín hiệu xác nhận.</strong> Thanh khoản dao động quanh trung bình
          20 phiên. Phân hóa mạnh giữa nhóm Ngân hàng (+) và Bất động sản (−), độ phân tán σ =
          2.4%.
        </p>
        <p>
          FPT and VCB duy trì sức mạnh tương đối với sentiment trung tính-tích cực. NVL và DXG vẫn
          yếu, có dấu hiệu phân phối ngắn hạn.
        </p>
        <p>
          AI không phát hiện chuỗi tín hiệu mạnh — confidence MEDIUM. Nên giữ tỷ trọng quan sát, ưu
          tiên các mã đầu ngành.
        </p>
      </>
    );
  }
  return (
    <div style={{ font: '14px/1.6 var(--font-body)', color: 'var(--fg-1)' }}>
      {copy}
      <div className="divider" />
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <span
          style={{
            font: '600 10.5px/1 var(--font-mono)',
            color: 'var(--fg-3)',
            alignSelf: 'center',
            textTransform: 'uppercase',
            letterSpacing: '0.12em',
          }}
        >
          Nguồn:
        </span>
        <TPill>VNI tick</TPill>
        <TPill>News×24</TPill>
        <TPill>KG path×3</TPill>
        <TPill>FX</TPill>
      </div>
    </div>
  );
}

// Dashboard area chart
interface DashboardChartProps {
  series: number[];
  up: boolean;
}

function DashboardChart({ series, up }: DashboardChartProps) {
  const w = 880,
    h = 280;
  const min = Math.min(...series) * 0.998;
  const max = Math.max(...series) * 1.002;
  const range = max - min;
  const stepX = w / (series.length - 1);
  const pts = series.map((v, i) => [i * stepX, h - ((v - min) / range) * (h - 24) - 12]);
  const linePath = pts
    .map((p, i) => (i === 0 ? 'M' : 'L') + p[0].toFixed(1) + ',' + p[1].toFixed(1))
    .join(' ');
  const areaPath = linePath + ` L${w},${h} L0,${h} Z`;
  const color = up ? '#10b981' : '#ef4444';
  // y-axis labels
  const ticks = 4;
  const yTicks = Array.from({ length: ticks + 1 }, (_, i) => min + (range / ticks) * i);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height: 280 }}>
      <defs>
        <linearGradient id="chartArea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity={0.25} />
          <stop offset="100%" stopColor={color} stopOpacity={0} />
        </linearGradient>
      </defs>
      {/* horizontal grid */}
      {yTicks.map((_, i) => (
        <line
          key={i}
          x1="40"
          x2={w}
          y1={h - (i / ticks) * (h - 24) - 12}
          y2={h - (i / ticks) * (h - 24) - 12}
          stroke="var(--border-light)"
          strokeWidth="0.5"
        />
      ))}
      {yTicks.map((y, i) => (
        <text
          key={'t' + i}
          x="36"
          y={h - (i / ticks) * (h - 24) - 8}
          fontSize="10.5"
          fill="var(--fg-3)"
          textAnchor="end"
          fontFamily="var(--font-mono)"
        >
          {y.toFixed(1)}
        </text>
      ))}
      <g transform="translate(40,0)">
        <path d={areaPath} fill="url(#chartArea)" />
        <path d={linePath} fill="none" stroke={color} strokeWidth="1.8" />
        {/* anchor dots */}
        <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="3.5" fill={color} />
        <circle
          cx={pts[pts.length - 1][0]}
          cy={pts[pts.length - 1][1]}
          r="6.5"
          fill={color}
          opacity="0.18"
        />
      </g>
      {/* x labels */}
      {['09:00', '10:00', '11:00', '12:00', '13:00', '14:30'].map((lbl, i, arr) => (
        <text
          key={lbl}
          x={40 + (i / (arr.length - 1)) * (w - 40)}
          y={h - 1}
          fontSize="10.5"
          fill="var(--fg-3)"
          textAnchor="middle"
          fontFamily="var(--font-mono)"
        >
          {lbl}
        </text>
      ))}
    </svg>
  );
}

// Watchlist table
interface WatchlistTableProps {
  rows: Stock[];
  onTicker: (ticker: string) => void;
}

function WatchlistTable({ rows, onTicker }: WatchlistTableProps) {
  return (
    <table className="dt" style={{ width: '100%' }}>
      <thead>
        <tr>
          <th>Mã</th>
          <th className="num">Giá</th>
          <th className="num">% Phiên</th>
          <th className="num">% 5 ngày</th>
          <th>Xu hướng</th>
          <th>Sentiment</th>
          <th>AI</th>
          <th className="num">KL</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((s) => (
          <tr key={s.ticker} onClick={() => onTicker(s.ticker)} style={{ cursor: 'pointer' }}>
            <td>
              <StockCell s={s} onClick={() => onTicker(s.ticker)} />
            </td>
            <td className="num tabular">{fmt(s.price)}</td>
            <td className={'num tabular ' + (s.changePct >= 0 ? 'dir-up' : 'dir-down')}>
              {fmtPct(s.changePct)}
            </td>
            <td className={'num tabular ' + (s.fiveDay >= 0 ? 'dir-up' : 'dir-down')}>
              {fmtPct(s.fiveDay)}
            </td>
            <td>
              <Sparkline
                data={s.series}
                tone={s.changePct >= 0 ? 'up' : 'down'}
                width={86}
                height={26}
              />
            </td>
            <td>
              <Sentiment tone={s.sentiment} compact />
            </td>
            <td>
              <ConfChip conf={s.confidence} pct={s.confidencePct} />
            </td>
            <td
              className="num tabular"
              style={{ color: 'var(--fg-3)', font: '500 12px/1 var(--font-mono)' }}
            >
              {fmtKbig(s.volume)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// Heatstrip
interface HeatStripProps {
  stocks: Stock[];
  onTicker: (ticker: string) => void;
}

function HeatStrip({ stocks, onTicker }: HeatStripProps) {
  const sorted = [...stocks].slice(0, 20).sort((a, b) => b.changePct - a.changePct);
  function color(pct: number) {
    const v = Math.max(-5, Math.min(5, pct)) / 5;
    if (v >= 0) {
      const a = 0.2 + Math.abs(v) * 0.65;
      return `rgba(16, 185, 129, ${a})`;
    }
    const a = 0.2 + Math.abs(v) * 0.65;
    return `rgba(239, 68, 68, ${a})`;
  }
  return (
    <div className="heatstrip">
      {sorted.map((s) => (
        <div
          key={s.ticker}
          className="cell"
          style={{ background: color(s.changePct) }}
          onClick={() => onTicker(s.ticker)}
          title={`${s.ticker} · ${fmtPct(s.changePct)}`}
        >
          <span>{s.ticker}</span>
          <span className="pct">{fmtPct(s.changePct, 1)}</span>
        </div>
      ))}
    </div>
  );
}

// Sector list
interface SectorListProps {
  sectors: { sector: string; avg: number }[];
}

function SectorList({ sectors }: SectorListProps) {
  const max = Math.max(...sectors.map((s) => Math.abs(s.avg))) || 1;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {sectors.map((s) => {
        const up = s.avg >= 0;
        const widthPct = (Math.abs(s.avg) / max) * 100;
        return (
          <div
            key={s.sector}
            style={{
              display: 'grid',
              gridTemplateColumns: '110px 1fr 64px',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span style={{ font: '500 12.5px/1 var(--font-body)', color: 'var(--fg-1)' }}>
              {s.sector}
            </span>
            <div
              style={{
                position: 'relative',
                height: 10,
                background: 'var(--bg-muted)',
                borderRadius: 5,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: up ? '50%' : `${50 - widthPct / 2}%`,
                  width: `${widthPct / 2}%`,
                  background: up ? 'var(--mint)' : 'var(--gap)',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  top: 0,
                  bottom: 0,
                  left: '50%',
                  width: 1,
                  background: 'var(--border)',
                }}
              />
            </div>
            <span
              className={'tabular ' + (up ? 'dir-up' : 'dir-down')}
              style={{ textAlign: 'right', font: '600 12px/1 var(--font-mono)' }}
            >
              {fmtPct(s.avg)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// KNOWLEDGE GRAPH SCREEN
// ════════════════════════════════════════════════════════════════════
interface ScreenKGProps {
  onTicker: (ticker: string) => void;
}

export function ScreenKG({ onTicker }: ScreenKGProps) {
  const nodes = KG_NODES;
  const edges = KG_EDGES;
  const [selected, setSelected] = useState<string>('foreign-sell');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const visibleNodes = nodes.filter((n) => (typeFilter === 'all' ? true : n.type === typeFilter));
  const visibleIds = new Set(visibleNodes.map((n) => n.id));
  const visibleEdges = edges.filter((e) => visibleIds.has(e.s) && visibleIds.has(e.t));

  const sel = nodes.find((n) => n.id === selected);
  const relatedEdges = edges.filter((e) => e.s === selected || e.t === selected);

  return (
    <main className="page">
      <PageHead
        eyebrow="Knowledge Graph"
        title="Đồ thị tri thức tài chính"
        sub={
          <>
            <span>{nodes.length} thực thể</span>
            <span className="sep">·</span>
            <span>{edges.length} quan hệ</span>
            <span className="sep">·</span>
            <span>Cập nhật bởi AI Analyst</span>
          </>
        }
        actions={
          <>
            <button className="btn ghost">
              <Icon k="filter" size={14} /> Bộ lọc
            </button>
            <button className="btn ghost">
              <Icon k="download" size={14} /> Xuất Cypher
            </button>
            <button className="btn primary">
              <Icon k="plus" size={14} /> Thêm thực thể
            </button>
          </>
        }
      />
      <div className="qf-page">
        <div className="kg-shell">
          <div className="kg-canvas-wrap">
            <div className="kg-toolbar">
              <Segment
                value={typeFilter}
                onChange={setTypeFilter}
                options={[
                  { k: 'all', label: 'Tất cả', count: nodes.length },
                  { k: 'Event', label: 'Sự kiện', count: nodes.filter((n) => n.type === 'Event').length },
                  { k: 'Sector', label: 'Ngành', count: nodes.filter((n) => n.type === 'Sector').length },
                  { k: 'Stock', label: 'Cổ phiếu', count: nodes.filter((n) => n.type === 'Stock').length },
                  { k: 'Leader', label: 'Lãnh đạo', count: nodes.filter((n) => n.type === 'Leader').length },
                ]}
              />
            </div>
            <KGViewer
              nodes={visibleNodes}
              edges={visibleEdges}
              selectedId={selected}
              onSelect={setSelected}
              height={620}
            />
            <div className="kg-legend">
              <div className="lg-row">
                <span className="dot" style={{ background: '#FCAF16' }} /> Sự kiện vĩ mô
              </div>
              <div className="lg-row">
                <span className="dot" style={{ background: '#7C6CF5' }} /> Ngành
              </div>
              <div className="lg-row">
                <span className="dot" style={{ background: '#2A2B86' }} /> Cổ phiếu
              </div>
              <div className="lg-row">
                <span className="dot" style={{ background: '#10b981' }} /> Lãnh đạo
              </div>
              <div className="divider" />
              <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>
                Kéo để pan · Cuộn để zoom
              </div>
            </div>
          </div>

          <div className="kg-side">
            <Section flush>
              <div style={{ padding: 16 }} className="kg-detail">
                {sel && (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <span
                        style={{
                          font: '700 10px/1 var(--font-mono)',
                          background: 'var(--iris-tint)',
                          color: 'var(--iris-deep)',
                          padding: '4px 8px',
                          borderRadius: 4,
                          textTransform: 'uppercase',
                          letterSpacing: '0.12em',
                        }}
                      >
                        {sel.type}
                      </span>
                      {sel.type === 'Stock' && (
                        <button className="btn sm ghost" onClick={() => onTicker(sel.id)}>
                          Xem chi tiết <Icon k="caretR" size={12} />
                        </button>
                      )}
                    </div>
                    <h4>{sel.label}</h4>
                    <div className="sub">
                      {sel.type === 'Event' && 'Sự kiện vĩ mô đang ảnh hưởng nhiều thực thể trong đồ thị.'}
                      {sel.type === 'Sector' &&
                        `Ngành kinh tế · ${
                          edges.filter((e) => e.t === sel.id && e.kind === 'BELONGS_TO').length
                        } cổ phiếu đại diện`}
                      {sel.type === 'Stock' &&
                        'Cổ phiếu niêm yết — nhấn xem chi tiết để mở trang phân tích.'}
                      {sel.type === 'Leader' && 'Nhân vật lãnh đạo có ảnh hưởng đến doanh nghiệp.'}
                    </div>
                    <div
                      style={{
                        font: '700 10px/1 var(--font-mono)',
                        color: 'var(--fg-3)',
                        letterSpacing: '0.14em',
                        textTransform: 'uppercase',
                        marginBottom: 6,
                      }}
                    >
                      Quan hệ ({relatedEdges.length})
                    </div>
                    {relatedEdges.map((e, i) => {
                      const other = nodes.find((n) => n.id === (e.s === selected ? e.t : e.s));
                      const dir = e.s === selected ? '→' : '←';
                      return (
                        <div key={i} className="kg-relation">
                          <div>
                            <span className="ed">{e.kind}</span>
                            <div className="t">
                              {dir} {other ? other.label : '(unknown)'}
                            </div>
                          </div>
                          <div className="w">{(e.w * 100).toFixed(0)}%</div>
                        </div>
                      );
                    })}
                  </>
                )}
              </div>
            </Section>

            <Section
              title="Path explanation"
              ai
              meta="3-hop path từ sự kiện đến cổ phiếu"
              actions={<ConfChip conf="med" pct={78} />}
            >
              <div style={{ font: '13px/1.55 var(--font-body)', color: 'var(--fg-2)' }}>
                <p style={{ margin: '0 0 8px' }}>
                  <strong style={{ color: 'var(--fg-1)' }}>CPI tăng</strong> →
                  <span style={{ color: 'var(--gold-deep)' }}> Áp lực tỷ giá</span> →
                  <strong style={{ color: 'var(--fg-1)' }}> Khối ngoại bán ròng</strong>
                </p>
                <p style={{ margin: '0 0 8px' }}>
                  Tác động lan tỏa đến <strong>3 ngành</strong> với độ tin cậy trung bình 64%.
                </p>
                <p style={{ margin: 0, color: 'var(--fg-3)' }}>
                  Trace:{' '}
                  <span style={{ font: 'var(--type-mono-sm)' }}>kg_path_2026_06_03_142817</span>
                </p>
              </div>
            </Section>
          </div>
        </div>
      </div>
    </main>
  );
}

// ════════════════════════════════════════════════════════════════════
// STOCK DETAIL
// ════════════════════════════════════════════════════════════════════
interface ScreenStockProps {
  data: DashboardData;
  ticker: string;
  onTicker: (ticker: string) => void;
}

export function ScreenStock({ data, ticker, onTicker }: ScreenStockProps) {
  const stocks = data.stocks;
  const s = stocks.find((x) => x.ticker === ticker) || stocks[0];
  const relatedNews = data.news.filter((n) => n.tickers.includes(s.ticker)).slice(0, 6);
  const peers = stocks.filter((x) => x.sector === s.sector && x.ticker !== s.ticker).slice(0, 4);

  // mock fundamentals
  const fund = {
    marketCap: (s.price * 1.8 + (s.ticker.charCodeAt(0) % 50)).toFixed(1) + ' nghìn tỷ',
    pe: (8 + (s.ticker.charCodeAt(0) % 12)).toFixed(2),
    pb: (1 + (s.ticker.charCodeAt(0) % 4) * 0.3).toFixed(2),
    eps: (s.price * 1000 * 0.12).toFixed(0) + ' đ',
    yield: (2 + (s.ticker.charCodeAt(1) % 6)).toFixed(1) + '%',
    high52: (s.price * 1.18).toFixed(1),
    low52: (s.price * 0.82).toFixed(1),
  };
  const up = s.changePct >= 0;

  return (
    <main className="page">
      <PageHead
        eyebrow={s.sector}
        title={
          <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 14, flexWrap: 'wrap' }}>
            <span
              style={{
                font: '700 28px/1 var(--font-mono)',
                color: 'var(--iris-deep)',
                letterSpacing: '0.02em',
              }}
            >
              {s.ticker}
            </span>
            <span style={{ font: '500 16px/1.3 var(--font-brand)', color: 'var(--fg-2)' }}>
              {s.name}
            </span>
          </span>
        }
        sub={
          <span style={{ display: 'inline-flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap' }}>
            <span>{s.exchange}</span>
            <span className="sep">·</span>
            <span
              className={up ? 'dir-up' : 'dir-down'}
              style={{ font: '700 20px/1 var(--font-mono)', whiteSpace: 'nowrap' }}
            >
              {fmt(s.price)} ₫
            </span>
            <span className={up ? 'dir-up' : 'dir-down'} style={{ whiteSpace: 'nowrap' }}>
              {fmtPct(s.changePct)} ({fmt(s.change)})
            </span>
          </span>
        }
        actions={
          <>
            <button className="btn ghost">
              <Icon k="bell" size={14} /> Đặt cảnh báo
            </button>
            <button className="btn ghost">
              <Icon k="plus" size={14} /> Watchlist
            </button>
            <button className="btn primary">
              <Icon k="sparkle" size={14} /> Hỏi AI về {s.ticker}
            </button>
          </>
        }
      />
      <div className="qf-page">
        {/* KPI row */}
        <div className="qf-grid qf-grid-4" style={{ marginBottom: 16 }}>
          <KpiCard label="Vốn hóa" value={fund.marketCap} />
          <KpiCard label="P/E · P/B" value={`${fund.pe} · ${fund.pb}`} sub="So với ngành: 9.8 · 1.6" />
          <KpiCard label="EPS · Cổ tức" value={`${fund.eps} · ${fund.yield}`} />
          <KpiCard
            label="52 tuần Cao / Thấp"
            value={`${fund.high52} / ${fund.low52}`}
            sub={`Hiện giá đang ở ${(
              ((s.price - parseFloat(fund.low52)) /
                (parseFloat(fund.high52) - parseFloat(fund.low52))) *
              100
            ).toFixed(0)}% của biên độ`}
          />
        </div>

        {/* Chart + AI thesis */}
        <div className="qf-grid qf-grid-2-1" style={{ marginBottom: 16 }}>
          <Section
            title={`${s.ticker} · Biểu đồ giá`}
            actions={
              <Segment
                value="d"
                onChange={() => {}}
                options={[
                  { k: 'i', label: '1P' },
                  { k: 'd', label: '1N' },
                  { k: 'w', label: '1T' },
                  { k: 'm', label: '1Th' },
                  { k: 'y', label: '1N' },
                ]}
              />
            }
          >
            <DashboardChart series={s.series} up={up} />
          </Section>

          <Section
            ai
            title="AI Thesis"
            meta="Tổng hợp từ 12 nguồn"
            actions={<ConfChip conf={s.confidence} pct={s.confidencePct} />}
          >
            <div style={{ font: '13.5px/1.55 var(--font-body)', color: 'var(--fg-1)' }}>
              <p style={{ margin: '0 0 10px' }}>
                <strong>{s.ticker}</strong> đang giao dịch ở vùng {fmt(s.price)} ₫,
                {up ? ' với động lượng tích cực' : ' chịu áp lực điều chỉnh'} trong phiên hôm nay.
              </p>
              <p style={{ margin: '0 0 10px' }}>
                Sentiment 24h:{' '}
                <Sentiment tone={s.sentiment} score={s.sentScore} compact /> · {s.newsCount24h} tin.
                Tin đáng chú ý:{' '}
                <strong>
                  {relatedNews[0]?.title || `${s.ticker} duy trì xu hướng`}
                </strong>
                .
              </p>
              <p style={{ margin: 0, color: 'var(--fg-2)' }}>
                Liên kết KG: {s.ticker} thuộc ngành <strong>{s.sector}</strong>, đang chịu ảnh hưởng
                từ 2 sự kiện vĩ mô đang theo dõi.
              </p>
            </div>
          </Section>
        </div>

        {/* News + KG snapshot + Peers */}
        <div className="qf-grid qf-grid-3" style={{ marginBottom: 16 }}>
          <Section
            flush
            title={`Tin ${s.ticker}`}
            meta={`${relatedNews.length} tin`}
            style={{ gridColumn: 'span 2' }}
          >
            <div className="scroll" style={{ maxHeight: 420 }}>
              {relatedNews.length ? (
                relatedNews.map((n) => (
                  <NewsItem key={n.id} n={n} onTicker={onTicker} />
                ))
              ) : (
                <div className="empty-hint">Không có tin nào cho {s.ticker} trong 24h qua.</div>
              )}
            </div>
          </Section>

          <Section title="Liên kết KG" meta="Subgraph quanh mã này" ai>
            <StockKGMini ticker={s.ticker} sector={s.sector} />
            <div className="divider" />
            <div
              style={{
                font: '700 10px/1 var(--font-mono)',
                color: 'var(--fg-3)',
                letterSpacing: '0.14em',
                textTransform: 'uppercase',
                marginBottom: 8,
              }}
            >
              Cùng ngành
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {peers.map((p) => (
                <button
                  key={p.ticker}
                  onClick={() => onTicker(p.ticker)}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '48px 1fr auto',
                    gap: 10,
                    alignItems: 'center',
                    padding: '8px 10px',
                    background: 'transparent',
                    border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <TPill tone="iris" style={{ justifyContent: 'center' }}>
                    {p.ticker}
                  </TPill>
                  <Sparkline
                    data={p.series}
                    tone={p.changePct >= 0 ? 'up' : 'down'}
                    width={80}
                    height={24}
                  />
                  <span
                    className={'tabular ' + (p.changePct >= 0 ? 'dir-up' : 'dir-down')}
                    style={{ font: '600 12px var(--font-mono)' }}
                  >
                    {fmtPct(p.changePct)}
                  </span>
                </button>
              ))}
            </div>
          </Section>
        </div>
      </div>
    </main>
  );
}

// Mini KG for stock detail
interface StockKGMiniProps {
  ticker: string;
  sector: string;
}

function StockKGMini({ ticker, sector }: StockKGMiniProps) {
  return (
    <svg viewBox="0 0 280 160" style={{ width: '100%', height: 160 }}>
      {/* edges */}
      <line x1="40" y1="40" x2="140" y2="80" stroke="#cbd5f1" strokeWidth="1.5" />
      <line x1="240" y1="40" x2="140" y2="80" stroke="#cbd5f1" strokeWidth="1.5" />
      <line
        x1="40"
        y1="130"
        x2="140"
        y2="80"
        stroke="#7C6CF5"
        strokeWidth="1.5"
        strokeDasharray="3 3"
      />
      <line x1="240" y1="130" x2="140" y2="80" stroke="#ef4444" strokeWidth="1.5" />

      {/* sector */}
      <circle cx="140" cy="80" r="26" fill="#7C6CF5" />
      <text
        x="140"
        y="82"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize="9.5"
        fill="#fff"
        fontWeight="700"
        fontFamily="var(--font-body)"
      >
        {sector}
      </text>

      {/* ticker */}
      <rect x="20" y="22" width="44" height="22" rx="4" fill="#2A2B86" />
      <text
        x="42"
        y="35"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize="10"
        fill="#fff"
        fontWeight="700"
        fontFamily="var(--font-mono)"
      >
        {ticker}
      </text>

      {/* event 1 */}
      <circle cx="240" cy="40" r="16" fill="#FCAF16" />
      <text
        x="240"
        y="42"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize="8"
        fill="#3b2a05"
        fontWeight="700"
        fontFamily="var(--font-mono)"
      >
        FED
      </text>

      {/* leader */}
      <circle cx="40" cy="130" r="14" fill="#10b981" />
      <text
        x="40"
        y="132"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize="8"
        fill="#fff"
        fontWeight="700"
        fontFamily="var(--font-body)"
      >
        CEO
      </text>

      {/* foreign sell */}
      <circle cx="240" cy="130" r="16" fill="#FCAF16" />
      <text
        x="240"
        y="132"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize="8"
        fill="#3b2a05"
        fontWeight="700"
        fontFamily="var(--font-mono)"
      >
        $out
      </text>

      {/* labels */}
      <text x="20" y="14" fontSize="9" fill="var(--fg-3)" fontFamily="var(--font-mono)">
        STOCK
      </text>
      <text x="115" y="118" fontSize="9" fill="var(--fg-3)" fontFamily="var(--font-mono)">
        SECTOR
      </text>
      <text x="216" y="14" fontSize="9" fill="var(--fg-3)" fontFamily="var(--font-mono)">
        EVENT
      </text>
    </svg>
  );
}

// ════════════════════════════════════════════════════════════════════
// NEWS FEED
// ════════════════════════════════════════════════════════════════════
interface ScreenNewsProps {
  data: DashboardData;
  onTicker: (ticker: string) => void;
}

export function ScreenNews({ data, onTicker }: ScreenNewsProps) {
  const { news, jobs } = data;
  const [sentF, setSentF] = useState<string>('all');
  const [statusF, setStatusF] = useState<string>('all');
  const [srcF, setSrcF] = useState<string>('all');

  const filtered = news.filter((n) => {
    if (sentF !== 'all' && n.tone !== sentF) return false;
    if (statusF !== 'all' && n.filterStatus !== statusF) return false;
    if (srcF !== 'all' && n.src !== srcF) return false;
    return true;
  });

  const stats = {
    total: news.length,
    analyzed: news.filter((n) => n.filterStatus === 'analyzed').length,
    filtered: news.filter((n) => n.filterStatus === 'filtered').length,
    pending: news.filter((n) => n.filterStatus === 'pending').length,
    pos: news.filter((n) => n.tone === 'pos').length,
    neg: news.filter((n) => n.tone === 'neg').length,
    neu: news.filter((n) => n.tone === 'neu').length,
  };
  const filterRate = ((stats.filtered / stats.total) * 100).toFixed(0);

  const sources = Array.from(new Set(news.map((n) => n.src)));

  return (
    <main className="page">
      <PageHead
        eyebrow="News intelligence"
        title="Dòng tin có gắn sentiment"
        sub={
          <>
            <span>{stats.total} tin / 24 giờ</span>
            <span className="sep">·</span>
            <span>Zero-cost filter loại {filterRate}% trước khi gọi LLM</span>
            <span className="sep">·</span>
            <span>Tiết kiệm khoảng $8.40 / ngày</span>
          </>
        }
        actions={
          <>
            <button className="btn ghost">
              <Icon k="refresh" size={14} /> Crawl lại
            </button>
            <button className="btn ghost">
              <Icon k="download" size={14} /> Xuất CSV
            </button>
          </>
        }
      />
      <div className="qf-page">
        {/* KPIs */}
        <div className="qf-grid qf-grid-4" style={{ marginBottom: 16 }}>
          <KpiCard
            label="Tin đã phân tích"
            value={fmtInt(stats.analyzed)}
            sub={`${stats.pending} đang chờ xử lý`}
          />
          <KpiCard
            label="Tin tích cực"
            value={fmtInt(stats.pos)}
            valueClass=""
            delta={`${((stats.pos / stats.total) * 100).toFixed(0)}%`}
            deltaTone="up"
          />
          <KpiCard
            label="Tin tiêu cực"
            value={fmtInt(stats.neg)}
            delta={`${((stats.neg / stats.total) * 100).toFixed(0)}%`}
            deltaTone="down"
          />
          <KpiCard
            label="Zero-cost filter"
            value={`${filterRate}%`}
            valueClass="iris"
            sub={`${stats.filtered} tin bị loại trước LLM`}
          />
        </div>

        {/* main feed + sidebar */}
        <div className="qf-grid qf-grid-2-1">
          <Section flush>
            <div className="filter-bar">
              <Segment
                value={sentF}
                onChange={setSentF}
                options={[
                  { k: 'all', label: 'Tất cả', count: stats.total },
                  { k: 'pos', label: 'Tích cực', count: stats.pos },
                  { k: 'neg', label: 'Tiêu cực', count: stats.neg },
                  { k: 'neu', label: 'Trung tính', count: stats.neu },
                ]}
              />
              <span style={{ width: 1, height: 20, background: 'var(--border)' }} />
              <Segment
                value={statusF}
                onChange={setStatusF}
                options={[
                  { k: 'all', label: 'Mọi trạng thái' },
                  { k: 'analyzed', label: 'Đã phân tích' },
                  { k: 'pending', label: 'Đang xử lý' },
                  { k: 'filtered', label: 'Đã lọc · zero-cost' },
                ]}
              />
              <select
                value={srcF}
                onChange={(e) => setSrcF(e.target.value)}
                style={{
                  height: 28,
                  padding: '0 8px',
                  borderRadius: 5,
                  border: '1px solid var(--border)',
                  background: 'var(--bg)',
                  color: 'var(--fg-2)',
                  font: '12px var(--font-body)',
                  cursor: 'pointer',
                }}
              >
                <option value="all">Mọi nguồn</option>
                {sources.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <span style={{ marginLeft: 'auto', font: 'var(--type-caption)', color: 'var(--fg-3)' }}>
                {filtered.length} tin hiển thị
              </span>
            </div>
            <div className="scroll" style={{ maxHeight: 720 }}>
              {filtered.length ? (
                filtered.map((n) => <NewsItem key={n.id} n={n} onTicker={onTicker} />)
              ) : (
                <div className="empty-hint">Không tin nào khớp bộ lọc.</div>
              )}
            </div>
          </Section>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Section ai title="Sentiment trending" meta="24 giờ qua">
              <SentimentTimeline news={news} />
            </Section>

            <Section title="Hiệu quả crawler" meta="Theo nguồn">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {jobs.slice(0, 6).map((j) => (
                  <div
                    key={j.id}
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr auto',
                      gap: 8,
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ font: '500 12.5px/1.2 var(--font-body)', color: 'var(--fg-1)' }}>
                        {j.src}
                      </div>
                      <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>
                        Lọc {Math.round((j.filteredOut / j.total) * 100)}% · {j.analyzed} tin LLM
                      </div>
                    </div>
                    <span className={'trace-pill ' + (j.status === 'failed' ? 'fail' : '')}>
                      {j.status === 'done'
                        ? 'OK'
                        : j.status === 'running'
                        ? 'Đang chạy'
                        : j.status === 'retry'
                        ? 'Retry'
                        : 'Lỗi'}
                    </span>
                  </div>
                ))}
              </div>
            </Section>
          </div>
        </div>
      </div>
    </main>
  );
}

// Sentiment timeline bars
interface SentimentTimelineProps {
  news: NewsItemData[];
}

function SentimentTimeline({ news }: SentimentTimelineProps) {
  // Bucket by 4-hour buckets over 24h
  const buckets = Array.from({ length: 6 }, () => ({ pos: 0, neg: 0, neu: 0 }));
  news.forEach((n) => {
    const hr = Math.floor(n.minutesAgo / 60);
    const b = Math.min(5, Math.floor(hr / 4));
    buckets[b][n.tone]++;
  });
  const max = Math.max(...buckets.map((b) => b.pos + b.neg + b.neu)) || 1;
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 130 }}>
      {buckets.map((b, i) => {
        const total = b.pos + b.neg + b.neu;
        const scale = total > 0 ? (total / max) * 120 : 0;
        return (
          <div
            key={i}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'stretch',
              gap: 4,
            }}
          >
            <div
              style={{
                height: scale,
                background: 'var(--bg-muted)',
                borderRadius: 4,
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column-reverse',
              }}
            >
              {total > 0 && (
                <>
                  <div style={{ height: `${(b.pos / total) * 100}%`, background: 'var(--mint)' }} />
                  <div style={{ height: `${(b.neu / total) * 100}%`, background: 'var(--gold)' }} />
                  <div style={{ height: `${(b.neg / total) * 100}%`, background: 'var(--gap)' }} />
                </>
              )}
            </div>
            <div style={{ font: '10px var(--font-mono)', color: 'var(--fg-3)', textAlign: 'center' }}>
              {-(i + 1) * 4}g
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// AI CHAT Q&A
// ════════════════════════════════════════════════════════════════════
interface ChatMessage {
  role: 'user' | 'ai';
  text: string | React.ReactNode;
  pending?: boolean;
  citations?: { n: number; src: string; t: string; date: string }[];
  conf?: 'high' | 'med' | 'low';
  confPct?: number;
}

const SAMPLE_CHAT: ChatMessage[] = [
  {
    role: 'user',
    text: 'Tại sao cổ phiếu VHM giảm mạnh tuần này?',
  },
  {
    role: 'ai',
    text: (
      <>
        <p>
          <strong>VHM</strong> giảm 5.8% trong 5 phiên gần nhất, có 3 nguyên nhân chính được tổng
          hợp từ Knowledge Graph:
        </p>
        <p>
          <strong>1. Áp lực vĩ mô</strong> — CPI tháng 5 vượt mục tiêu kiểm soát đã kích hoạt lo
          ngại NHNN thắt chặt tiền tệ
          <sup style={{ color: 'var(--iris-deep)', fontWeight: 700 }}>[1]</sup>, ảnh hưởng tiêu
          cực đến nhóm Bất động sản.
        </p>
        <p>
          <strong>2. Khối ngoại bán ròng</strong> tăng đột biến, riêng VHM chịu áp lực 420 tỷ đồng
          trong tuần
          <sup style={{ color: 'var(--iris-deep)', fontWeight: 700 }}>[2]</sup>.
        </p>
        <p>
          <strong>3. Tin nội bộ</strong> — cổ đông lớn đăng ký bán 2.3% vốn, làm yếu tâm lý ngắn
          hạn
          <sup style={{ color: 'var(--iris-deep)', fontWeight: 700 }}>[3]</sup>.
        </p>
        <p>
          Sentiment 24h: <Sentiment tone="neg" score={-0.62} compact /> · KG path 3 hops từ{' '}
          <strong>CPI → tỷ giá → khối ngoại → VHM</strong>.
        </p>
      </>
    ),
    citations: [
      {
        n: 1,
        src: 'CafeF',
        t: 'CPI tháng 5 tăng 4.6% so với cùng kỳ, vượt mục tiêu kiểm soát của Chính phủ',
        date: '03/06/2026',
      },
      {
        n: 2,
        src: 'Vietstock',
        t: 'Khối ngoại bán ròng 580 tỷ đồng cổ phiếu VHM trong tuần',
        date: '02/06/2026',
      },
      {
        n: 3,
        src: 'NDH',
        t: 'VHM: cổ đông lớn đăng ký bán 2.3% vốn, cổ phiếu chịu áp lực',
        date: '01/06/2026',
      },
    ],
    conf: 'high',
    confPct: 89,
  },
];

interface ScreenChatProps {
  onTicker: (ticker: string) => void;
}

export function ScreenChat({ onTicker: _onTicker }: ScreenChatProps) {
  const [stream, setStream] = useState<ChatMessage[]>(SAMPLE_CHAT);
  const [input, setInput] = useState<string>('');
  const endRef = useRef<HTMLDivElement>(null);

  function send(text: string) {
    if (!text.trim()) return;
    const u: ChatMessage = { role: 'user', text };
    const aiPlaceholder: ChatMessage = {
      role: 'ai',
      text: (
        <p style={{ color: 'var(--fg-3)' }}>
          <Icon k="sparkle" size={12} /> AI đang truy vấn Knowledge Graph và 8 nguồn tin…
        </p>
      ),
      pending: true,
    };
    setStream((prev) => [...prev, u, aiPlaceholder]);
    setInput('');

    setTimeout(() => {
      setStream((prev) =>
        prev.slice(0, -1).concat([
          {
            role: 'ai',
            text: (
              <>
                <p>Phân tích nhanh dựa trên dữ liệu hiện tại:</p>
                <p>
                  Tôi đã quét <strong>14 tin</strong> trong 24 giờ và đối chiếu với Knowledge
                  Graph. Có <strong>2 tín hiệu mạnh</strong> và <strong>1 tín hiệu yếu</strong> cần
                  lưu ý — chi tiết bên dưới với citation.
                </p>
                <p style={{ color: 'var(--fg-2)' }}>Bạn muốn tôi đào sâu vào tín hiệu nào trước?</p>
              </>
            ),
            citations: [
              { n: 1, src: 'Vietstock', t: 'Báo cáo tự động · tổng hợp 24h', date: 'Vừa xong' },
            ],
            conf: 'med',
            confPct: 76,
          },
        ])
      );
    }, 1100);
  }

  useEffect(() => {
    if (endRef.current) endRef.current.scrollTop = endRef.current.scrollHeight;
  }, [stream]);

  const suggestions = [
    'So sánh VCB và TCB về tăng trưởng tín dụng quý này',
    'Ngành nào đang được khối ngoại mua ròng?',
    'Rủi ro chính của HPG trong 3 tháng tới',
    'Tìm các mã có sentiment tích cực + KL tăng đột biến',
  ];

  return (
    <main className="page">
      <div className="chat-shell">
        <div className="chat-stream" ref={endRef}>
          <div className="chat-stream-inner">
            {/* Header */}
            <div style={{ textAlign: 'center', padding: '12px 0 8px' }}>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  font: '700 10.5px/1 var(--font-mono)',
                  color: 'var(--iris-deep)',
                  letterSpacing: '0.2em',
                  textTransform: 'uppercase',
                }}
              >
                <Icon k="sparkle" size={12} /> AI Analyst · RAG mode
              </div>
              <h1
                style={{
                  font: '700 24px var(--font-brand)',
                  color: 'var(--fg-1)',
                  margin: '8px 0 4px',
                  letterSpacing: '-0.015em',
                }}
              >
                Hỏi gì cũng được
              </h1>
              <p style={{ color: 'var(--fg-3)', margin: 0, font: '13.5px var(--font-body)' }}>
                Mọi câu trả lời đều có citation từ KG và nguồn tin
              </p>
            </div>

            {stream.map((m, i) => (
              <div key={i} className={'msg ' + m.role}>
                <div className="avatar">
                  {m.role === 'user' ? 'HN' : <Icon k="sparkle" size={16} />}
                </div>
                <div className="b">
                  <div className={'role ' + (m.role === 'ai' ? 'ai' : '')}>
                    {m.role === 'user' ? 'Bạn' : 'QuantyFin AI'}
                    {m.conf && (
                      <>
                        {' '}
                        · <ConfChip conf={m.conf} pct={m.confPct} />
                      </>
                    )}
                  </div>
                  <div className="text">
                    {typeof m.text === 'string' ? <p>{m.text}</p> : m.text}
                  </div>
                  {m.citations && (
                    <div className="cite-list">
                      <div
                        style={{
                          font: '700 10px/1 var(--font-mono)',
                          color: 'var(--fg-3)',
                          letterSpacing: '0.14em',
                          textTransform: 'uppercase',
                          marginBottom: 4,
                        }}
                      >
                        Citations · {m.citations.length} nguồn
                      </div>
                      {m.citations.map((c) => (
                        <div key={c.n} className="cite">
                          <span className="n">{c.n}</span>
                          <div className="ct">
                            <div className="ck-src">{c.src}</div>
                            <div className="ck-t">{c.t}</div>
                            <div className="ck-m">
                              <span>{c.date}</span>
                              <span>·</span>
                              <a style={{ color: 'var(--iris-deep)' }}>
                                Mở nguồn <Icon k="ext" size={10} />
                              </a>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="chat-input-wrap">
          <div className="chat-input-inner">
            <div className="chat-suggestions">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  style={{
                    font: '12.5px var(--font-body)',
                    padding: '6px 12px',
                    background: 'var(--bg-muted)',
                    border: '1px solid var(--border-light)',
                    borderRadius: 'var(--radius-pill)',
                    color: 'var(--fg-2)',
                    cursor: 'pointer',
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
              style={{
                display: 'flex',
                gap: 8,
                alignItems: 'center',
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius)',
                padding: '10px 12px',
              }}
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Hỏi về cổ phiếu, ngành, sự kiện vĩ mô, hay yêu cầu phân tích…"
                style={{
                  flex: 1,
                  border: 'none',
                  outline: 'none',
                  background: 'transparent',
                  font: '14px var(--font-body)',
                  color: 'var(--fg-1)',
                }}
              />
              <button type="submit" className="btn primary" style={{ height: 32, padding: '0 14px' }}>
                <Icon k="send" size={14} /> Gửi
              </button>
            </form>
            <div
              style={{
                font: 'var(--type-caption)',
                color: 'var(--fg-3)',
                marginTop: 8,
                display: 'flex',
                gap: 12,
                justifyContent: 'space-between',
              }}
            >
              <span>
                Mô hình: <strong style={{ color: 'var(--fg-2)' }}>Claude Sonnet 4</strong> · token
                budget: 92K còn lại
              </span>
              <span>
                <Icon k="shield" size={11} /> Mọi truy vấn có trace_id để audit
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

// ════════════════════════════════════════════════════════════════════
// ALERTS / TELEGRAM CONFIG
// ════════════════════════════════════════════════════════════════════
interface ScreenAlertsProps {
  data: DashboardData;
  onTicker: (ticker: string) => void;
}

export function ScreenAlerts({ data, onTicker }: ScreenAlertsProps) {
  const { alerts } = data;
  const [tab, setTab] = useState<string>('rules');

  return (
    <main className="page">
      <PageHead
        eyebrow="Alerts · Telegram"
        title="Cảnh báo & kênh phân phối"
        sub={
          <>
            <span>{alerts.length} cảnh báo đang hoạt động</span>
            <span className="sep">·</span>
            <span>
              Telegram bot:{' '}
              <strong style={{ color: 'var(--mint-deep)' }}>@quantyfin_bot</strong>
            </span>
            <span className="sep">·</span>
            <span>2 kênh, 1 cá nhân</span>
          </>
        }
        actions={
          <>
            <button className="btn ghost">
              <Icon k="copy" size={14} /> Sao chép token
            </button>
            <button className="btn primary">
              <Icon k="plus" size={14} /> Tạo rule mới
            </button>
          </>
        }
      />
      <div className="qf-page">
        <div className="qf-grid qf-grid-2-1">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Section
              flush
              title="Rule cảnh báo"
              actions={
                <Segment
                  value={tab}
                  onChange={setTab}
                  options={[
                    { k: 'rules', label: 'Rules', count: 6 },
                    { k: 'history', label: 'Lịch sử', count: alerts.length + 24 },
                  ]}
                />
              }
            >
              {tab === 'rules' ? (
                <RuleList />
              ) : (
                <div className="scroll" style={{ maxHeight: 540 }}>
                  {alerts.map((a) => (
                    <AlertRow key={a.id} a={a} onTicker={onTicker} />
                  ))}
                  {/* extend with mock historical */}
                  {Array.from({ length: 6 }).map((_, i) => (
                    <AlertRow
                      key={'h' + i}
                      a={{
                        id: 'h' + i,
                        sev: i % 3 === 0 ? ('high' as const) : i % 3 === 1 ? ('med' as const) : ('info' as const),
                        t: [
                          'VCB đạt giá mục tiêu 95.0 ₫',
                          'Khối lượng FPT vượt 2× trung bình',
                          'Sentiment ngành Bán lẻ chuyển sang tích cực',
                          'GAS có 3 tin tích cực trong 1 giờ',
                          'NVL chạm sàn liên tục 2 phiên',
                          'Đề xuất tái cân đối: nhóm Thép yếu hơn 5 phiên',
                        ][i],
                        m: [
                          'Price target hit',
                          'Volume spike',
                          'Sentiment shift',
                          'News surge',
                          'Price floor',
                          'AI suggestion',
                        ][i],
                        tickers: [
                          ['VCB'],
                          ['FPT'],
                          ['MWG', 'PNJ'],
                          ['GAS'],
                          ['NVL'],
                          ['HPG', 'HSG'],
                        ][i],
                        when: [
                          '2g trước',
                          '4g trước',
                          '6g trước',
                          '8g trước',
                          'Hôm qua',
                          'Hôm qua',
                        ][i],
                      }}
                      onTicker={onTicker}
                    />
                  ))}
                </div>
              )}
            </Section>

            <Section
              title="Telegram kênh & người nhận"
              actions={
                <button className="btn sm">
                  <Icon k="plus" size={12} /> Thêm
                </button>
              }
            >
              <TelegramTargets />
            </Section>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <Section ai title="Đề xuất rule" meta="AI quan sát hành vi 7 ngày">
              <SuggestedRules />
            </Section>
            <Section title="Tổng quan kênh" meta="24 giờ qua">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <BarRow label="Tin đã gửi" value="184" pct={100} color="var(--iris)" />
                <BarRow label="Tin đọc" value="142" pct={77} color="var(--mint)" />
                <BarRow label="Bot replies" value="48" pct={26} color="var(--gold)" />
                <BarRow label="Bị bỏ qua" value="42" pct={23} color="var(--border-hover)" />
              </div>
              <div className="divider" />
              <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>
                Khoảng thời gian hoạt động:{' '}
                <strong style={{ color: 'var(--fg-1)' }}>08:30–15:00 GMT+7</strong>
              </div>
            </Section>
            <Section title="Preview Telegram message" meta="Layout chuẩn">
              <TelegramPreview />
            </Section>
          </div>
        </div>
      </div>
    </main>
  );
}

function RuleList() {
  const rules = [
    {
      name: 'VHM giảm > 3% trong phiên',
      enabled: true,
      trigger: 'price.intraday < −3%',
      target: 'CH Cá nhân',
      last: 'Kích hoạt 2 lần / 7 ngày',
    },
    {
      name: 'Khối ngoại bán ròng > 800 tỷ trong giờ',
      enabled: true,
      trigger: 'foreign.flow_1h < −800',
      target: 'Group · QuantyFin team',
      last: 'Kích hoạt 1 lần hôm nay',
    },
    {
      name: 'KG path · CPI → Ngân hàng (3 hops)',
      enabled: true,
      trigger: 'kg.path_match',
      target: 'CH Cá nhân + Group',
      last: 'Cao confidence (89%)',
    },
    {
      name: 'FPT có ≥ 5 tin tích cực trong 24h',
      enabled: true,
      trigger: 'news.sentiment_count',
      target: 'CH Cá nhân',
      last: 'Kích hoạt 14:12',
    },
    {
      name: 'Cảnh báo crawler fail > 2 lần liên tiếp',
      enabled: false,
      trigger: 'pipeline.fail_streak',
      target: 'Group · Dev',
      last: 'Tạm tắt',
    },
    {
      name: 'Sentiment ngành Thép chuyển từ + → −',
      enabled: true,
      trigger: 'sector.sentiment_flip',
      target: 'Group · QuantyFin team',
      last: 'Lần cuối 28/05',
    },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {rules.map((r) => (
        <div
          key={r.name}
          style={{
            display: 'grid',
            gridTemplateColumns: '36px 1fr auto',
            gap: 12,
            alignItems: 'center',
            padding: '12px 16px',
            borderBottom: '1px solid var(--border-light)',
          }}
        >
          <label style={{ position: 'relative', display: 'inline-block', width: 32, height: 18 }}>
            <input type="checkbox" defaultChecked={r.enabled} style={{ opacity: 0, width: 0, height: 0 }} />
            <span
              style={{
                position: 'absolute',
                inset: 0,
                background: r.enabled ? 'var(--brand)' : 'var(--border)',
                borderRadius: 9,
                transition: 'all .2s',
              }}
            />
            <span
              style={{
                position: 'absolute',
                top: 2,
                left: r.enabled ? 16 : 2,
                width: 14,
                height: 14,
                background: '#fff',
                borderRadius: '50%',
                transition: 'all .2s',
              }}
            />
          </label>
          <div>
            <div style={{ font: '500 13px/1.3 var(--font-body)', color: 'var(--fg-1)' }}>
              {r.name}
            </div>
            <div
              style={{
                marginTop: 4,
                font: 'var(--type-caption)',
                color: 'var(--fg-3)',
                display: 'flex',
                gap: 8,
                flexWrap: 'wrap',
              }}
            >
              <span
                style={{
                  font: 'var(--type-mono-sm)',
                  padding: '2px 6px',
                  background: 'var(--bg-muted)',
                  borderRadius: 3,
                  color: 'var(--fg-2)',
                }}
              >
                {r.trigger}
              </span>
              <span>→ {r.target}</span>
              <span className="sep">·</span>
              <span>{r.last}</span>
            </div>
          </div>
          <button className="btn ghost sm">
            <Icon k="more" size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

function TelegramTargets() {
  const targets = [
    { name: 'QuantyFin team', kind: 'Group', members: 12, on: true },
    { name: 'CH Cá nhân (Hùng Nguyễn)', kind: 'Direct', members: 1, on: true },
    { name: 'Dev alerts', kind: 'Group', members: 4, on: false },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {targets.map((t) => (
        <div
          key={t.name}
          style={{
            display: 'grid',
            gridTemplateColumns: 'auto 1fr auto auto',
            gap: 12,
            alignItems: 'center',
            padding: '10px 12px',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg)',
          }}
        >
          <span
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: 'var(--iris-tint)',
              color: 'var(--iris-deep)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Icon k={t.kind === 'Group' ? 'user' : 'chat'} size={14} />
          </span>
          <div>
            <div style={{ font: '500 13px/1.2 var(--font-body)', color: 'var(--fg-1)' }}>
              {t.name}
            </div>
            <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>
              {t.kind} · {t.members} {t.kind === 'Group' ? 'members' : 'người'}
            </div>
          </div>
          <span className={'trace-pill ' + (t.on ? '' : 'fail')}>{t.on ? 'BẬT' : 'TẮT'}</span>
          <button className="btn ghost sm">
            <Icon k="more" size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

function SuggestedRules() {
  const sug = [
    {
      t: 'Cảnh báo khi sentiment FPT chuyển âm',
      why: 'FPT chiếm 18% tỷ trọng đọc tin của bạn nhưng chưa có rule.',
      conf: 'high' as const,
      pct: 92,
    },
    {
      t: 'Theo dõi khối ngoại nhóm Thép',
      why: '3 phiên gần nhất có bán ròng đột biến.',
      conf: 'med' as const,
      pct: 74,
    },
    {
      t: 'Crisis path: Tỷ giá → Ngân hàng',
      why: 'KG phát hiện chuỗi 3 hops với confidence 81%.',
      conf: 'high' as const,
      pct: 81,
    },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {sug.map((s, i) => (
        <div
          key={i}
          style={{
            padding: '10px 12px',
            background: 'var(--iris-tint)',
            border: '1px solid rgba(124,108,245,.18)',
            borderRadius: 'var(--radius-sm)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10 }}>
            <div style={{ font: '500 13px/1.4 var(--font-body)', color: 'var(--fg-1)' }}>{s.t}</div>
            <ConfChip conf={s.conf} pct={s.pct} />
          </div>
          <div style={{ marginTop: 4, font: 'var(--type-caption)', color: 'var(--fg-2)' }}>
            {s.why}
          </div>
          <div style={{ marginTop: 8, display: 'flex', gap: 6 }}>
            <button className="btn iris sm">Tạo rule</button>
            <button className="btn ghost sm">Bỏ qua</button>
          </div>
        </div>
      ))}
    </div>
  );
}

interface BarRowProps {
  label: string;
  value: string;
  pct: number;
  color: string;
}

function BarRow({ label, value, pct, color }: BarRowProps) {
  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          font: '12.5px var(--font-body)',
          color: 'var(--fg-2)',
          marginBottom: 4,
        }}
      >
        <span>{label}</span>
        <strong style={{ color: 'var(--fg-1)', font: '600 13px var(--font-mono)' }}>{value}</strong>
      </div>
      <div style={{ height: 8, background: 'var(--bg-muted)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

function TelegramPreview() {
  return (
    <div
      style={{
        background: '#0E1621',
        borderRadius: 12,
        padding: 14,
        maxWidth: '100%',
      }}
    >
      <div
        style={{
          background: '#182533',
          borderRadius: 8,
          padding: 12,
          color: '#fff',
          font: '13px/1.55 var(--font-body)',
          position: 'relative',
          maxWidth: 340,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span
            style={{
              width: 18,
              height: 18,
              borderRadius: 4,
              background: 'linear-gradient(135deg,#2A2B86,#7C6CF5)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              font: '700 9px/1 var(--font-brand)',
              color: '#fff',
            }}
          >
            Q
          </span>
          <strong style={{ font: '600 12.5px var(--font-brand)' }}>QuantyFin AI</strong>
          <span style={{ color: '#5fadef', font: '600 11px var(--font-mono)' }}>· bot</span>
        </div>
        <div
          style={{
            font: '600 12px var(--font-mono)',
            color: '#ef4d4d',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 6,
          }}
        >
          🚨 Cảnh báo cao
        </div>
        <p style={{ margin: '0 0 8px' }}>
          <strong>VHM</strong> giảm 3.2% trong phiên, vượt ngưỡng cảnh báo cá nhân.
        </p>
        <p style={{ margin: '0 0 8px', color: '#9faec0', font: '12px var(--font-body)' }}>
          AI tổng hợp: khối ngoại bán ròng + cổ đông lớn đăng ký bán. KG path 3 hops từ CPI → tỷ giá →
          khối ngoại.
        </p>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 8 }}>
          <span
            style={{
              background: '#2A4055',
              padding: '4px 8px',
              borderRadius: 4,
              font: '11px var(--font-mono)',
              color: '#7fb3ff',
            }}
          >
            VHM −3.2%
          </span>
          <span
            style={{
              background: '#2A4055',
              padding: '4px 8px',
              borderRadius: 4,
              font: '11px var(--font-mono)',
              color: '#7fb3ff',
            }}
          >
            Conf 89%
          </span>
        </div>
        <div
          style={{
            marginTop: 10,
            paddingTop: 8,
            borderTop: '1px solid #243443',
            font: '11px var(--font-mono)',
            color: '#5fadef',
          }}
        >
          /detail VHM &nbsp;·&nbsp; /chart 1d &nbsp;·&nbsp; /mute 1h
        </div>
        <div
          style={{
            position: 'absolute',
            bottom: -6,
            right: 14,
            font: '10px var(--font-mono)',
            color: '#6b7d92',
          }}
        >
          14:32 ✓✓
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// JOBS / PIPELINE
// ════════════════════════════════════════════════════════════════════
interface ScreenJobsProps {
  data: DashboardData;
}

export function ScreenJobs({ data }: ScreenJobsProps) {
  const { jobs } = data;
  const totalCrawled = jobs.reduce((sum, j) => sum + j.total, 0);
  const totalAnalyzed = jobs.reduce((sum, j) => sum + j.analyzed, 0);
  const totalFiltered = jobs.reduce((sum, j) => sum + j.filteredOut, 0);
  const failed = jobs.filter((j) => j.status === 'failed').length;
  const running = jobs.filter((j) => j.status === 'running').length;

  return (
    <main className="page">
      <PageHead
        eyebrow="Pipeline · Background tasks"
        title="Crawler jobs & ingestion pipeline"
        sub={
          <>
            <span>{jobs.length} sources</span>
            <span className="sep">·</span>
            <span>
              {running} running · {failed} failed
            </span>
            <span className="sep">·</span>
            <span>Last cycle: 14:30:08</span>
          </>
        }
        actions={
          <>
            <button className="btn ghost">
              <Icon k="refresh" size={14} /> Trigger cycle
            </button>
            <button className="btn primary">
              <Icon k="plus" size={14} /> Thêm source
            </button>
          </>
        }
      />
      <div className="qf-page">
        {/* Pipeline overview */}
        <Section title="Pipeline · 5 stages" meta="Realtime · auto-refresh 5s" style={{ marginBottom: 16 }}>
          <div className="pipe">
            <div className="stage">
              <div className="step">01 · Discover</div>
              <div className="name">Source list</div>
              <div className="count">{jobs.length}</div>
              <div className="sub">RSS · Search · Playwright</div>
            </div>
            <div className="stage">
              <div className="step">02 · Crawl</div>
              <div className="name">Fetch HTML</div>
              <div className="count">{fmtInt(totalCrawled)}</div>
              <div className="sub">URLs / 24h</div>
            </div>
            <div className="stage active">
              <div className="step">03 · Filter</div>
              <div className="name">Zero-cost filter</div>
              <div className="count">{fmtInt(totalFiltered)}</div>
              <div className="sub">{Math.round((totalFiltered / totalCrawled) * 100)}% bị loại</div>
            </div>
            <div className="stage">
              <div className="step">04 · Extract</div>
              <div className="name">LLM extractor</div>
              <div className="count">{fmtInt(totalAnalyzed)}</div>
              <div className="sub">tickers + sentiment</div>
            </div>
            <div className="stage">
              <div className="step">05 · KG load</div>
              <div className="name">Graph upsert</div>
              <div className="count">{fmtInt(Math.round(totalAnalyzed * 0.92))}</div>
              <div className="sub">edges + nodes</div>
            </div>
          </div>
        </Section>

        {/* Job table */}
        <Section
          flush
          title="Crawler jobs theo nguồn"
          actions={
            <>
              <Segment
                value="all"
                onChange={() => {}}
                options={[
                  { k: 'all', label: 'Tất cả' },
                  { k: 'rss', label: 'RSS' },
                  { k: 'search', label: 'Search' },
                  { k: 'pw', label: 'Playwright' },
                ]}
              />
            </>
          }
        >
          <table className="dt" style={{ width: '100%' }}>
            <thead>
              <tr>
                <th>Source</th>
                <th>Tier</th>
                <th>Status</th>
                <th className="num">Total</th>
                <th className="num">Filtered</th>
                <th className="num">Analyzed</th>
                <th className="num">Duration</th>
                <th>Trace</th>
                <th>Last run</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id}>
                  <td>
                    <div style={{ font: '500 13px/1.2 var(--font-body)', color: 'var(--fg-1)' }}>
                      {j.src}
                    </div>
                    <div style={{ font: 'var(--type-mono-sm)', color: 'var(--fg-3)' }}>{j.url}</div>
                  </td>
                  <td style={{ font: 'var(--type-mono-sm)', color: 'var(--fg-2)', textTransform: 'uppercase' }}>
                    {j.tier}
                  </td>
                  <td>
                    <span className={'trace-pill ' + (j.status === 'failed' ? 'fail' : '')}>
                      {j.status === 'done'
                        ? 'OK · 200'
                        : j.status === 'running'
                        ? 'Đang chạy'
                        : j.status === 'retry'
                        ? 'Retry 2/3'
                        : 'Lỗi · 504'}
                    </span>
                  </td>
                  <td className="num tabular">{fmtInt(j.total)}</td>
                  <td className="num tabular" style={{ color: 'var(--iris-deep)' }}>
                    {fmtInt(j.filteredOut)}
                  </td>
                  <td className="num tabular">{fmtInt(j.analyzed)}</td>
                  <td className="num tabular" style={{ color: 'var(--fg-3)' }}>
                    {(j.durationMs / 1000).toFixed(1)}s
                  </td>
                  <td style={{ font: 'var(--type-mono-sm)', color: 'var(--fg-3)' }}>{j.traceId}</td>
                  <td style={{ font: 'var(--type-mono-sm)', color: 'var(--fg-3)' }}>{j.lastRun}</td>
                  <td>
                    <button className="btn ghost sm">
                      <Icon k="more" size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        {/* Sub: LLM usage + Errors */}
        <div className="qf-grid qf-grid-2" style={{ marginTop: 16 }}>
          <Section title="LLM Gateway · 24h" meta="Token + cost theo model">
            <LLMUsageTable />
          </Section>
          <Section title="Logs · gần nhất" meta="trace_id liên kết">
            <LogList />
          </Section>
        </div>
      </div>
    </main>
  );
}

function LLMUsageTable() {
  const ms = [
    { name: 'Haiku 3.5', vendor: 'Anthropic', role: 'Extractor', tokens24h: 184392, cost24h: 0.42, share: 64 },
    { name: 'GPT-4o-mini', vendor: 'OpenAI', role: 'Sentiment', tokens24h: 98140, cost24h: 0.18, share: 24 },
    { name: 'Sonnet 4', vendor: 'Anthropic', role: 'Analyst (review)', tokens24h: 12640, cost24h: 0.84, share: 9 },
    { name: 'Gemini Flash', vendor: 'Google', role: 'Fallback', tokens24h: 4220, cost24h: 0.02, share: 3 },
  ];
  return (
    <div>
      <table className="dt" style={{ width: '100%' }}>
        <thead>
          <tr>
            <th>Model</th>
            <th>Role</th>
            <th className="num">Tokens 24h</th>
            <th className="num">Share</th>
            <th className="num">Cost</th>
          </tr>
        </thead>
        <tbody>
          {ms.map((m) => (
            <tr key={m.name}>
              <td>
                <div style={{ font: '500 13px var(--font-body)', color: 'var(--fg-1)' }}>{m.name}</div>
                <div style={{ font: 'var(--type-caption)', color: 'var(--fg-3)' }}>{m.vendor}</div>
              </td>
              <td style={{ font: 'var(--type-caption)', color: 'var(--fg-2)' }}>{m.role}</td>
              <td className="num tabular">{fmtInt(m.tokens24h)}</td>
              <td className="num tabular">
                <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                  <span>{m.share}%</span>
                  <span
                    style={{
                      display: 'inline-block',
                      width: 50,
                      height: 6,
                      background: 'var(--bg-muted)',
                      borderRadius: 3,
                      overflow: 'hidden',
                    }}
                  >
                    <span
                      style={{ display: 'block', width: m.share + '%', height: '100%', background: 'var(--iris)' }}
                    />
                  </span>
                </div>
              </td>
              <td className="num tabular">${m.cost24h.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div
        style={{
          marginTop: 12,
          padding: 10,
          background: 'var(--mint-tint)',
          borderRadius: 'var(--radius-sm)',
          font: '12.5px var(--font-body)',
          color: 'var(--mint-deep)',
        }}
      >
        <strong>Tiết kiệm 71%</strong> nhờ multi-tier routing — Haiku xử lý 64% throughput, Sonnet
        chỉ dùng cho phân tích chuyên sâu.
      </div>
    </div>
  );
}

function LogList() {
  const logs = [
    { lvl: 'info', m: 'KG upsert: +12 edges, +3 nodes', trace: 'trc_8f2a1bcd', at: '14:32:08' },
    { lvl: 'warn', m: 'CafeF rate-limited, applying backoff 30s', trace: 'trc_7e91a02d', at: '14:31:44' },
    { lvl: 'info', m: 'Sentiment batch · 24 items · 1.42s', trace: 'trc_3d4b21fc', at: '14:31:18' },
    { lvl: 'error', m: 'Tuổi Trẻ · timeout after 8s · scheduling retry', trace: 'trc_9a0e7211', at: '14:30:52' },
    { lvl: 'info', m: 'Zero-cost filter rejected 18 / 24 items', trace: 'trc_2c11ab8f', at: '14:30:30' },
    { lvl: 'info', m: 'Cycle started · 8 sources', trace: 'trc_1b04cf09', at: '14:30:00' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {logs.map((l, i) => (
        <div
          key={i}
          style={{
            display: 'grid',
            gridTemplateColumns: 'auto auto 1fr auto',
            gap: 10,
            alignItems: 'center',
            padding: '8px 0',
            borderBottom: '1px solid var(--border-light)',
            font: 'var(--type-mono-sm)',
          }}
        >
          <span style={{ color: 'var(--fg-3)' }}>{l.at}</span>
          <span
            style={{
              font: '600 10px/1 var(--font-mono)',
              padding: '3px 6px',
              borderRadius: 4,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              background:
                l.lvl === 'error'
                  ? 'var(--gap-bg)'
                  : l.lvl === 'warn'
                  ? 'var(--plan-bg)'
                  : 'var(--bg-muted)',
              color:
                l.lvl === 'error'
                  ? 'var(--gap)'
                  : l.lvl === 'warn'
                  ? 'var(--gold-deep)'
                  : 'var(--fg-2)',
              minWidth: 44,
              textAlign: 'center',
            }}
          >
            {l.lvl}
          </span>
          <span style={{ color: 'var(--fg-1)' }}>{l.m}</span>
          <span style={{ color: 'var(--iris-deep)' }}>{l.trace}</span>
        </div>
      ))}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// SETTINGS
// ════════════════════════════════════════════════════════════════════
export function ScreenSettings() {
  return <Settings />;
}

// ════════════════════════════════════════════════════════════════════
// LOGIN
// ════════════════════════════════════════════════════════════════════
interface ScreenLoginProps {
  onSignIn: () => void;
}

export function ScreenLogin({ onSignIn }: ScreenLoginProps) {
  const [email, setEmail] = useState<string>('hungnguyen@quantyfin.vn');
  const [pw, setPw] = useState<string>('••••••••••••');
  return (
    <div className="qf-login">
      <div className="pane-art">
        <div>
          <Logo variant="dark" />
        </div>
        <div>
          <span className="login-eyebrow">AI Agentic · VN Stock Market</span>
          <h1 style={{ marginTop: 16 }}>
            Phân tích <em>chứng khoán</em>
            <br />
            không còn là việc của con người
          </h1>
          <p className="lede">
            Knowledge Graph thời gian thực, sentiment đa nguồn, và một AI analyst luôn sẵn sàng trả
            lời — mọi câu trả lời đều có citation.
          </p>
        </div>
        <div className="meta-row">
          <span>
            <span className="k">v0.4.2-rc</span> · Vietnam · UTC+7
          </span>
          <span>Production workspace · 8 sources · 230 mã theo dõi</span>
        </div>
        {/* KG flourish */}
        <svg className="kg-art" width="520" height="520" viewBox="0 0 520 520">
          <g stroke="rgba(255,255,255,0.18)" strokeWidth="1" fill="none">
            <circle cx="260" cy="260" r="80" />
            <circle cx="260" cy="260" r="150" />
            <circle cx="260" cy="260" r="220" />
            <line x1="260" y1="40" x2="260" y2="480" />
            <line x1="40" y1="260" x2="480" y2="260" />
            <line x1="100" y1="100" x2="420" y2="420" />
            <line x1="420" y1="100" x2="100" y2="420" />
          </g>
          {[[260, 80], [420, 180], [440, 320], [330, 440], [160, 440], [80, 300], [100, 160], [200, 80]].map(
            ([x, y], i) => (
              <g key={i}>
                <circle cx={x} cy={y} r="6" fill="#FCAF16" opacity="0.7" />
                <circle cx={x} cy={y} r="12" fill="none" stroke="#FCAF16" opacity="0.25" />
              </g>
            )
          )}
          <circle cx="260" cy="260" r="14" fill="#7C6CF5" />
        </svg>
      </div>

      <div className="pane-form">
        <div className="pane-form-inner">
          <h2 className="form-h">Đăng nhập</h2>
          <div className="form-sub">Sử dụng tài khoản workspace của bạn.</div>
          <TextInput label="Email" value={email} onChange={setEmail} mono />
          <TextInput label="Mật khẩu" value={pw} onChange={setPw} mono />
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              font: 'var(--type-caption)',
              color: 'var(--fg-3)',
              margin: '4px 0 20px',
            }}
          >
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <input type="checkbox" defaultChecked /> Ghi nhớ phiên 14 ngày
            </label>
            <a style={{ color: 'var(--iris-deep)', cursor: 'pointer' }}>Quên mật khẩu?</a>
          </div>
          <button
            className="btn primary lg"
            style={{ width: '100%', justifyContent: 'center' }}
            onClick={onSignIn}
          >
            Đăng nhập <Icon k="arrowR" size={14} />
          </button>
          <div
            style={{
              margin: '14px 0',
              position: 'relative',
              textAlign: 'center',
              color: 'var(--fg-3)',
              font: 'var(--type-caption)',
            }}
          >
            <span
              style={{
                position: 'absolute',
                left: 0,
                right: 0,
                top: '50%',
                height: 1,
                background: 'var(--border-light)',
              }}
            />
            <span style={{ position: 'relative', padding: '0 10px', background: 'var(--bg)' }}>
              hoặc
            </span>
          </div>
          <button className="btn lg" style={{ width: '100%', justifyContent: 'center' }}>
            Đăng nhập với SSO · Workspace
          </button>
          <div style={{ marginTop: 18, font: 'var(--type-caption)', color: 'var(--fg-3)', textAlign: 'center' }}>
            Bằng cách đăng nhập, bạn đồng ý với <a style={{ color: 'var(--iris-deep)' }}>Điều khoản dịch vụ</a> và{' '}
            <a style={{ color: 'var(--iris-deep)' }}>Chính sách bảo mật</a>.
          </div>
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════
// NAMESPACE EXPORT FOR ALIGNMENT WITH ORIGINAL JS
// ════════════════════════════════════════════════════════════════════
export const Screens = {
  Dashboard: ScreenDashboard,
  KG: ScreenKG,
  Stock: ScreenStock,
  News: ScreenNews,
  Chat: ScreenChat,
  Alerts: ScreenAlerts,
  Jobs: ScreenJobs,
  Settings: ScreenSettings,
  Login: ScreenLogin,
};
