import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_saas_churn_dataset(n_customers=5000, seed=42):
    np.random.seed(seed)
    random.seed(seed)
    
    observation_end_date = datetime(2024, 12, 31)
    start_date = datetime(2023, 1, 1)
    total_days = (datetime(2024, 11, 30) - start_date).days
    
    industries = ['Fintech', 'E-commerce', 'Healthtech', 'Edtech', 'Martech', 'DevTools', 'Consulting']
    industry_weights = [0.22, 0.20, 0.15, 0.14, 0.13, 0.10, 0.06]
    
    company_sizes = ['1-10 (Startup)', '11-50 (Small)', '51-200 (Mid-Market)', '201-1000 (Enterprise)']
    size_weights = [0.42, 0.32, 0.18, 0.08]
    
    countries = ['United States', 'United Kingdom', 'Germany', 'Canada', 'Australia', 'India', 'France']
    country_weights = [0.45, 0.16, 0.12, 0.10, 0.07, 0.06, 0.04]
    
    plans = ['Starter', 'Professional', 'Enterprise']
    plan_weights = [0.50, 0.35, 0.15]
    plan_prices = {'Starter': 29, 'Professional': 99, 'Enterprise': 299}
    
    first_names = ['Apex', 'Cloud', 'Nexus', 'Pulse', 'Hyper', 'Nova', 'Vortex', 'Zenith', 'Echo', 'Sync',
                   'Peak', 'Flow', 'Quantum', 'Alpha', 'Velocity', 'Orbit', 'Loom', 'Starlight', 'Catalyst', 'Beacon']
    last_names = ['Analytics', 'Technologies', 'Labs', 'Solutions', 'Software', 'Networks', 'Dynamics', 'Digital',
                  'Ventures', 'Interactive', 'Data', 'Systems', 'Media', 'Global', 'Logistics', 'Security', 'Fintech', 'Consulting']
    
    data = []
    
    for i in range(1, n_customers + 1):
        cust_id = f"CUST-{10000 + i}"
        cust_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Signup Date
        # Slightly increasing signups over time (business growth)
        signup_bias = np.random.power(1.3)
        signup_day_offset = int(signup_bias * total_days)
        signup_date = start_date + timedelta(days=signup_day_offset)
        cohort_month = signup_date.strftime("%Y-%m")
        
        # Plan & Contract
        plan = np.random.choice(plans, p=plan_weights)
        mrr_base = plan_prices[plan]
        
        # Enterprise prefers Annual; Starter prefers Monthly
        if plan == 'Enterprise':
            contract = np.random.choice(['Annual', 'Month-to-Month'], p=[0.75, 0.25])
            comp_size = np.random.choice(company_sizes, p=[0.05, 0.15, 0.45, 0.35])
            pay_method = np.random.choice(['Invoicing', 'Credit Card', 'ACH / Direct Debit'], p=[0.55, 0.25, 0.20])
        elif plan == 'Professional':
            contract = np.random.choice(['Annual', 'Month-to-Month'], p=[0.45, 0.55])
            comp_size = np.random.choice(company_sizes, p=[0.25, 0.45, 0.25, 0.05])
            pay_method = np.random.choice(['Credit Card', 'ACH / Direct Debit', 'PayPal'], p=[0.60, 0.25, 0.15])
        else: # Starter
            contract = np.random.choice(['Annual', 'Month-to-Month'], p=[0.18, 0.82])
            comp_size = np.random.choice(company_sizes, p=[0.65, 0.25, 0.08, 0.02])
            pay_method = np.random.choice(['Credit Card', 'PayPal', 'ACH / Direct Debit'], p=[0.70, 0.22, 0.08])
            
        industry = np.random.choice(industries, p=industry_weights)
        country = np.random.choice(countries, p=country_weights)
        
        # Discount (10% to 20% off)
        discount_applied = np.random.choice(['Yes', 'No'], p=[0.28, 0.72])
        if discount_applied == 'Yes':
            discount_pct = np.random.choice([0.10, 0.15, 0.20])
            mrr = round(mrr_base * (1 - discount_pct), 2)
        else:
            mrr = float(mrr_base)
            
        # Onboarding completion
        # Enterprise gets white-glove onboarding (higher completion)
        onboard_prob = 0.88 if plan == 'Enterprise' else (0.70 if plan == 'Professional' else 0.52)
        onboarding_completed = np.random.choice(['Yes', 'No'], p=[onboard_prob, 1 - onboard_prob])
        
        # Feature adoption score (0-100)
        base_adoption = 72 if onboarding_completed == 'Yes' else 38
        if plan == 'Enterprise':
            base_adoption += 12
        elif plan == 'Starter':
            base_adoption -= 8
        feature_adoption = int(np.clip(np.random.normal(base_adoption, 16), 5, 100))
        
        # Monthly active usage hours
        usage_hours = round(max(0.5, np.random.normal(feature_adoption * 0.45 + (15 if plan == 'Enterprise' else 5), 8)), 1)
        
        # Support tickets count
        tickets_count = int(np.clip(np.random.poisson(2.5), 0, 14))
        
        # Resolution time hours
        if tickets_count == 0:
            avg_res_time = 0.0
        else:
            base_res = 12.0 if plan == 'Enterprise' else (22.0 if plan == 'Professional' else 34.0)
            avg_res_time = round(float(np.clip(np.random.exponential(base_res), 2.0, 96.0)), 1)
            
        # NPS Score (0-10)
        nps_mean = 8.4 if (feature_adoption > 65 and onboarding_completed == 'Yes') else (4.6 if feature_adoption < 40 else 6.8)
        nps_score = int(np.clip(np.round(np.random.normal(nps_mean, 1.8)), 0, 10))
        
        # Calculate maximum possible tenure in months from signup to observation end
        days_active_max = (observation_end_date - signup_date).days
        months_available = max(1, int(days_active_max / 30.4))
        
        # Churn Probability Modeling
        # Realistic SaaS hazard model
        z = -1.6  # baseline intercept
        
        # Contract effect: Month-to-month has much higher churn risk
        if contract == 'Month-to-Month':
            z += 1.35
        else:
            z -= 0.85
            
        # Onboarding effect: Not onboarding is a huge churn trigger
        if onboarding_completed == 'No':
            z += 1.45
            
        # Feature adoption effect
        z -= (feature_adoption - 50) * 0.038
        
        # Support friction effect
        if avg_res_time > 36:
            z += 0.85
        if tickets_count >= 6:
            z += 0.70
            
        # Plan effect
        if plan == 'Enterprise':
            z -= 0.75
        elif plan == 'Starter':
            z += 0.40
            
        # NPS effect
        if nps_score <= 4:
            z += 0.95
        elif nps_score >= 8:
            z -= 0.80
            
        churn_probability = 1.0 / (1.0 + np.exp(-z))
        churn_probability = np.clip(churn_probability, 0.03, 0.92)
        
        will_churn = np.random.rand() < churn_probability
        
        if will_churn:
            # Customer churns at some tenure <= months_available
            # Distribution of churn timing:
            # If onboarding was missed, churn peaks very early (month 1-3)
            # If month-to-month, steady drop
            # If annual, churn happens at contract boundary (e.g. month 12 or 24)
            if contract == 'Annual':
                if months_available >= 12:
                    # Churns at month 12 renewal or month 24
                    tenure = 12 if (months_available < 24 or np.random.rand() < 0.8) else 24
                    tenure = min(tenure, months_available)
                else:
                    # In annual contract, rarely churns before month 12 (breach/bankruptcy ~5%)
                    if np.random.rand() < 0.15:
                        tenure = random.randint(1, months_available)
                    else:
                        will_churn = False
                        tenure = months_available
            else:
                # Month to month
                if onboarding_completed == 'No' or feature_adoption < 35:
                    # Heavy early cliff (months 1, 2, 3)
                    tenure = int(np.clip(np.random.exponential(2.8) + 1, 1, months_available))
                else:
                    tenure = int(np.clip(np.random.exponential(6.5) + 1, 1, months_available))
                    
            if will_churn:
                churn_status = 1
                churn_date = signup_date + timedelta(days=int(tenure * 30.4))
                if churn_date > observation_end_date:
                    churn_status = 0
                    churn_date = None
                    tenure = months_available
            else:
                churn_status = 0
                churn_date = None
        else:
            churn_status = 0
            churn_date = None
            tenure = months_available
            
        # Assign Churn Reason
        if churn_status == 1:
            if onboarding_completed == 'No' or feature_adoption < 35:
                churn_reason = "Low Feature Adoption & Poor Onboarding"
            elif avg_res_time > 36 or tickets_count >= 5:
                churn_reason = "Customer Support Latency & Unresolved Issues"
            elif plan == 'Starter' and nps_score <= 5 and np.random.rand() < 0.5:
                churn_reason = "High Price / Budget Constraints"
            elif pay_method in ['Credit Card', 'PayPal'] and np.random.rand() < 0.16:
                churn_reason = "Involuntary Churn (Payment / Card Expiry Failure)"
            elif np.random.rand() < 0.45:
                churn_reason = "Switched to Competitor (Missing Key Integrations)"
            else:
                churn_reason = "Product Performance & Reliability Issues"
        else:
            churn_reason = "Active (Retained)"
            
        # Customer Lifetime Value
        clv = round(mrr * tenure, 2)
        
        data.append({
            'CustomerID': cust_id,
            'CustomerName': cust_name,
            'CompanySize': comp_size,
            'Industry': industry,
            'Country': country,
            'SignupDate': signup_date.strftime("%Y-%m-%d"),
            'CohortMonth': cohort_month,
            'PlanTier': plan,
            'ContractType': contract,
            'PaymentMethod': pay_method,
            'OnboardingCompleted': onboarding_completed,
            'FeatureAdoptionScore': feature_adoption,
            'MonthlyActiveUsageHours': usage_hours,
            'SupportTicketsCount': tickets_count,
            'AvgResolutionTimeHours': avg_res_time,
            'NPSScore': nps_score,
            'DiscountsApplied': discount_applied,
            'MonthlyRecurringRevenue': mrr,
            'TenureMonths': tenure,
            'ChurnStatus': churn_status,
            'ChurnDate': churn_date.strftime("%Y-%m-%d") if churn_date else "",
            'PrimaryChurnReason': churn_reason,
            'CustomerLifetimeValue': clv
        })
        
    df = pd.DataFrame(data)
    
    # Save raw dataset
    csv_path = os.path.join('data', 'saas_customer_churn_data.csv')
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} customer records saved to {csv_path}")
    print("\nDataset Summary:")
    print(f"Total Customers: {len(df):,}")
    print(f"Churned: {df['ChurnStatus'].sum():,} ({df['ChurnStatus'].mean()*100:.2f}%)")
    print(f"Active: {(len(df) - df['ChurnStatus'].sum()):,} ({(1 - df['ChurnStatus'].mean())*100:.2f}%)")
    print(f"Total MRR: ${df['MonthlyRecurringRevenue'].sum():,.2f}")
    print(f"Churned MRR: ${df[df['ChurnStatus']==1]['MonthlyRecurringRevenue'].sum():,.2f}")
    print(f"Average Customer Tenure: {df['TenureMonths'].mean():.1f} months")
    print("\nChurn Rate by Contract Type:")
    print(df.groupby('ContractType')['ChurnStatus'].agg(['count', 'mean']).rename(columns={'mean': 'ChurnRate'}))
    print("\nChurn Rate by Onboarding:")
    print(df.groupby('OnboardingCompleted')['ChurnStatus'].agg(['count', 'mean']).rename(columns={'mean': 'ChurnRate'}))
    print("\nTop Churn Reasons:")
    print(df[df['ChurnStatus']==1]['PrimaryChurnReason'].value_counts())

if __name__ == '__main__':
    generate_saas_churn_dataset()
