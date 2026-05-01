# GlideTrip — Design System

> **Aesthetic Direction:** Expedition Dark — a cartographic, instrument-grade interface that treats trip planning like charting a course. Dark surfaces, warm singular accent, utilitarian typography, and data density that respects the traveller's time.

---

## 1. Design Philosophy

### Purpose & Audience
GlideTrip is a multi-agent AI travel copilot. Users converse with an AI on the left panel while real-time search results (flights, hotels, local places) populate the right panel. The interface must feel like a **command center for exploration** — authoritative, data-rich, but never cold.

### Aesthetic Tone
**Utilitarian luxury.** Think flight instrument panels crossed with a leather-bound atlas. Dark backgrounds keep the eye focused on content. A singular warm accent (Ember) provides all directional cues. No playfulness, no pastels — precision and warmth through restraint.

### Differentiation
The memorable detail: a **topographic contour noise texture** subtly layered across the background — just enough to evoke terrain maps without competing with content. Combined with the `Outfit` display face and `Geist Mono` for data, this creates an interface that looks nothing like a generic chatbot.

### Baseline Configuration (per design-taste-frontend)
| Parameter | Value | Rationale |
|---|---|---|
| DESIGN_VARIANCE | 8 | Asymmetric split layout, fractional grid, left-aligned hero |
| MOTION_INTENSITY | 6 | Fluid CSS transitions, staggered card reveals, spring easing |
| VISUAL_DENSITY | 4 | Standard app spacing — generous but not wasteful |

---

## 2. Color Palette

### Neutrals (Zinc base — warm-shifted)

| Token | Hex | Usage |
|---|---|---|
| `--bg-base` | `#18181B` | Page background (Zinc-900) |
| `--bg-elevated` | `#27272A` | Card surfaces, chat panel bg (Zinc-800) |
| `--bg-recessed` | `#09090B` | Recessed wells, input fields (Zinc-950) |
| `--bg-subtle` | `#3F3F46` | Hover states, active backgrounds (Zinc-700) |
| `--border-default` | `#3F3F46` | Default borders (Zinc-700) |
| `--border-subtle` | `#27272A` | Faint separators (Zinc-800) |

### Accent — Ember (singular, desaturated orange)

| Token | Hex | Usage |
|---|---|---|
| `--accent` | `#E8793A` | CTA buttons, active indicators, brand mark |
| `--accent-hover` | `#D4692E` | Hover/pressed state |
| `--accent-muted` | `rgba(232,121,58,0.12)` | Chip backgrounds, subtle fills |
| `--accent-glow` | `rgba(232,121,58,0.08)` | Focus rings, input highlight |

### Text

| Token | Hex | Usage |
|---|---|---|
| `--text-primary` | `#FAFAFA` | Headings, strong labels (Zinc-50) |
| `--text-body` | `#A1A1AA` | Paragraph text, descriptions (Zinc-400) |
| `--text-secondary` | `#71717A` | Captions, metadata, timestamps (Zinc-500) |
| `--text-muted` | `#52525B` | Placeholders, disabled text (Zinc-600) |

### Semantic (category-coded, desaturated <80%)

| Token | Hex | Usage |
|---|---|---|
| `--sem-flight` | `#60A5FA` | Flight tab, flight card accent (Blue-400) |
| `--sem-hotel` | `#F472B6` | Hotel tab, hotel card accent (Pink-400) |
| `--sem-places` | `#34D399` | Places tab, place card accent (Emerald-400) |
| `--sem-directions` | `#A78BFA` | Directions/route accent (Violet-400) |
| `--sem-price` | `#4ADE80` | Price displays (Green-400) |
| `--sem-rating` | `#FBBF24` | Star ratings (Amber-400) |
| `--sem-error` | `#F87171` | Error states (Red-400) |

---

## 3. Typography

> Inter is **banned**. No serif fonts in this software UI.

### Font Stack

| Role | Family | Weight | Tracking | Loading |
|---|---|---|---|---|
| Display / H1 | **Outfit** | 600 | `tracking-tighter` | Google Fonts `wght@400;500;600;700` |
| Body / UI | **Geist** | 400-500 | `tracking-normal` | Self-hosted or Vercel `@vercel/font` |
| Data / Mono | **Geist Mono** | 400 | `tracking-tight` | Self-hosted or Vercel `@vercel/font` |

