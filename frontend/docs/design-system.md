# Design System - AgentHR 2026

## Overview

This document outlines the design system specifications for the AgentHR frontend application. The design system ensures consistency across all user interfaces and provides a unified visual language.

## Typography

### Font Families

The application uses two primary font families to create visual hierarchy and brand distinction:

#### Inter Variable
- **Purpose**: Primary UI font for body text, interface elements, and data displays
- **Usage**: All standard text, labels, buttons, forms, tables
- **Weights**: 400 (Regular), 500 (Medium), 600 (SemiBold), 700 (Bold)
- **Characteristics**:
  - Excellent legibility at small sizes
  - Variable font capabilities for performance optimization
  - Optimized for screen rendering
  - Modern, clean, professional appearance

```css
font-family: 'Inter Variable', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

#### Space Grotesk
- **Purpose**: Display font for headings, titles, and brand elements
- **Usage**: Page titles, section headers, hero text, branding
- **Weights**: 400 (Regular), 500 (Medium), 700 (Bold)
- **Characteristics**:
  - Distinctive, memorable personality
  - Strong visual impact for headlines
  - Complements Inter Variable
  - Adds character without sacrificing readability

```css
font-family: 'Space Grotesk', 'Inter Variable', sans-serif;
```

### Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| H1 | 2.5rem (40px) | 700 | 1.2 | Page titles |
| H2 | 2rem (32px) | 700 | 1.2 | Section headers |
| H3 | 1.5rem (24px) | 600 | 1.3 | Subsection headers |
| H4 | 1.25rem (20px) | 600 | 1.4 | Card titles |
| H5 | 1rem (16px) | 600 | 1.5 | Subtitles |
| H6 | 0.875rem (14px) | 600 | 1.5 | Small headers |
| Body Large | 1rem (16px) | 400 | 1.5 | Primary content |
| Body | 0.875rem (14px) | 400 | 1.5 | Standard text |
| Body Small | 0.75rem (12px) | 400 | 1.4 | Captions, labels |
| Caption | 0.625rem (10px) | 400 | 1.4 | Fine print |

## Color Palette

### Primary Gradients

The application uses signature gradients to create visual interest and brand identity:

#### Primary Gradient
- **From**: `#6366f1` (Indigo 500)
- **To**: `#8b5cf6` (Violet 500)
- **Usage**: Primary buttons, hero sections, highlights, brand elements
- **CSS**: `linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)`

#### Secondary Gradient
- **From**: `#3b82f6` (Blue 500)
- **To**: `#6366f1` (Indigo 500)
- **Usage**: Secondary actions, links, accents
- **CSS**: `linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)`

### Neutral Colors

#### Light Mode
| Shade | Hex | Usage |
|-------|-----|-------|
| 50 | #fafafa | Background, subtle fills |
| 100 | #f5f5f5 | Secondary backgrounds |
| 200 | #eeeeee | Borders, dividers |
| 300 | #e0e0e0 | Disabled states |
| 400 | #bdbdbd | Placeholders |
| 500 | #9e9e9e | Secondary text |
| 600 | #757575 | Primary text |
| 700 | #616161 | Emphasized text |
| 800 | #424242 | Headings |
| 900 | #212121 | High contrast text |

#### Dark Mode
| Shade | Hex | Usage |
|-------|-----|-------|
| 50 | #212121 | High contrast text |
| 100 | #424242 | Headings |
| 200 | #616161 | Emphasized text |
| 300 | #757575 | Primary text |
| 400 | #9e9e9e | Secondary text |
| 500 | #bdbdbd | Placeholders |
| 600 | #e0e0e0 | Disabled states |
| 700 | #eeeeee | Borders, dividers |
| 800 | #f5f5f5 | Secondary backgrounds |
| 900 | #fafafa | Background, subtle fills |

### Semantic Colors

#### Success
- **Main**: `#2e7d32` (Green 700)
- **Light**: `#4caf50` (Green 500)
- **Dark**: `#1b5e20` (Green 900)
- **Usage**: Confirmations, success states, matched skills

#### Error
- **Main**: `#d32f2f` (Red 700)
- **Light**: `#f44336` (Red 500)
- **Dark**: `#b71c1c` (Red 900)
- **Usage**: Errors, warnings, missing skills, destructive actions

#### Warning
- **Main**: `#ed6c02` (Orange 700)
- **Light**: `#ff9800` (Orange 500)
- **Dark**: `#e65100` (Orange 900)
- **Usage**: Warnings, attention needed, pending states

