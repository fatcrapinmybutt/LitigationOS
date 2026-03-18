---
name: data-intelligence-forge
description: "ELITE data intelligence — fusion of 22 data/DB/search skills. Covers data engineering, data science, visualization, quality, pipelines, database architecture, SQL optimization, embeddings, vector search, RAG, hybrid search, and similarity patterns."
metadata:
  model: opus
  forged_from: 22
  forge_date: 2026-03-12
---

# DATA-INTELLIGENCE-FORGE — Elite Composite Skill

> Forged from 22 individual skills into one supreme composite.
> Sources: data-engineer, data-scientist, data-storytelling, data-visualization, data-quality-frameworks, data-engineering-data-pipeline, data-engineering-data-driven-feature, database-architect, database-admin, database-optimizer, database-design, sql-pro, sql-optimization-patterns, embedding-strategies, vector-database-engineer, vector-index-tuning, hybrid-search-implementation, rag-engineer, rag-implementation, ai-rag-pipeline, local-rag-pipeline, similarity-search-patterns

## When to Apply

Activate this skill for ANY work related to:
- **Data Engineering**: pipelines, ETL/ELT, batch processing, streaming, data lakehouse
- **Data Science & Analytics**: statistical analysis, ML workflows, feature engineering
- **Data Visualization**: chart selection, dashboards, storytelling with data
- **Data Quality**: validation, profiling, monitoring, great expectations, schema enforcement
- **Database Architecture**: schema design, normalization, indexing strategies, partitioning
- **Database Administration**: performance tuning, backup/recovery, monitoring, maintenance
- **SQL Optimization**: query plans, index selection, join optimization, PRAGMA tuning
- **Embedding Strategies**: text embeddings, chunking, models, dimension selection
- **Vector Search**: FAISS, ChromaDB, pgvector, ANN algorithms, index types
- **RAG Patterns**: retrieval-augmented generation, chunking, reranking, hybrid search
- **Similarity Search**: cosine similarity, BM25, TF-IDF, hybrid scoring

---

## §1. Data Engineering

> pipelines, ETL/ELT, batch processing, streaming, data lakehouse

### Example: Minimal Batch Pipeline
*Source: data-engineering-data-pipeline*

```python
# Batch ingestion with validation
from batch_ingestion import BatchDataIngester
from storage.delta_lake_manager import DeltaLakeManager
from data_quality.expectations_suite import DataQualityFramework

ingester = BatchDataIngester(config={})

# Extract with incremental loading
df = ingester.extract_from_database(
    connection_string='postgresql://host:5432/db',
    query='SELECT * FROM orders',
    watermark_column='updated_at',
    last_watermark=last_run_timestamp
)

# Validate
schema = {'required_fields': ['id', 'user_id'], 'dtypes': {'id': 'int64'}}
df = ingester.validate_and_clean(df, schema)

# Data quality checks
dq = DataQualityFramework()
result = dq.validate_dataframe(df, suite_name='orders_suite', data_asset_name='orders')

# Write to Delta Lake
delta_mgr = DeltaLakeManager(storage_path='s3://lake')
delta_mgr.create_or_update_table(
    df=df,
    table_name='orders',
    partition_columns=['order_date'],
    mode='append'
)

# Save failed records
ingester.save_dead_letter_queue('s3://lake/dlq/orders')
```

## §2. Data Science & Analytics

> statistical analysis, ML workflows, feature engineering

### Phase 1: Data Analysis and Hypothesis Formation
*Source: data-engineering-data-driven-feature*

### 1. Exploratory Data Analysis
- Use Task tool with subagent_type="machine-learning-ops::data-scientist"
- Prompt: "Perform exploratory data analysis for feature: $ARGUMENTS. Analyze existing user behavior data, identify patterns and opportunities, segment users by behavior, and calculate baseline metrics. Use modern analytics tools (Amplitude, Mixpanel, Segment) to understand current user journeys, conversion funnels, and engagement patterns."
- Output: EDA report with visualizations, user segments, behavioral patterns, baseline metrics

