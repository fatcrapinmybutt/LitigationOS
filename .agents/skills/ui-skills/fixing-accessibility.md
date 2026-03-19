---
name: fixing-accessibility
description: Audit and fix HTML accessibility issues including ARIA labels, keyboard navigation, focus management, color contrast, and form errors.
---

# fixing-accessibility

Fix accessibility issues.

## Rule Categories by Priority

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Accessible names | Critical |
| 2 | Keyboard access | Critical |
| 3 | Focus and dialogs | Critical |
| 4 | Semantics | High |
| 5 | Forms and errors | High |
| 6 | Announcements | Medium-high |
| 7 | Contrast and states | Medium |
| 8 | Media and motion | Low-medium |
| 9 | Tool boundaries | Critical |

## 1. Accessible Names (Critical)
- Every interactive control must have an accessible name
- Icon-only buttons must have aria-label or aria-labelledby
- Every input, select, and textarea must be labeled
- Links must have meaningful text (no "click here")
- Decorative icons must be aria-hidden

## 2. Keyboard Access (Critical)
- Do not use div or span as buttons without full keyboard support
- All interactive elements must be reachable by Tab
- Focus must be visible for keyboard users
- Do not use tabindex greater than 0
- Escape must close dialogs or overlays when applicable

## 3. Focus and Dialogs (Critical)
- Modals must trap focus while open
- Restore focus to the trigger on close
- Set initial focus inside dialogs
- Opening a dialog should not scroll the page unexpectedly

## 4. Semantics (High)
- Prefer native elements (button, a, input) over role-based hacks
- If a role is used, required aria attributes must be present
- Lists must use ul or ol with li
- Do not skip heading levels
- Tables must use th for headers when applicable

## 5. Forms and Errors (High)
- Errors must be linked to fields using aria-describedby
- Required fields must be announced
- Invalid fields must set aria-invalid
- Helper text must be associated with inputs
- Disabled submit actions must explain why

## 6. Announcements (Medium-high)
- Critical form errors should use aria-live
- Loading states should use aria-busy or status text
- Toasts must not be the only way to convey critical information
- Expandable controls must use aria-expanded and aria-controls

## 7. Contrast and States (Medium)
- Ensure sufficient contrast for text and icons
- Hover-only interactions must have keyboard equivalents
- Disabled states must not rely on color alone
- Do not remove focus outlines without a visible replacement

## 8. Media and Motion (Low-medium)
- Images must have correct alt text (meaningful or empty)
- Videos with speech should provide captions when relevant
- Respect prefers-reduced-motion for non-essential motion
- Avoid autoplaying media with sound

## 9. Tool Boundaries (Critical)
- Prefer minimal changes, do not refactor unrelated code
- Do not add aria when native semantics already solve the problem
- Do not migrate UI libraries unless requested

## Common Fixes
```html
<!-- icon-only button: add aria-label -->
<button aria-label="Close"><svg aria-hidden="true">...</svg></button>

<!-- div as button: use native element -->
<button onclick="save()">Save</button>

<!-- form error: link with aria-describedby -->
<input id="email" aria-describedby="email-err" aria-invalid="true" />
<span id="email-err">Invalid email</span>
```
