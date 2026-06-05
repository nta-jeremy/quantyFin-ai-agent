---
status: final
updated: 2026-06-05
---
# DESIGN.md
> Canonical reference for QuantyFin AI Agent visual identity, inheriting strictly from the QuantyFin Design System.

## Brand & Style
- **Vibe:** Art-modern, minimal, hightech, AI-native, VN-first.
- **Surface archetypes used:** `[data-surface="app"]` for Cockpit Dashboard.
- **Language:** Vietnamese UI labels + English tech terms. No emoji. Sentence case. Numbers + named owners as units of trust.

## Colors
- `--brand`: `#2a2b86` (Primary CTA, active nav, BUILD status)
- `--iris`: `#7c6cf5` (AI/tech default, 90% accent surface)
- `--gold`: `#fcaf16` (Climax/Achievement moments, never text/buttons due to contrast)
- `--mint`: `#10b981` (Growth, LIVE status, success)
- `--rose`: `#f472b6` (Human, REVIEW status)
- `--gap`: `#ef4444` (Alert/Destructive, REJECTED)

## Typography
- **Be Vietnam Pro**: Body text, brand chrome, app headings.
- **Montserrat**: Impact display (used sparingly in app surface).
- **JetBrains Mono**: Status pills (e.g., LIVE, BUILD), SKU/Node IDs, technical metadata (Command Center logs).

## Layout & Spacing
- **App Surface (`data-surface="app"`)**: 
  - Body: 13.5px / 1.5 line-height.
  - Hero/H1: 28px.
  - Container: 100% fluid (Dashboard spanning full width).
- **Section Rule (Principle I)**: Max 4-5 sub-blocks per section to minimize cognitive load.

## Elevation & Depth
- Flat, minimal depth. Overlays and dialogs use standard shadows, but dashboard widgets stay flat or use subtle borders to maintain the "Cockpit" feel.

## Shapes
- **Status Pills**: Fully rounded (pill shape). JetBrains Mono uppercase, 0.6px tracking.

## Components
- **Buttons (`.btn`)**: Semantic usage. Primary uses `--brand`.
- **Data Tables**: Dense display for Crawler Terminal and Node Explorer.
- **KPI Cards**: Used in Command Center (e.g. "A Aurora gradient" for flagship AI token spend, "C Mesh + sparkline" for data-led metrics).
- **Icons**: Lucide (1.75px stroke, 24x24 viewBox, Sizes 14/16/20/24px). Status icons take status token color (never gold).

## Do's and Don'ts
- **Do** use `var(--focus-ring)` for all interactive elements.
- **Do** respect `--accent-freq: signal` for the App surface (accents only used as signals, not bold sections).
- **Don't** mix App surface rules with Portal rules (e.g. no italic Playfair conclusions in the Dashboard).
- **Don't** use >2 accents per section.
