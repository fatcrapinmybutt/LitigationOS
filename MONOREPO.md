# LitigationOS — Monorepo Manifest

All repositories previously under `fatcrapinmybutt` have been consolidated here using
`git subtree add --squash`. Each import is a true squash-merge with full provenance
tracking — future `git subtree pull` updates are supported.

## Import Map

| Directory | Origin Repository | URL | Notes |
|-----------|------------------|-----|-------|
| *(root)* | LitigationOS | https://github.com/fatcrapinmybutt/LitigationOS | Primary — private |
| `imported/fredprime-legal-system/` | fredprime-legal-system | https://github.com/fatcrapinmybutt/fredprime-legal-system | 5.7 MB — CI/Docker/Python litigation OS |
| `imported/the_manbearpig/` | the_manbearpig | https://github.com/fatcrapinmybutt/the_manbearpig | 218 KB — MBP Python engines |
| `imported/cortex/legal/` | cortex-legal | https://github.com/fatcrapinmybutt/cortex-legal | Legal domain starter schema |
| `imported/cortex/site/` | cortex-site | https://github.com/fatcrapinmybutt/cortex-site | Public-facing site (index.html) |
| `imported/cortex/realestate/` | cortex-realestate | https://github.com/fatcrapinmybutt/cortex-realestate | Real-estate domain schema |
| `imported/cortex/fraud/` | cortex-fraud | https://github.com/fatcrapinmybutt/cortex-fraud | Fraud domain starter schema |
| `imported/cortex/healthcare/` | cortex-healthcare | https://github.com/fatcrapinmybutt/cortex-healthcare | Healthcare domain schema |
| `imported/cortex/cyber/` | cortex-cyber | https://github.com/fatcrapinmybutt/cortex-cyber | Cybersecurity domain schema |
| `imported/cortex/journalism/` | cortex-journalism | https://github.com/fatcrapinmybutt/cortex-journalism | Journalism domain schema |
| `imported/cortex/finance/` | cortex-finance | https://github.com/fatcrapinmybutt/cortex-finance | Finance domain schema |
| `imported/cortex/supply-chain/` | cortex-supply-chain | https://github.com/fatcrapinmybutt/cortex-supply-chain | Supply-chain domain schema |

## Skipped / Already Consolidated

| Repository | Reason |
|-----------|--------|
| `cortex-osint` | **Identical commit history** to LitigationOS — it is the same repo mirrored to a different remote. Importing it as a subtree would duplicate all root-level files. LitigationOS is 2 commits ahead. |
| `MICHIGAN-HIGHER-COURTS` | Empty repository (0 KB, no content). |
| `-copilot-20260214163430` | Auto-generated Copilot session repo — contains only a 103-byte README stub. |

## Updating a Subtree

To pull in upstream changes from any imported repo:

```bash
# Example: pull latest fredprime-legal-system changes
git fetch fredprime
git subtree pull --prefix=imported/fredprime-legal-system fredprime/main --squash

# Example: pull latest cortex-finance
git fetch cortex-finance
git subtree pull --prefix=imported/cortex/finance cortex-finance/main --squash
```

## Re-adding Remotes After Fresh Clone

```bash
git remote add fredprime          https://github.com/fatcrapinmybutt/fredprime-legal-system
git remote add themanbearpig      https://github.com/fatcrapinmybutt/the_manbearpig
git remote add cortex-legal       https://github.com/fatcrapinmybutt/cortex-legal
git remote add cortex-site        https://github.com/fatcrapinmybutt/cortex-site
git remote add cortex-realestate  https://github.com/fatcrapinmybutt/cortex-realestate
git remote add cortex-fraud       https://github.com/fatcrapinmybutt/cortex-fraud
git remote add cortex-healthcare  https://github.com/fatcrapinmybutt/cortex-healthcare
git remote add cortex-cyber       https://github.com/fatcrapinmybutt/cortex-cyber
git remote add cortex-journalism  https://github.com/fatcrapinmybutt/cortex-journalism
git remote add cortex-finance     https://github.com/fatcrapinmybutt/cortex-finance
git remote add cortex-supply-chain https://github.com/fatcrapinmybutt/cortex-supply-chain
```

## Consolidation Date

**2026-04-14** — performed by GitHub Copilot agent via `git subtree add --squash`.
