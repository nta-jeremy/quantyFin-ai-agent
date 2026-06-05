# QuantyFin Design System — DESIGN.md

> Canonical reference for the QuantyFin design system: brand, tokens, architecture, the four surfaces, principles, the Tailwind v4 layer, the component library, and how to consume it in a real repo.
>
> Companion docs (only three in this repo): **`CLAUDE.md`** (how to work in this repo + project state) · **`DESIGN.md`** (this file) · **`SKILL.md`** (the invocable agent skill).

---

> Brand identity + production-ready component library for **QuantyFin**, a Vietnamese fashion retail brand.
>
> Supports four surface archetypes from one foundation: **marketing landing**, **internal application** (back-office, dashboards, internal mobile), **executive briefing / report portal**, and **in-store / POS / signage**.

**Aesthetic:** chuẩn brand identity, art-modern, minimal, hightech, AI-native, VN-first (Be Vietnam Pro + JetBrains Mono).

**Stack:** Tailwind v4, shadcn-standard — semantic role tokens + a tokenized type scale, an `@apply` component layer, and an open-code React + Radix registry. QuantyFin brand tokens stay available alongside the shadcn roles.

---

## Quick start

```html
<!doctype html>
<html lang="vi">
<head>
  <!-- 1 · Tokens (source of truth: :root + 4 surface adapters) -->
  <link rel="stylesheet" href="colors_and_type.css" />

  <!-- 2 · Tailwind v4 + DS component layer.
       CDN / no-build → inline the bundle (browser build only compiles inline):
         paste the contents of tailwind/quantyfin.components.css inside the style block below.
       Production build (Vite/PostCSS) → use tailwind/quantyfin.tailwind.css as the entry instead. -->
  <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
  <style type="text/tailwindcss">/* … paste tailwind/quantyfin.components.css here … */</style>

  <!-- 3 · Add the composite kits you need (token-driven CSS modules) -->
  <link rel="stylesheet" href="ui_kits/quantyFin-app/index.css" />
  <link rel="stylesheet" href="ui_kits/quantyFin-fashion/index.css" />
  <link rel="stylesheet" href="ui_kits/quantyFin-ai/index.css" />
  <link rel="stylesheet" href="ui_kits/quantyFin-collab/index.css" />
</head>
<body data-surface="app">
  <!-- Surface contract: scale, density, motion, color budget
       resolve from [data-surface]. Set it on <body> or a container.
       Values: portal (default) | marketing | app | store -->
</body>
</html>
```

---

## Architecture — 3 layers

| Layer | What | Surface-aware? |
|---|---|---|
| **I · Foundation** | `:root` — brand color, accent semantics, status palette, font families, easings, a11y floor | No, universal |
| **II · Surface adapters** | `[data-surface="..."]` — type scale, gutter, row height, motion budget, color frequency | **Yes — 4 adapters** |
| **III · UI kits** | `ui_kits/quantyFin-{app, fashion, ai, collab}/*.css` — composite components | Consumes adapter tokens |

The portal/briefing surface is the default — omit `data-surface` and you get portal scale.

---

## Surfaces — quick reference

| Surface | When | Body | Hero | Container | Motion | Accent |
|---|---|---|---|---|---|---|
| **Marketing** | quantyfin.vn landing, careers, brand story, campaign | 19px / 1.6 | 88–120px | 1200px | rich (scroll-reveal OK) | bold |
| **App** | Back-office, dashboards, vendor portal, internal mobile | **13.5px / 1.5** | h1 28px | 100% fluid | instant (state-only) | signal |
| **Portal** *(default)* | Executive briefings, reports, internal microsites | 19px / 1.7 | 80–120px | 1280px | 1 ambient/page | narrative |
| **Store** | POS terminals, signage, fitting-room tablet (v3.1) | 17px / 1.45 | signage 96–160px | variable | ambient-loop / none | high-contrast |

---

## File map