### Scale

| Element | Classes |
|---|---|
| Page title (Landing) | `text-4xl md:text-5xl font-semibold tracking-tighter leading-none` |
| Section header | `text-xl font-semibold tracking-tight` |
| Card title | `text-[15px] font-medium leading-snug` |
| Body text | `text-sm leading-relaxed` (14px) |
| Caption / metadata | `text-xs` (12px) |
| Data values (prices, times) | `font-mono text-sm tabular-nums` |

---

## 4. Shapes & Surfaces

### Border Radii

| Element | Radius |
|---|---|
| Page-level containers | `rounded-2xl` (16px) |
| Cards (flight, hotel, place) | `rounded-xl` (12px) |
| Buttons (primary CTA) | `rounded-[10px]` |
| Pills / Badges / Chips | `rounded-full` |
| Input fields | `rounded-xl` (12px) |
| User chat bubble | `rounded-2xl rounded-br-sm` |
| AI chat content | No bubble — flows as inline content |

### Shadows

| Usage | Value |
|---|---|
| Card rest | `shadow-[0_1px_3px_rgba(0,0,0,0.3)]` |
| Card hover | `shadow-[0_4px_16px_rgba(0,0,0,0.4)]` |
| Input focus | `ring-2 ring-accent-glow` (no box-shadow glow) |
| Elevated panels | `shadow-[0_8px_32px_rgba(0,0,0,0.5)]` |
| Glass refraction | `shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]` + `border border-white/[0.06]` |

### Surface Treatment

- **Background noise**: A fixed `::after` pseudo-element on `body` with a subtle SVG noise filter, `opacity: 0.03`, `pointer-events: none`, `z-50`. Creates the topographic texture without impacting scroll performance.
- **Glass panels** (Results panel header, input bar): `backdrop-blur-xl bg-bg-elevated/80` + glass refraction shadow. True frosted glass with inner refraction border per skill spec.

---

## 5. Layout Architecture

### Landing Hero (pre-chat)

```
+----------------------------------------------------------+
|  [Logo]                                          [dark]  | <- nav, left-aligned
|                                                          |
|                                                          |
|  GlideTrip                                               | <- left-aligned H1
|  One conversation.                                       |
|  Your entire trip planned.                               | <- subtitle, --text-body
|                                                          |
|  +----------------------------------- [->]-+             | <- input, rounded-xl
|  | Where are you headed?                    |             |
|  +------------------------------------------+             |
|                                                          |
|  [chip] Weekend getaway to Goa                           | <- prompt chips row
|  [chip] Budget Manali trip                               |
|  [chip] Explore Kochi cuisine                            |
|                                                          |
|  Flights . Hotels . Local Places . Directions            | <- capability badges
|                                                          |
|             Powered by Gemini . LangGraph . SerpAPI      | <- footer
+----------------------------------------------------------+
```

**Key rules:**
- Left-aligned content (ANTI-CENTER BIAS for DESIGN_VARIANCE 8)
- Content positioned at ~40% vertical center, pushed left with `pl-[8vw] md:pl-[12vw]`
- Prompt chips use `--accent-muted` background, `--text-primary` text
- No emojis — use Phosphor/Lucide icons for chip decorations
- `min-h-[100dvh]` (never `h-screen`)

### Copilot Layout (post-chat)

```
+-----------------------+-+-----------------------------+
|  [Logo] GlideTrip     | |  Flights (3)  Hotels  Places | <- tabs
|---------------------- | |-----------------------------+
|                       | |                             |
|  [user bubble]        | |  +- Flight Card ----------+ |
|                       | |  | AI 302  DEL -> BLR      | |
|  [research steps]     | |  | 07:15 -> 10:00  Rs4,830 | |
|  [ai markdown]        | |  +------------------------+ |
|                       | |                             |
|  [user bubble]        | |  +- Flight Card ----------+ |
|  [ai markdown]        | |  | 6E 891  DEL -> BLR      | |
|                       | |  | 11:40 -> 14:10  Rs3,210 | |
|                       | |  +------------------------+ |
|                       | |                             |
|                       | |                             |
|  +--------------[->]+ | |                             |
|  | Ask about trip... | | |      [Map placeholder]     |
|  +-------------------+ | |                             |
|         45%           |1|         55%                 |
+-----------------------+-+-----------------------------+
```

