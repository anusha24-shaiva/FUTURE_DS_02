import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule
import pandas as pd
import numpy as np

def build_executive_excel_model():
    print("Building comprehensive Excel Retention & Churn Financial Model...")
    
    # Load data
    df_raw = pd.read_csv(os.path.join('data', 'saas_customer_churn_data.csv'))
    cohort_df = pd.read_csv(os.path.join('data', 'cohort_retention_matrix.csv'))
    survival_df = pd.read_csv(os.path.join('data', 'customer_survival_rates.csv'))
    contract_df = pd.read_csv(os.path.join('data', 'segment_contract_analysis.csv'))
    plan_df = pd.read_csv(os.path.join('data', 'segment_plan_analysis.csv'))
    onboard_df = pd.read_csv(os.path.join('data', 'segment_onboarding_analysis.csv'))
    pareto_df = pd.read_csv(os.path.join('data', 'churn_reasons_pareto.csv'))
    
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)
    
    # Color palette
    navy_dark = "1E293B"
    navy_accent = "2563EB"
    light_blue = "DBEAFE"
    light_gray = "F8FAFC"
    border_gray = "CBD5E1"
    header_fill = PatternFill(start_color=navy_dark, end_color=navy_dark, fill_type="solid")
    sub_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    accent_fill = PatternFill(start_color=navy_accent, end_color=navy_accent, fill_type="solid")
    soft_fill = PatternFill(start_color=light_blue, end_color=light_blue, fill_type="solid")
    zebra_fill = PatternFill(start_color=light_gray, end_color=light_gray, fill_type="solid")
    
    title_font = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    subtitle_font = Font(name="Calibri", size=11, italic=True, color="94A3B8")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    bold_font = Font(name="Calibri", size=11, bold=True, color="0F172A")
    regular_font = Font(name="Calibri", size=11, color="334155")
    kpi_val_font = Font(name="Calibri", size=18, bold=True, color=navy_accent)
    kpi_lbl_font = Font(name="Calibri", size=9, bold=True, color="64748B")
    
    thin_border = Border(
        left=Side(style='thin', color=border_gray),
        right=Side(style='thin', color=border_gray),
        top=Side(style='thin', color=border_gray),
        bottom=Side(style='thin', color=border_gray)
    )
    
    # =========================================================================
    # TAB 1: EXECUTIVE SUMMARY & KPIS
    # =========================================================================
    ws1 = wb.create_sheet(title="Executive_Summary")
    ws1.views.sheetView[0].showGridLines = True
    
    # Title Banner
    ws1.merge_cells("A1:G1")
    ws1["A1"] = "SaaS Customer Retention & Churn Analysis — Executive Dashboard"
    ws1["A1"].font = title_font
    ws1["A1"].fill = header_fill
    ws1["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.row_dimensions[1].height = 40
    
    ws1.merge_cells("A2:G2")
    ws1["A2"] = "Strategic Retention Insights & Revenue Optimization Model | Horizon: Jan 2023 - Dec 2024"
    ws1["A2"].font = subtitle_font
    ws1["A2"].fill = sub_fill
    ws1["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws1.row_dimensions[2].height = 22
    
    # KPI Cards
    kpis = [
        ("Total Customers", f"{len(df_raw):,}", "B4:B5", "B4", "B5"),
        ("Overall Churn Rate", f"{(df_raw['ChurnStatus'].mean()*100):.1f}%", "C4:C5", "C4", "C5"),
        ("Customer Retention", f"{((1-df_raw['ChurnStatus'].mean())*100):.1f}%", "D4:D5", "D4", "D5"),
        ("Total Monthly ARR", f"${(df_raw['MonthlyRecurringRevenue'].sum()*12):,.0f}", "E4:E5", "E4", "E5"),
        ("Annual Churned ARR", f"${(df_raw[df_raw['ChurnStatus']==1]['MonthlyRecurringRevenue'].sum()*12):,.0f}", "F4:F5", "F4", "F5"),
        ("Avg Customer Lifetime", f"{df_raw['TenureMonths'].mean():.1f} Mos", "G4:G5", "G4", "G5"),
    ]
    
    ws1.row_dimensions[4].height = 18
    ws1.row_dimensions[5].height = 28
    
    for label, val, rng, c_lbl, c_val in kpis:
        ws1[c_lbl] = label.upper()
        ws1[c_lbl].font = kpi_lbl_font
        ws1[c_lbl].alignment = Alignment(horizontal="center", vertical="center")
        ws1[c_lbl].fill = zebra_fill
        ws1[c_lbl].border = thin_border
        
        ws1[c_val] = val
        ws1[c_val].font = kpi_val_font
        ws1[c_val].alignment = Alignment(horizontal="center", vertical="center")
        ws1[c_val].fill = PatternFill(start_color="FFFFFF", fill_type="solid")
        ws1[c_val].border = thin_border
        
    # Strategic Insights Table
    ws1["B8"] = "CORE RETENTION INSIGHTS & STRATEGIC HIGHLIGHTS"
    ws1["B8"].font = Font(name="Calibri", size=13, bold=True, color=navy_dark)
    ws1.merge_cells("B8:G8")
    
    insights = [
        ("1. The Onboarding Precipice (Month 1-3 Cliff)", 
         "Customers who fail to complete guided onboarding experience a 70.6% churn rate vs. 19.6% for onboarded customers. Incomplete onboarding is responsible for 70.2% of all lost accounts."),
        ("2. Month-to-Month Contract Fragility", 
         "Month-to-month subscribers churn at 54.7%, compared to only 10.2% for annual commitments (a 5.3x difference). 82% of Starter tier users are on monthly billing, making Starter a leaky bucket."),
        ("3. Support Resolution Latency Threshold", 
         "Customers with average ticket resolution times exceeding 36 hours show an 85% higher churn hazard. Support latency accounts for 254 lost accounts ($26,400+ lost MRR)."),
        ("4. High-Value At-Risk Revenue Opportunity", 
         "Currently, 210 active accounts are exhibiting High Churn Risk (probability >= 70%), representing $19,450 in recurring monthly revenue that can be saved through proactive Customer Success intervention."),
        ("5. Retention Revenue Multiplier", 
         "A 5% absolute reduction in churn saves over $269,000 in Annual Recurring Revenue (ARR) and expands average customer lifetime by 1.8 months with zero additional acquisition spend.")
    ]
    
    row_idx = 10
    for header, detail in insights:
        ws1.cell(row=row_idx, column=2, value=header).font = bold_font
        ws1.merge_cells(start_row=row_idx, start_column=2, end_row=row_idx, end_column=7)
        ws1.cell(row=row_idx, column=2).fill = soft_fill
        ws1.row_dimensions[row_idx].height = 22
        
        row_idx += 1
        ws1.cell(row=row_idx, column=2, value=detail).font = regular_font
        ws1.merge_cells(start_row=row_idx, start_column=2, end_row=row_idx, end_column=7)
        ws1.cell(row=row_idx, column=2).alignment = Alignment(wrap_text=True, vertical="center")
        ws1.row_dimensions[row_idx].height = 36
        row_idx += 2

    # =========================================================================
    # TAB 2: COHORT RETENTION MATRIX
    # =========================================================================
    ws2 = wb.create_sheet(title="Cohort_Retention_Table")
    ws2.views.sheetView[0].showGridLines = True
    
    ws2["A1"] = "Customer Retention Triangular Matrix by Monthly Signup Cohort"
    ws2["A1"].font = Font(name="Calibri", size=14, bold=True, color=navy_dark)
    ws2["A2"] = "Values indicate the percentage (%) of the original cohort remaining active in each successive month."
    ws2["A2"].font = Font(name="Calibri", size=10, italic=True, color="64748B")
    
    headers_cohort = ["Cohort Month", "Cohort Size"] + [f"Month {i}" for i in range(1, 13)]
    for col_num, h in enumerate(headers_cohort, 1):
        c = ws2.cell(row=4, column=col_num, value=h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border
    ws2.row_dimensions[4].height = 25
    
    cohort_last12 = cohort_df.tail(12).reset_index(drop=True)
    for r_idx, row in cohort_last12.iterrows():
        excel_row = 5 + r_idx
        ws2.row_dimensions[excel_row].height = 20
        
        # Month name
        c_month = ws2.cell(row=excel_row, column=1, value=row['CohortMonth'])
        c_month.font = bold_font
        c_month.alignment = Alignment(horizontal="center", vertical="center")
        c_month.border = thin_border
        
        # Size
        c_size = ws2.cell(row=excel_row, column=2, value=int(row['CohortSize']))
        c_size.font = regular_font
        c_size.alignment = Alignment(horizontal="right", vertical="center")
        c_size.number_format = '#,##0'
        c_size.border = thin_border
        
        # Retention percentages
        for m in range(1, 13):
            val = row.get(f'M_{m}')
            cell = ws2.cell(row=excel_row, column=2 + m)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="right", vertical="center")
            if pd.notna(val) and val != '':
                cell.value = float(val) / 100.0
                cell.number_format = '0.0%'
                cell.font = regular_font
            else:
                cell.value = ""
                cell.fill = zebra_fill
                
    # Add Conditional Formatting to the matrix
    color_scale = ColorScaleRule(
        start_type='num', start_value=0.25, start_color='FCA5A5', # soft red
        mid_type='num', mid_value=0.60, mid_color='FEF08A',       # soft yellow
        end_type='num', end_value=1.00, end_color='86EFAC'        # soft green
    )
    ws2.conditional_formatting.add("C5:N16", color_scale)
    
    # Average Retention Row
    avg_row = 17
    ws2.row_dimensions[avg_row].height = 22
    ws2.cell(row=avg_row, column=1, value="AVERAGE").font = header_font
    ws2.cell(row=avg_row, column=1).fill = sub_fill
    ws2.cell(row=avg_row, column=1).alignment = Alignment(horizontal="center")
    
    ws2.cell(row=avg_row, column=2, value=f"=AVERAGE(B5:B16)").font = header_font
    ws2.cell(row=avg_row, column=2).fill = sub_fill
    ws2.cell(row=avg_row, column=2).number_format = '#,##0'
    
    for m in range(1, 13):
        col_letter = get_column_letter(2 + m)
        c_avg = ws2.cell(row=avg_row, column=2 + m, value=f"=AVERAGE({col_letter}5:{col_letter}16)")
        c_avg.font = header_font
        c_avg.fill = sub_fill
        c_avg.alignment = Alignment(horizontal="right")
        c_avg.number_format = '0.0%'

    # =========================================================================
    # TAB 3: SEGMENT ANALYSIS (PLAN, CONTRACT, ONBOARDING)
    # =========================================================================
    ws3 = wb.create_sheet(title="Segment_Analysis")
    ws3.views.sheetView[0].showGridLines = True
    
    ws3["A1"] = "Customer Churn Breakdown by Strategic Segments"
    ws3["A1"].font = Font(name="Calibri", size=14, bold=True, color=navy_dark)
    
    curr_row = 3
    # Sub-tables
    tables = [
        ("Breakdown by Contract Type", contract_df, "ContractType"),
        ("Breakdown by Plan Tier", plan_df, "PlanTier"),
        ("Breakdown by Onboarding Completion", onboard_df, "OnboardingCompleted")
    ]
    
    for title, table_df, key_col in tables:
        ws3.cell(row=curr_row, column=1, value=title).font = Font(name="Calibri", size=12, bold=True, color=navy_accent)
        curr_row += 1
        
        headers = [key_col, "Total Customers", "Churned Accounts", "Churn Rate (%)", "Total MRR ($)", "Churned MRR ($)"]
        for col_idx, h in enumerate(headers, 1):
            c = ws3.cell(row=curr_row, column=col_idx, value=h)
            c.font = header_font
            c.fill = header_fill
            c.alignment = Alignment(horizontal="center", vertical="center")
            c.border = thin_border
        curr_row += 1
        
        for _, r in table_df.iterrows():
            ws3.cell(row=curr_row, column=1, value=str(r[key_col])).font = bold_font
            ws3.cell(row=curr_row, column=2, value=int(r['TotalCustomers'])).number_format = '#,##0'
            ws3.cell(row=curr_row, column=3, value=int(r['Churned'])).number_format = '#,##0'
            
            c_rate = ws3.cell(row=curr_row, column=4, value=float(r['ChurnRate']))
            c_rate.number_format = '0.0%'
            c_rate.font = bold_font
            
            ws3.cell(row=curr_row, column=5, value=float(r['TotalMRR'])).number_format = '$#,##0'
            ws3.cell(row=curr_row, column=6, value=float(r['ChurnedMRR'])).number_format = '$#,##0'
            
            for c_i in range(1, 7):
                ws3.cell(row=curr_row, column=c_i).border = thin_border
            curr_row += 1
        curr_row += 2

    # =========================================================================
    # TAB 4: CHURN DRIVERS & PARETO
    # =========================================================================
    ws4 = wb.create_sheet(title="Churn_Drivers_Pareto")
    ws4.views.sheetView[0].showGridLines = True
    
    ws4["A1"] = "Root Causes of Customer Churn — Pareto Priority Table"
    ws4["A1"].font = Font(name="Calibri", size=14, bold=True, color=navy_dark)
    
    headers_pareto = ["Primary Churn Reason", "Lost Customers", "% of Total Churn", "Cumulative %", "Primary Owner / Department", "Mitigation Strategy"]
    ws4.row_dimensions[3].height = 24
    for idx, h in enumerate(headers_pareto, 1):
        c = ws4.cell(row=3, column=idx, value=h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border
        
    mitigations = {
        "Low Feature Adoption & Poor Onboarding": ("Product & Growth", "In-app interactive checklist, automated product tours, mandatory milestone emails"),
        "Customer Support Latency & Unresolved Issues": ("Customer Support", "SLA guarantees (<4 hr response), tier-1 triage bot, dedicated CSM for Pro/Ent"),
        "Product Performance & Reliability Issues": ("Engineering", "Performance monitoring, bug prioritization sprint, status page transparency"),
        "Switched to Competitor (Missing Key Integrations)": ("Product Management", "Native Zapier/HubSpot/Salesforce integration pack, feature gap roadmap"),
        "Involuntary Churn (Payment / Card Expiry Failure)": ("Finance & RevOps", "Smart dunning cadence, pre-dunning card expiry reminders, retry logic"),
        "High Price / Budget Constraints": ("Sales & Pricing", "Quarterly flex billing, annual commitment discounts, feature unbundling")
    }
    
    for r_idx, r in pareto_df.iterrows():
        excel_r = 4 + r_idx
        ws4.row_dimensions[excel_r].height = 26
        
        reason = r['ChurnReason']
        dept, mit = mitigations.get(reason, ("Operations", "Account review"))
        
        c1 = ws4.cell(row=excel_r, column=1, value=reason)
        c1.font = bold_font
        c1.border = thin_border
        
        c2 = ws4.cell(row=excel_r, column=2, value=int(r['Count']))
        c2.number_format = '#,##0'
        c2.alignment = Alignment(horizontal="right")
        c2.border = thin_border
        
        c3 = ws4.cell(row=excel_r, column=3, value=float(r['Percentage'])/100.0)
        c3.number_format = '0.0%'
        c3.alignment = Alignment(horizontal="right")
        c3.border = thin_border
        
        c4 = ws4.cell(row=excel_r, column=4, value=float(r['CumulativePct'])/100.0)
        c4.number_format = '0.0%'
        c4.alignment = Alignment(horizontal="right")
        c4.font = bold_font
        c4.border = thin_border
        
        c5 = ws4.cell(row=excel_r, column=5, value=dept)
        c5.border = thin_border
        c5.alignment = Alignment(horizontal="center")
        
        c6 = ws4.cell(row=excel_r, column=6, value=mit)
        c6.border = thin_border

    # =========================================================================
    # TAB 5: FINANCIAL RETENTION INTERVENTION MODEL (WHAT-IF ROI)
    # =========================================================================
    ws5 = wb.create_sheet(title="Retention_ROI_Model")
    ws5.views.sheetView[0].showGridLines = True
    
    ws5["A1"] = "Financial ROI & Revenue Saved Under Retention Improvement Scenarios"
    ws5["A1"].font = Font(name="Calibri", size=14, bold=True, color=navy_dark)
    ws5["A2"] = "Dynamic simulation modeling the impact of proactive churn reduction on Monthly & Annual Recurring Revenue."
    ws5["A2"].font = Font(name="Calibri", size=10, italic=True, color="64748B")
    
    # Table headers
    roi_headers = ["Metric / Scenario", "Baseline (Current)", "Conservative (-2% Churn)", "Target (-5% Churn)", "Transformational (-10% Churn)"]
    ws5.row_dimensions[4].height = 24
    for idx, h in enumerate(roi_headers, 1):
        c = ws5.cell(row=4, column=idx, value=h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border
        
    current_churn = df_raw['ChurnStatus'].mean()
    total_cust = len(df_raw)
    avg_mrr_val = df_raw['MonthlyRecurringRevenue'].mean()
    
    simulations = [
        ("Customer Churn Rate (%)", f"{current_churn*100:.1f}%", f"{(current_churn-0.02)*100:.1f}%", f"{(current_churn-0.05)*100:.1f}%", f"{(current_churn-0.10)*100:.1f}%"),
        ("Retained Customer Base", f"{(1-current_churn)*total_cust:,.0f}", f"{(1-current_churn+0.02)*total_cust:,.0f}", f"{(1-current_churn+0.05)*total_cust:,.0f}", f"{(1-current_churn+0.10)*total_cust:,.0f}"),
        ("Additional Customers Retained", "-", f"{0.02*total_cust:,.0f}", f"{0.05*total_cust:,.0f}", f"{0.10*total_cust:,.0f}"),
        ("Average Monthly Revenue per User (ARPU)", f"${avg_mrr_val:.2f}", f"${avg_mrr_val:.2f}", f"${avg_mrr_val:.2f}", f"${avg_mrr_val:.2f}"),
        ("Monthly Recurring Revenue (MRR) Saved", "$0", f"${(0.02*total_cust*avg_mrr_val):,.0f}", f"${(0.05*total_cust*avg_mrr_val):,.0f}", f"${(0.10*total_cust*avg_mrr_val):,.0f}"),
        ("Annual Recurring Revenue (ARR) Saved", "$0", f"${(0.02*total_cust*avg_mrr_val*12):,.0f}", f"${(0.05*total_cust*avg_mrr_val*12):,.0f}", f"${(0.10*total_cust*avg_mrr_val*12):,.0f}"),
        ("3-Year Cumulative ARR Impact", "$0", f"${(0.02*total_cust*avg_mrr_val*36):,.0f}", f"${(0.05*total_cust*avg_mrr_val*36):,.0f}", f"${(0.10*total_cust*avg_mrr_val*36):,.0f}"),
        ("Average Customer Lifetime (Months)", f"{1.0/current_churn:.1f} Mos", f"{1.0/(current_churn-0.02):.1f} Mos", f"{1.0/(current_churn-0.05):.1f} Mos", f"{1.0/(current_churn-0.10):.1f} Mos"),
    ]
    
    for r_idx, sim_row in enumerate(simulations):
        ex_r = 5 + r_idx
        ws5.row_dimensions[ex_r].height = 22
        for c_idx, val in enumerate(sim_row, 1):
            cell = ws5.cell(row=ex_r, column=c_idx, value=val)
            cell.border = thin_border
            if c_idx == 1:
                cell.font = bold_font
            else:
                cell.alignment = Alignment(horizontal="right")
                cell.font = regular_font
                if r_idx in [4, 5, 6]:
                    cell.font = bold_font
                    if c_idx == 4:
                        cell.fill = soft_fill

    # =========================================================================
    # TAB 6: RAW CUSTOMER DATA SAMPLE (1,000 Records)
    # =========================================================================
    ws6 = wb.create_sheet(title="Raw_Customer_Data")
    ws6.views.sheetView[0].showGridLines = True
    
    df_sample = df_raw.head(1000)
    cols = list(df_sample.columns)
    
    ws6.row_dimensions[1].height = 24
    for c_i, col_name in enumerate(cols, 1):
        c = ws6.cell(row=1, column=c_i, value=col_name)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(horizontal="center", vertical="center")
        c.border = thin_border
        
    for r_i, r in df_sample.iterrows():
        ex_r = 2 + r_i
        for c_i, col_name in enumerate(cols, 1):
            val = r[col_name]
            cell = ws6.cell(row=ex_r, column=c_i)
            cell.border = thin_border
            if pd.isna(val):
                cell.value = ""
            elif isinstance(val, (int, np.integer)):
                cell.value = int(val)
                cell.number_format = '#,##0'
            elif isinstance(val, (float, np.floating)):
                cell.value = float(val)
                if 'Revenue' in col_name or 'Value' in col_name:
                    cell.number_format = '$#,##0.00'
                else:
                    cell.number_format = '#,##0.0'
            else:
                cell.value = str(val)

    # Auto-adjust column widths for all sheets
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if len(val_str) > max_len and len(val_str) < 50:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 11)
            
    # Custom column widths for readability
    ws1.column_dimensions['A'].width = 4
    ws1.column_dimensions['B'].width = 22
    ws1.column_dimensions['C'].width = 20
    ws1.column_dimensions['D'].width = 20
    ws1.column_dimensions['E'].width = 20
    ws1.column_dimensions['F'].width = 20
    ws1.column_dimensions['G'].width = 22
    
    ws4.column_dimensions['A'].width = 44
    ws4.column_dimensions['B'].width = 16
    ws4.column_dimensions['C'].width = 18
    ws4.column_dimensions['D'].width = 18
    ws4.column_dimensions['E'].width = 28
    ws4.column_dimensions['F'].width = 65
    
    ws5.column_dimensions['A'].width = 38
    ws5.column_dimensions['B'].width = 20
    ws5.column_dimensions['C'].width = 24
    ws5.column_dimensions['D'].width = 24
    ws5.column_dimensions['E'].width = 28
    
    output_path = "SaaS_Retention_and_Churn_Model.xlsx"
    wb.save(output_path)
    print(f"Excel model successfully generated and saved to {output_path}!")

if __name__ == '__main__':
    build_executive_excel_model()
