#!/usr/bin/env python3
"""Tool #187 — Parenting Time Calculation Engine.
Calculates days since last contact, parenting time owed,
and make-up time per Michigan law."""

import json, os, sys, sqlite3
from datetime import datetime, timedelta
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_parenting_time_calc():
    today = datetime.now()
    # L.D.W. born Nov 9, 2022
    child_dob = datetime(2022, 11, 9)
    child_age_days = (today - child_dob).days
    child_age_years = child_age_days / 365.25
    
    # Parenting time suspended approximately August 2025
    suspension_date = datetime(2025, 8, 1)
    days_since_suspension = (today - suspension_date).days
    
    calc = {
        "tool_id": 187,
        "title": "PARENTING TIME CALCULATION ENGINE",
        "subtitle": "Days Lost, Time Owed, and Michigan Law Requirements",
        "as_of": today.strftime("%Y-%m-%d"),
        "child": {
            "initials": "L.D.W.",
            "dob": "2022-11-09",
            "age_days": child_age_days,
            "age_years": round(child_age_years, 1),
            "life_percentage_without_father": round((days_since_suspension / child_age_days) * 100, 1),
        },
        "parenting_time": {
            "suspension_date": suspension_date.strftime("%Y-%m-%d"),
            "days_since_suspension": days_since_suspension,
            "weeks_since_suspension": days_since_suspension // 7,
            "months_since_suspension": round(days_since_suspension / 30.44, 1),
        },
        "calculations": [],
        "legal_framework": [],
    }

    # Standard MI parenting time = every other weekend + 1 weeknight
    standard_nights_per_month = 6  # ~2 weekends (4 nights) + 2 weeknights
    nights_owed = int(days_since_suspension / 30.44 * standard_nights_per_month)
    
    calc["calculations"] = [
        {
            "metric": "Standard MI Parenting Time",
            "value": f"{standard_nights_per_month} overnights/month",
            "source": "Michigan Friend of the Court parenting time guidelines",
        },
        {
            "metric": "Total Overnights DENIED",
            "value": nights_owed,
            "formula": f"{calc['parenting_time']['months_since_suspension']} months × {standard_nights_per_month} nights/month",
        },
        {
            "metric": "Percentage of L.D.W.'s Life Without Father",
            "value": f"{calc['child']['life_percentage_without_father']}%",
            "impact": "DEVASTATING — developmental psychology literature is clear on harm",
        },
        {
            "metric": "Make-Up Time Owed (MCL 722.27a(8))",
            "value": f"{nights_owed} overnights",
            "authority": "MCL 722.27a(8) — court SHALL provide make-up time",
            "note": "Make-up time is MANDATORY, not discretionary",
        },
        {
            "metric": "Holidays Missed",
            "value": "Thanksgiving 2025, Christmas 2025, New Year 2026, Easter 2026, July 4 2026",
            "impact": "Each missed holiday is an additional deprivation",
        },
        {
            "metric": "Birthdays Missed",
            "value": "L.D.W.'s 3rd birthday (Nov 9, 2025)",
            "impact": "Father absent from critical milestone — irreversible harm",
        },
    ]

    calc["legal_framework"] = [
        {"law": "MCL 722.27a(1)", "text": "Parenting time shall be granted in frequency/duration/type reasonably calculated to promote strong relationship", "application": "PRESUMPTION of parenting time — suspension requires extraordinary findings"},
        {"law": "MCL 722.27a(3)", "text": "Court may SUSPEND parenting time ONLY if clear and convincing evidence of danger", "application": "No such finding was made — Emily's ex-parte order was procedurally defective"},
        {"law": "MCL 722.27a(7)", "text": "Parenting time denied ONLY if preponderance shows child's physical/mental/emotional health endangered", "application": "No evidence of any danger from Andrew — burden is on Emily"},
        {"law": "MCL 722.27a(8)", "text": "Court SHALL provide make-up time for wrongfully denied parenting time", "application": f"{nights_owed} overnights of make-up time are MANDATORY"},
        {"law": "MCR 3.218", "text": "Domestic relations referees may conduct investigations", "application": "Request independent investigation of parenting time fitness"},
        {"law": "Troxel v Granville 530 US 57 (2000)", "text": "Parental liberty is a fundamental constitutional right", "application": "Strict scrutiny applies to complete deprivation of parenting time"},
    ]

    calc["arguments_for_restoration"] = [
        f"L.D.W. has been denied ALL contact with father for {days_since_suspension} days",
        f"This represents {calc['child']['life_percentage_without_father']}% of L.D.W.'s entire life",
        f"Standard parenting time of {nights_owed} overnights has been wrongfully denied",
        "No clear and convincing evidence of danger was ever presented (MCL 722.27a(3))",
        "Emily's ex-parte motion lacked required statutory findings",
        "Developmental psychology research unanimously shows harm from parental absence at this age",
        "Make-up time of {nights_owed} overnights is MANDATORY under MCL 722.27a(8)".format(nights_owed=nights_owed),
        "Continued separation causes irreversible attachment damage — immediate restoration is essential",
    ]

    return calc

def main():
    calc = build_parenting_time_calc()
    
    md_path = os.path.join(REPORT_DIR, 'PARENTING_TIME_CALCULATION.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {calc['title']}\n\n*{calc['subtitle']}*\n\n")
        f.write(f"**As of: {calc['as_of']}**\n\n")
        
        f.write("## 👶 Child Status\n\n")
        c = calc["child"]
        f.write(f"- **Initials:** {c['initials']}\n")
        f.write(f"- **Age:** {c['age_years']} years ({c['age_days']} days)\n")
        f.write(f"- **Life without father:** {c['life_percentage_without_father']}%\n\n")
        
        f.write("## ⏰ Days Since Suspension\n\n")
        pt = calc["parenting_time"]
        f.write(f"- **Suspension date:** {pt['suspension_date']}\n")
        f.write(f"- **Days denied:** {pt['days_since_suspension']}\n")
        f.write(f"- **Weeks denied:** {pt['weeks_since_suspension']}\n")
        f.write(f"- **Months denied:** {pt['months_since_suspension']}\n\n")
        
        f.write("## 📊 Calculations\n\n")
        for item in calc["calculations"]:
            f.write(f"### {item['metric']}\n")
            f.write(f"**{item['value']}**\n\n")
            for k in ["formula", "authority", "impact", "source", "note"]:
                if k in item:
                    f.write(f"*{k.title()}: {item[k]}*\n\n")
        
        f.write("## ⚖️ Legal Framework\n\n")
        for law in calc["legal_framework"]:
            f.write(f"- **{law['law']}**: {law['text']}\n  → *{law['application']}*\n\n")
        
        f.write("## 🎯 Arguments for Immediate Restoration\n\n")
        for arg in calc["arguments_for_restoration"]:
            f.write(f"- {arg}\n")
        
        f.write(f"\n---\n*Tool #187 | Calculated {calc['as_of']}*\n")
    
    json_path = os.path.join(REPORT_DIR, 'parenting_time_calculation.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(calc, f, indent=2)
    
    pt = calc["parenting_time"]
    print(f"Tool #187 — PARENTING TIME CALCULATION ENGINE")
    print(f"  {pt['days_since_suspension']} days denied | {calc['child']['life_percentage_without_father']}% of L.D.W.'s life")
    print(f"  {len(calc['calculations'])} calculations | {len(calc['legal_framework'])} legal authorities")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