### 2. Business Hypothesis Development
- Use Task tool with subagent_type="business-analytics::business-analyst"
- Context: Data scientist's EDA findings and behavioral patterns
- Prompt: "Formulate business hypotheses for feature: $ARGUMENTS based on data analysis. Define clear success metrics, expected impact on key business KPIs, target user segments, and minimum detectable effects. Create measurable hypotheses using frameworks like ICE scoring or RICE prioritization."
- Output: Hypothesis document, success metrics definition, expected ROI calculations

### 3. Statistical Experiment Design
- Use Task tool with subagent_type="machine-learning-ops::data-scientist"
- Context: Business hypotheses and success metrics
- Prompt: "Design statistical experiment for feature: $ARGUMENTS. Calculate required sample size for statistical power, define control and treatment groups, specify randomization strategy, and plan for multiple testing corrections. Consider Bayesian A/B testing approaches for faster decision making. Design for both primary and guardrail metrics."
- Output: Experiment design document, power analysis, statistical test plan

### Phase 2: Feature Architecture and Analytics Design
*Source: data-engineering-data-driven-feature*

### 4. Feature Architecture Planning
- Use Task tool with subagent_type="data-engineering::backend-architect"
- Context: Business requirements and experiment design
- Prompt: "Design feature architecture for: $ARGUMENTS with A/B testing capability. Include feature flag integration (LaunchDarkly, Split.io, or Optimizely), gradual rollout strategy, circuit breakers for safety, and clean separation between control and treatment logic. Ensure architecture supports real-time configuration updates."
- Output: Architecture diagrams, feature flag schema, rollout strategy

### 5. Analytics Instrumentation Design
- Use Task tool with subagent_type="data-engineering::data-engineer"
- Context: Feature architecture and success metrics
- Prompt: "Design comprehensive analytics instrumentation for: $ARGUMENTS. Define event schemas for user interactions, specify properties for segmentation and analysis, design funnel tracking and conversion events, plan cohort analysis capabilities. Implement using modern SDKs (Segment, Amplitude, Mixpanel) with proper event taxonomy."
- Output: Event tracking plan, analytics schema, instrumentation guide

### 6. Data Pipeline Architecture
- Use Task tool with subagent_type="data-engineering::data-engineer"
- Context: Analytics requirements and existing data infrastructure
- Prompt: "Design data pipelines for feature: $ARGUMENTS. Include real-time streaming for live metrics (Kafka, Kinesis), batch processing for detailed analysis, data warehouse integration (Snowflake, BigQuery), and feature store for ML if applicable. Ensure proper data governance and GDPR compliance."
- Output: Pipeline architecture, ETL/ELT specifications, data flow diagrams

### Phase 6: Analysis and Decision Making
*Source: data-engineering-data-driven-feature*

### 14. Statistical Analysis
- Use Task tool with subagent_type="machine-learning-ops::data-scientist"
- Context: Experiment data and original hypotheses
- Prompt: "Analyze A/B test results for: $ARGUMENTS. Calculate statistical significance with confidence intervals, check for segment-level effects, analyze secondary metrics impact, investigate any unexpected patterns. Use both frequentist and Bayesian approaches. Account for multiple testing if applicable."
- Output: Statistical analysis report, significance tests, segment analysis

### 15. Business Impact Assessment
- Use Task tool with subagent_type="business-analytics::business-analyst"
- Context: Statistical analysis and business metrics
- Prompt: "Assess business impact of feature: $ARGUMENTS. Calculate actual vs expected ROI, analyze impact on key business metrics, evaluate cost-benefit including operational overhead, project long-term value. Make recommendation on full rollout, iteration, or rollback."
- Output: Business impact report, ROI analysis, recommendation document

### 16. Post-Launch Optimization
- Use Task tool with subagent_type="machine-learning-ops::data-scientist"
- Context: Launch results and user feedback
- Prompt: "Identify optimization opportunities for: $ARGUMENTS based on data. Analyze user behavior patterns in treatment group, identify friction points in user journey, suggest improvements based on data, plan follow-up experiments. Use cohort analysis for long-term impact."
- Output: Optimization recommendations, follow-up experiment plans

## §3. Data Visualization

> chart selection, dashboards, storytelling with data

### Chart Selection Guide
*Source: data-visualization*

### Which Chart for Which Data?

