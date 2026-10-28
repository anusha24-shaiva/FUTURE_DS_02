# 📊 Power BI Retention & Churn Analytics Dashboard Blueprint

This comprehensive implementation guide enables BI developers, data analysts, and analytics engineers to build and deploy an enterprise-grade Customer Retention & Churn Dashboard in **Microsoft Power BI Desktop / Power BI Service**.

---

## 1. 🏗️ Data Architecture & Star Schema Model

To optimize Power BI VertiPaq engine performance and ensure fast visual rendering, use the following **Star Schema**:

```
                  ┌──────────────────────┐
                  │       Dim_Date       │
                  │ (Calendar Hierarchy) │
                  └──────────┬───────────┘
                             │ 1
                             │
                             │ * (SignupDate)
┌───────────────────┐        ▼        ┌───────────────────┐
│   Dim_Customer    │ 1             * │     Dim_Plan      │
│  (Customer Demo,  ├─────────────────┤  (Plan Tiers,     │
│   Company Size)   │                 │   Base Pricing)   │
└───────────────────┘                 └─────────┬─────────┘
          │ 1                                   │ 1
          │                                     │
          │ *                                   │ *
          └──────────────────► ◄────────────────┘
                       ┌──────────────────────┐
                       │  Fact_Subscriptions  │
                       │  (Monthly Records,   │
                       │   MRR, Churn Status) │
                       └──────────────────────┘
```

### Table Specifications:
- **`Fact_Subscriptions`**: Primary transactional table containing `CustomerID`, `SignupDate`, `CohortMonth`, `PlanTier`, `ContractType`, `PaymentMethod`, `MonthlyRecurringRevenue`, `TenureMonths`, `ChurnStatus`, `ChurnDate`, `PrimaryChurnReason`, `FeatureAdoptionScore`, `SupportTicketsCount`, `AvgResolutionTimeHours`.
- **`Dim_Customer`**: Unique `CustomerID`, `CustomerName`, `CompanySize`, `Industry`, `Country`.
- **`Dim_Plan`**: `PlanTier` (`Starter`, `Professional`, `Enterprise`), `BaseMonthlyPrice`, `TargetSegment`.
- **`Dim_Date`**: Standard Date Table from `2023-01-01` to `2024-12-31` with `Year`, `Month`, `MonthYear`, `Quarter`, `Day`.

---

## 2. 🧮 Production DAX Measure Library

Create a dedicated measure table called `_KeyMeasures` and insert the following DAX calculations:

### Customer Volume & Status Measures
```dax
-- Total Customers Ever Signed Up
Total Customers = 
COUNTROWS(Fact_Subscriptions)

-- Active Retained Customers
Active Customers = 
CALCULATE(
    COUNTROWS(Fact_Subscriptions),
    Fact_Subscriptions[ChurnStatus] = 0
)

-- Churned Customers
Churned Customers = 
CALCULATE(
    COUNTROWS(Fact_Subscriptions),
    Fact_Subscriptions[ChurnStatus] = 1
)

-- Customer Churn Rate %
Customer Churn Rate % = 
DIVIDE([Churned Customers], [Total Customers], 0)

-- Customer Retention Rate %
Customer Retention Rate % = 
1 - [Customer Churn Rate %]
```

### Revenue & Unit Economics Measures
```dax
-- Total Monthly Recurring Revenue (MRR)
Total MRR = 
SUM(Fact_Subscriptions[MonthlyRecurringRevenue])

-- Retained Active MRR
Retained MRR = 
CALCULATE(
    SUM(Fact_Subscriptions[MonthlyRecurringRevenue]),
    Fact_Subscriptions[ChurnStatus] = 0
)

-- Churned MRR
Churned MRR = 
CALCULATE(
    SUM(Fact_Subscriptions[MonthlyRecurringRevenue]),
    Fact_Subscriptions[ChurnStatus] = 1
)

-- MRR Churn Rate %
MRR Churn Rate % = 
DIVIDE([Churned MRR], [Total MRR], 0)

-- Annualized Recurring Revenue (ARR)
Total ARR = 
[Total MRR] * 12

-- Churned ARR Leaked
Churned ARR = 
[Churned MRR] * 12

-- Average Revenue Per User (ARPU)
ARPU = 
DIVIDE([Total MRR], [Total Customers], 0)

-- Average Customer Lifetime (in Months)
Avg Customer Lifetime Months = 
AVERAGE(Fact_Subscriptions[TenureMonths])

-- Customer Lifetime Value (LTV)
Customer Lifetime Value = 
[ARPU] * [Avg Customer Lifetime Months]
```

