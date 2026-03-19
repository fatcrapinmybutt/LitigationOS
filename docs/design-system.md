# LitigationOS Design System v1.0

## Design Philosophy

**Mission**: Transform complex litigation data into clear, actionable interfaces that empower pro se litigants to manage their cases with confidence.

**Principles**:
1. **Clarity over decoration** — Every pixel serves a purpose
2. **Accessibility first** — WCAG 2.1 AA minimum, targeting AAA
3. **Information density** — Legal work demands data-rich screens
4. **Trust through professionalism** — Court-quality visual language
5. **Status at a glance** — Color-coded urgency across all surfaces

---

## 1. Color Palette

### Primary Colors

| Token | Name | Hex | RGB | Usage |
|-------|------|-----|-----|-------|
| `--color-primary` | Navy Blue | `#0F172A` | 15, 23, 42 | Headings, nav bar, primary actions |
| `--color-primary-light` | Slate Blue | `#334155` | 51, 65, 85 | Secondary headings, hover states |
| `--color-primary-muted` | Steel | `#64748B` | 100, 116, 139 | Muted text, labels, captions |
| `--color-accent` | Court Blue | `#0369A1` | 3, 105, 161 | Links, interactive elements, CTA |
| `--color-accent-hover` | Deep Court | `#075985` | 7, 89, 133 | Hover state for accent |

### Semantic Colors (Status System)

| Token | Name | Hex | Usage |
|-------|------|-----|-------|
| `--color-success` | Verdict Green | `#059669` | Filed, approved, GO status |
| `--color-success-bg` | Green Tint | `#ECFDF5` | Success backgrounds |
| `--color-warning` | Caution Amber | `#D97706` | Approaching deadlines, partial readiness |
| `--color-warning-bg` | Amber Tint | `#FFFBEB` | Warning backgrounds |
| `--color-danger` | Critical Red | `#DC2626` | Overdue, blocked, NO-GO status |
| `--color-danger-bg` | Red Tint | `#FEF2F2` | Danger backgrounds |
| `--color-info` | Process Blue | `#2563EB` | In-progress, informational |
| `--color-info-bg` | Blue Tint | `#EFF6FF` | Info backgrounds |

### Lane Colors (6 Litigation Lanes)

| Lane | Name | Color | Hex | Badge BG |
|------|------|-------|-----|----------|
| A | Custody | Indigo | `#4F46E5` | `#EEF2FF` |
| B | Housing | Emerald | `#059669` | `#ECFDF5` |
| C | Convergence | Purple | `#7C3AED` | `#F5F3FF` |
| D | PPO | Rose | `#E11D48` | `#FFF1F2` |
| E | Misconduct | Amber | `#D97706` | `#FFFBEB` |
| F | Appellate | Sky | `#0284C7` | `#F0F9FF` |

### Surface Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|-----------|-----------|-------|
| `--bg-primary` | `#FFFFFF` | `#0F172A` | Main content background |
| `--bg-secondary` | `#F8FAFC` | `#1E293B` | Cards, panels, sidebars |
| `--bg-tertiary` | `#F1F5F9` | `#334155` | Nested cards, table rows alt |
| `--border-default` | `#E2E8F0` | `#475569` | Card borders, dividers |
| `--border-strong` | `#CBD5E1` | `#64748B` | Focused input borders |

---

## 2. Typography

### Font Stack

```
Heading: "EB Garamond", Georgia, "Times New Roman", serif
Body: "Lato", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
Mono: "JetBrains Mono", "Cascadia Code", "Consolas", monospace
```

**Rationale**: EB Garamond conveys legal authority and tradition (used in court filings). Lato provides clean readability for dense data screens. JetBrains Mono for code, case numbers, and database references.

### Type Scale

| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `--text-display` | 32px | 700 | 1.2 | Page titles, hero headings |
| `--text-h1` | 24px | 700 | 1.3 | Screen titles |
| `--text-h2` | 20px | 600 | 1.35 | Section headings |
| `--text-h3` | 16px | 600 | 1.4 | Card titles, subsections |
| `--text-body` | 14px | 400 | 1.6 | Body text, descriptions |
| `--text-body-sm` | 13px | 400 | 1.5 | Secondary text, metadata |
| `--text-caption` | 12px | 400 | 1.4 | Labels, timestamps, badges |
| `--text-mono` | 13px | 400 | 1.5 | Case numbers, hashes, code |

### Heading Font Usage (EB Garamond)

