# Startup Intelligence Engine (SIE) Methodology v1

## 1. Purpose

The Startup Intelligence Engine is an explainable startup intelligence framework designed to evaluate startups through structured, evidence-based analysis.

SIE is not just a report generator. Its purpose is to create a consistent methodology for understanding startup quality, fundraising readiness, investment potential, and company-building progress.

The system evaluates startups across six core intelligence pillars and produces a canonical `SIEMethodologyAnalysis` object that can power founder coaching, investor diligence, rankings, benchmarking, and historical tracking.

---

## 2. Core Intelligence Pillars

SIE evaluates every startup across six pillars:

1. Market Intelligence
2. Team Intelligence
3. Product Intelligence
4. Execution Intelligence
5. Traction Intelligence
6. Financial Health

Each pillar produces a structured analysis using the same standard contract.

---

## 3. Standard Analysis Contract

Every intelligence pillar should return:

- `summary`
- `confidence`
- `strengths`
- `weaknesses`
- `evidence`
- `recommendations`
- `score_breakdown`

This creates consistency across the methodology and allows the platform to compare, rank, benchmark, and track startups over time.

---

## 4. Scoring Methodology

Each pillar is scored using weighted subscores.

### Market Intelligence

| Dimension             | Weight |
| --------------------- | -----: |
| Market Size           |   0.25 |
| Market Growth         |   0.20 |
| Market Timing         |   0.20 |
| Competitive Intensity |   0.15 |
| Customer Demand       |   0.20 |

### Team Intelligence

| Dimension              | Weight |
| ---------------------- | -----: |
| Founder-Market Fit     |   0.25 |
| Technical Capability   |   0.20 |
| Business Capability    |   0.20 |
| Leadership             |   0.20 |
| Execution Track Record |   0.15 |

### Product Intelligence

| Dimension          | Weight |
| ------------------ | -----: |
| Customer Value     |   0.25 |
| Differentiation    |   0.20 |
| Usability          |   0.15 |
| Defensibility      |   0.20 |
| Adoption Potential |   0.20 |

### Execution Intelligence

| Dimension              | Weight |
| ---------------------- | -----: |
| Go-to-Market Execution |   0.20 |
| Product Execution      |   0.20 |
| Operational Execution  |   0.20 |
| Strategic Execution    |   0.20 |
| Execution Velocity     |   0.20 |

### Traction Intelligence

| Dimension             | Weight |
| --------------------- | -----: |
| Customer Growth       |   0.20 |
| Revenue Growth        |   0.20 |
| Retention             |   0.20 |
| Engagement            |   0.20 |
| Commercial Validation |   0.20 |

### Financial Health

| Dimension             | Weight |
| --------------------- | -----: |
| Revenue Quality       |   0.20 |
| Unit Economics        |   0.20 |
| Burn Efficiency       |   0.20 |
| Runway                |   0.20 |
| Fundraising Readiness |   0.20 |

---

## 5. Pillar Score Calculation

Each pillar score is calculated as a weighted average of its subscores.

Example:

```text
Product Score =
(Customer Value * 0.25) +
(Differentiation * 0.20) +
(Usability * 0.15) +
(Defensibility * 0.20) +
(Adoption Potential * 0.20)
```