#### Info
- **Main**: `#0288d1` (Light Blue 700)
- **Light**: `#03a9f4` (Light Blue 500)
- **Dark**: `#01579b` (Light Blue 900)
- **Usage**: Information, hints, neutral feedback

## Spacing Scale

The spacing scale is based on a 4px base unit, ensuring consistent spacing throughout the application.

| Token | Value | Usage |
|-------|-------|-------|
| spacing-0 | 0 | No spacing |
| spacing-1 | 4px | Tiny gaps, icon padding |
| spacing-2 | 8px | Small gaps, compact layouts |
| spacing-3 | 12px | Default padding, small margins |
| spacing-4 | 16px | Standard padding, medium margins |
| spacing-5 | 20px | Generous padding |
| spacing-6 | 24px | Large padding, section spacing |
| spacing-7 | 28px | Extra large spacing |
| spacing-8 | 32px | Component separation |
| spacing-10 | 40px | Section separation |
| spacing-12 | 48px | Large section gaps |
| spacing-16 | 64px | Page-level spacing |
| spacing-20 | 80px | Hero sections |

### Spacing Guidelines

- **Component padding**: Use spacing-3 (12px) for compact, spacing-4 (16px) for standard
- **Gap between elements**: Use spacing-2 (8px) to spacing-4 (16px)
- **Section margins**: Use spacing-6 (24px) to spacing-8 (32px)
- **Page margins**: Use spacing-8 (32px) to spacing-12 (48px)

## Bento Grid Specifications

The Bento Grid layout system provides a flexible, responsive grid for organizing content in card-based layouts.

### Grid Structure

Based on CSS Grid with 12-column layout:

```css
display: grid;
grid-template-columns: repeat(12, 1fr);
gap: 16px; /* spacing-4 */
```

### Card Sizes

Bento cards span multiple grid columns to create visual hierarchy:

| Size | Column Span | Width | Usage |
|------|-------------|-------|-------|
| Small | 3 cols | 25% | Stats, metrics, mini cards |
| Medium | 4 cols | 33.33% | Standard content cards |
| Large | 6 cols | 50% | Featured content |
| X-Large | 8 cols | 66.66% | Primary content |
| Full | 12 cols | 100% | Full-width sections |

### Card Specifications

#### Dimensions
- **Min height**: 200px
- **Border radius**: 16px
- **Padding**: 24px (spacing-6)
- **Gap**: 16px (spacing-4)

#### Visual Style
- **Background**: Paper color (light: #ffffff, dark: #1e1e1e)
- **Border**: 1px solid transparent
- **Elevation**: 1 (subtle shadow)
- **Hover elevation**: 2 (raised on hover)
- **Transition**: All properties 200ms cubic-bezier(0.4, 0, 0.2, 1)

#### Responsive Behavior
- **Desktop (> 1200px)**: Full 12-column grid
- **Tablet (768px - 1200px)**: 8-column grid, cards adjust
- **Mobile (< 768px)**: 4-column grid, most cards stack to full width

### Bento Card Types

#### Metric Card (Small)
- 3 columns
- Displays single metric with label
- Icon + value + trend indicator

#### Content Card (Medium)
- 4 columns
- Title + description + action
- Optional media

#### Feature Card (Large)
- 6 columns
- Rich content, multiple elements
- Can contain smaller cards internally

#### Hero Card (Full)
- 12 columns
- Full-width featured content
- Used for key highlights

## Motion and Animation

### Transitions
- **Default duration**: 200ms
- **Easing**: cubic-bezier(0.4, 0, 0.2, 1)
- **Properties**: color, background-color, border-color, box-shadow, transform

### Hover Effects
- **Elevation increase**: 1 → 2
- **Scale**: 1.0 → 1.02 (subtle)
- **Brightness**: 100% → 105% (for images)

## Accessibility

### Color Contrast
- **WCAG AA**: Minimum contrast ratio 4.5:1 for normal text
- **WCAG AAA**: Minimum contrast ratio 7:1 for normal text
- All color combinations meet WCAG AA standards

### Focus States
- **Focus outline**: 2px solid #6366f1
- **Focus offset**: 2px
- **Always visible** on keyboard navigation

### Touch Targets
- **Minimum size**: 44x44px
- **Recommended**: 48x48px

## Related Files

- `/Users/fraud/Projects/agenthr/frontend/src/contexts/ThemeContext.tsx` - Theme configuration
- `/Users/fraud/Projects/agenthr/frontend/src/components/Layout.tsx` - Layout implementation
- `/Users/fraud/Projects/agenthr/frontend/package.json` - Font dependencies
