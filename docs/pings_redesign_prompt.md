# P.I.N.G.S Core v2 — Complete UI Modernization Prompt

> Copy and paste this entire prompt to your AI coding agent to execute the redesign.

---

## Project Context

This is **P.I.N.G.S Core v2**, a React + Vite + TailwindCSS dashboard for a multi-agent AI system.

**Stack:**
- React 18 + React Router DOM
- Vite build tool
- TailwindCSS v3 with CSS custom properties for theming
- `web/src/index.css` — global design tokens and component classes
- `web/tailwind.config.js` — Tailwind theme extension
- `web/src/App.jsx` — root layout (sidebar + main content + mobile nav)
- `web/src/components/` — Sidebar, BootSequence, Toast, MobileNav, EmptyState, Spinner
- `web/src/pages/` — Chat, ResearchPage, MissionControl, Tasks, Calendar, Skills, HomeLab, History, Settings

**Current Design Problems (the "vibecoded" issues):**
1. The sidebar is a flat, featureless glass strip — no visual weight, no brand identity, no hierarchy differentiation between nav items
2. All page headers follow the same generic template: tiny gradient square icon + `font-brand` label. Zero page uniqueness.
3. Chat bubbles look like a basic SMS app. The user bubble has no personality; the agent bubble is just a dim, borderless rect.
4. The `EmptyState` and loading states are invisible — no visual delight, no animations that feel intentional.
5. The `BootSequence` is an unimpressive terminal-text box. It has potential to be cinematic.
6. MissionControl's circular gauges are technically correct but visually dull — no glow, no layered tracks, no label embellishment.
7. The Research page's mode selector buttons are borderless colored chips — they feel accidental, not intentional design.
8. `input-field` and `btn-primary` look indistinguishable from any 2019 dashboard kit.
9. No consistent spacing rhythm — cards float without relationship to their containers.
10. Typography is purely functional — no size contrast, no weight contrast, no visual hierarchy landmarks.
11. The `SidebarBrand` is just text. The brand logo (concentric circles SVG in BootSequence) is never reused.
12. No "alive" micro-interactions — nothing reacts to hover with depth, nothing expands with spring physics.

---

## What To Change: Full Specification

### 1. Design Token Layer (`web/src/index.css`)

Replace the current `:root` block with a richer token set that supports multiple visual dimensions:

```css
:root {
  /* Accent system */
  --accent-rgb: 108, 92, 231;
  --accent: rgb(var(--accent-rgb));
  --accent-light: #a29bfe;
  --accent-dark: #4834d4;
  --accent-glow: rgba(var(--accent-rgb), 0.18);
  --accent-subtle: rgba(var(--accent-rgb), 0.06);

  /* Backgrounds — 5 distinct layers */
  --bg-base: #07070a;          /* deepest — page canvas */
  --bg-elevated: #0e0e14;      /* sidebar, drawers */
  --bg-surface: #141420;       /* cards */
  --bg-overlay: #1c1c2c;       /* hover states, dropdowns */
  --bg-glass: rgba(14, 14, 20, 0.7); /* glass panels */

  /* Text — 4 levels */
  --text-primary: #ededf5;
  --text-secondary: #9b9bb8;
  --text-muted: #5c5c78;
  --text-inverse: #07070a;

  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.055);
  --border-medium: rgba(255, 255, 255, 0.10);
  --border-glow: rgba(var(--accent-rgb), 0.20);

  /* Shadows */
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 20px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 40px rgba(0, 0, 0, 0.5);
  --shadow-glow: 0 0 30px rgba(var(--accent-rgb), 0.15);

  /* Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-pill: 9999px;
}
```

Add a layered animated mesh background that includes a subtle noise texture overlay:

```css
.mesh-bg {
  background-color: var(--bg-base);
  background-image:
    radial-gradient(ellipse 90% 60% at 15% 15%, rgba(var(--accent-rgb), 0.07) 0%, transparent 65%),
    radial-gradient(ellipse 50% 50% at 85% 5%,  rgba(var(--accent-rgb), 0.04) 0%, transparent 55%),
    radial-gradient(ellipse 70% 80% at 55% 95%, rgba(var(--accent-rgb), 0.04) 0%, transparent 60%),
    radial-gradient(ellipse 40% 40% at 5%  80%,  rgba(var(--accent-rgb), 0.05) 0%, transparent 50%);
}
```

Upgrade the `.glass` hierarchy to three tiers with distinct blur + saturation levels:

```css
.glass        { background: rgba(14, 14, 20, 0.60); backdrop-filter: blur(12px) saturate(1.3); }
.glass-strong { background: rgba(14, 14, 20, 0.80); backdrop-filter: blur(20px) saturate(1.4); }
.glass-modal  { background: rgba(10, 10, 16, 0.92); backdrop-filter: blur(32px) saturate(1.5); }
```

All three should share:
```css
border: 1px solid var(--border-subtle);
```

Add a premium gradient-border class using `::before` mask trick (keep existing `.glass-glow-border` but make it brighter):
```css
.glass-glow-border::before {
  background: linear-gradient(
    135deg,
    rgba(var(--accent-rgb), 0.45),
    rgba(var(--accent-rgb), 0.08) 35%,
    transparent 65%,
    rgba(255, 255, 255, 0.06)
  );
}
```

Add a new `.card-hover` class for all interactive cards:
```css
.card-hover {
  transition: transform 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275),
              box-shadow 0.25s ease,
              border-color 0.25s ease;
}
.card-hover:hover {
  transform: translateY(-2px);
  border-color: rgba(var(--accent-rgb), 0.20);
  box-shadow: var(--shadow-lg), var(--shadow-glow);
}
```

Add a glowing `.btn-accent` that replaces the dull `.btn-primary`:
```css
.btn-accent {
  background: linear-gradient(135deg, var(--accent), var(--accent-dark));
  color: white;
  border: none;
  box-shadow: 0 4px 15px rgba(var(--accent-rgb), 0.3);
  transition: box-shadow 0.2s ease, transform 0.15s ease;
}
.btn-accent:hover {
  box-shadow: 0 6px 25px rgba(var(--accent-rgb), 0.45);
  transform: translateY(-1px);
}
.btn-accent:active {
  transform: translateY(0);
  box-shadow: 0 2px 10px rgba(var(--accent-rgb), 0.25);
}
```