### Advanced Cohort Retention DAX
```dax
-- Cohort Retention Rate % across Month N
Cohort Retention % = 
VAR OriginalCohortSize = 
    CALCULATE(
        [Total Customers],
        ALLEXCEPT(Fact_Subscriptions, Fact_Subscriptions[CohortMonth])
    )
VAR SurvivingCustomers = 
    CALCULATE(
        COUNTROWS(Fact_Subscriptions),
        FILTER(
            Fact_Subscriptions,
            Fact_Subscriptions[ChurnStatus] = 0 || 
            Fact_Subscriptions[TenureMonths] >= SELECTEDVALUE(Dim_TenureMonth[MonthNumber])
        )
    )
RETURN
    DIVIDE(SurvivingCustomers, OriginalCohortSize, 0)
```

### Risk & Proactive Intervention Measures
```dax
-- High Churn Risk Accounts Watchlist
High Risk Accounts Count = 
CALCULATE(
    COUNTROWS(Fact_Subscriptions),
    Fact_Subscriptions[ChurnStatus] = 0,
    Fact_Subscriptions[ChurnRiskScore] >= 70
)

-- High Risk MRR at Stake
High Risk MRR = 
CALCULATE(
    SUM(Fact_Subscriptions[MonthlyRecurringRevenue]),
    Fact_Subscriptions[ChurnStatus] = 0,
    Fact_Subscriptions[ChurnRiskScore] >= 70
)
```

---

## 3. 🖥️ 4-Page Power BI Report Blueprint

### Page 1: Executive KPI & Revenue Pulse
- **Visual 1 (Top Ribbon Cards)**: `[Active Customers]`, `[Customer Churn Rate %]`, `[Total MRR]`, `[Churned ARR]`, `[Average Customer Lifetime Months]`.
- **Visual 2 (Line Chart)**: Monthly Churn Trend vs. Target Benchmark (5.0% monthly ceiling).
- **Visual 3 (Waterfall Chart)**: MRR Bridge (`Starting MRR` ➔ `New Signups MRR` ➔ `Contraction/Churned MRR` ➔ `Ending MRR`).
- **Visual 4 (Donut / Treemap)**: Active vs. Churned Accounts by Plan Tier.
- **Slicers**: Date Range Slider, Plan Tier (`Starter`, `Pro`, `Enterprise`), Contract Type (`Monthly`, `Annual`).

### Page 2: Cohort Decay & Lifetime Survival Matrix
- **Visual 1 (Matrix Visual - Cohort Heatmap)**:
  - Rows: `CohortMonth` (e.g. `2024-01`, `2024-02`, etc.)
  - Columns: `TenureMonth` (Month 1 to Month 12)
  - Values: `[Cohort Retention %]`
  - Conditional Formatting: Background color scale from Red (30%) ➔ Yellow (60%) ➔ Green (100%).
- **Visual 2 (Area Chart - Survival Curve)**:
  - X-Axis: `TenureMonths` (1 to 24)
  - Y-Axis: Cumulative Survival Probability %
  - Highlight Markers: Month 1 Onboarding Cliff and Month 12 Renewal Boundary.

### Page 3: Churn Driver Pareto & Root Cause Diagnostics
- **Visual 1 (Pareto Bar & Line Combo)**:
  - Bars: Number of churned accounts by `PrimaryChurnReason`.
  - Line: Cumulative Churn Percentage (`80/20 rule threshold`).
- **Visual 2 (Decomposition Tree Visual)**:
  - Root: `[Churn Rate %]`
  - Explain By: `ContractType` ➔ `OnboardingCompleted` ➔ `AvgResolutionTimeHours` ➔ `PlanTier`.
- **Visual 3 (Scatter Plot)**:
  - X-Axis: `AvgResolutionTimeHours` (Support Latency)
  - Y-Axis: `FeatureAdoptionScore`
  - Size: `MonthlyRecurringRevenue`
  - Color: `ChurnStatus` (Red = Churned, Green = Retained).

### Page 4: At-Risk Account Watchlist & Action Playbook
- **Visual 1 (Table Visual - Customer Success Worklist)**:
  - Columns: `CustomerID`, `CustomerName`, `PlanTier`, `MRR`, `FeatureAdoptionScore`, `SupportTicketsCount`, `ChurnRiskScore`, `RecommendedPlaybookAction`.
- **Visual 2 (Gauge Visual)**:
  - High-Risk MRR Exposed vs. Quarterly Retention Goal.
- **Interactive Action Button**: Export table to Excel / CSV for immediate CSM outreach.

---

## 4. 🎨 Design & Styling Guidelines
- **Theme**: Dark Navy / Executive Slate (`#0F172A`, `#1E293B`, `#2563EB`, `#10B981`, `#EF4444`).
- **Typography**: Segoe UI / Aptos, clean sans-serif.
- **Grid Layout**: 8px grid alignment with card borders (1px solid `#334155`) and 8px border radius.
