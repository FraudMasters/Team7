# Design System 2026 - AgentHR

## Overview

Design System 2026 represents a significant enhancement to the AgentHR design system, introducing modern gradients, Framer Motion-powered micro-interactions, and a comprehensive component library built on Material-UI v6. This system provides fluid animations, responsive layouts, and a cohesive visual experience across the application.

## What's New in 2026

### Gradient System
A comprehensive gradient palette with 50+ gradient definitions for backgrounds, borders, overlays, and special effects.

### Framer Motion Integration
Smooth, physics-based animations powered by Framer Motion, with pre-configured variants and utility functions.

### Enhanced Components
New component library including BentoGrid, GradientCard, MotionWrapper, GradientButton, AnimatedBox, HoverCard, and TransitionContainer.

### Design Tokens
TypeScript-based design tokens for gradients, animations, spacing, typography, and colors.

## Gradient System

The 2026 gradient system provides CSS custom properties and TypeScript tokens for consistent gradient usage throughout the application.

### Primary Gradients

#### Primary Gradient
- **CSS Variable**: `--gradient-primary`
- **TypeScript**: `gradients.primary.main`
- **Value**: `linear-gradient(135deg, #1976d2 0%, #1565c0 100%)`
- **Usage**: Primary buttons, hero sections, brand elements

#### Primary Reverse
- **CSS Variable**: `--gradient-primary-reverse`
- **TypeScript**: `gradients.primary.reverse`
- **Value**: `linear-gradient(135deg, #1565c0 0%, #1976d2 100%)`
- **Usage**: Alternative primary styling, depth variation

#### Primary Subtle
- **CSS Variable**: `--gradient-primary-subtle`
- **TypeScript**: `gradients.primary.subtle`
- **Value**: `linear-gradient(135deg, rgba(25, 118, 210, 0.08) 0%, rgba(21, 101, 192, 0.08) 100%)`
- **Usage**: Subtle backgrounds, card highlights

### Secondary Gradients

#### Secondary Gradient
- **CSS Variable**: `--gradient-secondary`
- **TypeScript**: `gradients.secondary.main`
- **Value**: `linear-gradient(135deg, #dc004e 0%, #c51162 100%)`
- **Usage**: Secondary actions, accents

#### Secondary Subtle
- **CSS Variable**: `--gradient-secondary-subtle`
- **TypeScript**: `gradients.secondary.subtle`
- **Value**: `linear-gradient(135deg, rgba(220, 0, 78, 0.08) 0%, rgba(197, 17, 98, 0.08) 100%)`
- **Usage**: Subtle secondary backgrounds

### Semantic Gradients

#### Success Gradient
- **CSS Variable**: `--gradient-success`
- **TypeScript**: `gradients.success.main`
- **Value**: `linear-gradient(135deg, #4caf50 0%, #2e7d32 100%)`
- **Usage**: Confirmations, success states, matched skills

#### Error Gradient
- **CSS Variable**: `--gradient-error`
- **TypeScript**: `gradients.error.main`
- **Value**: `linear-gradient(135deg, #f44336 0%, #d32f2f 100%)`
- **Usage**: Errors, destructive actions, missing skills

#### Warning Gradient
- **CSS Variable**: `--gradient-warning`
- **TypeScript**: `gradients.warning.main`
- **Value**: `linear-gradient(135deg, #ff9800 0%, #ed6c02 100%)`
- **Usage**: Warnings, attention needed

#### Info Gradient
- **CSS Variable**: `--gradient-info`
- **TypeScript**: `gradients.info.main`
- **Value**: `linear-gradient(135deg, #03a9f4 0%, #0288d1 100%)`
- **Usage**: Information, hints, neutral feedback

### Neutral Gradients

#### Grey Gradient
- **CSS Variable**: `--gradient-grey`
- **TypeScript**: `gradients.neutral.grey`
- **Value**: `linear-gradient(135deg, #9e9e9e 0%, #616161 100%)`
- **Usage**: Neutral surfaces, dividers