| Data Relationship | Best Chart | Never Use |
|------------------|-----------|-----------|
| **Change over time** | Line chart | Pie chart |
| **Comparing categories** | Bar chart (horizontal for many categories) | Line chart |
| **Part of a whole** | Stacked bar, treemap | Pie chart (controversial but: bar is always clearer) |
| **Distribution** | Histogram, box plot | Bar chart |
| **Correlation** | Scatter plot | Bar chart |
| **Ranking** | Horizontal bar chart | Vertical bar, pie |
| **Geographic** | Choropleth map | Bar chart |
| **Composition over time** | Stacked area chart | Multiple pie charts |
| **Single metric** | Big number (KPI card) | Any chart (overkill) |
| **Flow / process** | Sankey diagram | Bar chart |

### The Pie Chart Problem

Pie charts are almost always the wrong choice:

```
❌ Pie chart problems:
   - Hard to compare similar-sized slices
   - Can't show more than 5-6 categories
   - 3D pie charts are always wrong
   - Impossible to read exact values

✅ Use instead:
   - Horizontal bar chart (easy comparison)
   - Stacked bar (part of whole)
   - Treemap (hierarchical parts)
   - Just a table (if precision matters)
```

### Chart Recipes
*Source: data-visualization*

### Line Chart (Time Series)

```bash
infsh app run infsh/python-executor --input '{
  "code": "import matplotlib.pyplot as plt\nimport matplotlib\nmatplotlib.use(\"Agg\")\n\nfig, ax = plt.subplots(figsize=(12, 6))\nfig.patch.set_facecolor(\"white\")\n\nmonths = [\"Jan\", \"Feb\", \"Mar\", \"Apr\", \"May\", \"Jun\", \"Jul\", \"Aug\", \"Sep\", \"Oct\", \"Nov\", \"Dec\"]\nthis_year = [120, 135, 148, 162, 178, 195, 210, 228, 245, 268, 290, 320]\nlast_year = [95, 102, 108, 115, 122, 130, 138, 145, 155, 165, 178, 190]\n\nax.plot(months, this_year, color=\"#3b82f6\", linewidth=2.5, marker=\"o\", markersize=6, label=\"2024\")\nax.plot(months, last_year, color=\"#94a3b8\", linewidth=2, linestyle=\"--\", label=\"2023\")\nax.fill_between(range(len(months)), last_year, this_year, alpha=0.1, color=\"#3b82f6\")\n\nax.annotate(\"$320K\", xy=(11, 320), fontsize=14, fontweight=\"bold\", color=\"#3b82f6\")\nax.annotate(\"$190K\", xy=(11, 190), fontsize=12, color=\"#94a3b8\")\n\nax.set_ylabel(\"Revenue ($K)\", fontsize=12)\nax.set_title(\"Revenue grew 68% year-over-year\", fontsize=16, fontweight=\"bold\")\nax.legend(fontsize=12)\nax.spines[\"top\"].set_visible(False)\nax.spines[\"right\"].set_visible(False)\nax.grid(axis=\"y\", alpha=0.3)\nplt.tight_layout()\nplt.savefig(\"line-chart.png\", dpi=150)\nprint(\"Saved\")"
}'
```

### Horizontal Bar Chart (Comparison)

```bash
infsh app run infsh/python-executor --input '{
  "code": "import matplotlib.pyplot as plt\nimport matplotlib\nmatplotlib.use(\"Agg\")\n\nfig, ax = plt.subplots(figsize=(10, 6))\n\ncategories = [\"Email\", \"Social\", \"SEO\", \"Paid Ads\", \"Referral\", \"Direct\"]\nvalues = [12, 18, 35, 22, 8, 5]\ncolors = [\"#94a3b8\"] * len(values)\ncolors[2] = \"#3b82f6\"  # Highlight the winner\n\n# Sort by value\nsorted_pairs = sorted(zip(values, categories, colors))\nvalues, categories, colors = zip(*sorted_pairs)\n\nax.barh(categories, values, color=colors, height=0.6)\nfor i, v in enumerate(values):\n    ax.text(v + 0.5, i, f\"{v}%\", va=\"center\", fontsize=12, fontweight=\"bold\")\n\nax.set_xlabel(\"% of Total Traffic\", fontsize=12)\nax.set_title(\"SEO drives the most traffic\", fontsize=16, fontweight=\"bold\")\nax.spines[\"top\"].set_visible(False)\nax.spines[\"right\"].set_visible(False)\nplt.tight_layout()\nplt.savefig(\"bar-chart.png\", dpi=150)\nprint(\"Saved\")"
}'
```