**Split ratio:** `45% / 1px divider / 55%`
- Chat panel: `w-full md:w-[45%]`, background `--bg-base`
- Divider: `w-px bg-border-default`, visible `md:` only
- Results panel: `hidden md:flex w-[55%]`, background `--bg-elevated`
- Mobile: chat full-width, results accessible via swipe or tab toggle

---

## 6. Component Specifications

### 6.1 Chat Panel

#### Header
- Logo icon (Lucide `Navigation` filled or custom SVG compass) + "GlideTrip" in `Outfit 600`, `--accent` color
- Sticky top, `bg-bg-base`

#### User Message Bubble
- `bg-accent text-white rounded-2xl rounded-br-sm`
- `px-5 py-3 text-[15px] max-w-[85%]`
- Right-aligned within chat feed
- `shadow-[0_2px_8px_rgba(232,121,58,0.2)]`

#### AI Message
- No bubble wrapper — content flows left-aligned
- Markdown rendered with `prose prose-invert` (dark mode prose)
- `prose-a:text-accent prose-headings:text-text-primary prose-headings:font-semibold`
- `max-w-none w-full text-[15px] leading-relaxed text-text-body`

#### Research Steps Expander
- Container: `rounded-xl border border-border-default bg-bg-recessed`
- Toggle header: icon (spinning `Loader2` during stream, `Search` after) + step summary
- Expanded list: each step has a `2px` dot indicator
  - Active step: `bg-accent animate-pulse`
  - Completed step: `bg-sem-places`
- Smooth height animation via CSS `grid-template-rows: 0fr -> 1fr` transition

#### Typing Indicator
- Three dots: `bg-accent/60 w-2 h-2 rounded-full animate-bounce` with staggered `animation-delay` (0ms, 150ms, 300ms)

#### Input Bar
- Positioned `absolute bottom-0` with gradient mask (`from-bg-base via-bg-base to-transparent`)
- `bg-bg-recessed border border-border-default rounded-xl`
- Focus: `border-accent ring-2 ring-accent-glow`
- Send button: `bg-accent rounded-[10px] w-9 h-9`
  - Disabled: `bg-bg-subtle opacity-50`
  - Active press: `scale-[0.96] -translate-y-[1px]` (tactile feedback)
  - Streaming: show `Loader2` icon with `animate-spin`
- `Enter` to send, `Shift+Enter` for newline

#### Error State
- `bg-sem-error/10 border border-sem-error/20 rounded-xl p-4`
- Red `AlertCircle` icon + error message in `text-sem-error text-sm font-medium`

### 6.2 Results Panel

#### Tab Bar
- Sticky top, `bg-bg-elevated/80 backdrop-blur-xl` (glass treatment)
- Glass refraction: `shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] border-b border-white/[0.06]`
- Three tabs: Flights / Hotels / Places
  - Each tab: icon (Lucide `PlaneTakeoff`, `Building2`, `MapPin`) + label + count
  - Active: `text-accent` + `2px` bottom border in `--accent`
  - Inactive: `text-text-secondary hover:text-text-primary`
  - Tab count uses `font-mono` for data values

#### Empty State
- Centered within content area
- Icon (`PlaneTakeoff` / `Building2` / `MapPin`) at `w-10 h-10 text-text-muted opacity-40`
- Text: "No flights found yet" in `text-text-secondary text-sm`
- Dashed border container: `border border-dashed border-border-default rounded-xl p-10`

#### Content Area
- `overflow-y-auto` with `px-6 py-5`
- Cards stacked with `gap-3`
- Staggered reveal on mount: CSS `animation-delay: calc(var(--index) * 80ms)` fade-slide-up

### 6.3 Flight Card

```
+----------------------------------------------------+
|  [airline logo]   DEL 07:15 --> BLR 10:00          |
|                   Air India . 2h 45m . Economy     |
|                                                    |
|                                 Rs4,830  [Select]  |
+----------------------------------------------------+
```