#### Neutral Gradient (Theme-Aware)
- **CSS Variable**: `--gradient-neutral`
- **TypeScript**: `gradients.neutral.light` or `gradients.neutral.dark`
- **Light**: `linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)`
- **Dark**: `linear-gradient(135deg, #1e1e1e 0%, #121212 100%)`
- **Usage**: Theme-aware backgrounds

### Rainbow Gradients

#### Rainbow Gradient
- **CSS Variable**: `--gradient-rainbow`
- **TypeScript**: `gradients.rainbow.main`
- **Value**: Full spectrum horizontal gradient
- **Usage**: Decorative elements, pride features, playful accents

### Special Effect Gradients

#### Glossy Effect
- **CSS Variable**: `--gradient-glossy`
- **TypeScript**: `gradients.effects.glossy`
- **Value**: `linear-gradient(180deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0) 50%, rgba(0, 0, 0, 0.05) 100%)`
- **Usage**: Buttons and cards for glossy finish

#### Glass Effect (Glassmorphism)
- **CSS Variable**: `--gradient-glass`
- **TypeScript**: `gradients.effects.glass`
- **Light**: `linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)`
- **Dark**: `linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%)`
- **Usage**: Frosted glass effect for overlays and modals

#### Shine Effect
- **CSS Variable**: `--gradient-shine`
- **TypeScript**: `gradients.effects.shine`
- **Value**: `linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.4) 50%, transparent 100%)`
- **Usage**: Loading states, hover highlights, shimmer effects

### Radial Gradients

#### Glow Effects
- **Primary Glow**: `radial-gradient(circle, rgba(25, 118, 210, 0.3) 0%, transparent 70%)`
- **Success Glow**: `radial-gradient(circle, rgba(76, 175, 80, 0.3) 0%, transparent 70%)`
- **Error Glow**: `radial-gradient(circle, rgba(244, 67, 54, 0.3) 0%, transparent 70%)`
- **Warning Glow**: `radial-gradient(circle, rgba(255, 152, 0, 0.3) 0%, transparent 70%)`
- **Usage**: Ambient glow effects, emphasis, backdrop blurs

### Mesh Gradients

#### Primary Mesh
- **CSS Variable**: `--gradient-mesh-primary`
- **TypeScript**: `gradients.mesh.primary`
- **Description**: Multi-point radial gradient creating organic color blending
- **Usage**: Hero sections, page backgrounds, feature highlights

#### Colorful Mesh
- **CSS Variable**: `--gradient-mesh-colorful`
- **TypeScript**: `gradients.mesh.colorful`
- **Description**: Full-spectrum mesh with vibrant colors
- **Usage**: Creative backgrounds, celebration pages

### Overlay Gradients

#### Top Overlay
- **CSS Variable**: `--gradient-overlay-top`
- **TypeScript**: `gradients.overlay.top`
- **Value**: `linear-gradient(180deg, rgba(0, 0, 0, 0.6) 0%, transparent 100%)`
- **Usage**: Text readability on images, top-placed content

#### Bottom Overlay
- **CSS Variable**: `--gradient-overlay-bottom`
- **TypeScript**: `gradients.overlay.bottom`
- **Value**: `linear-gradient(0deg, rgba(0, 0, 0, 0.6) 0%, transparent 100%)`
- **Usage**: Text readability on images, bottom-placed content

#### Full Overlay
- **CSS Variable**: `--gradient-overlay-full`
- **TypeScript**: `gradients.overlay.full`
- **Value**: Gradient on top and bottom with transparent middle
- **Usage**: Full-image overlays with content in middle

### Utility Gradients

#### Fade Gradients
- **Fade Right**: `linear-gradient(90deg, transparent 0%, currentColor 100%)`
- **Fade Left**: `linear-gradient(270deg, transparent 0%, currentColor 100%)`
- **Fade Up**: `linear-gradient(0deg, transparent 0%, currentColor 100%)`
- **Fade Down**: `linear-gradient(180deg, transparent 0%, currentColor 100%)`
- **Usage**: Text gradients, fade effects, directional transitions

