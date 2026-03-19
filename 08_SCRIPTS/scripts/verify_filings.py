import os, re

filings = [
    r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_A\EMERGENCY_MOTION_RESTORE_PARENTING_TIME_v2.md',
    r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_A\MOTION_FOR_DISQUALIFICATION_v2.md',
    r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_A\MOTION_FOR_RECONSIDERATION_v2.md',
    r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_F\COA_APPELLANT_BRIEF_366810_v2.md',
    r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\LANE_F\COA_EMERGENCY_APPLICATION_366810_v2.md',
    r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\04_MSC\MSC_COMPLAINT_SUPERINTENDING_CONTROL_v2.md',
    r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\03_JTC\JTC_FORMAL_COMPLAINT_v2.md',
]

all_pass = True
for fp in filings:
    name = os.path.basename(fp)
    print(f"\n{'='*60}")
    print(f"VERIFYING: {name}")
    print(f"{'='*60}")
    
    if not os.path.exists(fp):
        print(f"  FAIL: File does not exist!")
        all_pass = False
        continue
    
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sz = len(content)
    lines = content.count('\n')
    print(f"  Size: {sz:,} chars, {lines} lines")
    
    # Check 1: No Tiffany Watson
    tiffany = len(re.findall(r'[Tt]iffany', content))
    if tiffany > 0:
        print(f"  FAIL: Found {tiffany} references to 'Tiffany' - must be 'Emily'")
        all_pass = False
    else:
        print(f"  PASS: No 'Tiffany' references")
    
    # Check 2: Emily Watson present
    emily = len(re.findall(r'Emily\s+(Ann\s+)?Watson', content))
    print(f"  INFO: {emily} references to 'Emily Watson'")
    
    # Check 3: No placeholder brackets
    placeholders = re.findall(r'\[[A-Z][a-z]+\s+[A-Z][a-z]+\]|\[ADDRESS\]|\[PHONE\]|\[DATE\]|\[CASE\s*#?\]', content, re.IGNORECASE)
    if placeholders:
        print(f"  WARN: Found placeholders: {placeholders[:5]}")
    else:
        print(f"  PASS: No placeholder brackets")
    
    # Check 4: No Barnes
    barnes = len(re.findall(r'[Bb]arnes', content))
    if barnes > 0:
        print(f"  FAIL: Found {barnes} references to 'Barnes' - should be removed")
        all_pass = False
    else:
        print(f"  PASS: No Barnes references")
    
    # Check 5: Day count check (no 567, 703, 704)
    bad_days = re.findall(r'\b(567|703|704)\b', content)
    if bad_days:
        print(f"  FAIL: Found bad day counts: {bad_days}")
        all_pass = False
    else:
        print(f"  PASS: No incorrect day counts (567/703/704)")
    
    # Check 6: Certificate of Service
    has_cos = 'Certificate of Service' in content or 'CERTIFICATE OF SERVICE' in content
    if has_cos:
        print(f"  PASS: Certificate of Service present")
    else:
        # JTC may not have one
        if 'JTC' in name:
            print(f"  INFO: No CoS (expected for JTC filing)")
        else:
            print(f"  WARN: No Certificate of Service found")
    
    # Check 7: Watson address in CoS
    watson_addr = '2160 Garland' in content
    if watson_addr:
        print(f"  PASS: Watson address (2160 Garland) present")
    elif 'JTC' in name:
        print(f"  INFO: No Watson address (expected for JTC)")
    else:
        print(f"  WARN: Watson address not found")
    
    # Check 8: Case numbers
    case_nums = re.findall(r'2024-001507-DC|366810|2023-5907-PP', content)
    print(f"  INFO: Case numbers found: {set(case_nums)}")
    
    # Check 9: Andrews contact info
    andrew_addr = '1423 W. Norton' in content or '1423 W Norton' in content
    print(f"  {'PASS' if andrew_addr else 'WARN'}: Andrews address {'present' if andrew_addr else 'not found'}")
    
    # Check 10: MCR/MCL citations
    mcr_cites = len(re.findall(r'MCR \d+\.\d+', content))
    mcl_cites = len(re.findall(r'MCL \d+\.\d+', content))
    print(f"  INFO: {mcr_cites} MCR citations, {mcl_cites} MCL citations")

print(f"\n{'='*60}")
print(f"FINAL RESULT: {'ALL PASS' if all_pass else 'ISSUES FOUND'}")
print(f"{'='*60}")