### KPI / Big Number Card

```bash
infsh app run infsh/html-to-image --input '{
  "html": "<div style=\"display:flex;gap:20px;padding:20px;background:white;font-family:system-ui\"><div style=\"background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:24px;width:200px;text-align:center\"><p style=\"color:#64748b;font-size:14px;margin:0\">Monthly Revenue</p><p style=\"font-size:48px;font-weight:900;margin:8px 0;color:#1e293b\">$89K</p><p style=\"color:#22c55e;font-size:14px;margin:0\">↑ 23% vs last month</p></div><div style=\"background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:24px;width:200px;text-align:center\"><p style=\"color:#64748b;font-size:14px;margin:0\">Active Users</p><p style=\"font-size:48px;font-weight:900;margin:8px 0;color:#1e293b\">12.4K</p><p style=\"color:#22c55e;font-size:14px;margin:0\">↑ 8% vs last month</p></div><div style=\"background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:24px;width:200px;text-align:center\"><p style=\"color:#64748b;font-size:14px;margin:0\">Churn Rate</p><p style=\"font-size:48px;font-weight:900;margin:8px 0;color:#1e293b\">2.1%</p><p style=\"color:#ef4444;font-size:14px;margin:0\">↑ 0.3% vs last month</p></div></div>"
}'
```

### Heatmap

```bash
infsh app run infsh/python-executor --input '{
  "code": "import matplotlib.pyplot as plt\nimport numpy as np\nimport matplotlib\nmatplotlib.use(\"Agg\")\n\nfig, ax = plt.subplots(figsize=(10, 6))\n\ndays = [\"Mon\", \"Tue\", \"Wed\", \"Thu\", \"Fri\", \"Sat\", \"Sun\"]\nhours = [\"9AM\", \"10AM\", \"11AM\", \"12PM\", \"1PM\", \"2PM\", \"3PM\", \"4PM\", \"5PM\"]\ndata = np.random.randint(10, 100, size=(len(hours), len(days)))\ndata[2][1] = 95  # Tuesday 11AM peak\ndata[2][3] = 88  # Thursday 11AM\n\nim = ax.imshow(data, cmap=\"Blues\", aspect=\"auto\")\nax.set_xticks(range(len(days)))\nax.set_yticks(range(len(hours)))\nax.set_xticklabels(days, fontsize=12)\nax.set_yticklabels(hours, fontsize=12)\n\nfor i in range(len(hours)):\n    for j in range(len(days)):\n        color = \"white\" if data[i][j] > 60 else \"black\"\n        ax.text(j, i, data[i][j], ha=\"center\", va=\"center\", fontsize=10, color=color)\n\nax.set_title(\"Website Traffic by Day & Hour\", fontsize=16, fontweight=\"bold\")\nplt.colorbar(im, label=\"Visitors\")\nplt.tight_layout()\nplt.savefig(\"heatmap.png\", dpi=150)\nprint(\"Saved\")"
}'
```

### Storytelling with Data
*Source: data-visualization*

### The Narrative Arc

| Step | What to Do | Example |
|------|-----------|---------|
| 1. **Context** | Set up what the reader needs to know | "We track customer acquisition cost monthly" |
| 2. **Tension** | Show the problem or change | "CAC increased 40% in Q3" |
| 3. **Resolution** | Show the insight or solution | "But LTV increased 80%, so unit economics improved" |

### Title as Insight

```
❌ Descriptive titles (what the chart shows):
   "Q3 Revenue by Product Line"
   "Monthly Active Users 2024"
   "Customer Satisfaction Survey Results"

✅ Insight titles (what the chart means):
   "Enterprise product drives 70% of revenue growth"
   "User growth accelerated after the free tier launch"
   "Support response time is the #1 satisfaction driver"
```

