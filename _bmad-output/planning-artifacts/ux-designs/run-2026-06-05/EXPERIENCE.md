---
status: final
updated: 2026-06-05
---
# EXPERIENCE.md
> Canonical reference for the QuantyFin AI Agent behavior, flows, and Information Architecture.

## Foundation
- **Form-factor:** Desktop Web Application (Cockpit Dashboard) + Telegram Bot Interface.
- **UI System:** React + Tailwind v4 component layer (shadcn-compatible), strictly inheriting the QuantyFin Design System `colors_and_type.css`.
- **Surface:** `[data-surface="app"]`

## Information Architecture
### 1. The Admin Cockpit (Web/App)
- **Crawler Terminal:** Real-time logs and data pipeline monitoring (vn-stock, CafeF, NDH). Uses JetBrains Mono for logs and technical output.
- **Command Center:** Health overview of the AI pipeline. KPI cards showing token spending, LiteLLM metrics, and cost analysis.
- **Node Explorer:** Visual representation of the Knowledge Graph (Entities: Companies, Leaders, Events; Relationships: Sentiment, Risk).

### 2. The Investor Interface (Telegram)
- **Risk Alerts:** Proactive push notifications for negative sentiment/anomalies (e.g., negative news + price drop).
- **Q&A Chat:** Conversational queries processed by the AI Engine via Cypher translations.

## Voice and Tone
- **Dashboard:** Direct, technical, transparent. Uses English technical terms (KPI, LLM, Crawler, Token) mixed with Vietnamese UI labels.
- **Telegram Bot:** Concise, analytical, risk-aware. Does not use fluff or marketing language. Relies on data points as the unit of trust.

## Component Patterns
- **Terminal Log Blocks:** Monospace dense lists for data ingestion tracking.
- **Interactive Graph Nodes:** Clickable entities in the Node Explorer revealing contextual popovers with entity resolution details.
- **Status Indicators:** `LIVE`, `BUILD`, `GAP` applied to crawlers and LLM processes.

## State Patterns
- **Loading:** Instant state transitions (no ambient motion per the `app` surface rules). `Skeleton` loaders for Node Graph generation.
- **Empty States:** Clear instructions to configure a crawler or start a query.

## Interaction Primitives
- **Hover:** Subtle background lifts on data rows.
- **Click:** Instant snap (no rich motion).
- **Focus:** WCAG AA compliant focus rings (`var(--focus-ring)`) on all inputs and actions.

## Accessibility Floor
- Tap targets minimum 44px for core dashboard actions.
- Contrast minimums strictly enforced via the QuantyFin token palette (e.g., gold is never used for text).
- `prefers-reduced-motion: reduce` removes all graph physics animations.

## Key Flows
### Flow 1: System Admin Audits the AI Pipeline
**Protagonist:** Administrator (Quản trị viên hệ thống)
1. Logs into the **Cockpit**.
2. Lands on the **Command Center**. Sees a spike in Token Usage (KPI Card - Crimson alert).
3. Clicks into the **Crawler Terminal** to investigate the exact worker/agent causing the spike.
4. Identifies a redundant data source and dynamically disables it via a settings toggle.
5. The system instantly reflects the updated status (`GAP` -> `LIVE`).

### Flow 2: F1 Investor Receives Risk Alert
**Protagonist:** F1 Investor (Nhà đầu tư F1)
1. Receives a proactive Telegram push notification: "Cảnh báo: Sentiment tiêu cực + Giảm giá đối với mã VIC."
2. Taps the inline button in Telegram to ask: "Chuyện gì đang xảy ra với VIC?"
3. The Telegram Bot (via LiteLLM & Cypher query) synthesizes the Knowledge Graph relationships and responds with the exact news sources causing the sentiment shift.
