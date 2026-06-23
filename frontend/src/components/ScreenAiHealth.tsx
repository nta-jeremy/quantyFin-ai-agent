import { PageHead, Section, KpiCard, Icon } from './SharedUI';
import { LLM_MODELS, LLMModel } from '../lib/mockData';

interface ScreenAiHealthProps {
  data?: any;
}

export function ScreenAiHealth({ data: _data }: ScreenAiHealthProps) {
  // Calculate total tokens and cost dynamically from LLM_MODELS
  const totalTokens = (LLM_MODELS ?? []).reduce((sum: number, m: LLMModel) => sum + (m.tokens24h || 0), 0);
  const totalCost = (LLM_MODELS ?? []).reduce((sum: number, m: LLMModel) => sum + (m.cost24h || 0), 0);

  // Sparkline data (deterministic trend proxy for the last 7 periods)
  const tokenSparkData = [1200000, 1350000, 1100000, 1420000, 1580000, 1390000, totalTokens];
  const costSparkData = [45, 52, 38, 59, 62, 55, totalCost];

  // Formatting helpers — use vi-VN locale consistently throughout this screen
  const formatNum = (num: number) => num.toLocaleString('vi-VN');
  const formatCost = (num: number) => {
    return '$' + num.toLocaleString('vi-VN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const handleRefresh = () => {
    // Placeholder: trigger data refresh when API integration is available
    console.info('[ScreenAiHealth] Refresh requested');
  };

  const handleConfigure = () => {
    // Placeholder: open engine configuration panel when available
    console.info('[ScreenAiHealth] Configure Engine requested');
  };

  return (
    <main className="page" id="screen-ai-health">
      <PageHead
        eyebrow="AI Pipeline Health"
        title="Trạng thái & Hiệu suất AI Pipeline"
        sub={
          <>
            <span>CrewAI Orchestrator</span>
            <span className="sep">·</span>
            <span>LiteLLM Router</span>
            <span className="sep">·</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--mint)' }} />
              Active
            </span>
          </>
        }
        actions={
          <>
            <button
              className="btn ghost"
              onClick={handleRefresh}
              style={{ minHeight: 44 }}
              aria-label="Làm mới dữ liệu"
            >
              <Icon k="refresh" size={14} /> Làm mới
            </button>
            <button
              className="btn primary"
              onClick={handleConfigure}
              style={{ background: 'var(--brand)', minHeight: 44 }}
              aria-label="Cấu hình AI Engine"
            >
              <Icon k="cog" size={14} /> Cấu hình Engine
            </button>
          </>
        }
      />

      <div className="qf-page">
        {/* KPI Row (4 Cards) */}
        <div className="qf-grid qf-grid-4" style={{ marginBottom: 16 }}>
          <KpiCard
            label="Tổng Token (24h)"
            value={formatNum(totalTokens)}
            valueClass="tabular"
            sub="Tổng lưu lượng token qua gateway"
            spark={tokenSparkData}
            sparkTone="iris"
          />
          <KpiCard
            label="Chi phí ước tính"
            value={formatCost(totalCost)}
            valueClass="tabular"
            sub="Chi phí API ước tính (USD)"
            spark={costSparkData}
            sparkTone="gold"
          />
          <KpiCard
            label="Độ trễ trung bình"
            value="382 ms"
            valueClass="tabular"
            sub="Phản hồi trung bình từ LLM Gateway"
          />
          <KpiCard
            label="Hiệu suất trích xuất"
            value="98.2%"
            valueClass="tabular"
            sub="Tỷ lệ định danh thực thể thành công"
          />
        </div>

        {/* Pipeline flowchart */}
        <Section
          title="Sơ đồ luồng xử lý AI Data Pipeline"
          meta="Lưu đồ ngang thể hiện trạng thái xử lý dữ liệu qua các tầng"
          style={{ marginBottom: 16 }}
        >
          <div className="pipe" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            <div className="stage">
              <div className="step">01 · Crawl</div>
              <div className="name">Raw News</div>
              <div className="count">1,248</div>
              <div className="sub">tin tức thô nhận được</div>
            </div>
            <div className="stage">
              <div className="step">02 · Filter</div>
              <div className="name">Zero-Cost Filter</div>
              <div className="count">982</div>
              <div className="sub">tin đã vượt qua bộ lọc / loại trùng</div>
            </div>
            <div className="stage active">
              <div className="step">03 · Extract</div>
              <div className="name">LLM Extractor</div>
              <div className="count">245</div>
              <div className="sub">thực thể & cảm xúc được trích xuất</div>
            </div>
            <div className="stage">
              <div className="step">04 · Upsert</div>
              <div className="name">Graph Upsert</div>
              <div className="count">182</div>
              <div className="sub">thực thể & mối quan hệ vào Neo4j</div>
            </div>
          </div>
        </Section>

        {/* Details Row: Table and Settings */}
        <div className="qf-grid qf-grid-2-1">
          <Section
            flush
            title="LiteLLM Models Usage"
            meta="Thống kê lưu lượng sử dụng mô hình LLM chi tiết trong 24 giờ qua"
          >
            <table className="dt" style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Vendor</th>
                  <th>Role</th>
                  <th className="num">Tokens</th>
                  <th className="num">Cost</th>
                  <th className="num">Share</th>
                </tr>
              </thead>
              <tbody>
                {(LLM_MODELS ?? []).map((m: LLMModel) => (
                  <tr key={m.name}>
                    <td>
                      <span
                        style={{
                          font: '600 13px/1 var(--font-mono)',
                          color: 'var(--fg-1)',
                        }}
                      >
                        {m.name}
                      </span>
                    </td>
                    <td>{m.vendor}</td>
                    <td>
                      <span
                        style={{
                          font: '500 12.5px/1 var(--font-body)',
                          color: 'var(--fg-2)',
                        }}
                      >
                        {m.role}
                      </span>
                    </td>
                    <td
                      className="num tabular"
                      style={{ font: '500 12.5px/1 var(--font-mono)' }}
                    >
                      {formatNum(m.tokens24h)}
                    </td>
                    <td
                      className="num tabular"
                      style={{ font: '500 12.5px/1 var(--font-mono)' }}
                    >
                      {formatCost(m.cost24h)}
                    </td>
                    <td
                      className="num tabular"
                      style={{ font: '500 12.5px/1 var(--font-mono)' }}
                    >
                      {m.share}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>

          <Section title="AI Engine Settings" meta="Trạng thái cấu hình của CrewAI Engine">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px 12px',
                  background: 'var(--bg-2)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-light)',
                }}
              >
                <span style={{ font: '500 13px/1 var(--font-body)', color: 'var(--fg-2)' }}>
                  Agents Active
                </span>
                <span
                  style={{
                    font: '700 13px/1 var(--font-mono)',
                    color: 'var(--mint-deep)',
                  }}
                >
                  3 / 3 Running
                </span>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px 12px',
                  background: 'var(--bg-2)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-light)',
                }}
              >
                <span style={{ font: '500 13px/1 var(--font-body)', color: 'var(--fg-2)' }}>
                  Cache Hit Rate
                </span>
                <span
                  style={{
                    font: '700 13px/1 var(--font-mono)',
                    color: 'var(--iris-deep)',
                  }}
                >
                  42.8%
                </span>
              </div>

              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '10px 12px',
                  background: 'var(--bg-2)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--border-light)',
                }}
              >
                <span style={{ font: '500 13px/1 var(--font-body)', color: 'var(--fg-2)' }}>
                  Rate Limit Gateway
                </span>
                <span
                  style={{
                    font: '700 13px/1 var(--font-mono)',
                    color: 'var(--mint-deep)',
                  }}
                >
                  Normal (0% drops)
                </span>
              </div>
            </div>
          </Section>
        </div>
      </div>
    </main>
  );
}