```
components.json               shadcn config — css entry (tailwind/globals.css), cssVariables, baseColor, iconLibrary
registry.json                 DS manifest — theme + components + 4 kits (introspectable / AI-ready, shadcn registry shape)
REGISTRY.md                   Install workflow — npx shadcn add (QuantyFin items by url/@quantyfin namespace + upstream auto-branded)
public/r/                     Built registry — one installable JSON per item (registry-item schema, file contents inlined)
colors_and_type.css           Tokens + 4 surface adapters (single source of truth)
tailwind/                     Tailwind v4 bridge (shadcn-standard)
├── globals.css               CANONICAL theme — shadcn shape: :root role aliases + .dark + @theme inline + @layer base
├── quantyfin.tailwind.css         Build entry: @import "tailwindcss" + @theme roles + type scale + @apply component layer
├── quantyfin.components.css       No-Preflight bundle (theme + utilities + @apply components + typography) — inline this in CDN/no-build
├── quantyfin.theme.css            Tokens-only theme bridge (utilities, no component layer)
└── README.md                 How the bridge works + caveats
                              Component layer (@apply, formerly foundation/*.css):
                              buttons · typography · forms · overlays · identity · data-viz · state

ui_kits/                      Composite components (load on demand)
├── quantyFin-app/                 Shell · top-bar · side-rail · data-table · filter · cmd-K · charts  [CORE · generic]
├── quantyFin-ai/                  Prompt · halo · confidence · diff · disclosure                       [CORE · generic]
├── quantyFin-collab/              Comment · annotation · approval · activity · presence                [CORE · generic]
└── quantyFin-fashion/             Swatch · BOM table · size matrix · style card · tech-pack A4         [SCOPED · fashion domain]

registry/                     React component source (Tier 3 · open-code, shadcn-installable via registry.json)
├── lib/utils.ts              cn() — clsx + tailwind-merge
└── ui/                       button · badge · input · label · card · switch · dialog · tabs (.tsx) — CVA + Radix, quantyFin-branded via role tokens

preview/                      Living docs — IA mirrors shadcn (Foundations · Components · Brand).
                              Every specimen carries an `@dsCard group="…"` tag on line 1.
├── foundations/             Theming & tokens
│   ├── colors.html · colors-light-hightech.html                                                  [Colors]
│   ├── typography.html · type-{body,brand,display,kpi,mix,mono}.html                             [Type]
│   └── spacing.html · radii.html · elevation.html · motion.html                                  [Spacing]
├── components/              One specimen per component family
│   ├── buttons · forms · overlays · identity · data-viz · state · header · iconography · kpi-cards · react · react-radix [Components]
│   └── kits/                Composite kit specimens (app-*, ai-*, collab-*, fashion-*)            [Components]
└── brand/                   logo-lockups.html                                                    [Brand]

examples/                     NOT design system — products that CONSUME it. Excluded from the DS.
├── itdx-portal/              Hi-fi recreation of the live EA portal (a product, not a kit)
├── plm-screens/              18 PLM application screens (product mockups, 1-to-1 with 13 modules)
└── portal-specimens/         EA/TOGAF domain cards + badges (product specimens, not DS primitives)
```

---

## Scope classification

> What is the design system, what is scoped, and what only *consumes* the system.

### 🟢 Core — the design system (keep)
- `colors_and_type.css` — `:root` tokens + 4 surface adapters
- `tailwind/quantyfin.tailwind.css` (+ `quantyfin.components.css` / `quantyfin.theme.css`) — Tailwind v4 layer: semantic role tokens + type scale + `@apply` component layer (buttons, typography, forms, overlays, identity, data-viz, state — formerly `foundation/*.css`)
- `ui_kits/quantyFin-app` · `quantyFin-ai` · `quantyFin-collab` — generic, cross-product kits
- `fonts/` (Be Vietnam Pro) · `assets/quantyFin-logo.png`
- Docs: `README` · `PRINCIPLES` · `CHANGELOG` · `SKILL`
- Living docs: `preview/foundations/` · `preview/components/` (+ `components/kits/`) · `preview/brand/` — each tagged with `@dsCard group`

### 🟡 Scoped — in the system, but NOT universal (keep + label)
- Portal-only components (milestone card, insight, roman numerals, stakeholder ribbon) — see the **Narrative** section
- `ui_kits/quantyFin-fashion/` — fashion **domain** kit (specimen: `preview/components/kits/fashion-atoms.html`)
- `preview/components/kpi-cards.html` · `preview/foundations/colors-light-hightech.html` (portal-flavored, brand-neutral)

### 🔴 Out of scope — relocated or removed
- `examples/itdx-portal/` — recreation of a real product (was `ui_kits/itdx-portal/`)
- `examples/plm-screens/` — PLM product mockups (was `preview/screens/`)
- `examples/portal-specimens/` — EA/TOGAF domain cards + badges (product specimens, not DS primitives)
m the foundation docs. Business strategy (targets, financials, roadmaps) lives in a separate strategy repo, never here.

