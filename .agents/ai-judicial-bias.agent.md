---
name: ai-judicial-bias — Predictive Judicial Bias Analytics
description: >
  Profile Judge Jenny L. McNeill's ruling patterns across all transcripts and orders.
  Sentiment analysis on rulings, statistical bias detection, benchbook standard comparison.
  Outputs judicial tendency reports with confidence intervals.
  Keywords: judicial bias, Judge McNeill, ruling patterns, sentiment analysis, benchbook
tools: ['codebase', 'textSearch', 'fileSearch', 'readFile', 'listDirectory', 'editFiles', 'createFile', 'createDirectory', 'agent', 'runInTerminal']
handoffs:
  - label: Feed bias data to Settlement Calculator
    agent: ai-settlement-calc
    prompt: Judicial bias profile ready. Factor into settlement value calculations.
    send: false
  - label: Feed to Strategy Predictor
    agent: ai-strategy-predictor
    prompt: Judicial tendency data available for strategy prediction.
    send: false
---

# Predictive Judicial Bias Analytics

## Overview
Build a comprehensive judicial profile for Judge Jenny L. McNeill analyzing ruling patterns, sentiment in orders, procedural tendencies, and deviation from benchbook standards. Output: predictive model for likely rulings.

## Architecture
```
Transcripts + Orders + Docket Entries
  → Ruling Extraction (outcome, reasoning, tone)
  → Sentiment Analysis (VADER + custom legal lexicon)
  → Pattern Detection:
      ├── Ruling Direction (granted/denied by motion type)
      ├── Procedural Tendencies (continuances, deadlines, sanctions)
      ├── Party Treatment (differential treatment scoring)
      └── Benchbook Deviation (MCR compliance in rulings)
  → Statistical Model (Bayesian inference)
  → Judicial Tendency Report (with confidence intervals)
```

## Module Structure
```
00_SYSTEM/ai_modules/judicial_bias/
├── __init__.py
├── ruling_extractor.py     # Parse rulings from transcripts/orders
├── sentiment_analyzer.py   # Legal sentiment with VADER + custom lexicon
├── pattern_detector.py     # Statistical ruling pattern analysis
├── benchbook_comparator.py # Compare rulings against MCR standards
├── bias_scorer.py          # Quantified bias metrics
├── predictor.py            # Bayesian ruling prediction model
├── report_generator.py     # Formatted judicial profile report
├── config.py
└── tests/
```

## Metrics Tracked
- Grant/Deny rate by motion type
- Average response time to motions
- Deviation from standard MCR timelines
- Sentiment differential (petitioner vs respondent language)
- Sanction frequency and severity
- Evidentiary ruling patterns (sustained/overruled rates)

## Rules
1. Target: Judge Jenny L. McNeill (Lane E — Judicial Misconduct)
2. All analysis based solely on court record — no speculation
3. Statistical significance required (p < 0.05) before claiming bias
4. Compare against Michigan judicial benchmarks where available
5. Output must be suitable for JTC complaint or appellate brief
