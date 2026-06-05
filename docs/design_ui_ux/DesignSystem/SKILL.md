---
name: quantyFin-design
description: Generate well-branded interfaces and assets for QuantyFin (Vietnamese fashion retail brand). Production-ready design system on Tailwind v4 (shadcn-standard) supporting four surface archetypes — marketing landing, internal application (back-office, dashboards, internal mobile), executive briefing / report portal, and in-store/POS/signage — from one shared token foundation. Semantic role tokens (background/foreground/primary/muted/border/ring…) + tokenized type scale + an @apply component layer + 4 UI kits (app, fashion, AI, collab). Aesthetic: art-modern, minimal, hightech, AI-native. Be Vietnam Pro + JetBrains Mono typographic core. VN-first content, full Vietnamese diacritic support.
user-invocable: true
---

## Orientation

Read in this order:
1. **`DESIGN.md`** — the design system: brand, tokens, 3-layer architecture, 4 surfaces, principles (universal + portal narrative), the Tailwind v4 layer, components, and how to consume the DS in a real repo.
2. **`CLAUDE.md`** — how to work in this repo + project state/history.

Also explore: `colors_and_type.css` (tokens + 4 surface adapters), `tailwind/globals.css` + `tailwind/quantyfin.tailwind.css` (semantic roles + @apply component layer), `ui_kits/*/*.css` (composite kits), `components.json` + `registry.json` + `public/r/` (installable shadcn registry), `registry/ui/*.tsx` (open-code React components), and the living docs in `preview/` (IA mirrors shadcn: `preview/foundations/`, `preview/components/` + `preview/components/kits/`, `preview/brand/` — each specimen tagged `@dsCard group`).

---

## Architecture — 3 layers

System is built as Foundation → Surface adapters → UI kits.

- **Foundation** lives in `:root` (`colors_and_type.css`): brand color, accent semantics, status palette, font families, easings, a11y floor. Universal — never overridden.
- **Surface adapters** in the same file (`[data-surface="portal|marketing|app|store"]`) resolve scale tokens: type-size, gutter, row height, motion budget, color frequency.
- **Component layer** (`@apply` + tokens) in `tailwind/quantyfin.tailwind.css` (buttons, typography, forms, overlays, identity, data-viz, state) reads all sizing through adapter tokens. CDN/no-build: inline `tailwind/quantyfin.components.css`. *Formerly `foundation/*.css` — retired into this layer.*
- **UI kits** in `ui_kits/quantyFin-{app,fashion,ai,collab}/*.css` compose primitives into domain-specific patterns.

Always set `data-surface` on `<body>` or container. Component CSS **never** hard-codes scale.

---

## Four surface archetypes

| Surface | Use for | Body | Motion | Accent budget |
|---|---|---|---|---|
| **Marketing** | quantyfin.vn landing, careers, brand story, campaign | 19px / 1.6 | rich (scroll-reveal OK) | bold |
| **Application** | Back-office, dashboards, vendor portal, internal mobile/tablet | **13.5px / 1.5** | instant (state-only) | signal only |
| **Portal** *(default)* | Executive briefings, reports, internal microsites | 19px / 1.7 | 1 ambient/page | narrative (1 gold/page) |
| **Store** | POS terminals, signage, fitting-room tablet | 17px / 1.45 | none on POS, ambient-loop signage | high-contrast |

If unsure which surface, ask the user.

---

## Workflow

When the user invokes this skill without clear context, ask:
1. Which surface archetype?
2. Vietnamese or English copy?
3. If it's app: which module / what density / list or detail view?
4. Does the artifact need to print or run on touch?

For visual artifacts (slides, mocks, throwaway prototypes), create static HTML files that drop in `colors_and_type.css` + relevant kits. For production code, lift token names (not hex values) and follow the adapter pattern.

---

## Quick anchors

- Base = `colors_and_type.css` (tokens) + the Tailwind component layer. **No-build CDN:** load Tailwind v4 browser script + inline `tailwind/quantyfin.components.css`. **Build (Vite/PostCSS):** `@import "tailwind/globals.css"` (canonical theme) then `tailwind/quantyfin.tailwind.css`. Then add the kits you need.
- Utilities come in two flavours (both valid): **semantic roles** (`bg-primary`, `text-muted-foreground`, `bg-card`, `border-border`, `bg-chart-1`) and **quantyFin-named** (`bg-brand`, `text-fg-2`, `bg-mist`). Type scale is tokenized — use `text-h1/text-body/text-eyebrow`, never arbitrary `text-[Npx]`.
- Set `data-surface="..."` on `<body>` to pick the surface scale.
- **Brand navy `#2a2b86`** is the workhorse. **Gold `#fcaf16`** is decoration only — never text or buttons (contrast fails on white).
- Body font is **Be Vietnam Pro**. Numerals/heroes use **Montserrat** (portal/marketing) or **Be Vietnam Pro** (app — keeps admin density). Tags + technical metadata use **JetBrains Mono**. Playfair italic appears only on the portal surface, once per page.
- Status pills are `LIVE / BUILD / GAP / PLAN` — uppercase mono pill, never emoji. An extended lifecycle set (`DRAFT / REVIEW / PROTO / FIT / PP / APPROVED / SHIPPED / REJECTED / ARCHIVED`) ships in the **fashion kit (scoped)**, not the foundation.
- Drill-down on portal = right slide-in drawer. On app = drawer or modal, sized per density.
- AI affordances always use **iris tone + ✦ sparkle**; mark AI-filled fields with `.ai-halo`; show confidence chip (high/med/low + %); include disclosure footnote for compliance.
- Multiplayer surfaces use `.comment-thread`, `.annot-pin` on images, `.approval-card`/`.approval-stack`, `.activity-feed`, role badges.

---

## Don't

- Don't apply portal's narrative discipline (Roman numerals, Playfair italic, claim→evidence) outside the portal surface — they are scoped, not universal. See the **Narrative** section in `DESIGN.md`.
- Don't introduce new hex colors. Compose from `--brand / --iris / --gold / --mint / --rose / --gap` + tint/deep variants.
- Don't use emoji. Use status pills, icons (Lucide), or named avatars.
- Don't translate generic technical terms (KPI, ROI, SKU, API). Any domain glossary belongs to the relevant scoped kit, not the foundation.
- Don't hard-code font-size in component CSS — read `var(--type-*)` through the adapter.