- `bg-bg-elevated border border-border-default rounded-xl p-4`
- Airline logo: `w-10 h-10 rounded-lg bg-bg-recessed` with airline initial fallback
- Route: `text-text-primary font-medium` with thin arrow SVG between airports
- Time/duration: `font-mono text-sm text-text-secondary tabular-nums`
- Price: `font-mono font-semibold text-sem-price`
- Select button: `bg-accent-muted text-accent text-sm rounded-[8px] hover:bg-accent hover:text-white`
- Hover: `shadow-[0_4px_16px_rgba(0,0,0,0.4)]` + `border-border-subtle -> border-accent/30`
- Left accent stripe: `4px` left border in `--sem-flight`

### 6.4 Hotel Card

```
+----------------------------------------------------+
|  +------+  The Oberoi, Bangalore                   |
|  | img  |  ***** 4.7 (2,148 reviews)               |
|  |      |  MG Road, Central Bangalore              |
|  +------+                                          |
|                               Rs8,450/night [Book] |
+----------------------------------------------------+
```

- Same card base as Flight
- Thumbnail: `w-20 h-20 rounded-lg object-cover` (use `thumbnail` from API data, fallback to `Building2` icon)
- Star rating: `text-sem-rating` filled star icons
- Review count: `font-mono text-xs text-text-secondary`
- Price: `font-mono font-semibold text-sem-price` + "/night" in `text-text-secondary`
- Left accent stripe: `4px` left border in `--sem-hotel`

### 6.5 Place Card

```
+----------------------------------------------------+
|  +------+  Vidyarthi Bhavan                        |
|  | img  |  * 4.6  .  Dosa restaurant               |
|  |      |  Gandhi Bazaar, Basavanagudi              |
|  +------+  "Iconic 80-year-old South Indian..."    |
+----------------------------------------------------+
```

- Same card base
- Thumbnail: `w-20 h-full rounded-l-xl object-cover` (flush left edge)
- Type badge: `bg-sem-places/10 text-sem-places text-[11px] rounded-full px-2 py-0.5`
- Description: `text-xs text-text-secondary line-clamp-2`
- Left accent stripe: `4px` left border in `--sem-places`

### 6.6 Map Area (Future)

- Bottom portion of results panel, `h-[35%] min-h-[280px]`
- `border-t border-border-default bg-bg-recessed`
- Placeholder: `MapPin` icon + "Map integration coming soon" in `text-text-muted`
- When implemented: Leaflet with dark tile layer (CartoDB Dark Matter or Stamen Toner)

---

## 7. Motion & Animation

### Transition Baseline (MOTION_INTENSITY = 6)
All interactive elements: `transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]`

### Specific Animations

| Element | Animation | Spec |
|---|---|---|
| Card hover | Shadow + border shift | `duration-300`, hardware-accelerated via `transform` |
| Card mount (results) | Fade + slide up | `opacity: 0->1, translateY: 8px->0`, staggered `80ms` per card |
| Tab underline | Width expansion | `scaleX(0) -> scaleX(1)` with `origin-left` |
| User bubble appear | Scale + fade | `scale(0.95) -> scale(1), opacity: 0->1`, `duration-200` |
| Steps expander | Grid rows | `grid-template-rows: 0fr->1fr`, `duration-300` |
| Input focus ring | Ring fade in | `ring-opacity: 0->1`, `duration-200` |
| Typing dots | Bounce cascade | `animation-delay` 0/150/300ms, `ease-in-out` |
| Landing to Copilot | Full page transition | Content fades out, copilot fades in, `duration-500` |
| Prompt chips hover | Subtle lift | `translateY(-1px)`, `duration-200` |
| Send button active | Tactile press | `scale(0.96) translateY(-1px)`, `duration-100` |

### Forbidden Motion
- No `window.addEventListener('scroll')` — use Intersection Observer if needed
- No animation on `top`, `left`, `width`, `height` — only `transform` and `opacity`
- No continuous/infinite background animations (except the typing dots during streaming)

---

## 8. Interaction States

### Loading — Skeleton Shimmer
When results are being fetched:
- Flight skeleton: `h-20 rounded-xl bg-bg-subtle animate-pulse` x 3, staggered
- Hotel skeleton: Same with `w-20 h-20` thumbnail placeholder
- Shimmer: `background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent)` sweeping left-to-right

### Empty States
Each tab has a distinct empty state:
- **Flights**: `PlaneTakeoff` icon + "No flights found yet. Ask me to search!"
- **Hotels**: `Building2` icon + "No hotels found yet. Ask me to search!"
- **Places**: `MapPin` icon + "No places explored yet."
- All use dashed border container, centered text, `text-text-secondary`

