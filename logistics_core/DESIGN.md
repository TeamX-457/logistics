---
name: Logistics Core
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#45464d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#855300'
  on-secondary: '#ffffff'
  secondary-container: '#fea619'
  on-secondary-container: '#684000'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#271901'
  on-tertiary-container: '#98805d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
  mono-sm:
    fontFamily: Geist Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  margin: 32px
---

## Brand & Style

This design system is built for a premium logistics marketplace where efficiency, reliability, and precision are paramount. The brand personality is mature and institutional, avoiding decorative flourishes in favor of high-information density and utilitarian clarity.

The visual style is **Minimalist with a Professional Edge**. It utilizes a "Flat-Plus" approach: primarily flat surfaces defined by surgical 1px borders, punctuated by subtle "glow" shadows to indicate interactive depth. The aesthetic is inspired by high-end enterprise dashboards and technical instrumentation, ensuring that the UI feels like a tool rather than a consumer app.

**Key Principles:**
- **Clarity over Expression:** Every element must serve a functional purpose.
- **Precision:** Perfect alignment to an 8px grid.
- **High Contrast:** Ensuring legibility in high-stress logistics environments (warehouses, transit hubs).
- **No Decoration:** Gradients, rounded/pill-shaped components, and playful illustrations are strictly prohibited.

## Colors

The palette is rooted in logistics industry standards, utilizing a "Caution and Command" logic.

**Primary (Deep Navy):** #0F172A. Used for primary branding, heavy headers, and main navigation backgrounds. It evokes the stability of a global carrier.
**Accent (Amber):** #F59E0B. Reserved strictly for primary actions (CTAs), alerts, and status indicators that require immediate driver or dispatcher attention.
**Neutral (Slate):** A range of grays from Slate-50 (#F8FAFC) for backgrounds to Slate-900 (#0F172A) for text.

**Color Modes:**
- **Light Mode:** Crisp white (#FFFFFF) surfaces with Slate-200 borders. Text predominantly Slate-900.
- **Dark Mode:** Deep Slate-950 (#020617) backgrounds. Surfaces use Slate-900 with subtle Slate-800 borders. This is a "True Dark" implementation optimized for low-light terminal use.

## Typography

The system utilizes **Geist** for its technical, developer-centric aesthetic which suits the logistics "supply chain as code" metaphor.

- **Weight Scale:** SemiBold (600) is used for headers and primary labels. Regular (400) is used for all body text and data entry.
- **Data Display:** For tracking numbers, VINs, and coordinates, use the monospaced variant of Geist to ensure character alignment and prevent "jitter" when numbers update.
- **Hierarchy:** Use color (Slate-500 vs Slate-900) rather than extreme size differences to establish hierarchy, maintaining a compact information density.

## Layout & Spacing

The system follows a strict **8px grid**. All margins, paddings, and component heights must be multiples of 8.

- **Grid Model:** 12-column fixed grid for desktop (max-width: 1440px) with 24px gutters. For mobile, a 4-column fluid grid with 16px margins.
- **Density:** High density is preferred. Layouts should utilize "Information Clusters"—grouping related data (e.g., origin/destination/ETA) into tight modules rather than spreading them across the screen.
- **Alignment:** All text elements must align to the baseline grid to maintain a clean, architectural look across complex data tables.

## Elevation & Depth

This design system avoids traditional high-opacity drop shadows. Depth is communicated through:

1.  **Borders:** 1px solid borders (Slate-200 in light, Slate-800 in dark) define the primary boundaries of all containers.
2.  **Tonal Stacking:** Modals and flyouts use a slightly lighter background than the base (in Dark Mode) or a white surface on a Slate-50 background (in Light Mode).
3.  **The "Ring" Shadow:** For active states or floating elements, use a high-spread, extremely low-opacity (2-4%) shadow combined with a 2px "ring" or "glow" using the Primary or Accent color to highlight focus without adding visual bulk.

## Shapes

The shape language is **Soft (0.25rem)**. This provides a subtle nod to modern hardware interfaces while remaining professional and structured.

- **Base Radius:** 4px (0.25rem) for all buttons, inputs, and small cards.
- **Large Radius:** 8px (0.5rem) for main dashboard containers and modals.
- **Sharpness:** Interactive icons and small utility tags may remain sharp (0px) if they are part of a dense data table to maximize space.
- **Strict Rule:** No fully rounded (pill) shapes or circles, except for profile avatars.

## Components

**Buttons:**
- **Primary:** Deep Navy background, White text. 4px radius. No gradient.
- **Action:** Amber background, Primary Navy text. Used for "Book Now" or "Approve."
- **Ghost:** 1px Slate-200 border, no background.

**Inputs:**
- 1px Slate-300 border. Focused state uses a 1px Primary Navy border with a 2px Primary-tinted ring shadow. Label text is always 12px Medium, positioned above the field.

**Cards:**
- White background, 1px Slate-200 border. No shadow unless hovered. Hover state adds a subtle 4px blur shadow.

**Status Chips:**
- Rectangular with 2px radius. Use a light tinted background (e.g., 10% opacity) of the status color (Green for "Delivered", Amber for "Delayed") with high-contrast bold text.

**Iconography:**
- Use 2px stroke weight icons (Lucide/Heroicons). Icons must be monochromatic (Slate-600) unless indicating a specific status or action. Avoid filled icons.

**Data Tables:**
- The core of the system. Use "Zebra" striping only on hover. Headers are Slate-50 background with 12px uppercase labels. 1px horizontal dividers only.