## Animation System

The 2026 animation system provides Framer Motion integration with pre-configured variants, transitions, and utility functions.

### Motion Configuration

Located at `frontend/src/config/motion.ts`, this file provides:

- **Transitions**: Standard transition configurations for different speeds
- **Variants**: Pre-built animation variants (fade, slide, scale, rotate, flip, blur)
- **Stagger Config**: Configuration for staggered children animations
- **Hover/Tap Presets**: Interactive state animations
- **Preset Combinations**: Common UI patterns (modal, dropdown, card, page transitions)

### Animation Variants

#### Fade Variants
- `fade`: Basic opacity transition
- `fadeUp`: Fade with upward movement
- `fadeDown`: Fade with downward movement
- `fadeLeft`: Fade with leftward movement
- `fadeRight`: Fade with rightward movement

#### Slide Variants
- `slideUp`: Slide from bottom
- `slideDown`: Slide from top
- `slideLeft`: Slide from right
- `slideRight`: Slide from left

#### Scale Variants
- `scale`: Grow/shrink from center
- `scaleUp`: Scale with upward movement
- `scaleDown`: Scale with downward movement

#### Rotate Variants
- `rotate`: 360-degree rotation
- `rotateX`: 3D X-axis rotation
- `rotateY`: 3D Y-axis rotation

#### Blur Variants
- `blurIn`: Fade in with blur removal
- `blurOut`: Fade out with blur addition

### Animation Presets

Pre-configured animation combinations for common UI patterns:

#### Modal Preset
- Initial: Scale down and fade out
- Animate: Scale up and fade in
- Exit: Scale down and fade out

#### Dropdown Preset
- Initial: Fade out and slide up
- Animate: Fade in and slide down
- Exit: Fade out and slide up

#### Card Preset
- Initial: Scale down slightly
- Animate: Scale to normal
- Hover: Scale up slightly

#### Page Transition Preset
- Initial: Fade out
- Animate: Fade in
- Direction: Configurable (up, down, left, right)

### Transition Presets

Speed and easing combinations:

- **default**: Standard 300ms with ease-out
- **fast**: Quick 200ms with ease-out
- **slow**: Leisurely 500ms with ease-out
- **spring**: Physics-based spring animation
- **sharp**: Quick 200ms with sharp easing

### Utility Functions

Located at `frontend/src/utils/motion.ts`:

#### `getTransition(speed, type)`
Get a transition configuration by speed and type.

#### `getVariants(preset)`
Get pre-configured animation variants by preset name.

#### `createVariants(config)`
Create custom animation variants from configuration.

#### `createStaggerVariants(config, stagger)`
Create variants with staggered children animations.

#### `combineVariants(...variantSets)`
Combine multiple variant sets into one.

#### `prefersReducedMotion()`
Check if user prefers reduced motion.

## Components

### BentoGrid

Responsive CSS Grid layout system for card-based designs.

**Location**: `frontend/src/components/design-system/BentoGrid.tsx`

**Features**:
- 12-column responsive grid
- Auto-fit columns with min-width
- Column and row spanning by breakpoint
- Position control (start/end)
- Theme-based spacing

**Example**:
```tsx
<BentoGrid gap={4} columns={12}>
  <BentoItem xs={12} sm={6} md={4} lg={3}>
    <Card>Small card</Card>
  </BentoItem>
  <BentoItem xs={12} sm={6} md={8} lg={6}>
    <Card>Large card</Card>
  </BentoItem>
</BentoGrid>
```

### GradientCard

Card component with animated gradient borders.

**Location**: `frontend/src/components/design-system/GradientCard.tsx`

**Features**:
- Multiple gradient variants (primary, secondary, success, error, warning, info, rainbow)
- Configurable border width and position
- Framer Motion hover effects (scale, elevation, shimmer)
- Theme-aware gradients