Add a new `@keyframes scanline` and `@keyframes float` for micro-animations:
```css
@keyframes scanline {
  from { transform: translateY(-100%); }
  to   { transform: translateY(100vh); }
}
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50%       { transform: translateY(-4px); }
}
@keyframes gradientShift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

---

### 2. Sidebar (`web/src/components/Sidebar.jsx`)

The sidebar needs to feel like a **premium OS dock**, not a nav list. Changes:

**Brand section (`SidebarBrand`):**
- Reuse the concentric-circles SVG logo from `BootSequence.jsx` (the 4-ring radar icon). Make it 28×28px.
- Show `P.I.N.G.S` in `font-brand` next to it when expanded. Add a `text-glow` on hover.
- Add a bottom border separator line with a subtle gradient fade: `linear-gradient(to right, transparent, var(--border-medium), transparent)`.

**Nav items:**
- The active indicator (left pill) should be 4px wide, 20px tall, with `border-radius: 0 4px 4px 0`, and a `box-shadow: 0 0 12px var(--accent)`.
- Active links should have a right-to-left gradient background: `background: linear-gradient(to right, rgba(var(--accent-rgb), 0.15), transparent)`.
- Inactive items: on hover, the icon should gain a 1px accent-colored glow: `filter: drop-shadow(0 0 4px rgba(var(--accent-rgb), 0.5))`.
- When collapsed, show icon-only with a tooltip. The tooltip should appear as a small glass pill to the right.

**Bottom section:**
- `System Online` indicator: upgrade the pulsing dot to a 3-ring sonar animation (one inner solid dot + two outer rings that scale and fade — using `ping-ring` keyframe already defined).
- Add a subtle system status text that shows `v2.0` with monofont muted style.

**New Chat button:**
- Replace the plain rectangle button with a full-width gradient button that has a subtle shimmer animation on hover.
- When collapsed: show only a `+` icon centered, with a circular glow border.

---

### 3. Chat Page (`web/src/pages/Chat.jsx`)

**Header bar:**
- Replace the tiny gradient square with the full brand logo (concentric circles) at 32×32.
- Show the active agent name + model in a two-line format: `Chat / P.I.N.G.S` on line 1, `via MiMo V2.5` in muted monofont on line 2.
- Add a pulsing green dot with `ping-ring` animation to indicate live connection.

**User chat bubble (`.chat-bubble-user`):**
- Give it a proper gradient background: `linear-gradient(135deg, rgba(var(--accent-rgb), 0.25), rgba(var(--accent-rgb), 0.12))`.
- Add a right-side accent border: `border-right: 2px solid rgba(var(--accent-rgb), 0.5)`.
- Round all corners except bottom-right (already done, keep).
- Add `box-shadow: 0 2px 16px rgba(var(--accent-rgb), 0.12)`.

**Agent chat bubble (`.chat-bubble-agent`):**
- Add a very subtle top-left accent glow: `box-shadow: -2px -2px 0 rgba(var(--accent-rgb), 0.15), var(--shadow-sm)`.
- The agent avatar (the colored initial square) should be 32×32, `border-radius: 10px`, and float slightly above the bubble top edge with `margin-top: -4px`.
- Agent name label: `font-brand text-[11px] tracking-widest uppercase` with the agent's color.

**Thinking/loading bubble:**
- Replace the 3 bouncing dots with a more cinematic animation: a left-to-right shimmer wave effect across a blurred background strip.
- OR: 3 dots that wave in sequence with a `cubic-bezier(0.4, 0, 0.6, 1)` curve, colored with the accent.

**Input area:**
- Give the outer container a premium look: `glass-glow-border` class + inner padding of `p-3`.
- The textarea should have NO visible border of its own — the container provides the visual boundary.
- The send button: use `.btn-accent` style — gradient background, glowing shadow on hover, `active:scale-95`.
- The model selector button: style as a pill badge `bg-overlay border border-subtle text-muted` that glows on hover.
- File attachment button: on hover, the paperclip icon should gain accent color + `drop-shadow` glow.

**Agent @ mention menu:**
- Must slide up with spring physics (`cubic-bezier(0.34, 1.56, 0.64, 1)`).
- Each `AgentCard` gets a left-colored stripe (3px) matching the agent's color.
- Show an animated green pulse dot per agent (indicating online).
- Add a header section: `SELECT AGENT` in `text-[9px] tracking-widest uppercase text-muted font-mono`.

**Empty state:**
- Replace with a centered design: the concentric-circles logo floating with the `float` animation, a large `font-brand` headline, and 3 suggested prompt chips below.

---

### 4. Research Page (`web/src/pages/ResearchPage.jsx`)

**Search bar container:**
- Make it a `glass-glow-border` panel with `p-6` padding.
- The search input should be large: `text-base`, `h-12`, with a magnifying glass icon inset on the left.
- The Research button should use `.btn-accent` style with a search icon.

**Mode selector:**
- Replace the flat chip buttons with a proper **segmented control**: a row of buttons inside a rounded pill container with a sliding capsule background (like `CapsuleTabs` already implemented — reuse that pattern).
- Each mode should have a small colored dot to its left when active.

**Research queue items:**
- Show as a banner notification bar instead of plain card: left-colored accent stripe + rotating dots spinner + topic text + mode badge.

**Past Research list:**
- Each run card should be `card-hover` class.
- Add a visual distinction between runs with and without reports: runs WITH reports get a small `REPORT READY` badge with `status-pill-success` styling.
- The source count and date should be in a footer row using `·` as divider with muted text.

**Report reader panel:**
- Give it a `glass-glow-border` with a distinct header zone using `bg-overlay` background.
- `CapsuleTabs` (already good) — increase the active capsule opacity and glow strength.
- The discuss/ask input at the bottom: give it a distinct `bg-base` background to visually ground it.

---

### 5. Mission Control (`web/src/pages/MissionControl.jsx`)

**Circular Gauges (`CircularGauge` component):**
- Add an outer "track ring" circle in `rgba(255,255,255,0.04)`.
- Add a middle "scale markers" ring using a dashed stroke in `rgba(255,255,255,0.06)`.
- The fill stroke should have `filter: drop-shadow(0 0 8px currentColor)` for a glowing effect.
- Show the percentage value centered inside the SVG (not with CSS offset hacks) — use SVG `<text>` element.
- Below the gauge, show the label in `font-brand font-medium text-[11px] tracking-widest uppercase`.

**Metric card grid:**
- Each gauge card should be `card card-hover p-5` with a subtle gradient in the top half: `background: linear-gradient(to bottom, var(--bg-overlay), var(--bg-surface))`.
- Add a thin top-border line in the card's accent color for visual grouping.

**Agent list cards:**
- The agent avatar: increase to 44×44px, use a radial gradient background: `radial-gradient(circle at top left, {statusColor}30, {statusColor}08)`.
- Status dot: increase to 10×10px with a 2px white border and the `ping-ring` animation when active.
- Add a "Last active: X ago" time display using relative time (e.g., "3m ago" not a raw timestamp).

**Journal/Log feed:**
- Each log entry should have a left-border colored by event type (blue=chat, green=task, purple=research, red=error).
- Log filter badges should be `status-pill` styled, not bare text buttons.
- Add a "LIVE" badge at the top of the journal section that pulses green.

---

### 6. Boot Sequence (`web/src/components/BootSequence.jsx`)

Make the boot sequence genuinely cinematic:
- Center it with the brand logo at top (animated: concentric rings that scale in one by one with staggered delay).
- Logo size: 80×80px.
- Brand name: `font-brand text-3xl font-bold` with a `text-glow` class.
- Below the logo: a full-width monospace terminal block with a `bg-black/40 rounded-xl p-6 border border-border-subtle` container.
- Each boot message appears with a `fadeIn` + slight `translateY(4px) → translateY(0)` animation.
- The blinking cursor: `inline-block w-2 h-[14px] bg-accent animate-pulse`.
- The skip button: `btn-ghost` style, smaller, sits at the very bottom.
- Add a scanline overlay: a very-low-opacity `linear-gradient` strip that scrolls top-to-bottom using the `scanline` keyframe.

---

### 7. Toast Notifications (`web/src/components/Toast.jsx`)

- Toasts should slide in from the right with spring physics.
- Add a left-colored border: success=green, error=red, warning=yellow, info=accent.
- Add a subtle progress bar at the bottom that drains over the toast lifetime.
- Icons should be larger (20px) and match the color theme.

---

### 8. Tailwind Config additions (`web/tailwind.config.js`)

Add to `theme.extend`:
```js
animation: {
  'float':     'float 3s ease-in-out infinite',
  'scanline':  'scanline 4s linear infinite',
  'ping-ring': 'ping-ring 1.5s ease-out infinite',
  'gradient-shift': 'gradientShift 4s ease infinite',
},
keyframes: {
  float: {
    '0%, 100%': { transform: 'translateY(0px)' },
    '50%':      { transform: 'translateY(-4px)' },
  },
  scanline: {
    from: { transform: 'translateY(-100%)' },
    to:   { transform: 'translateY(100vh)' },
  },
  'ping-ring': {
    '0%':   { transform: 'scale(1)', opacity: '0.6' },
    '100%': { transform: 'scale(2.5)', opacity: '0' },
  },
  gradientShift: {
    '0%':   { backgroundPosition: '0% 50%' },
    '50%':  { backgroundPosition: '100% 50%' },
    '100%': { backgroundPosition: '0% 50%' },
  },
}
```

---

## Execution Order

Execute these changes in this exact order to avoid broken intermediate states:

1. **`web/src/index.css`** — Update tokens, glass tiers, `.card-hover`, `.btn-accent`, new keyframes
2. **`web/tailwind.config.js`** — Add new animation + keyframe entries
3. **`web/src/components/SidebarBrand.jsx`** — Embed the concentric-circle radar logo SVG
4. **`web/src/components/Sidebar.jsx`** — New active indicator, gradient hover, sonar status dot, new chat button
5. **`web/src/components/BootSequence.jsx`** — Cinematic boot screen
6. **`web/src/components/EmptyState.jsx`** — Floating logo + suggested prompts
7. **`web/src/components/Toast.jsx`** — Left-border toasts + progress bar
8. **`web/src/pages/Chat.jsx`** — Upgraded bubbles, input area, @ menu, empty state
9. **`web/src/pages/ResearchPage.jsx`** — Search bar, mode selector, cards
10. **`web/src/pages/MissionControl.jsx`** — Gauges, agent cards, journal feed

---

## Non-Goals (Do NOT change)

- Do NOT change any API call logic, state management, or business logic.
- Do NOT change file routing in `App.jsx`.
- Do NOT modify `Tasks.jsx`, `Calendar.jsx`, `Skills.jsx`, `Settings.jsx`, or `HomeLab.jsx` unless specifically asked.
- Do NOT install new npm packages — use only what's already installed (React, Tailwind, ReactMarkdown).
- Do NOT change the Tailwind config's `content` array or `colors` mapping to CSS variables.

---

## Visual Reference

The target aesthetic should feel like a **hybrid of**:
- [Linear.app](https://linear.app) — tight spacing, crisp typography, purposeful use of dark
- [Vercel dashboard](https://vercel.com) — glassmorphism, subtle borders, high contrast text
- [Raycast](https://raycast.com) — springy micro-interactions, command-palette precision
- [Framer](https://framer.com) — gradient-bordered cards, layered depth, alive UI

The system name **P.I.N.G.S** should feel like a real AI OS — not a weekend hobby project. Every component should communicate "this was engineered, not just coded."