### Error States
- Chat error: Inline red banner below messages (described in 6.1)
- Results error: Replace card list with error message in same dashed container style but `border-sem-error/30`

### Streaming State
- Send button shows `Loader2` spinner
- Input is `disabled` with `opacity-60`
- Steps expander appears with pulsing dot
- AI content streams with blinking cursor (`2px` wide bar, `bg-accent`, `animation: blink 0.9s step-end infinite`)

---

## 9. Responsive Strategy

| Breakpoint | Layout |
|---|---|
| `< 768px` (mobile) | Chat full-width. Results hidden or accessible via bottom sheet / tab toggle. Single column, `px-4 py-6`. |
| `768px - 1024px` (tablet) | 45/55 split, reduced padding `px-4` |
| `> 1024px` (desktop) | Full 45/55 split, `px-6 lg:px-8` |

Mobile overrides:
- Landing hero: `pl-6` instead of `pl-[12vw]`, `text-3xl` instead of `text-5xl`
- Cards: full width, reduced padding `p-3`
- Input bar: `px-4`

---

## 10. Icon System

**Library:** `lucide-react` (already installed — verified in `package.json`)

> Note: Phosphor (`@phosphor-icons/react`) is preferred per the design-taste skill but is not currently installed. If migrating, run `npm install @phosphor-icons/react` first. For now, `lucide-react` is acceptable since it is already a dependency.

**Standardized stroke width:** `strokeWidth={1.5}` globally (thinner than default for premium feel)

**Key icon mappings:**
| Context | Icon |
|---|---|
| Brand logo | `Navigation` (filled) |
| Flights tab | `PlaneTakeoff` |
| Hotels tab | `Building2` |
| Places tab | `MapPin` |
| Send message | `Send` |
| Loading | `Loader2` (with `animate-spin`) |
| Research steps | `Search` (completed), `Loader2` (active) |
| Error | `AlertCircle` |
| Star rating | `Star` (filled) |
| Expand/collapse | `ChevronDown` / `ChevronUp` |
| Directions | `Route` |
| Close / dismiss | `X` |

---

## 11. Data Display Conventions

- **Prices**: Always `font-mono tabular-nums` — e.g. `Rs4,830` not `Rs4830`
- **Ratings**: Numeric with one decimal — `4.7` not `5`
- **Distances/Durations**: From API as-is — `2h 45m`, `12 km`
- **Dates**: `YYYY-MM-DD` in data, `Mon, 15 Jan` in display
- **Counts**: Tab labels show `(3)` next to category name, `font-mono`
- **No generic placeholder data**: When displaying mock data in dev, use realistic names (e.g. "Vidyarthi Bhavan" not "Restaurant 1")

---

## 12. Tailwind v4 Integration Notes

The project uses **Tailwind CSS v4** with the Vite plugin (`@tailwindcss/vite`).

- Custom colors should be registered as CSS custom properties in `index.css` using `@theme`
- The `tailwind.config.js` maps to the design tokens listed above
- Use `@theme` block for extending the default theme in v4
- Do **not** use `tailwindcss` in `postcss.config.js` — use `@tailwindcss/postcss` or Vite plugin (already configured)

---

## 13. Forbidden Patterns (Hard Rules)

Per the design-taste-frontend skill:

- **NO Inter font** — use Outfit / Geist / Geist Mono
- **NO emojis** in code, markup, or content — use icons
- **NO purple/blue AI gradients** — singular Ember accent only
- **NO `h-screen`** — use `min-h-[100dvh]`
- **NO pure black `#000000`** — darkest is Zinc-950 `#09090B`
- **NO neon/outer glows** — use inner borders and tinted shadows
- **NO 3-column equal card rows** — stack vertically or use asymmetric grid
- **NO Unsplash links** — use `https://picsum.photos/seed/{id}/W/H` or API thumbnails
- **NO generic placeholder names** — use realistic, context-appropriate data
- **NO `window.addEventListener('scroll')` — use Intersection Observer
- **NO animating `top/left/width/height`** — only `transform` and `opacity`
- **NO centered hero layouts** (DESIGN_VARIANCE = 8) — left-aligned
