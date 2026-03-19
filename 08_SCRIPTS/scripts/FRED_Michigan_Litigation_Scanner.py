
import os
import json
from datetime import datetime

# ===== Decision Tree Engine for Michigan Courts =====
class LitigationScanner:
    def __init__(self, scan_path):
        self.scan_path = scan_path
        self.extracted_data = []
        self.decision_paths = []

    def scan_directory(self):
        print(f"[SCAN] Scanning: {self.scan_path}")
        for root, _, files in os.walk(self.scan_path):
            for file in files:
                if file.endswith(('.txt', '.docx', '.pdf', '.json', '.csv')):
                    full_path = os.path.join(root, file)
                    self.extracted_data.append({
                        'filename': file,
                        'path': full_path,
                        'timestamp': datetime.now().isoformat()
                    })
        print(f"[RESULT] Found {len(self.extracted_data)} candidate files.")

    def extract_legal_relevance(self):
        print("[EXTRACT] Determining court level and issue type...")
        for item in self.extracted_data:
            name = item['filename'].lower()
            if 'custody' in name:
                item['type'] = 'Family/Custody'
                item['court'] = '14th Circuit'
            elif 'support' in name or 'foc' in name:
                item['type'] = 'Child Support'
                item['court'] = '14th Circuit - FOC'
            elif 'claim' in name:
                item['type'] = 'Small Claims'
                item['court'] = '60th District'
            elif 'civil' in name:
                item['type'] = 'Civil'
                item['court'] = '60th District or 14th Circuit'
            elif 'federal' in name or '1983' in name:
                item['type'] = 'Federal Civil Rights'
                item['court'] = 'U.S. District Court'
            else:
                item['type'] = 'Uncategorized'
                item['court'] = 'Unknown'

    def generate_decision_tree(self):
        print("[BUILD] Creating decision trees for each identified case type...")
        for item in self.extracted_data:
            path = []
            if item['type'] == 'Family/Custody':
                path = [
                    'Check for Established Custodial Environment (ECE)',
                    'Apply Vodvarka v Grasmeyer factors (MCL 722.27)',
                    'File Motion to Modify Custody',
                    'Generate Verified Motion, Proposed Order, CoS',
                    'Request Evidentiary Hearing if contested'
                ]
            elif item['type'] == 'Child Support':
                path = [
                    'Compare incomes and parenting time',
                    'Run Michigan Child Support Formula (MCL 552)',
                    'File Motion to Modify Support',
                    'Serve opposing party, wait 21 days'
                ]
            elif item['type'] == 'Small Claims':
                path = [
                    'Check claim amount (must be <$6,500 per MCL 600.8401)',
                    'Prepare Summons and Complaint',
                    'Serve via certified mail or process server',
                    'Prepare evidence, witnesses, and exhibits for hearing'
                ]
            elif item['type'] == 'Civil':
                path = [
                    'Determine cause of action (fraud, trespass, breach)',
                    'Draft Verified Complaint (MCR 2.113)',
                    'File in 60th District or 14th Circuit depending on amount',
                    'Serve via MCR 2.105, attach Summons and CoS'
                ]
            elif item['type'] == 'Federal Civil Rights':
                path = [
                    'Identify constitutional violation (e.g., custody, PPO misuse)',
                    'Draft §1983 Complaint (MCR 2.111 + FRCP)',
                    'File Civil Cover Sheet (JS-44)',
                    'Prepare Summons for each defendant',
                    'Serve per Rule 4 of FRCP',
                    'Prepare for Removal/Remand motions if needed'
                ]
            else:
                path = ['Manual review required. File type unclassified.']

            self.decision_paths.append({
                'filename': item['filename'],
                'case_type': item['type'],
                'court': item['court'],
                'steps': path
            })

    def save_analysis(self, output_path):
        result = {
            'scan_location': self.scan_path,
            'extracted_files': self.extracted_data,
            'litigation_paths': self.decision_paths
        }
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"[SAVE] Full decision tree and scan results saved to: {output_path}")

# ==== EXECUTION ENTRY ====
if __name__ == "__main__":
    scan_path = input("Enter folder to scan (e.g., F:\): ").strip()
    engine = LitigationScanner(scan_path)
    engine.scan_directory()
    engine.extract_legal_relevance()
    engine.generate_decision_tree()
    engine.save_analysis("FRED_MICHIGAN_DECISION_TREE.json")
