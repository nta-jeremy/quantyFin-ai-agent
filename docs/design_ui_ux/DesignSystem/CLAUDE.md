# Working with the QuantyFin Design System

You are implementing UI with the **QuantyFin Design System** — a Tailwind v4, shadcn-standard
token foundation + component library for QuantyFin (Vietnamese fashion retail). One token
system serves four surfaces: **marketing · application · portal · store**.

Read **`DESIGN.md`** for the full reference; **`SKILL.md`** is the invocable skill. This file
is the short contract: follow it on every task.

## How to consume

- **React (Vite/Next + Tailwind v4):** load `colors_and_type.css` + `tailwind/globals.css`,
  then install components — `npx shadcn add @quantyfin/<name>` (QuantyFin components) or
  `npx shadcn add <name>` from the upstream shadcn registry (they render quantyFin-branded
  automatically because the theme defines the role tokens). Or copy `registry/ui/*.tsx`
  + `registry/lib/utils.ts`.
- **Non-React (server-rendered, plain HTML, Vue…):** load `colors_and_type.css` + the
  Tailwind layer (build: `tailwind/quantyfin.tailwind.css`; no-build CDN: inline
  `tailwind/quantyfin.components.css`), add `ui_kits/*` as needed, and use the semantic classes
  (`.btn`, `.tag`, `.field`, `.avatar`…) or role/utility classes directly.
- Mirror real product assembly from `preview/components/*` (specimens) and `examples/*`
  (full screens) — don't reinvent patterns the DS already ships.

## Non-negotiable rules

- **Set `data-surface`** (`marketing | app | portal | store`) on `<body>` or a container.
  Omitting it = portal scale. Components never hard-code type sizes or gutters — they read
  surface-resolved tokens.
- **Use tokens, never raw hex.** Brand via `bg-primary`/`bg-brand`, text via
  `text-foreground`/`text-muted-foreground`/`text-fg-2`, etc. Compose accents from
  `--brand · --iris · --gold · --mint · --rose · --gap` (+ tint/deep). Don't invent colors.
- **Type scale is tokenized** — use `text-h1 / text-body / text-eyebrow / text-label`, never
  arbitrary `text-[Npx]`.
- **Gold is decoration only** (logo, one climax moment per page). Never gold text or buttons.
- **No emoji.** Status = tag pills (`LIVE / BUILD / GAP / PLAN`), not 🟢🔴.
- **Sentence case**, no exclamation marks, no marketing fluff. VN-first copy; keep generic
  tech terms in English (KPI, ROI, SKU, API).
- **A11y floor:** visible focus ring, tap target ≥ 44px (56–72px on store),
  honor `prefers-reduced-motion`.
- **Light is default;** dark mode is opt-in via the `.dark` class (build mode).
- **Portal narrative discipline** (claim→evidence→`Kết luận`, Roman numerals, Playfair
  italic) applies ONLY to `data-surface="portal"`. Never on app/marketing/store.

## Where things live

- `colors_and_type.css` — tokens + 4 surface adapters (source of truth)
- `tailwind/globals.css` — canonical theme (role tokens, `.dark`, `@layer base`)
- `tailwind/quantyfin.tailwind.css` / `quantyfin.components.css` — `@apply` component layer
- `registry/ui/*.tsx` + `registry.json` + `public/r/` — React components + installable registry
- `ui_kits/quantyFin-{app,ai,collab,fashion}/` — composite blocks
- `preview/` — living specimens · `examples/` — products that consume the DS (reference only)

Keep brand cohesion: one token system, QuantyFin navy `#2a2b86` + the accent palette, four fonts
(Be Vietnam Pro · Montserrat · Playfair Display · JetBrains Mono). When unsure which surface
or pattern, check `DESIGN.md` or ask.
