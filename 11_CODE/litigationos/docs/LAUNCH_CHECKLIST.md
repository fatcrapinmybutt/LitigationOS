# LitigationOS — Pre-Launch Checklist

> **Version:** 0.2.0  
> **Target Launch:** TBD  
> **Status:** 🔴 Pre-Launch

---

## 1. Legal ⚖️

- [ ] **"Not Legal Advice" disclaimer** — Prominent on landing page, in-app splash screen, CLI first-run, and every generated document footer. Reference `src/litigationos/legal_notices.py`.
- [ ] **Terms of Service** — Drafted and published at `https://litigationos.com/terms`. Covers: limitation of liability, no attorney-client relationship, user responsibility for court filings, data ownership.
- [ ] **Privacy Policy** — Drafted and published at `https://litigationos.com/privacy`. Covers: local-first architecture, zero telemetry by default, optional anonymized usage analytics (opt-in only), no data sold.
- [ ] **EULA / License** — Confirm license file (`LICENSE`) is accurate. Dual-license if commercial: open-source community edition + commercial Pro/Enterprise.
- [ ] **Jurisdiction disclaimers** — Michigan-specific rules ship built-in. Disclaimer that rules may change and users must verify with current MCR/MCL.
- [ ] **Third-party attribution** — Audit all dependencies (CustomTkinter, Jinja2, pypdf, ReportLab, etc.) for license compliance. No GPL contamination in commercial tiers.
- [ ] **Court form copyright** — SCAO forms are public domain. Verify no copyrighted form text is embedded verbatim in templates.
- [ ] **AI output disclaimer** — AI Legal Brain (MANBEARPIG) outputs are assistive, not authoritative. Users must review all generated content.
- [ ] **Data retention policy** — Document what data is stored, where (`~/.home/LitigationOS/litigationos.db`), and how users can delete it.

---

## 2. Technical 🔧

### Testing
- [ ] **Unit test coverage ≥ 80%** — Run `python -m pytest tests/ --cov=litigationos --cov-report=term-missing`
- [ ] **All 13 engines tested** — Verify test files exist for: CaseEngine, FilingEngine, DocumentEngine, DeadlineEngine, EvidenceEngine, CourtRulesEngine, SettingsEngine, AILegalBrainEngine, RAGEngine, OllamaEngine, FilingFactoryEngine, OnboardingEngine, MonetizationEngine.
- [ ] **Model validation tests** — All 9 Pydantic models (Case, Filing, Deadline, Claim, Evidence, Party, Document, Template, TimelineEvent) have boundary/edge-case tests.
- [ ] **CLI smoke tests** — `litigationos version`, `litigationos init`, `litigationos cases`, `litigationos deadlines` all work on clean install.
- [ ] **GUI smoke test** — App launches, all 11 screens render, no crash on empty database.
- [ ] **Michigan plugin tests** — Deadline calculations, court rules lookup, SCAO forms catalog, filing validation.

### Security
- [ ] **Dependency audit** — Run `pip audit` or `safety check`. Zero known CVEs in production deps.
- [ ] **SQL injection review** — All database queries use parameterized statements (`?` placeholders). No f-string SQL.
- [ ] **Path traversal review** — File operations in EvidenceEngine and DocumentEngine sanitize user-supplied paths.
- [ ] **No secrets in repo** — Scan with `trufflehog` or `gitleaks`. No API keys, tokens, or credentials committed.
- [ ] **Input validation** — All user inputs validated via Pydantic models before database insertion.

### Error Handling
- [ ] **Graceful AI degradation** — App works fully when Ollama/ChromaDB unavailable. RAGEngine and OllamaEngine fall back silently.
- [ ] **Database lock handling** — WAL mode enabled. `busy_timeout=60000` set. No `SQLITE_BUSY` under normal use.
- [ ] **File permission errors** — Evidence import, document export, and PDF generation handle `PermissionError` gracefully.
- [ ] **Empty state UX** — All screens display helpful empty states (not blank screens) when no data exists.

### Performance
- [ ] **Startup time < 3 seconds** — Profile with `python -m cProfile -s cumtime -m litigationos version`.
- [ ] **Database scales to 10,000 evidence items** — FTS5 search returns in < 500ms.
- [ ] **Filing generation < 10 seconds** — For a standard motion with 5 exhibits.

---

## 3. Marketing 📣