- **Display + H1**: EB Garamond Bold — screen titles, filing names
- **H2**: EB Garamond SemiBold — section headings
- **H3 and below**: Lato SemiBold — subsections (switch to sans for smaller sizes)

---

## 3. Spacing System

**Base unit**: 4px

| Token | Value | Usage |
|-------|-------|-------|
| `--space-0` | 0px | Reset |
| `--space-1` | 4px | Tight inline spacing |
| `--space-2` | 8px | Icon-to-text, badge padding |
| `--space-3` | 12px | Input padding, small gaps |
| `--space-4` | 16px | Card padding, list gaps |
| `--space-5` | 20px | Section gaps |
| `--space-6` | 24px | Card inner padding |
| `--space-8` | 32px | Section separators |
| `--space-10` | 40px | Page section gaps |
| `--space-12` | 48px | Major section separators |
| `--space-16` | 64px | Page top/bottom margins |

---

## 4. Component Library

### 4.1 Navigation

**Sidebar (Primary Navigation)**
- Width: 240px (expanded), 64px (collapsed)
- Background: `--bg-secondary`
- Active item: `--color-accent` text + `--color-info-bg` background
- Icons: 20px, Lucide icon set
- Sections: Dashboard, Cases, Filings, Evidence, Timeline, Calendar, Deadlines, Settings

**Top Bar**
- Height: 56px
- Background: `--bg-primary`
- Contains: Breadcrumb, search (⌘K), notifications bell, lane selector

### 4.2 Cards

**Standard Card**
```
Border: 1px solid var(--border-default)
Border-radius: 8px
Padding: var(--space-6)
Background: var(--bg-primary)
Shadow: 0 1px 3px rgba(0,0,0,0.1)
Hover: shadow 0 4px 12px rgba(0,0,0,0.1)
```

**Status Card** (Filing/Deadline)
```
Left border: 4px solid [status color]
+ Standard card properties
```

**Lane Card**
```
Top border: 3px solid [lane color]
+ Standard card properties
```

### 4.3 Buttons

| Variant | Background | Text | Border | Usage |
|---------|-----------|------|--------|-------|
| Primary | `--color-accent` | `#FFFFFF` | none | Main CTA: "File", "Generate PDF" |
| Secondary | transparent | `--color-accent` | 1px `--color-accent` | Secondary: "Cancel", "Export" |
| Danger | `--color-danger` | `#FFFFFF` | none | Destructive: "Delete draft" |
| Ghost | transparent | `--color-primary-muted` | none | Tertiary: "Back", "Skip" |
| Success | `--color-success` | `#FFFFFF` | none | Confirm: "Mark as Filed" |

**Button sizes**: `sm` (28px height), `md` (36px), `lg` (44px touch target)

### 4.4 Badges / Status Chips

| Status | Background | Text | Border |
|--------|-----------|------|--------|
| GO | `#ECFDF5` | `#059669` | `#059669` |
| NO-GO | `#FEF2F2` | `#DC2626` | `#DC2626` |
| CONDITIONAL | `#FFFBEB` | `#D97706` | `#D97706` |
| IN PROGRESS | `#EFF6FF` | `#2563EB` | `#2563EB` |
| BLOCKED | `#F1F5F9` | `#64748B` | `#64748B` |
| FILED | `#ECFDF5` | `#059669` | none (solid bg) |

### 4.5 Tables

- Header: `--bg-tertiary`, `--text-caption` uppercase, font-weight 600
- Row: `--bg-primary`, border-bottom `--border-default`
- Row alt: `--bg-secondary`
- Row hover: `--color-info-bg`
- Cell padding: `--space-3` vertical, `--space-4` horizontal
- Sortable columns: arrow indicator, accent color on active sort

### 4.6 Form Inputs

```
Height: 36px
Border: 1px solid var(--border-default)
Border-radius: 6px
Padding: 0 var(--space-3)
Focus: border 2px solid var(--color-accent), box-shadow 0 0 0 3px rgba(3,105,161,0.15)
Error: border var(--color-danger), helper text in danger color
Disabled: opacity 0.5, cursor not-allowed
```

### 4.7 Data Visualization

**Chart Colors (ordered)**:
1. `#0369A1` (Court Blue — primary data)
2. `#4F46E5` (Indigo — secondary)
3. `#059669` (Green — positive)
4. `#D97706` (Amber — caution)
5. `#DC2626` (Red — danger)
6. `#7C3AED` (Purple — tertiary)

