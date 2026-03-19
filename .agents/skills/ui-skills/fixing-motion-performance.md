---
name: fixing-motion-performance
description: Audit and fix animation performance issues including layout thrashing, compositor properties, scroll-linked motion, and blur effects.
---

# fixing-motion-performance

Fix animation performance issues.

## Rendering Steps Glossary
- **Composite**: transform, opacity
- **Paint**: color, borders, gradients, masks, images, filters
- **Layout**: size, position, flow, grid, flex

## Rule Categories by Priority

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Never patterns | Critical |
| 2 | Choose the mechanism | Critical |
| 3 | Measurement | High |
| 4 | Scroll | High |
| 5 | Paint | Medium-high |
| 6 | Layers | Medium |
| 7 | Blur and filters | Medium |
| 8 | View transitions | Low |
| 9 | Tool boundaries | Critical |

## 1. Never Patterns (Critical)
- Do not interleave layout reads and writes in the same frame
- Do not animate layout continuously on large surfaces
- Do not drive animation from scrollTop, scrollY, or scroll events
- No requestAnimationFrame loops without a stop condition
- Do not mix multiple animation systems that each measure or mutate layout

## 2. Choose the Mechanism (Critical)
- Default to transform and opacity for motion
- Use JS-driven animation only when interaction requires it
- Paint or layout animation acceptable only on small, isolated surfaces
- One-shot effects acceptable more often than continuous motion
- Prefer downgrading technique over removing motion entirely

## 3. Measurement (High)
- Measure once, then animate via transform or opacity
- Batch all DOM reads before writes
- Do not read layout repeatedly during an animation
- Prefer FLIP-style transitions for layout-like effects

## 4. Scroll (High)
- Prefer Scroll or View Timelines for scroll-linked motion
- Use IntersectionObserver for visibility and pausing
- Do not poll scroll position for animation
- Pause or stop animations when off-screen
- Scroll-linked motion must not trigger continuous layout/paint on large surfaces

## 5. Paint (Medium-high)
- Paint-triggering animation only on small, isolated elements
- Do not animate paint-heavy properties on large containers
- Do not animate CSS variables for transform, opacity, or position
- Scope animated CSS variables locally, avoid inheritance

## 6. Layers (Medium)
- Compositor motion requires layer promotion, never assume it
- Use will-change temporarily and surgically
- Avoid many or large promoted layers
- Validate layer behavior with tooling when performance matters

## 7. Blur and Filters (Medium)
- Keep blur animation small (<=8px)
- Use blur only for short, one-time effects
- Never animate blur continuously
- Never animate blur on large surfaces
- Prefer opacity and translate before blur

## 8. View Transitions (Low)
- Use view transitions only for navigation-level changes
- Avoid for interaction-heavy UI
- Avoid when interruption or cancellation is required
- Treat size changes as potentially layout-triggering

## 9. Tool Boundaries (Critical)
- Do not migrate or rewrite animation libraries unless requested
- Apply rules within the existing animation system
- Never partially migrate APIs or mix styles within the same component

## Common Fixes
```css
/* layout thrashing: animate transform instead of width */
/* before */ .panel { transition: width 0.3s; }
/* after */  .panel { transition: transform 0.3s; }

/* scroll-linked: use scroll-timeline instead of JS */
.reveal { animation: fade-in linear; animation-timeline: view(); }
```

```js
// FLIP: measure once, animate via transform
const first = el.getBoundingClientRect();
el.classList.add('moved');
const last = el.getBoundingClientRect();
el.style.transform = `translateX(${first.left - last.left}px)`;
requestAnimationFrame(() => {
  el.style.transition = 'transform 0.3s';
  el.style.transform = '';
});
```