### Landing Page (`litigationos.com`)
- [ ] **Hero section** — "The autonomous litigation intelligence system. File smarter. Win more."
- [ ] **Feature grid** — 13 engines with icons and one-line descriptions.
- [ ] **"How it works"** — 3-step visual: Upload Evidence → AI Analysis → Court-Ready Filings.
- [ ] **Pricing table** — Free / Pro ($49/mo) / Enterprise ($199/mo) with feature comparison.
- [ ] **Demo video** — 90-second walkthrough of case creation → evidence upload → filing generation.
- [ ] **Testimonials** — Collect beta user feedback (pro se litigants, legal aid orgs).

### Collateral
- [ ] **Demo screenshots** — Dashboard, Filing Wizard, Evidence Map, Deadline Dashboard, Timeline View.
- [ ] **Feature comparison matrix** — LitigationOS vs Clio vs MyCase vs LegalZoom (see PRODUCT_SPEC.md).
- [ ] **Blog post** — "Why Pro Se Litigants Deserve Better Tools" (launch announcement).
- [ ] **README badges** — PyPI version, test status, license, Python version.

### Community
- [ ] **GitHub README** — Updated with installation, features, screenshots, contributing guide.
- [ ] **GitHub Discussions** — Enabled for Q&A, feature requests, show-and-tell.
- [ ] **Discord / Community channel** — Optional for real-time support.

---

## 4. Distribution 📦

### PyPI
- [ ] **Package builds cleanly** — `python -m build` produces `.whl` and `.tar.gz` without errors.
- [ ] **Package installs cleanly** — `pip install dist/litigationos-*.whl` in a fresh venv works.
- [ ] **Entry point works** — `litigationos version` prints version after pip install.
- [ ] **Test PyPI upload** — Publish to `test.pypi.org` first. Verify install from test index.
- [ ] **Production PyPI upload** — `twine upload dist/*` to production PyPI.
- [ ] **PyPI metadata** — Description, classifiers, project URLs, keywords all populated in `pyproject.toml`.

### GitHub Releases
- [ ] **Git tag** — `git tag v0.2.0 && git push --tags`.
- [ ] **GitHub Release** — Create release with changelog, binary attachments (wheel + sdist).
- [ ] **Release notes** — Highlight key features, breaking changes, migration steps.

### Documentation Site
- [ ] **Docs framework** — MkDocs or Sphinx with RTD theme.
- [ ] **API reference** — Auto-generated from docstrings.
- [ ] **User guide** — Installation, Quick Start, Case Management, Filing Workflow, Evidence Management.
- [ ] **Michigan-specific guide** — MCR rules, SCAO forms, court directory, deadline calculations.
- [ ] **Developer guide** — Architecture, contributing, plugin development, engine API.

---

## 5. Revenue 💰

### Stripe Integration
- [ ] **Stripe account** — Created and verified.
- [ ] **Products created** — Free (no charge), Pro ($49/mo), Enterprise ($199/mo).
- [ ] **Subscription flow** — MonetizationEngine integrates with Stripe Checkout for upgrades.
- [ ] **Webhook handler** — Handles `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`.
- [ ] **Billing portal** — Stripe Customer Portal for plan changes, payment method updates, invoices.

### Pricing Tiers (Enforced by MonetizationEngine)
- [ ] **Free tier limits** — 1 case, 50 evidence items, 5 filings/month, basic AI (5 queries/day).
- [ ] **Pro tier limits** — Unlimited cases, unlimited evidence, 50 filings/month, full AI (100 queries/day), priority support.
- [ ] **Enterprise tier limits** — Unlimited everything, API access, custom jurisdictions, white-label, dedicated support.
- [ ] **Upgrade prompts** — In-app prompts when tier limits are reached (non-blocking, informational).
- [ ] **Grace period** — 7-day grace on expired subscriptions before downgrade to Free.

### Billing Flow
- [ ] **Trial period** — 14-day Pro trial for new users (no credit card required).
- [ ] **Payment methods** — Credit card, debit card (via Stripe).
- [ ] **Invoicing** — Monthly invoices auto-sent via Stripe.
- [ ] **Cancellation** — Self-service via billing portal. Data retained for 90 days post-cancellation.
- [ ] **Refund policy** — 30-day money-back guarantee documented in ToS.

---

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Lead Developer | | | ⬜ |
| Legal Review | | | ⬜ |
| Security Audit | | | ⬜ |
| QA Lead | | | ⬜ |
| Product Owner | | | ⬜ |
