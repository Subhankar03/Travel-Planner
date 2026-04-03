---
page: copilot_layout
---
The main interactive "Copilot" layout for GlideTrip, which appears after the user
enters their first prompt on the landing page. It’s a clean, 2-column split interface.

**DESIGN SYSTEM (REQUIRED):**
Platform: Web, Desktop-first
Theme: Light, warm, energetic, modern with generous whitespace
Font: Inter (headings 600–700, body 400)

Background & Surfaces:
- Page Background: Warm Snow (#FFFCF9) — very subtle warm white
- Surface / Cards: Pure White (#FFFFFF) with soft warm shadow
- Surface Alt: Warm Ivory (#FFF7ED) — for hover states, subtle highlights
- Panel Divider: Soft Warm (#E7E5E4)

Primary Palette (Orange):
- Primary: Vibrant Tangerine (#F97316) — CTA buttons, brand accents, active states
- Primary Hover: Deep Orange (#EA580C)
- Primary Light: Pale Peach (#FFEDD5) — chip backgrounds, light fills
- Primary Subtle: Faint Peach (#FFF7ED) — hover backgrounds

Text:
- Text Primary: Charcoal (#1C1917) — headings, strong text
- Text Body: Dark Warm (#44403C) — paragraph text
- Text Secondary: Stone (#78716C) — captions, metadata
- Text Muted: Pebble (#A8A29E) — placeholders, timestamps

Semantic Colors:
- Price / Positive: Emerald (#22C55E)
- Star / Rating: Amber (#F59E0B)
- Flight Accent: Sky Blue (#3B82F6)
- Hotel Accent: Rose (#F43F5E)
- Places Accent: Teal (#14B8A6)

Shape:
- Buttons: Rounded (10px), medium shadow on hover
- Cards: Rounded (14px), 1px border (#E7E5E4), subtle drop shadow
- Badges / Pills: Fully rounded (999px)
- Input Fields: Rounded (12px), 1px border, light inner shadow on focus

**Page Structure:**
1. **Left Panel (45% width, Linear Chat):**
   - **Header:** Simple "GlideTrip" logo top left (Inter 700, 20px, Orange).
   - **Chat Feed (Scrollable):**
     - User Message: Align right, Primary (#F97316) background, White text, fully
       rounded pill shape (padding 12x20px).
     - AI "Research Process" Expander: Align left, Warm Ivory (#FFF7ED) background,
       Charcoal text. Looks like a small folder tab with a downward chevron, labeled
       "Planning 3 days in Goa...".
     - AI Message: Align left, Warm Snow (#FFFCF9) background (no bubble, just
       clean text directly on the page for an 'editorial' feel). Inter 400, 16px,
       Charcoal (#1C1917), 1.6 line height.
   - **Input Bar (Fixed Bottom):** Text area (rounded 12px, white bg, warm shadow)
     with an inset circular send button (Orange, white arrow).

2. **Divider (1px vertical line):**
   - Soft Warm (#E7E5E4) running full height to separate columns.

3. **Right Panel (55% width, Cumulative Results & Map):**
   - **Background:** White (#FFFFFF).
   - **Content Sections (Stacked vertically with anchor nav tabs at top):**
     - *Tabs (Sticky top):* "✈️ Flights" | "🏨 Hotels" | "📍 Places". Active tab
       has Orange text and bottom border.
     - *Flights Section:* Show 1 horizontal card. Left: airline logo placeholder.
       Middle: 09:00 DEL -> 11:30 GOI (IndiGo). Right: ₹5,400 (color: Emerald),
       "Book" button.
     - *Hotels Section:* Show 1 horizontal card. Left: hotel thumbnail (placeholder
       rounded square). Middle: "Taj Exotica Resort & Spa", 5-stars (Amber).
       Right: ₹18,000/night, "View" button.
   - **Map Area (Bottom 40% of right panel):**
     - A Leaflet map placeholder embedded nicely at the bottom.
     - Show 2-3 custom map markers:
       - Hotels: Rose (#F43F5E) circular marker with a little "H" or bed icon.
       - Places: Teal (#14B8A6) circular marker with "P" or star icon.