### Annotation Techniques

| Technique | When to Use |
|-----------|------------|
| **Call-out label** | Highlight a specific data point ("Peak: 320K") |
| **Reference line** | Show target/benchmark ("Goal: 100K") |
| **Shaded region** | Mark a time period ("Product launch window") |
| **Arrow + text** | Draw attention to trend change |
| **Before/after line** | Show impact of an event |

### Dark Mode Charts
*Source: data-visualization*

```bash
infsh app run infsh/python-executor --input '{
  "code": "import matplotlib.pyplot as plt\nimport matplotlib\nmatplotlib.use(\"Agg\")\n\n# Dark theme\nplt.rcParams.update({\n    \"figure.facecolor\": \"#0f172a\",\n    \"axes.facecolor\": \"#0f172a\",\n    \"axes.edgecolor\": \"#334155\",\n    \"axes.labelcolor\": \"white\",\n    \"text.color\": \"white\",\n    \"xtick.color\": \"white\",\n    \"ytick.color\": \"white\",\n    \"grid.color\": \"#1e293b\"\n})\n\nfig, ax = plt.subplots(figsize=(12, 6))\nmonths = [\"Jan\", \"Feb\", \"Mar\", \"Apr\", \"May\", \"Jun\"]\nvalues = [45, 52, 58, 72, 85, 98]\n\nax.plot(months, values, color=\"#818cf8\", linewidth=3, marker=\"o\", markersize=8)\nax.fill_between(range(len(months)), values, alpha=0.15, color=\"#818cf8\")\nax.set_title(\"MRR Growth: On track for $100K\", fontsize=18, fontweight=\"bold\")\nax.set_ylabel(\"MRR ($K)\", fontsize=13)\nax.spines[\"top\"].set_visible(False)\nax.spines[\"right\"].set_visible(False)\nax.grid(axis=\"y\", alpha=0.2)\n\nfor i, v in enumerate(values):\n    ax.annotate(f\"${v}K\", (i, v), textcoords=\"offset points\", xytext=(0, 12), ha=\"center\", fontsize=11, fontweight=\"bold\")\n\nplt.tight_layout()\nplt.savefig(\"dark-chart.png\", dpi=150, facecolor=\"#0f172a\")\nprint(\"Saved\")"
}'
```

## §4. Data Quality

> validation, profiling, monitoring, great expectations, schema enforcement

## §5. Database Architecture

> schema design, normalization, indexing strategies, partitioning

## §6. Database Administration

> performance tuning, backup/recovery, monitoring, maintenance

## §7. SQL Optimization

> query plans, index selection, join optimization, PRAGMA tuning

## §8. Embedding Strategies

> text embeddings, chunking, models, dimension selection

### Document Chunking Strategies
*Source: rag-implementation*

### Recursive Character Text Splitter

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]  # Try in order
)

chunks = splitter.split_documents(documents)
```

### Token-Based Splitting

```python
from langchain_text_splitters import TokenTextSplitter

splitter = TokenTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    encoding_name="cl100k_base"  # OpenAI tiktoken encoding
)
```

### Semantic Chunking

```python
from langchain_experimental.text_splitter import SemanticChunker

splitter = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=95
)
```

### Markdown Header Splitter

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False
)
```

## §9. Vector Search

> FAISS, ChromaDB, pgvector, ANN algorithms, index types

## §10. RAG Patterns

> retrieval-augmented generation, chunking, reranking, hybrid search

### Document Chunking Strategies
*Source: rag-implementation*

### Recursive Character Text Splitter

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]  # Try in order
)

chunks = splitter.split_documents(documents)
```

### Token-Based Splitting

```python
from langchain_text_splitters import TokenTextSplitter

splitter = TokenTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    encoding_name="cl100k_base"  # OpenAI tiktoken encoding
)
```

### Semantic Chunking

```python
from langchain_experimental.text_splitter import SemanticChunker

splitter = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=95
)
```

### Markdown Header Splitter

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on,
    strip_headers=False
)
```

## §11. Similarity Search

> cosine similarity, BM25, TF-IDF, hybrid scoring

## Legal Citations Index

### MCR
- MCR 2.003