---


## Content discipline (universal)

- **Vietnamese UI labels + English tech terms.** Default Vietnamese for human copy. Never translate generic technical terms (KPI, ROI, SKU, API). Any domain-specific glossary belongs to the relevant scoped kit, not the foundation.
- **No emoji** — never. Status uses tag pills, not 🟢🔴.
- **Sentence case** for headings and buttons.
- **No exclamation marks**, no marketing fluff.
- **Numbers + named owners** are the unit of trust (e.g. "65% hoàn thành", "@owner approved") — use placeholder copy in the DS, real content only in consuming pages.
- **Insight before data** in portal surface — every section ends with a `Kết luận` italic Playfair callout. App/marketing/store don't follow this rule (see the Narrative section below).

## Color cheat sheet

| Token | Hex | Use |
|---|---|---|
| `--brand` | `#2a2b86` | Primary CTA, active nav, headline emphasis, BUILD status |
| `--iris` | `#7c6cf5` | **AI/tech default**, 90% of accent surface, info banners |
| `--gold` | `#fcaf16` | Decoration only — logo, climax moments. **Never text/buttons** (3:1 contrast fails) |
| `--mint` | `#10b981` | Growth, LIVE status, approval, success |
| `--rose` | `#f472b6` | Human/social, REVIEW |
| `--gap` | `#ef4444` | **Alert only** — destructive, REJECTED |

## Typography stack

| Family | Use |
|---|---|
| **Be Vietnam Pro** | Body, brand chrome, app headings. VN-first diacritic support |
| **Montserrat** | Marketing/portal hero, impact display, numerals (portal/marketing only — app uses BVP) |
| **JetBrains Mono** | Status pills, SKU codes, technical metadata, KBD hints |
| **Playfair Display Italic** | Hero accents — **portal surface only** (1 art moment / page) |

---

## Iconography

Primary set: **Lucide** (CDN UMD: `https://unpkg.com/lucide@latest/dist/umd/lucide.js`).
- Monoline, 1.75px stroke, 24×24 viewBox
- Sizes: 14 / 16 / 20 / 24px · `currentColor`
- Status icons take status token color · **never gold** for icons

---

## Asset sources

- **Logo:** `assets/quantyFin-logo.png`
- **Fonts:** self-hosted Be Vietnam Pro in `fonts/`; Montserrat / JetBrains Mono / Playfair via Google Fonts CDN

---

## Versioning

SemVer per artefact. Foundation major bump cascades major to all kits. Foundation minor → kits bump patch if affected. Token changes touching `:root` or adapter blocks are foundation; component-only changes are kit-local. Products that consume the system (e.g. anything under `examples/`) are versioned in their own repos, not here.

---

# Consuming the design system in a real repo

This makes the QuantyFin DS a **shadcn-compatible registry**: components install with
`npx shadcn add …`, and the theme tokens make upstream shadcn components drop in
quantyFin-branded.

> ⚠️ The shadcn CLI is a Node tool — it runs in a **real React repo's terminal**,
> not in this HTML preview. The files here (`public/r/*.json`, `components.json`,
> `registry.json`, `registry/`) are everything the CLI needs; verify the `add`
> commands in an actual project.

---

## What's here

```
registry.json            Source manifest (15 items: theme · components · 4 kits · 8 UI · utils)
registry/                Component SOURCE (open-code .tsx + lib/utils.ts)
public/r/{name}.json     BUILT registry — one installable file per item, file contents inlined
public/r/registry.json   Served index
components.json          shadcn config (css → globals.css, tsx, aliases, @quantyfin namespace)
```

Each `public/r/{name}.json` follows the **registry-item schema**: `name`, `type`,
`dependencies` (npm), `registryDependencies` (other items), `files[].content`
(inlined source), and — for `theme` — `cssVars` (light + dark role values).

---

## Build the registry

Regenerate `public/r/*.json` from `registry.json` + source whenever a component changes:
inline each item's file contents into its `public/r/{name}.json`. (In this project the
build was run via script; in a real repo use `shadcn build` or your own generator.)

---

## Install — three flows

### 1 · QuantyFin components, by URL
Serve `public/r/` at any static host, then:
```bash
npx shadcn@latest add https://YOUR_HOST/r/button.json
npx shadcn@latest add https://YOUR_HOST/r/dialog.json   # pulls @radix-ui/react-dialog + lucide-react, and theme/utils via registryDependencies
```