**Urgency Gauge**: Green → Amber → Red gradient for deadline proximity

---

## 5. Iconography

**Icon Set**: Lucide Icons (open source, consistent, 1px stroke)
**Default size**: 20px (navigation), 16px (inline), 24px (feature cards)
**Color**: Inherits text color via `currentColor`

| Context | Icon Examples |
|---------|-------------|
| Navigation | `layout-dashboard`, `briefcase`, `file-text`, `shield`, `calendar`, `clock` |
| Status | `check-circle` (GO), `x-circle` (NO-GO), `alert-triangle` (warning), `loader` (progress) |
| Actions | `plus`, `edit`, `trash-2`, `download`, `upload`, `search`, `filter` |
| Filing | `file-plus`, `file-check`, `printer`, `send`, `stamp` |
| Evidence | `paperclip`, `image`, `file-audio`, `link`, `lock` |

---

## 6. Layout Grid

### Desktop (≥1024px)

```
Sidebar: 240px fixed
Content: fluid, max-width 1440px
Gutter: 24px
Columns: 12
Column gap: 16px
Page padding: 24px
```

### Compact (768–1023px)

```
Sidebar: 64px (collapsed icons only)
Content: fluid
Columns: 8
```

### Mobile (< 768px)

```
Sidebar: hidden (hamburger overlay)
Content: full width
Columns: 4
Page padding: 16px
```

---

## 7. Shadows & Elevation

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` | Subtle depth (buttons, chips) |
| `--shadow-md` | `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)` | Cards, dropdowns |
| `--shadow-lg` | `0 4px 12px rgba(0,0,0,0.1)` | Modals, popovers, hover states |
| `--shadow-xl` | `0 10px 25px rgba(0,0,0,0.15)` | Dialogs, floating panels |

---

## 8. Animation & Motion

| Property | Duration | Easing | Usage |
|----------|----------|--------|-------|
| Color transitions | 150ms | ease-in-out | Hover, focus, toggle |
| Layout shifts | 200ms | ease-out | Expand/collapse, tab switch |
| Modal entrance | 250ms | cubic-bezier(0.16,1,0.3,1) | Slide up + fade |
| Toast notifications | 300ms | ease-out | Slide in from right |

**Reduced motion**: All animations collapse to instant transitions when `prefers-reduced-motion: reduce` is active.

---

## 9. Accessibility Standards

| Requirement | Standard | Implementation |
|-------------|----------|---------------|
| Color contrast (normal text) | 4.5:1 minimum | All text/background combos tested |
| Color contrast (large text) | 3:1 minimum | Headings 18px+ at 700 weight |
| Focus indicators | 3px solid outline | `--color-accent` with 3px offset |
| Touch targets | 44×44px minimum | All buttons/links on mobile |
| Keyboard navigation | Full tab order | Logical flow, skip links |
| Screen reader | ARIA labels | All interactive elements labeled |
| Color-only indicators | Never | Always pair with icon/text |
| Text scaling | Up to 200% | Layout remains functional |

---

## 10. Dark Mode

All surface and text colors have dark mode equivalents defined in the Surface Colors table (Section 1). The dark theme uses `--bg-primary: #0F172A` (Navy) as the base, with semantic colors remaining unchanged for consistency.

**Dark mode toggle**: System preference detection + manual override stored in `localStorage`.

---

## 11. CustomTkinter Implementation Notes

LitigationOS uses CustomTkinter (Python). Map design tokens to CTk:

```python
THEME = {
    "CTk": {"fg_color": ["#FFFFFF", "#0F172A"]},
    "CTkFrame": {"fg_color": ["#F8FAFC", "#1E293B"], "border_color": ["#E2E8F0", "#475569"]},
    "CTkButton": {
        "fg_color": ["#0369A1", "#0369A1"],
        "hover_color": ["#075985", "#075985"],
        "text_color": ["#FFFFFF", "#FFFFFF"],
        "corner_radius": 6
    },
    "CTkLabel": {"text_color": ["#0F172A", "#F8FAFC"]},
    "CTkEntry": {
        "fg_color": ["#FFFFFF", "#1E293B"],
        "border_color": ["#E2E8F0", "#475569"],
        "text_color": ["#0F172A", "#F8FAFC"],
        "corner_radius": 6
    }
}
```

---

*Design System v1.0 — LitigationOS | Generated with ui-ux-designer + ui-ux-pro-max skills*
*Typography: Legal Professional (EB Garamond + Lato) | Palette: Government/Public Service adapted*
