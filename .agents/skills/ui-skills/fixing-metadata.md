---
name: fixing-metadata
description: Audit and fix HTML metadata including page titles, meta descriptions, canonical URLs, Open Graph tags, Twitter cards, favicons, JSON-LD structured data, and robots directives.
---

# fixing-metadata

Fix metadata issues for SEO and social sharing.

## Workflow
1. Identify pages with missing or incorrect metadata
2. Audit against priority rules — fix critical issues first
3. Ensure title, description, canonical, and og:url all agree
4. Verify social cards render correctly on a real URL
5. Keep diffs minimal and scoped to metadata only

## Rule Categories by Priority

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Correctness and duplication | Critical |
| 2 | Title and description | High |
| 3 | Canonical and indexing | High |
| 4 | Social cards | High |
| 5 | Icons and manifest | Medium |
| 6 | Structured data | Medium |
| 7 | Locale and alternates | Low-medium |
| 8 | Tool boundaries | Critical |

## 1. Correctness and Duplication (Critical)
- Define metadata in one place per page, avoid competing systems
- Do not emit duplicate title, description, canonical, or robots tags
- Metadata must be deterministic, no random or unstable values
- Escape and sanitize any user-generated or dynamic strings
- Every page must have safe defaults for title and description

## 2. Title and Description (High)
- Every page must have a title
- Use a consistent title format across the site
- Keep titles short and readable, avoid stuffing
- Shareable pages should have a meta description
- Descriptions must be plain text, no markdown or quote spam

## 3. Canonical and Indexing (High)
- Canonical must point to the preferred URL for the page
- Use noindex only for private, duplicate, or non-public pages
- Robots meta must match actual access intent
- Previews or staging pages should be noindex by default
- Paginated pages must have correct canonical behavior

## 4. Social Cards (High)
- Shareable pages must set Open Graph title, description, and image
- OG and Twitter images must use absolute URLs
- Prefer correct image dimensions and stable aspect ratios
- og:url must match the canonical URL
- Use a sensible og:type (usually website or article)
- Set twitter:card appropriately (summary_large_image by default)

## 5. Icons and Manifest (Medium)
- Include at least one favicon that works across browsers
- Include apple-touch-icon when relevant
- Manifest must be valid and referenced when used
- Set theme-color intentionally
- Icon paths should be stable and cacheable

## 6. Structured Data (Medium)
- Do not add JSON-LD unless it maps to real page content
- JSON-LD must be valid and reflect what is rendered
- Do not invent ratings, reviews, prices, or organization details
- Prefer one structured data block per page unless required

## 7. Locale and Alternates (Low-medium)
- Set the html lang attribute correctly
- Set og:locale when localization exists
- Add hreflang alternates only when pages truly exist
- Localized pages must canonicalize correctly per locale

## 8. Tool Boundaries (Critical)
- Prefer minimal changes, do not refactor unrelated code
- Do not migrate frameworks or SEO libraries unless requested
- Follow the project's existing metadata pattern