### 2 · QuantyFin components, by namespace
With the `@quantyfin` entry in `components.json` `registries`:
```bash
npx shadcn@latest add @quantyfin/button @quantyfin/card @quantyfin/tabs
```

### 3 · Upstream shadcn components — auto-branded
You do **not** need to author Select / Popover / Dropdown / Accordion / Tooltip / Sonner…
Pull them from the official registry; because `tailwind/globals.css` defines the role
tokens, they render quantyFin-branded (navy primary, iris ring, `--radius`) with no edits:
```bash
npx shadcn@latest add select popover dropdown-menu accordion tooltip sonner
```
Open-code edit afterwards only if you want QuantyFin specifics (pill radius, gold/status variants),
exactly as `registry/ui/button.tsx` customizes the stock button.

---

## Setup in a fresh React app (one-time)

```bash
npm create vite@latest my-app -- --template react-ts
cd my-app && npm i tailwindcss @tailwindcss/vite
# copy tailwind/globals.css (+ colors_and_type.css) in, import globals.css in main.tsx
npx shadcn@latest init        # pick the existing components.json
npx shadcn@latest add @quantyfin/button   # or a URL, or upstream names
```

The theme is the single source of brand: swap nothing in components, just keep
`globals.css` loaded.

---

# Tailwind v4 bridge

Chuyển DS sang Tailwind **mà không đổi source of truth**. CSS variables trong
`colors_and_type.css` (`:root` + 4 surface adapter) vẫn là nguồn duy nhất; Tailwind
chỉ là lớp framework đọc qua chúng.

## Cách hoạt động

`quantyfin.tailwind.css` gồm 3 phần:

1. `@import "tailwindcss";` — **bắt buộc là dòng đầu tiên** (CSS spec). Không đặt comment trước nó.
2. `@theme inline { … }` — map mỗi DS var thành Tailwind theme token. Vì là `inline`,
   utility tham chiếu thẳng `var(--…)` nên override theo `[data-surface]` vẫn chảy qua tự động.
   Sinh ra utilities: `bg-brand`, `text-fg-2`, `border-line`, `bg-paper/mist/lavender/ink`,
   `rounded-lg`, `shadow-sm`, `font-sans/brand/display/serif/mono`, …
3. `@layer components { … }` — class semantic (`.btn` + variants) viết lại bằng `@apply` +
   token. Markup giữ nguyên class cũ.

## Nạp trong specimen (no-build CDN)

```html
<link rel="stylesheet" href="colors_and_type.css" />              <!-- 1 · DS vars (bắt buộc) -->
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>  <!-- 2 -->
<style type="text/tailwindcss"> …nội dung quantyfin.tailwind.css… </style>        <!-- 3 -->
```

**Vì sao inline?** Browser build compile **một lần** từ nội dung trong `<style type="text/tailwindcss">`.
- Không fetch được external `@import` (file rời) → phải inline.
- Inject 2 pha (fetch rồi append) làm `@apply` trong `@layer components` không resolve.
- Inline đủ trong 1 pass → `@apply` + theme chạy đúng.

Mẫu tham chiếu: `preview/_tailwind/buttons.html` (component layer) · `preview/_tailwind/colors.html` (token→utility).

## Production build (có PostCSS/Vite)

Dùng thẳng `quantyfin.tailwind.css` làm entry — `@import "tailwindcss"` + `@theme` + `@apply`
chạy native, không cần inline. Đảm bảo `colors_and_type.css` được nạp để var resolve.

## ⚠️ Lưu ý cho roll-out toàn bộ

- **Layer order:** rule base unlayered trong `colors_and_type.css` (vd `html,body{background:var(--bg)}`)
  **đè** utility-layer của Tailwind → `bg-mist` trên `<body>` không thắng. Đã thử gói base vào
  `@layer base` nhưng trong **browser CDN** nó merge/đụng thứ tự với Preflight → body mất nền.
  → **CDN:** set nền `<body>` bằng token trực tiếp (`style="background:var(--bg-2)"`); utility hoạt động
  bình thường trên mọi element khác (div/section…) vì không có rule unlayered cạnh tranh.
  → **Production build (PostCSS/Vite):** kiểm soát được layer order, lúc đó mới gói base reset vào
  `@layer base` để `bg-*` thắng trên cả `<body>`.
