<div align="center">

# 🏠 CORTEX Real Estate Intelligence Pack

### Property Ownership Research · Title Chain Analysis · LLC Piercing · Investment Intelligence

**Turn raw property records into an interactive intelligence graph.**

[![Buy on Gumroad](https://img.shields.io/badge/Buy_Now-$29_One_Time-ff6666?style=for-the-badge&logo=gumroad&logoColor=white)](https://andrewpioneer6.gumroad.com/l/cjamvzo)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Try_It_Free-4CAF50?style=for-the-badge&logo=github&logoColor=white)](https://fatcrapinmybutt.github.io/cortex-site/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

---

<img src="https://img.shields.io/badge/Entity_Types-25+-blueviolet?style=flat-square" /> <img src="https://img.shields.io/badge/Categories-15+-green?style=flat-square" /> <img src="https://img.shields.io/badge/Focus_Modes-8-orange?style=flat-square" /> <img src="https://img.shields.io/badge/Authority_Patterns-10+-red?style=flat-square" />

</div>

---

## 🔍 What Is This?

The **CORTEX Real Estate Intelligence Pack** is a domain-specific knowledge graph configuration for the [CORTEX OSINT platform](https://fatcrapinmybutt.github.io/cortex-site/). It transforms scattered public property records, corporate filings, tax assessments, and permit data into a **navigable, interactive intelligence graph** that reveals hidden ownership structures, shell company networks, and investment opportunities.

**This is not a database.** It's a *lens* — a pre-configured intelligence schema that tells CORTEX how to recognize, classify, link, and visualize real estate entities and their relationships.

---

## 💡 Why Real Estate Intelligence?

Property ownership is deliberately obscured. LLCs hold LLCs that hold trusts that hold properties. Beneficial owners hide behind registered agents. Tax liens accumulate across dozens of shell entities controlled by a single developer.

Traditional tools give you **one record at a time**. CORTEX gives you the **entire network at once**.

| Challenge | How CORTEX Solves It |
|-----------|---------------------|
| **Who really owns this property?** | Trace ownership chains through LLCs, trusts, and nominees back to beneficial owners |
| **Is this LLC a shell company?** | Pattern detection: registered agent overlap, same-day formation, address clustering |
| **Are these properties connected?** | Entity resolution across deeds, mortgages, permits, and corporate filings |
| **What liens exist across a portfolio?** | Cross-entity lien aggregation — see total exposure, not just per-parcel |
| **Is this a good investment?** | Permit activity, zoning changes, comparable sales, and development pipeline in one graph |
| **Is there fraud happening?** | Straw buyer detection, title washing patterns, fraudulent conveyance indicators |

---

## 🧩 Entity Types (25+)

The pack defines rich entity schemas for everything in the real estate ecosystem:

### Core Property Entities
| Entity | Icon | Description |
|--------|------|-------------|
| 🏠 **Property** | `shape: hexagon` | Parcels, lots, buildings — the atomic unit of real estate |
| 📋 **Deed** | `shape: document` | Recorded conveyance instruments — warranty, quitclaim, sheriff's |
| 🏷️ **Parcel** | `shape: diamond` | Tax parcel with APN/PIN, legal description, assessed value |
| 🏗️ **Building** | `shape: box` | Structures on parcels — type, year built, sq ft, condition |

### Ownership & Entity Entities
| Entity | Icon | Description |
|--------|------|-------------|
| 👤 **Owner** | `shape: circle` | Individual property owners — natural persons |
| 🏢 **LLC** | `shape: octagon` | Limited liability companies — the #1 ownership veil |
| 🛡️ **Trust** | `shape: shield` | Land trusts, living trusts, irrevocable trusts |
| 🏛️ **Corporation** | `shape: pentagon` | C-corps, S-corps, nonprofits holding real property |
| 🤝 **Partnership** | `shape: parallelogram` | General & limited partnerships in property deals |
| 📇 **Registered Agent** | `shape: tag` | The person/entity receiving legal service — shell company indicator |
| 🧑‍💼 **Beneficial Owner** | `shape: star` | The real human behind the entity stack |

### Financial Entities
| Entity | Icon | Description |
|--------|------|-------------|
| 💰 **Mortgage** | `shape: rectangle` | Recorded liens securing debt against real property |
| ⚠️ **Lien** | `shape: triangle` | Tax liens, mechanic's liens, judgment liens, HOA liens |
| 📊 **Assessment** | `shape: bar` | County assessor valuations — land + improvement |
| 🏦 **Lender** | `shape: bank` | Banks, credit unions, hard money lenders, private lenders |
| 💵 **Transaction** | `shape: arrow` | Sales, refinances, transfers — with price and date |

### Development & Zoning Entities
| Entity | Icon | Description |
|--------|------|-------------|
| 📐 **Permit** | `shape: clipboard` | Building permits, demolition permits, electrical/plumbing/mechanical |
| 🗺️ **Zoning** | `shape: grid` | Zoning classification — residential, commercial, industrial, mixed-use |
| 🏗️ **Development** | `shape: crane` | Active development projects — planned, approved, under construction |
| 🌍 **Subdivision** | `shape: map` | Platted subdivisions with lot/block/unit structure |

### Legal & Regulatory Entities
| Entity | Icon | Description |
|--------|------|-------------|
| ⚖️ **Court Case** | `shape: gavel` | Foreclosures, quiet title actions, partition suits, evictions |
| 📜 **Easement** | `shape: path` | Recorded easements — utility, access, conservation |
| 🚫 **Violation** | `shape: alert` | Code violations, condemnation orders, environmental notices |
| 🏛️ **Government Agency** | `shape: building` | County recorder, assessor, planning commission, housing authority |
| 👔 **Agent/Broker** | `shape: person` | Licensed real estate agents, brokers, appraisers |

---

## 📂 Categories (15)

Entities and relationships are organized into intelligence categories:

| Category | Color | Focus |
|----------|-------|-------|
| **Ownership** | `#2196F3` | Who owns what — deed chains, entity stacks |
| **Finance** | `#4CAF50` | Mortgages, liens, assessments, transactions |
| **Legal** | `#F44336` | Court cases, easements, violations, disputes |
| **Development** | `#FF9800` | Permits, projects, construction activity |
| **Zoning** | `#9C27B0` | Land use, zoning changes, variances |
| **Corporate** | `#607D8B` | LLC/Corp/Trust formation, agents, officers |
| **Tax** | `#795548` | Assessments, exemptions, delinquencies, sales |
| **Title** | `#00BCD4` | Chain of title, encumbrances, insurance |
| **Environmental** | `#8BC34A` | Phase I/II, contamination, brownfields |
| **Insurance** | `#FF5722` | Title insurance, hazard, flood zones |
| **Market** | `#3F51B5` | Comparables, trends, absorption rates |
| **Tenant** | `#E91E63` | Leases, rent rolls, occupancy, evictions |
| **Infrastructure** | `#009688` | Utilities, roads, transit, connectivity |
| **Historical** | `#827717` | Prior owners, historical use, demolitions |
| **Regulatory** | `#AD1457` | HUD, CFPB, state licensing, RESPA compliance |

---

## 🎯 Focus Modes (8)

One-click intelligence views that filter and highlight what matters:

### 🔗 Ownership Mode
Trace the full ownership chain from current deed holder back through every conveyance, entity transfer, and trust assignment. **Reveals beneficial owners behind LLC stacks.**

### 🕵️ Fraud Detection Mode
Highlights suspicious patterns: straw buyers, same-day transfers, below-market transactions, quitclaim chains, address clustering among "unrelated" LLCs. **Built for investigators and title companies.**

### 💰 Investment Mode
Shows permit activity, zoning changes, comparable sales, and development pipeline around a target property. **Perfect for investors, flippers, and developers evaluating deals.**

### 🏚️ Foreclosure Mode
Tracks lis pendens → default → auction → REO → resale pipeline. Cross-references tax delinquencies and lien stacking. **Built for distressed asset buyers and servicers.**

### 🗺️ Zoning Mode
Visualizes current zoning, pending variance applications, conditional use permits, and historical rezoning patterns. **Essential for developers and land use attorneys.**

### 🏗️ Development Mode
Maps active permits, contractor networks, inspection timelines, and certificate of occupancy status. **For tracking construction activity and development pipelines.**

### 💸 Tax Mode
Aggregates assessed values, exemption claims, delinquency status, and tax sale history across all entities controlled by a single owner. **Reveals hidden portfolio exposure.**

### 📜 Title Mode
Reconstructs the full chain of title with every recorded instrument: deeds, mortgages, releases, easements, liens, and judgments. **For title examiners and real estate attorneys.**

---

## 📡 Authority Patterns (10+)

Pre-configured patterns for matching authoritative data sources:

| Authority | Pattern | Source Type |
|-----------|---------|-------------|
| **County Recorder** | Deed books, instrument numbers, recording dates | Public record |
| **County Assessor** | APN/PIN, assessed values, property class codes | Public record |
| **ALTA Standards** | Title examination standards, endorsement codes | Industry standard |
| **HUD Regulations** | RESPA, Fair Housing, settlement procedures | Federal regulation |
| **State Licensing** | Agent/broker license numbers, disciplinary actions | State regulatory |
| **MLS Data** | Listing numbers, DOM, price history, agent info | Industry database |
| **Uniform Commercial Code** | UCC filings, fixture filings, financing statements | Public record |
| **FEMA Flood Maps** | Flood zone designations, FIRM panel numbers | Federal data |
| **EPA Records** | Superfund, brownfields, RCRA, underground tanks | Federal environmental |
| **Census/ACS** | Demographics, income, housing characteristics | Federal statistical |
| **Court Records** | Case numbers, docket entries, judgment amounts | Public record |
| **Corporate Filings** | Secretary of State records, annual reports, officers | Public record |

---

## 🆚 Why CORTEX vs. The Competition?

| Feature | CoStar ($500+/mo) | ATTOM ($1,000+/mo) | Reonomy ($300+/mo) | **CORTEX ($29 once)** |
|---------|-------------------|--------------------|--------------------|----------------------|
| Property records | ✅ | ✅ | ✅ | ✅ Load any source |
| Ownership tracing | ❌ Manual | ⚠️ Limited | ⚠️ Basic | ✅ **Full graph** |
| LLC piercing | ❌ | ❌ | ❌ | ✅ **Entity resolution** |
| Shell company detection | ❌ | ❌ | ❌ | ✅ **Pattern analysis** |
| Fraud indicators | ❌ | ❌ | ❌ | ✅ **Built-in** |
| Custom entity types | ❌ Locked | ❌ Locked | ❌ Locked | ✅ **Fully extensible** |
| Interactive graph | ❌ | ❌ | ❌ | ✅ **Force-directed** |
| Works offline | ❌ | ❌ | ❌ | ✅ **100% local** |
| Monthly cost | $500+ | $1,000+ | $300+ | **$0 after purchase** |
| Data lock-in | ✅ Their data | ✅ Their data | ✅ Their data | **Your data, forever** |

> **CORTEX doesn't sell you data. It gives you the intelligence framework to analyze *any* data — your data, public records, MLS exports, county downloads, court filings.**

---

## 📦 What's in This Pack?

```
cortex-realestate/
├── README.md              ← You are here
├── realestate.json        ← Domain intelligence pack (load into CORTEX)
└── LICENSE                ← MIT — use it however you want
```

### `realestate.json`
The core intelligence schema. Load it into CORTEX and it instantly knows how to:
- Recognize 25+ real estate entity types
- Classify relationships across 15 categories
- Match 10+ authoritative data source patterns
- Switch between 8 focused intelligence views
- Color-code, shape-code, and size-code entities by type and risk

---

## 🚀 Quick Start

1. **Get CORTEX** → [Download from Gumroad](https://andrewpioneer6.gumroad.com/l/cjamvzo) ($29 one-time)
2. **Load the pack** → Drag `realestate.json` into CORTEX or use `File → Load Domain Pack`
3. **Import your data** → CSV, JSON, or paste from county recorder, assessor, or MLS
4. **Explore** → Click any entity to see its connections. Switch focus modes. Trace ownership chains.

---

## 🎯 Who Is This For?

| Role | Use Case |
|------|----------|
| 🏠 **Real Estate Investors** | Due diligence, portfolio analysis, deal sourcing, risk assessment |
| ⚖️ **Real Estate Attorneys** | Title examination, quiet title research, foreclosure defense, fraud cases |
| 🕵️ **Private Investigators** | Asset searches, skip tracing, fraud investigation, hidden ownership |
| 🏦 **Lenders & Underwriters** | Collateral analysis, lien priority, borrower entity verification |
| 🏗️ **Developers** | Site selection, zoning research, permit tracking, entitlement monitoring |
| 📋 **Title Companies** | Chain of title reconstruction, exception identification, curative work |
| 🏛️ **Government / Regulators** | Code enforcement, tax delinquency, blight remediation, redevelopment |
| 📊 **Analysts & Researchers** | Market analysis, ownership concentration, gentrification tracking |

---

## 💬 Example Investigations

### "Who really owns this apartment complex?"
> Load the property → CORTEX finds the LLC on the deed → traces the LLC to its registered agent → finds 12 other LLCs with the same agent → discovers all 12 hold properties → maps them to a single beneficial owner through overlapping officer names.

### "Is this a straw buyer situation?"
> Import recent transactions → Fraud mode highlights: buyer formed LLC 3 days before closing, purchase price 40% below market, seller is a different LLC with the same registered agent, property immediately transferred to a third LLC. Pattern score: **HIGH RISK**.

### "What's the total lien exposure across this developer's portfolio?"
> Search the developer by name → CORTEX finds 8 LLCs → maps 23 properties across them → aggregates: $2.1M in mortgages, $340K in mechanic's liens, $89K in tax delinquencies, 2 active foreclosures. **Total exposure: $2.53M**.

---

## 🧠 Built on CORTEX

This pack runs on the **CORTEX** open-source intelligence platform — a local-first, privacy-respecting, extensible knowledge graph engine.

- **100% offline** — your data never leaves your machine
- **Domain packs** — swap intelligence contexts in seconds (law, real estate, cyber, finance)
- **Interactive graph** — force-directed visualization with click-to-explore navigation
- **Extensible** — add your own entity types, categories, and focus modes

**[Get CORTEX →](https://andrewpioneer6.gumroad.com/l/cjamvzo)**

---

<div align="center">

### ⭐ Star this repo if you want more domain packs!

**[🏠 Buy Now — $29](https://andrewpioneer6.gumroad.com/l/cjamvzo)** · **[🌐 Live Demo](https://fatcrapinmybutt.github.io/cortex-site/)** · **[📦 All Domain Packs](https://github.com/fatcrapinmybutt?tab=repositories)**

*Property intelligence shouldn't cost $500/month.*

</div>