**Example**:
```tsx
<GradientCard variant="primary" hoverEffect="scale">
  <CardContent>
    <Typography variant="h5">Featured Content</Typography>
  </CardContent>
</GradientCard>
```

### MotionWrapper

Wrapper component for Framer Motion animations.

**Location**: `frontend/src/components/design-system/MotionWrapper.tsx`

**Features**:
- Pre-configured animation presets
- Custom transition and variant support
- Hover/tap/focus state animations
- Stagger children support

**Example**:
```tsx
<MotionWrapper preset="fadeUp" speed="fast">
  <div>This content fades up on mount</div>
</MotionWrapper>
```

### GradientButton

Button component with gradient backgrounds and micro-interactions.

**Location**: `frontend/src/components/design-system/GradientButton.tsx`

**Features**:
- All gradient variants from theme
- Animation variants (scale, lift, shimmer, glow)
- Shimmer effect overlay on hover
- Icon support

**Example**:
```tsx
<GradientButton variant="primary" animation="shimmer">
  Click Me
</GradientButton>
```

### AnimatedBox

Box component with Framer Motion animations.

**Location**: `frontend/src/components/design-system/AnimatedBox.tsx`

**Features**:
- All Box props plus animation support
- Pre-configured animation presets
- Theme-aware sx prop
- forwardRef support

**Example**:
```tsx
<AnimatedBox preset="scale" hover whileHover={{ scale: 1.05 }}>
  <Typography>Animated content</Typography>
</AnimatedBox>
```

### HoverCard

Card with smooth hover animations.

**Location**: `frontend/src/components/design-system/HoverCard.tsx`

**Features**:
- Multiple hover animation types
- Configurable duration and easing
- Render prop for hover state
- Outlined/bordered variants

**Example**:
```tsx
<HoverCard animationType="lift" duration={300}>
  <HoverCardHeader title="Lift on Hover" />
  <HoverCardContent>
    This card lifts up when you hover over it.
  </HoverCardContent>
</HoverCard>
```

### TransitionContainer

Container for page/component transitions with AnimatePresence.

**Location**: `frontend/src/components/design-system/TransitionContainer.tsx`

**Features**:
- Pre-configured transition types
- Directional control
- Container modes (full, width, height, auto)
- Speed presets

**Example**:
```tsx
<TransitionContainer type="slide" direction="right" speed="fast">
  <PageContent />
</TransitionContainer>
```

## Custom Hooks

### useMotion

Custom hook for managing Framer Motion animations.

**Location**: `frontend/src/hooks/useMotion.ts`

**Features**:
- AnimationControl API (play, pause, stop, restart, reverse, toggle)
- MotionState tracking
- Variant preset support
- Reduced motion accessibility

**Example**:
```tsx
const { controls, state } = useMotion({
  preset: 'fadeUp',
  autoplay: true,
});

<motion.div animate={controls}>
  Animated content
</motion.div>
```

## CSS Keyframe Animations

The 2026 system includes comprehensive CSS keyframe animations for non-Framer Motion use cases.

**Location**: `frontend/src/styles/animations.css`

### Available Animations

#### Fade Animations
- `fadeIn`, `fadeOut`
- `fadeInUp`, `fadeInDown`
- `fadeInLeft`, `fadeInRight`

#### Slide Animations
- `slideInUp`, `slideInDown`
- `slideInLeft`, `slideInRight`
- `slideOutUp`, `slideOutDown`
- `slideOutLeft`, `slideOutRight`

#### Zoom Animations
- `zoomIn`, `zoomOut`
- `zoomInUp`, `zoomInDown`

#### Bounce Animations
- `bounce` (infinite)
- `bounceIn`, `bounceOut`

#### Special Effects
- `pulse`, `pulseGlow`
- `shake`, `wobble`
- `float`, `drip`
- `flash`, `jell`
- `heartbeat`

