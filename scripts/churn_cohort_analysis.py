import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Set aesthetic styling for charts
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['figure.dpi'] = 300

def run_churn_analysis():
    print("Starting comprehensive Customer Retention & Churn Analysis...")
    os.makedirs('visualizations', exist_ok=True)
    os.makedirs('dashboard', exist_ok=True)
    
    # 1. Load Data
    data_path = os.path.join('data', 'saas_customer_churn_data.csv')
    df = pd.read_csv(data_path)
    df['SignupDate'] = pd.to_datetime(df['SignupDate'])
    
    total_customers = len(df)
    churned_customers = int(df['ChurnStatus'].sum())
    active_customers = total_customers - churned_customers
    churn_rate = churned_customers / total_customers
    retention_rate = 1.0 - churn_rate
    
    total_mrr = float(df['MonthlyRecurringRevenue'].sum())
    churned_mrr = float(df[df['ChurnStatus'] == 1]['MonthlyRecurringRevenue'].sum())
    retained_mrr = total_mrr - churned_mrr
    mrr_churn_rate = churned_mrr / total_mrr
    
    avg_tenure = float(df['TenureMonths'].mean())
    avg_ltv = float(df['CustomerLifetimeValue'].mean())
    avg_mrr = float(df['MonthlyRecurringRevenue'].mean())
    
    print(f"Dataset Metrics: Total={total_customers}, Churn Rate={churn_rate:.1%}, Retained MRR=${retained_mrr:,.2f}")

    # =========================================================================
    # 2. Cohort Retention Analysis (Signup Cohort x Month-on-Month Retention)
    # =========================================================================
    print("\nCalculating Triangular Cohort Retention Matrix...")
    
    # For each customer, determine active status at month 0, 1, 2, ..., 12
    cohort_months = sorted(df['CohortMonth'].unique())
    max_cohort_span = 12
    
    cohort_table_records = []
    
    for cm in cohort_months:
        cohort_df = df[df['CohortMonth'] == cm]
        cohort_size = len(cohort_df)
        
        # Calculate maximum possible months elapsed since this cohort joined (as of 2024-12-31)
        signup_dt = pd.to_datetime(cm + "-01")
        months_since_signup = int((pd.to_datetime("2024-12-31") - signup_dt).days / 30.4)
        
        row = {'CohortMonth': cm, 'CohortSize': cohort_size}
        
        for m in range(0, max_cohort_span + 1):
            if m > months_since_signup:
                row[f'M_{m}'] = np.nan
            else:
                # Active if customer hasn't churned, or churned after month m
                active_count = len(cohort_df[(cohort_df['ChurnStatus'] == 0) | (cohort_df['TenureMonths'] >= m)])
                retention_pct = round((active_count / cohort_size) * 100, 1)
                row[f'M_{m}'] = retention_pct
                
        cohort_table_records.append(row)
        
    cohort_df_matrix = pd.DataFrame(cohort_table_records)
    cohort_df_matrix.to_csv(os.path.join('data', 'cohort_retention_matrix.csv'), index=False)
    
    # Generate Cohort Heatmap Visualization (Select last 12 cohorts for clean presentation)
    display_cohorts = cohort_df_matrix.tail(12).set_index('CohortMonth')
    retention_columns = [f'M_{i}' for i in range(1, 13)]
    heatmap_data = display_cohorts[retention_columns]
    
    plt.figure(figsize=(13, 7))
    # Elegant, rich modern colormap for retention matrix
    cmap_retention = sns.color_palette("crest", as_cmap=True)
    ax = sns.heatmap(
        heatmap_data, 
        annot=True, 
        fmt=".1f", 
        cmap=cmap_retention, 
        vmin=20, 
        vmax=100,
        cbar_kws={'label': 'Retention Rate (%)'},
        linewidths=1.2,
        linecolor='#ffffff'
    )
    plt.title("SaaS Customer Retention Heatmap by Monthly Cohort (% Retained)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Months Since Customer Onboarding", fontsize=11, labelpad=10)
    plt.ylabel("Signup Cohort", fontsize=11)
    plt.xticks(np.arange(12) + 0.5, [f"Month {i}" for i in range(1, 13)], rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join('visualizations', 'cohort_retention_heatmap.png'), dpi=300)
    plt.close()
    print("Saved cohort_retention_heatmap.png")

    # =========================================================================
    # 3. Customer Lifetime & Survival Curve Analysis (Kaplan-Meier Style)
    # =========================================================================
    print("\nComputing Customer Survival Probability & Churn Hazard Rates...")
    
    max_tenure_observed = int(df['TenureMonths'].max())
    tenure_bins = range(1, max_tenure_observed + 1)
    survival_records = []
    
    at_risk = total_customers
    cumulative_survival = 1.0
    
    for t in tenure_bins:
        # Churned exactly at tenure t
        churned_at_t = len(df[(df['ChurnStatus'] == 1) & (df['TenureMonths'] == t)])
        # Censored / active at tenure t
        censored_at_t = len(df[(df['ChurnStatus'] == 0) & (df['TenureMonths'] == t)])
        
        hazard_rate = churned_at_t / at_risk if at_risk > 0 else 0
        cumulative_survival *= (1.0 - hazard_rate)
        
        survival_records.append({
            'TenureMonth': t,
            'AtRisk': at_risk,
            'Churned': churned_at_t,
            'HazardRate': round(hazard_rate * 100, 2),
            'SurvivalProbability': round(cumulative_survival * 100, 2)
        })
        
        at_risk -= (churned_at_t + censored_at_t)
        if at_risk <= 0:
            break
            
    survival_df = pd.DataFrame(survival_records)
    survival_df.to_csv(os.path.join('data', 'customer_survival_rates.csv'), index=False)
    
    # Plot Kaplan-Meier Survival Curve & Hazard Spikes
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Electric Cyan & Indigo Survival Curve
    ax1.plot(survival_df['TenureMonth'], survival_df['SurvivalProbability'], marker='o', color='#06b6d4', linewidth=3, markersize=5.5)
    ax1.fill_between(survival_df['TenureMonth'], survival_df['SurvivalProbability'], alpha=0.18, color='#06b6d4')
    ax1.axvline(x=1, color='#f43f5e', linestyle='--', linewidth=2, label='Month 1 Onboarding Cliff')
    ax1.axvline(x=12, color='#f59e0b', linestyle='--', linewidth=2, label='Month 12 Contract Renewal')
    ax1.set_title("Customer Survival Curve Over Lifetime (Tenure)", fontsize=13, fontweight='bold', pad=12)
    ax1.set_xlabel("Tenure (Months)", fontsize=10, labelpad=8)
    ax1.set_ylabel("Survival Probability (%)", fontsize=10)
    ax1.set_ylim(0, 105)
    ax1.legend(loc='lower left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1')
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Gradient-style Hazard Bars
    hazard_colors = [
        '#f43f5e' if val > 8 else ('#f59e0b' if val > 4 else '#38bdf8') 
        for val in survival_df['HazardRate']
    ]
    ax2.bar(survival_df['TenureMonth'], survival_df['HazardRate'], color=hazard_colors, edgecolor='#334155', alpha=0.9, width=0.7)
    ax2.set_title("Monthly Churn Hazard Rate (% Leaving at Month t)", fontsize=13, fontweight='bold', pad=12)
    ax2.set_xlabel("Tenure (Months)", fontsize=10, labelpad=8)
    ax2.set_ylabel("Hazard Rate (%)", fontsize=10)
    ax2.grid(True, linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(os.path.join('visualizations', 'survival_curve_tenure.png'), dpi=300)
    plt.close()
    print("Saved survival_curve_tenure.png")

    # =========================================================================
    # 4. Segment Breakdown (Contract, Plan, Onboarding, Support)
    # =========================================================================
    print("\nAnalyzing Churn by Customer Segments...")
    
    segment_contract = df.groupby('ContractType').agg(
        TotalCustomers=('CustomerID', 'count'),
        Churned=('ChurnStatus', 'sum'),
        ChurnRate=('ChurnStatus', 'mean'),
        TotalMRR=('MonthlyRecurringRevenue', 'sum'),
        ChurnedMRR=('MonthlyRecurringRevenue', lambda s: s[df.loc[s.index, 'ChurnStatus'] == 1].sum())
    ).reset_index()
    segment_contract['ChurnRatePct'] = (segment_contract['ChurnRate'] * 100).round(1)
    
    segment_plan = df.groupby('PlanTier').agg(
        TotalCustomers=('CustomerID', 'count'),
        Churned=('ChurnStatus', 'sum'),
        ChurnRate=('ChurnStatus', 'mean'),
        TotalMRR=('MonthlyRecurringRevenue', 'sum'),
        ChurnedMRR=('MonthlyRecurringRevenue', lambda s: s[df.loc[s.index, 'ChurnStatus'] == 1].sum())
    ).reset_index()
    segment_plan['ChurnRatePct'] = (segment_plan['ChurnRate'] * 100).round(1)
    
    segment_onboard = df.groupby('OnboardingCompleted').agg(
        TotalCustomers=('CustomerID', 'count'),
        Churned=('ChurnStatus', 'sum'),
        ChurnRate=('ChurnStatus', 'mean'),
        TotalMRR=('MonthlyRecurringRevenue', 'sum'),
        ChurnedMRR=('MonthlyRecurringRevenue', lambda s: s[df.loc[s.index, 'ChurnStatus'] == 1].sum())
    ).reset_index()
    segment_onboard['ChurnRatePct'] = (segment_onboard['ChurnRate'] * 100).round(1)
    
    # Save combined segment CSV
    segment_contract.to_csv(os.path.join('data', 'segment_contract_analysis.csv'), index=False)
    segment_plan.to_csv(os.path.join('data', 'segment_plan_analysis.csv'), index=False)
    segment_onboard.to_csv(os.path.join('data', 'segment_onboarding_analysis.csv'), index=False)
    
    # Plot Plan & Contract Comparison Chart
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    colors_plan = ['#06b6d4', '#6366f1', '#a855f7']
    bars1 = axes[0].bar(segment_plan['PlanTier'], segment_plan['ChurnRatePct'], color=colors_plan, edgecolor='#1e293b', width=0.55)
    axes[0].set_title("Customer Churn Rate by Plan Tier", fontsize=12, fontweight='bold', pad=10)
    axes[0].set_ylabel("Churn Rate (%)", fontsize=10)
    axes[0].set_ylim(0, 60)
    for bar in bars1:
        yval = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2, yval + 1.2, f"{yval:.1f}%", ha='center', fontweight='bold', fontsize=10)
    axes[0].grid(axis='y', linestyle=':', alpha=0.6)
    
    colors_contract = ['#10b981', '#f43f5e']
    bars2 = axes[1].bar(segment_contract['ContractType'], segment_contract['ChurnRatePct'], color=colors_contract, edgecolor='#1e293b', width=0.45)
    axes[1].set_title("Customer Churn Rate by Contract Type", fontsize=12, fontweight='bold', pad=10)
    axes[1].set_ylabel("Churn Rate (%)", fontsize=10)
    axes[1].set_ylim(0, 70)
    for bar in bars2:
        yval = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2, yval + 1.5, f"{yval:.1f}%", ha='center', fontweight='bold', fontsize=10)
    axes[1].grid(axis='y', linestyle=':', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(os.path.join('visualizations', 'churn_by_plan_and_contract.png'), dpi=300)
    plt.close()
    print("Saved churn_by_plan_and_contract.png")

    # =========================================================================
    # 5. Primary Churn Reasons Pareto Breakdown
    # =========================================================================
    churn_reasons_df = df[df['ChurnStatus'] == 1]['PrimaryChurnReason'].value_counts().reset_index()
    churn_reasons_df.columns = ['ChurnReason', 'Count']
    churn_reasons_df['Percentage'] = (churn_reasons_df['Count'] / churned_customers * 100).round(1)
    churn_reasons_df['CumulativePct'] = churn_reasons_df['Percentage'].cumsum().round(1)
    churn_reasons_df.to_csv(os.path.join('data', 'churn_reasons_pareto.csv'), index=False)
    
    plt.figure(figsize=(10, 5))
    palette_reasons = ['#f43f5e', '#fb7185', '#f97316', '#fbbf24', '#a855f7', '#06b6d4'][::-1]
    bars = plt.barh(churn_reasons_df['ChurnReason'][::-1], churn_reasons_df['Count'][::-1], color=palette_reasons, edgecolor='#1e293b')
    plt.title("Primary Drivers of Customer Churn (Root Cause Breakdown)", fontsize=13, fontweight='bold', pad=15)
    plt.xlabel("Number of Churned Customers", fontsize=10)
    for bar in bars:
        w = bar.get_width()
        pct = (w / churned_customers) * 100
        plt.text(w + 15, bar.get_y() + bar.get_height()/2, f"{int(w):,} ({pct:.1f}%)", va='center', fontsize=9, fontweight='bold')
    plt.xlim(0, max(churn_reasons_df['Count']) * 1.25)
    plt.tight_layout()
    plt.savefig(os.path.join('visualizations', 'churn_reasons_pareto.png'), dpi=300)
    plt.close()
    print("Saved churn_reasons_pareto.png")

    # =========================================================================
    # 6. Retention Drivers & Feature Importance (Machine Learning)
    # =========================================================================
    print("\nTraining Predictive Model to Calculate Retention Drivers...")
    
    feature_cols = [
        'ContractType_Month-to-Month', 'OnboardingCompleted_No', 'FeatureAdoptionScore',
        'MonthlyActiveUsageHours', 'SupportTicketsCount', 'AvgResolutionTimeHours',
        'NPSScore', 'DiscountsApplied_Yes', 'PlanTier_Enterprise', 'PlanTier_Starter'
    ]
    
    df_ml = pd.get_dummies(df[[
        'ContractType', 'OnboardingCompleted', 'FeatureAdoptionScore',
        'MonthlyActiveUsageHours', 'SupportTicketsCount', 'AvgResolutionTimeHours',
        'NPSScore', 'DiscountsApplied', 'PlanTier', 'ChurnStatus'
    ]], drop_first=True)
    
    X = df_ml.drop('ChurnStatus', axis=1)
    y = df_ml['ChurnStatus']
    
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    rf.fit(X, y)
    
    feat_importances = pd.DataFrame({
        'Feature': X.columns,
        'Importance': rf.feature_importances_
    }).sort_values('Importance', ascending=False)
    feat_importances['ImportancePct'] = (feat_importances['Importance'] * 100).round(1)
    feat_importances.to_csv(os.path.join('data', 'retention_drivers_importance.csv'), index=False)
    
    # Clean feature names for visualization
    name_map = {
        'OnboardingCompleted_Yes': 'Onboarding Completed (Positive)',
        'ContractType_Month-to-Month': 'Month-to-Month Contract (Risk Factor)',
        'FeatureAdoptionScore': 'Feature Adoption Score (Positive)',
        'AvgResolutionTimeHours': 'Support Resolution Time (Risk Factor)',
        'NPSScore': 'Net Promoter Score / Satisfaction',
        'MonthlyActiveUsageHours': 'Monthly Active Usage Hours',
        'SupportTicketsCount': 'Support Tickets Volume',
        'PlanTier_Starter': 'Starter Plan Tier',
        'PlanTier_Professional': 'Professional Plan Tier',
        'DiscountsApplied_Yes': 'Discount Promotion Applied'
    }
    feat_importances['FeatureLabel'] = feat_importances['Feature'].map(lambda x: name_map.get(x, x))
    
    plt.figure(figsize=(10, 5))
    bars_fi = plt.barh(feat_importances['FeatureLabel'][::-1], feat_importances['ImportancePct'][::-1], color='#6366f1', edgecolor='#312e81')
    plt.title("Key Retention Drivers & Churn Predictors (Feature Importance %)", fontsize=13, fontweight='bold', pad=15)
    plt.xlabel("Relative Importance Weight (%)", fontsize=10)
    for bar in bars_fi:
        w = bar.get_width()
        plt.text(w + 0.6, bar.get_y() + bar.get_height()/2, f"{w:.1f}%", va='center', fontsize=9, fontweight='bold')
    plt.xlim(0, max(feat_importances['ImportancePct']) * 1.2)
    plt.tight_layout()
    plt.savefig(os.path.join('visualizations', 'churn_drivers_feature_importance.png'), dpi=300)
    plt.close()
    print("Saved churn_drivers_feature_importance.png")

    # =========================================================================
    # 7. Customer Risk Scoring for Retention Operations Playbook
    # =========================================================================
    # Calculate churn risk probabilities for active customers
    churn_probs = rf.predict_proba(X)[:, 1]
    df['ChurnRiskScore'] = np.round(churn_probs * 100, 1)
    
    def assign_risk_tier(prob):
        if prob >= 70:
            return 'High Risk (Immediate Action)'
        elif prob >= 40:
            return 'Medium Risk (Monitor & Nurture)'
        else:
            return 'Low Risk (Healthy)'
            
    df['RiskTier'] = df['ChurnRiskScore'].apply(assign_risk_tier)
    
    # Priority At-Risk Accounts (Active accounts with high MRR and High Risk)
    at_risk_active = df[(df['ChurnStatus'] == 0) & (df['ChurnRiskScore'] >= 50)].sort_values(
        ['MonthlyRecurringRevenue', 'ChurnRiskScore'], ascending=[False, False]
    )
    at_risk_active.head(100).to_csv(os.path.join('data', 'top_at_risk_customers_watchlist.csv'), index=False)
    print(f"Identified {len(at_risk_active)} active at-risk customers saved to top_at_risk_customers_watchlist.csv")

    # =========================================================================
    # 8. Export Master Analytics JSON for Interactive Dashboard Web App
    # =========================================================================
    dashboard_payload = {
        'summary': {
            'totalCustomers': total_customers,
            'activeCustomers': active_customers,
            'churnedCustomers': churned_customers,
            'churnRate': round(churn_rate * 100, 2),
            'retentionRate': round(retention_rate * 100, 2),
            'totalMRR': round(total_mrr, 2),
            'retainedMRR': round(retained_mrr, 2),
            'churnedMRR': round(churned_mrr, 2),
            'mrrChurnRate': round(mrr_churn_rate * 100, 2),
            'avgTenureMonths': round(avg_tenure, 1),
            'avgLTV': round(avg_ltv, 2),
            'avgMRR': round(avg_mrr, 2),
            'highRiskActiveCount': int((df[(df['ChurnStatus'] == 0) & (df['ChurnRiskScore'] >= 70)]).shape[0]),
            'highRiskActiveMRR': round(float(df[(df['ChurnStatus'] == 0) & (df['ChurnRiskScore'] >= 70)]['MonthlyRecurringRevenue'].sum()), 2)
        },
        'cohorts': cohort_df_matrix.tail(12).fillna('').to_dict(orient='records'),
        'survival': survival_df.to_dict(orient='records'),
        'segments': {
            'byPlan': segment_plan.to_dict(orient='records'),
            'byContract': segment_contract.to_dict(orient='records'),
            'byOnboarding': segment_onboard.to_dict(orient='records')
        },
        'reasons': churn_reasons_df.to_dict(orient='records'),
        'drivers': feat_importances[['FeatureLabel', 'ImportancePct']].to_dict(orient='records'),
        'sampleCustomers': df[['CustomerID', 'CustomerName', 'PlanTier', 'ContractType', 'OnboardingCompleted', 
                               'FeatureAdoptionScore', 'MonthlyRecurringRevenue', 'TenureMonths', 
                               'ChurnRiskScore', 'RiskTier', 'ChurnStatus', 'PrimaryChurnReason']].head(60).to_dict(orient='records')
    }
    
    with open(os.path.join('dashboard', 'analytics_data.json'), 'w') as f:
        json.dump(dashboard_payload, f, indent=2)
    print("Saved dashboard/analytics_data.json successfully.")
    
    print("\nAll Customer Retention & Churn calculations and visualizations completed!")

if __name__ == '__main__':
    run_churn_analysis()