- `foundation/*.css` đã **retired** (v3.7) — component layer giờ sống trong `@apply` (`quantyfin.tailwind.css` / inline `quantyfin.components.css`). Specimen + examples không còn `<link foundation/index.css>`.

## Canonical theme — `globals.css` (shadcn shape)

`tailwind/globals.css` là file theme **canonical** theo đúng shape shadcn/ui:
- `:root` — **role layer**: semantic tokens (`--background`, `--foreground`, `--card`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--input`, `--ring`, `--chart-1..5`, `--sidebar*`, `--radius`) **alias lên token QuantyFin** (`colors_and_type.css` vẫn là nguồn giá trị thô).
- `.dark` — override cùng bộ role token (opt-in qua class `.dark`; QuantyFin mặc định light).
- `@theme inline` — map role → utility (`bg-background`, `text-muted-foreground`, `border-border`, `ring-ring`, `bg-chart-1`, `bg-sidebar`…) + brand palette + fonts + radius scale (sm/md/lg/xl explicit QuantyFin, 2xl/3xl/4xl = `calc(var(--radius)*…)`) + type scale.
- `@layer base` — `* { @apply border-border outline-ring/50 }` + `body { @apply bg-background text-foreground }`.

**Quan hệ file:** `globals.css` = nguồn theme chuẩn (build mode: Vite/PostCSS import được). CDN no-build không `@import` file rời được → bản mirror đã inline nằm trong `quantyfin.components.css` (giữ đồng bộ với globals.css). **Dark mode chỉ chạy ở build-mode/globals** (CDN bundle hiện không kèm `.dark`).

## Trạng thái

- ✅ **Theme parity shadcn** (Tier 1): `globals.css` canonical · role tokens đầy đủ (+ chart-1..5, sidebar*, radius scale) · `@layer base` · `.dark` (opt-in).
- ✅ Bridge Tailwind v4: `quantyfin.tailwind.css` (full component layer) + `quantyfin.theme.css` (tokens-only, no-Preflight).
- ✅ Tailwind enabled trên **toàn bộ** specimen (Foundations · Components · Kits).
- ✅ Component layer `@apply` đầy đủ cho foundation: **buttons · forms · identity · state · overlays · data-viz**.
- ✅ Flagships: `preview/_tailwind/` — buttons · forms · identity · colors.
- ◻ Kits (`quantyFin-app/ai/collab/fashion`) giữ dạng CSS module token-driven, đã Tailwind-enabled — không port composite sang @apply (đã token-driven, không lợi ích thêm).

---

# Principles — universal (all surfaces)

> **Universal design principles** that apply across all four surface archetypes (marketing · application · portal · store).
>

---

## 0 · How to read this

Each principle has:
- **Rule** — what the principle enforces.
- **Applies to** — `marketing | app | portal | store` (or `all`).
- **Why** — the reason it survives across surfaces.
- **Operationalisation** — how a component or token enforces it.

These are the principles that hold no matter which surface you're building. Break one and the brand cohesion fractures.

---

## I · 4–5 sub-blocks max per section

| | |
|---|---|
| **Rule** | Any section, card, or block group caps at 5 children. Exceed → split into a new section. |
| **Applies to** | All surfaces. |
| **Why** | Cognitive load discipline. A scrolled-past hero, a dashboard widget, a POS checkout, a roadmap row — humans miscount beyond 5. |
| **Operationalisation** | Reviewer convention. No token enforces this. When you see a 6-item list, the answer is *taxonomy*, not *typography*. |

---

## III · 2 accents max per section

| | |
|---|---|
| **Rule** | A single section uses ≤ 2 of `{iris, gold, mint, rose}`. Rainbows kill hierarchy. |
| **Applies to** | All surfaces — **but the budget shifts by surface**: marketing can be bold (`--accent-freq: bold` allows full-bleed brand sections), app must be restrained (`--accent-freq: signal` permits accent only as status). |
| **Why** | Accent = semantic load. Two accents force the eye to pair them; three or more flatten into noise. |
| **Operationalisation** | `--accent-freq` token per surface adapter declares the allowance (`narrative | bold | signal | high-contrast`). Pair this with **content review**, not CSS. |

---

## IX · Cross-page / cross-screen consistency

| | |
|---|---|
| **Rule** | Anything used twice must become a component, not a one-off. Year card in portal hero = year card in roadmap. Form input in PLM = form input in vendor portal. |
| **Applies to** | All surfaces — **especially** at the boundary where two kits meet (e.g. app kit's CTA button and marketing kit's CTA button share the same `--brand` anchor and `cubic-bezier(.4, 0, .2, 1)` easing). |
| **Why** | Foundation cohesion is what holds the four surfaces together as ONE brand instead of four disconnected products. |
| **Operationalisation** | Foundation tokens (color, font family, easings, focus ring) live in `:root` and **must not** be overridden by surface adapters or kits. Only *scale* tokens (type-body, gutter, motion-budget, accent-freq) vary by surface. |

---

## X · Accessibility floor

| | |
|---|---|
| **Rule** | Every interactive element has a visible focus ring (`var(--focus-ring)`). Every tap target ≥ `var(--tap-min)` (44px default · 56px store · 72px primary CTA in store). `prefers-reduced-motion: reduce` disables every animation. |
| **Applies to** | All surfaces. |
| **Why** | Non-negotiable. WCAG AA on portal · WCAG AA on app · *touch-grade* on store. |
| **Operationalisation** | `--focus-ring`, `--tap-min`, `--focus-ring-gold`, `--focus-ring-gap` in `:root`. A `@media (prefers-reduced-motion: reduce)` global utility ships in the foundation reset. Marketing kit hero animations *must* be wrapped in the query. |

---

## XI · Surface contract

| | |
|---|---|
| **Rule** | Every non-portal artifact declares its surface with `data-surface="..."` on `<body>` (or a container). Omitting the attribute = portal scale by default. |
| **Applies to** | All surfaces. |
| **Why** | The adapter pattern only works if the surface is announced. Without the attribute, app screens accidentally use portal's 19px body and break density. |
| **Operationalisation** | Component implementations *never* hard-code type sizes or gutters. They read `var(--type-body)`, `var(--gutter)`, `var(--container-max)`, etc. — values that the adapter resolves. Lint rule: any component CSS with raw `px` font-size is a smell. |

---

## XII · Foundation immutability

| | |
|---|---|
| **Rule** | Foundation tokens (brand color, accent semantics, font families, easings, status palette) are *never* overridden by surface adapters or kits. Adapters add or refine scale tokens only. |
| **Applies to** | All surfaces. |
| **Why** | If `--brand` could be redefined per surface, brand cohesion collapses. The discipline that says "navy is `#2a2b86` everywhere" is what makes one system possible. |
| **Operationalisation** | Code review. Any PR touching `:root` brand/accent/status tokens triggers a DS guild review. Adapter PRs touch only scale tokens. |

---

## Decision flow when authoring a new component

1. **Identify the surface** — am I building for marketing, app, portal, or store?
2. **Read the adapter** — what does `var(--type-body)`, `var(--gutter)`, `var(--row-compact)` resolve to here?
3. **Use foundation directly** for color, family, status. Never re-define.
4. **Check Principle I (5-block max)** — am I cramming?
5. **Check Principle III (accent budget)** — what does this surface's `--accent-freq` allow?
6. **Check Principle X (a11y floor)** — focus ring, tap-min, reduce-motion respected?
7. **If portal surface** — also read the **Narrative** section below for the narrative discipline overlay.

---

---

# Narrative — portal surface only

> **Portal-only narrative discipline.** These principles apply ONLY when `data-surface="portal"` (or no surface attribute, since portal is the default). They define the *briefing voice* of the system — lean-back, projector-readable, claim-driven prose.
>
> Do NOT apply these to marketing landing pages, admin applications, or POS surfaces. Doing so will make those products feel like board decks.
>

---

## 0 · Scope

Portal surface = executive briefings, reports, internal microsites, annual report digital, the kind of artifact someone sits *with* on a 14″ laptop in a meeting and reads top-to-bottom. Long-scroll narrative. Reading speed: ~3–4 minutes per chapter.

These six principles together produce that voice. Strip them and the portal becomes generic. Apply them outside the portal and you ruin the application's velocity.

---

## II · Claim → evidence → conclusion

| | |
|---|---|
| **Rule** | Every section opens with a one-line *claim* (eyebrow + section title), supports it with data (KPI, chart, table, ribbon), and ends with an italic **Kết luận** callout. Never end on raw data. |
| **Why portal-only** | The shape mimics a board memo. Admin apps don't make claims — they expose state. Marketing pages don't conclude — they push to action. |
| **Operationalisation** | `.insight` component with gold left-spine, mono `Kết luận` label, italic Playfair accent inside the body. Mandatory per section. |
| **Example** | `01 · at a glance` → `Hiện trạng quantified` → 4 stat cards → **Kết luận:** Foundation pass — component layer fail. |

---

## IV · Roman numeral rhythm (I–V)

| | |
|---|---|
| **Rule** | Any list of ≤ 5 items uses Montserrat italic 800 Roman numerals (I, II, III, IV, V) as the ordinal. Per-tone color (iris default · gold climax · mint growth · rose human). |
| **Why portal-only** | Numerals create gravitas. They suit the "five reasons", "three pillars", "four stakeholders" rhythm of a briefing. They are wrong for a product card, a form field group, or a checkout step. |
| **Operationalisation** | `.roman` utility class + `.roman.iris/gold/mint/rose`. Sizes via `--type-roman` (clamp 64–96px). For inline lists in flowing prose, do **not** use them — only in numeral-prefixed list patterns (stakeholder ribbon, principle row, chapter heading). |
| **Anti-pattern** | Using II / III as bullets inside a body paragraph. They are heading-scale ordinals, not inline counters. |

---

## V · Timeline / milestone card DNA unified

| | |
|---|---|
| **Rule** | Whenever the portal references a point on a timeline (a year, a phase, a milestone), the card anatomy is identical: `[tc-year]` mono ordinal · `[tc-theme]` Be Vietnam Pro · `[tc-meta]` mono · `[tc-bignum]` Montserrat 800 gradient · `[tc-label]` Be Vietnam Pro tracked. |
| **Why portal-only** | A milestone card is a narrative atom for roadmap / briefing surfaces. It has no place in marketing or app surfaces. |
| **Operationalisation** | Anatomy in "Portal component anatomy" below. Tone is assigned by **position in the sequence**, not by hardcoded content — drive it from a per-card `--tone` variable: early/foundation steps → mint (growth) or iris (default); mid steps → rose / brand-light; final/climax step → gold. The mapping carries no business meaning. |
| **Discipline** | **Never bake a specific calendar year, target, or business goal into the component, the token layer, or this spec.** That content lives only in the page that consumes the card. The design system stays content-free. |

---

## VI · ≥19px body (projector legibility)

| | |
|---|---|
| **Rule** | Portal body text minimum is 19px / 1.7 line-height. Lede is 22–23px. Labels 14px floor. |
| **Why portal-only** | A 14″ laptop at arm's length needs ~14px; a 1080p projector at 3m needs ~19px. The portal is consumed in *both* modes, so we calibrate for the harder. App surface has the opposite problem — desk, 30 cm distance, 14.5px is comfortable. |
| **Operationalisation** | `--type-body: 400 19px/1.7 var(--font-body)` in `:root` (which is the portal default). The marketing and app adapters override this. |
| **Tension** | This is the principle most likely to be misapplied. Resist the impulse to scale every QuantyFin interface up. |

---

## VII · Insight callout per section

| | |
|---|---|
| **Rule** | Every portal section closes with an `.insight` block — gold left-spine, mono `Kết luận` label, italic Playfair accent. |
| **Why portal-only** | The italic Playfair is the system's *one art moment*. It works once-per-section in a narrative. It would feel out of place every 200px on a landing page or on every form field in an app. |
| **Operationalisation** | `.insight` + `.insight-label` + `.insight-body` in `colors_and_type.css`. The `<em>` inside `.insight-body` is Playfair italic 700 in `--iris` or `--gold-deep`. |
| **Discipline** | Insight ends a section, never opens one. The eye lands on the claim first, scans evidence, then earns the conclusion. |

---

## VIII · 1 ambient motion per page

| | |
|---|---|
| **Rule** | Pick ONE ambient animation per page: hero brush-line draw · hero chart pulse · milestone card hover lift. Never combine. |
| **Why portal-only** | The portal is read once, lean-back; one motion is delight. Marketing wants *rich* motion (scroll-reveal, parallax). App wants *zero* ambient — every animation must trigger from state. The budget differs by surface. |
| **Operationalisation** | `--motion-budget: ambient` is the portal default. Marketing uses `rich`, app uses `instant`, store uses `ambient-loop` (signage) or `none` (POS). All ambient motion respects `prefers-reduced-motion: reduce`. |

---

## Portal component anatomy

> These are the **portal-surface** composite patterns. All classes already live in `colors_and_type.css`; this section documents their anatomy.e of them carry business content — copy is always supplied by the consuming page.

### Section template (recurring rhythm)

```
[s-eyebrow]  mono 13px · 0.32em tracking · flanking dashes
[s-title]    Montserrat 800 · max-width ~920px · inline <em class="em-accent">
[s-sub]      body-lg lede · max-width ~720px
… content blocks (≤ 5, per Principle I) …
[insight]    gold-spine callout · "Kết luận" label · closes the section
```

### Insight callout — `.insight`
- `.insight-label` mono, 0.3em tracking, leading 18px dash.
- `.insight-body` 22px; the `<em>` is Playfair italic 700 in `--iris` or `--gold-deep`.
- 3px gold left-spine, inset 24px top/bottom. One per section, always closing (Principle VII).

### CTA system — `.cta`
- `.cta-primary` brand bg / white text / hover lift. One primary per section.
- `.cta-secondary` transparent / border / hover `--bg-muted`.
- `.cta-gold` gold bg / ink text — climax only.

### Milestone card — `.tc-*` (see Principle V)
- `[tc-year]` mono ordinal · `[tc-theme]` Be Vietnam Pro 700 · `[tc-meta]` mono · `[tc-bignum]` Montserrat 800 gradient · `[tc-label]` tracked.
- Tone via per-card `--tone` variable — assigned by sequence position, never by hardcoded year/target.

### Ordinal ribbon — `.ribbon` (lists of ≤ 5, see Principle IV)
- `--tone` / `--tone-tint` drive the whole row. 100px ordinal column (Montserrat italic 800 roman numeral), 4px left spine, optional seal circle.

### KPI card variants (pick by context)
- **A Aurora gradient** — flagship dashboard cards. **B Soft glass tint** — lighter, secondary.
- **C Mesh + sparkline** — data-led. **D Hero dark** — brand-anchor cover.
- **E Radial** — at-a-glance progress. **F Composition bar** — split metrics.
- Specimen: `preview/components/kpi-cards.html`.

### Status pills
- JetBrains Mono, uppercase, 0.6px tracking, pill. Foreground uses the `-deep` token variant for legibility.
- Generic lifecycle set is `LIVE / BUILD / GAP / PLAN`; domain lifecycle pills (e.g. fashion PLM) belong to the relevant scoped kit, not here.

---

## How to know if you're outside portal scope

If your artifact has any of the following, you are NOT building portal — go to PRINCIPLES.md instead:

- A data table with > 5 rows that the user will sort and edit
- A form with > 3 inputs the user will fill in to complete a task
- Real-time presence, comments, mentions
- A cart, checkout flow, or transaction completion CTA
- A POS keypad, scanner readout, or price display
- Touch interaction designed for a finger ≥ 56px tap target
- Animation that runs more than once per page on idle
- A search bar with autocomplete and faceted filters

Portal is *read*. Other surfaces are *operated*. Mix them up and the design system fractures.

---

---

# examples/ (consumers, not the DS)

> These are **products that consume** the QuantyFin Design System — applications and product mockups built *with* the foundation + kits. They are kept as reference implementations, but they are **out ofscope** for the design system itself.
>
> See the "Scope classification" section above.

## Contents

| Folder | What | Was at | Why it's not DS |
|---|---|---|---|
| `itdx-portal/` | Hi-fi recreation of the live ITDX EA portal (Next.js product). Header, KPI row, TOGAF domain grid, drill-down side panel. | `ui_kits/itdx-portal/` | Its own README calls it a *"consumer of foundation"*. It's an app built with the DS, not a kit of the DS. |
| `plm-screens/` | 18 PLM application screens (style detail, BOM editor, production dashboard, vendor portal, mobile companion…), mapped 1-to-1 with 13 PLM modules. | `preview/screens/` | Full product screens / reference implementations of the PLM app — they exercise the DS but are not DS components. |
| `portal-specimens/` | EA/TOGAF domain cards + badges (the briefing-portal domain grid). | `preview/portal/` | EA framing is product content; moved out so the design system itself carries zero TOGAF/EA references. |

## Paths still resolve

Both folders sit at depth 2 from repo root, same as their old locations, so the existing
`../../colors_and_type.css`, `../../tailwind/quantyfin.components.css`, `../../ui_kits/*` references are unchanged.
Open any file directly — no rewiring needed.

## If you extend these

Treat them like any other DS consumer: lift token *names* (not hex), set `data-surface`, and never
redefine foundation tokens. New product screens go here under `examples/`, never back into `preview/`
or `ui_kits/`.