### Utility Classes

Apply animations using CSS classes:

```html
<div class="animate-fade-in">Fades in on load</div>
<div class="animate-slide-in-up">Slides up on load</div>
<div class="animate-bounce">Bounces infinitely</div>
```

### Animation Delays

```html
<div class="animate-fade-in animate-delay-short">100ms delay</div>
<div class="animate-fade-in animate-delay-medium">200ms delay</div>
<div class="animate-fade-in animate-delay-long">300ms delay</div>
```

### Reduced Motion Support

All animations respect `prefers-reduced-motion` media query for accessibility.

## Design Tokens

### TypeScript Tokens

**Location**: `frontend/src/styles/tokens.ts`

Imports and usage:
```tsx
import { gradients, animations, spacing, typography } from '@/styles/tokens';

// Use in styled components
const StyledComponent = styled.div`
  background: ${gradients.primary.main};
  padding: ${spacing.md};
  font-size: ${typography.fontSize.base};
`;
```

### CSS Variables

Gradients are available as CSS custom properties:

```css
.my-component {
  background: var(--gradient-primary);
  border: 1px solid var(--gradient-glass);
  animation: var(--animation-fade-in) var(--animation-duration-standard);
}
```

## Best Practices

### Gradient Usage
1. **Use subtle gradients for backgrounds**: Prevent visual fatigue
2. **Reserve bold gradients for CTAs**: Maintain visual hierarchy
3. **Consider theme awareness**: Use theme-aware variants for neutral backgrounds
4. **Test contrast ratios**: Ensure text readability on gradient backgrounds

### Animation Usage
1. **Prefer presets over custom variants**: Maintain consistency
2. **Respect reduced motion preferences**: Always check `prefersReducedMotion()`
3. **Use stagger for lists**: Create smooth sequential reveals
4. **Keep animations under 500ms**: Maintain perceived performance

### Component Selection
1. **BentoGrid**: Dashboard layouts, card grids, responsive content
2. **GradientCard**: Featured content, highlighted cards, CTAs
3. **MotionWrapper**: Page transitions, list reveals, modal animations
4. **GradientButton**: Primary actions, emphasized CTAs
5. **AnimatedBox**: Flexible animated containers, micro-interactions
6. **HoverCard**: Interactive cards, expandable content
7. **TransitionContainer**: Route transitions, view switching

## Accessibility

### Reduced Motion
All components respect `prefers-reduced-motion` and disable animations when requested.

### Keyboard Navigation
All interactive components maintain focus states and keyboard accessibility.

### Color Contrast
All gradient combinations meet WCAG AA standards for color contrast.

### Focus Indicators
Animated components preserve focus visibility during animations.

## Migration from Previous Design System

### CSS Variable Updates
Replace old gradient references with new 2026 variables:
- `--gradient-primary` → Same (enhanced variants available)
- New: `--gradient-primary-subtle`, `--gradient-primary-light`

### Component Imports
Update imports to use new design system components:
```tsx
// Old
import { Card } from '@mui/material';

// New (still works, but enhanced versions available)
import { GradientCard, HoverCard } from '@/components/design-system';
```

### Animation Updates
Replace CSS animations with Framer Motion for smoother transitions:
```tsx
// Old
<div className="animate-fade-in">Content</div>

// New
<MotionWrapper preset="fade">Content</MotionWrapper>
```

## Related Files

- `frontend/src/styles/gradients.css` - CSS gradient definitions
- `frontend/src/styles/animations.css` - CSS keyframe animations
- `frontend/src/styles/tokens.ts` - TypeScript design tokens
- `frontend/src/config/motion.ts` - Framer Motion configuration
- `frontend/src/utils/motion.ts` - Motion utility functions
- `frontend/src/hooks/useMotion.ts` - Motion custom hook
- `frontend/src/components/design-system/` - Component library
- `frontend/src/contexts/EmotionThemeContext.tsx` - Theme with gradients
