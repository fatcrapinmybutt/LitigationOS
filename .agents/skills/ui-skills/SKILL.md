---
name: ui-skills
description: "Opinionated, evolving constraints to guide agents when building interfaces"
source: "https://github.com/ibelick/ui-skills"
risk: safe
---

# UI Skills

Enforces an opinionated UI baseline to prevent AI-generated interface slop. Includes four sub-skills:

| Skill | Purpose |
|-------|---------|
| baseline-ui | Opinionated UI baseline (Tailwind, components, animation, typography, layout, design) |
| fixing-accessibility | Keyboard, labels, focus, semantics, WCAG compliance |
| fixing-metadata | Correct titles, meta, social cards, SEO, structured data |
| fixing-motion-performance | Safe, performance-first UI motion |

## Usage

- Apply all constraints to any UI work in this conversation.
- To review a file: `/baseline-ui <file>`, `/fixing-accessibility <file>`, etc.

## Sub-skill files

See individual skill files in this directory for full constraint details:
- `baseline-ui.md`
- `fixing-accessibility.md`
- `fixing-metadata.md`
- `fixing-motion-performance.md`
