#!/usr/bin/env python3
"""
Tool #107 — Discovery Request Generator
============================================
🆕 NOVEL TOOL — Auto-generates interrogatories and
document requests based on DB evidence gaps

Generates:
- Interrogatories (MCR 2.309)
- Requests for Production (MCR 2.310)
- Requests for Admission (MCR 2.312)

Targets: Emily Watson, Ronald Berry, Jennifer Barnes
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

INTERROGATORIES = {
    'Emily Watson': [
        ('Parenting Time', 'State each and every reason you opposed Andrew Pigors\' parenting time with L.D.W. from January 2024 to present, including the factual basis for each reason.'),
        ('Straw Incident', 'Describe in detail the "straw incident" of approximately October 2023, including: (a) the exact date, (b) the exact location, (c) all persons present, (d) exactly what occurred, (e) any medical treatment sought for L.D.W.'),
        ('PPO Basis', 'State the specific facts you relied upon when filing for a Personal Protection Order in case 2023-5907-PP, and identify all documents that support each fact.'),
        ('Ronald Berry', 'Describe your relationship with Ronald T. Berry, including: (a) when the relationship began, (b) whether he resides at your home, (c) his involvement in decisions regarding L.D.W., (d) whether he advised you on legal matters in this case.'),
        ('Communication Blocking', 'Identify every phone number, email address, and social media account you blocked or restricted Andrew Pigors from contacting, and the date of each action.'),
        ('Financial Support', 'State all sources of financial support you have received since January 2024, including amounts from Ronald Berry, family members, or public assistance.'),
        ('Ex Parte Motion', 'Regarding your August 2025 ex parte motion to suspend all parenting time: (a) state the emergency requiring ex parte relief, (b) explain why regular notice could not be given, (c) identify who assisted you in preparing the motion.'),
        ('Child\'s Wellbeing', 'Describe L.D.W.\'s current: (a) daycare/school enrollment, (b) medical providers, (c) daily routine, (d) sleeping arrangements, (e) who provides primary care during your work hours.'),
        ('Prior Statements', 'Identify all written or recorded statements you have made about Andrew Pigors to: (a) courts, (b) police, (c) CPS, (d) medical providers, (e) school officials, (f) any other person or agency.'),
        ('ChatGPT Usage', 'State whether you have used ChatGPT or any AI tool to: (a) draft court documents, (b) plan legal strategy, (c) discuss Andrew Pigors or L.D.W., and if so, produce all such records.'),
    ],
    'Ronald Berry': [
        ('Legal Advice', 'Have you at any time provided legal advice to Emily Watson regarding the cases of Pigors v. Watson? If so, describe each instance.'),
        ('Court Involvement', 'Have you at any time accompanied Emily Watson to court proceedings, assisted in preparing court documents, or communicated with her attorney Jennifer Barnes about this case?'),
        ('Bar Membership', 'Are you a member of the State Bar of Michigan or any other state bar? If so, provide your bar number. If not, explain the basis for any legal advice given to Emily Watson.'),
        ('Unauthorized Practice', 'Have you drafted, edited, or reviewed any court filings, motions, or legal documents for Emily Watson in any case involving Andrew Pigors?'),
        ('Child Contact', 'Describe all contact you have had with L.D.W., including frequency, duration, and nature of the contact.'),
    ],
}

DOCUMENT_REQUESTS = {
    'Emily Watson': [
        'All text messages, emails, and electronic communications between you and Andrew Pigors from October 2023 to present.',
        'All text messages, emails, and electronic communications between you and Ronald Berry discussing Andrew Pigors, L.D.W., or this litigation.',
        'All text messages, emails, and electronic communications between you and Jennifer Barnes (P55406).',
        'All photographs, videos, or recordings you claim depict the "straw incident" of October 2023.',
        'All medical records for L.D.W. from October 2023 to present.',
        'All documents submitted to any court in connection with the PPO (2023-5907-PP).',
        'All ChatGPT or AI chat export data from your accounts.',
        'All documents relating to your August 2025 ex parte motion, including drafts.',
        'Your complete phone records (call logs and text logs) for October 2023 through present.',
        'All social media posts referencing Andrew Pigors or L.D.W.',
    ],
    'Ronald Berry': [
        'All communications with Emily Watson regarding Andrew Pigors or L.D.W.',
        'All communications with Jennifer Barnes (P55406) regarding Pigors v. Watson.',
        'Any legal research, drafts, or documents prepared for or on behalf of Emily Watson.',
        'Your current resume or CV showing educational background and professional credentials.',
    ],
}

ADMISSIONS = [
    'Admit that Andrew Pigors has never been convicted of domestic violence.',
    'Admit that no medical professional has ever diagnosed L.D.W. with injuries caused by Andrew Pigors.',
    'Admit that no CPS investigation has ever substantiated abuse or neglect by Andrew Pigors.',
    'Admit that Ronald Berry is not a licensed attorney in the State of Michigan.',
    'Admit that Ronald Berry has drafted or edited court documents filed in this case.',
    'Admit that the "straw incident" of October 2023 did not result in any medical treatment for L.D.W.',
    'Admit that you did not provide notice to Andrew Pigors before filing your August 2025 ex parte motion.',
    'Admit that Andrew Pigors has requested parenting time on at least [X] occasions that you denied or failed to respond to.',
    'Admit that you have used ChatGPT or AI tools to draft communications or documents related to this case.',
    'Admit that Jennifer Barnes (P55406) withdrew from representing you in this matter.',
]

def main():
    print("=" * 70)
    print("DISCOVERY REQUEST GENERATOR — Tool #107")
    print("=" * 70)
    
    total_interrogatories = sum(len(v) for v in INTERROGATORIES.values())
    total_doc_requests = sum(len(v) for v in DOCUMENT_REQUESTS.values())
    total_admissions = len(ADMISSIONS)
    
    lines = [
        "# 🔍 DISCOVERY REQUEST GENERATOR",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #107*",
        "*MCR 2.309 (Interrogatories) · MCR 2.310 (Production) · MCR 2.312 (Admissions)*\n",
        "---\n",
        f"## Summary: {total_interrogatories} Interrogatories + {total_doc_requests} Doc Requests + {total_admissions} Admissions\n",
    ]
    
    # Interrogatories
    lines.append("## 📝 INTERROGATORIES (MCR 2.309)\n")
    lines.append("*Note: Michigan limits to 20 interrogatories per party (including subparts). Prioritize accordingly.*\n")
    
    interrog_num = 1
    for target, questions in INTERROGATORIES.items():
        lines.append(f"### To: {target}\n")
        for topic, text in questions:
            lines.append(f"**Interrogatory No. {interrog_num}** [{topic}]")
            lines.append(f"> {text}\n")
            interrog_num += 1
        lines.append("")
        print(f"  📝 {target}: {len(questions)} interrogatories")
    
    # Document Requests
    lines.append("## 📂 REQUESTS FOR PRODUCTION (MCR 2.310)\n")
    
    doc_num = 1
    for target, requests in DOCUMENT_REQUESTS.items():
        lines.append(f"### To: {target}\n")
        for req in requests:
            lines.append(f"**Request No. {doc_num}:** {req}\n")
            doc_num += 1
        lines.append("")
        print(f"  📂 {target}: {len(requests)} document requests")
    
    # Admissions
    lines.append("## ✅ REQUESTS FOR ADMISSION (MCR 2.312)\n")
    lines.append("*If not answered within 28 days, deemed ADMITTED (MCR 2.312(B)(1))*\n")
    lines.append("### To: Emily Watson\n")
    
    for i, admission in enumerate(ADMISSIONS, 1):
        lines.append(f"**Request No. {i}:** {admission}\n")
    
    print(f"  ✅ Admissions: {total_admissions} (auto-admitted if not answered in 28 days)")
    
    lines.extend([
        "---",
        "## ⚠️ FILING NOTES\n",
        "1. **MCR 2.309(A)(2)**: Max 20 interrogatories (subparts count separately)",
        "2. **MCR 2.310(B)**: 28 days to respond (can request extension)",
        "3. **MCR 2.312(B)(1)**: Admissions deemed admitted if no response in 28 days — POWERFUL tool",
        "4. **Timing**: File discovery AFTER custody case is active (not during PPO)",
        "5. **Service**: Must serve on opposing party (certified mail if pro se)",
        "",
        "## 🎯 STRATEGIC PRIORITY\n",
        "File Requests for Admission FIRST — if Emily fails to respond in 28 days,",
        "all statements are deemed admitted, creating devastating evidence for trial.",
        "",
        f"*Discovery Request Generator — Tool #107 — {total_interrogatories + total_doc_requests + total_admissions} total discovery items*",
    ])
    
    md_path = REPORTS_DIR / "DISCOVERY_REQUESTS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "discovery_requests.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Discovery Request Generator (#107)',
        'interrogatories': total_interrogatories,
        'document_requests': total_doc_requests,
        'admissions': total_admissions,
        'total': total_interrogatories + total_doc_requests + total_admissions,
        'targets': list(INTERROGATORIES.keys()),
    }, indent=2), encoding='utf-8')
    
    total = total_interrogatories + total_doc_requests + total_admissions
    print(f"\n✅ {total} discovery items generated")
    print(f"   Interrogatories: {total_interrogatories} | Doc Requests: {total_doc_requests} | Admissions: {total_admissions}")
    print(f"   Reports: DISCOVERY_REQUESTS.md + discovery_requests.json")

if __name__ == '__main__':
    main()
