# QUICK REFERENCE: PPO Scanned Document Files

## ⚡ TL;DR

**Your 3 files are STUBS** with only metadata. 

**Real content is here:**
```
C:\Users\andre\LitigationOS\08_TEXT\court_docs_ppo_cust_scanned_*.pdf.txt
```

---

## 📍 File Locations

### ❌ EMPTY STUB FILES (What you have)
```
C:\Users\andre\LitigationOS\01_FILINGS\TRIAL_14TH\
  ├─ custody_court_docs_ppo_cust_scanned_0001.txt (161.16 KB - STUB ONLY)
  ├─ custody_court_docs_ppo_cust_scanned_0004.txt (118.6 KB - STUB ONLY)
  ├─ custody_court_docs_ppo_cust_scanned_0007.txt (88.07 KB - STUB ONLY)
  └─ ... plus 5 more
```

### ✅ REAL OCR TEXT (What you need)
```
C:\Users\andre\LitigationOS\08_TEXT\
  ├─ court_docs_ppo_cust_scanned_0001.pdf.txt ✓ CONTAINS ACTUAL TEXT
  ├─ court_docs_ppo_cust_scanned_0004.pdf.txt ✓ CONTAINS ACTUAL TEXT
  ├─ court_docs_ppo_cust_scanned_0007.pdf.txt ✓ CONTAINS ACTUAL TEXT
  └─ ... plus 28+ more files with extracted content
```

---

## 📄 What's in the Text Files

**court_docs_ppo_cust_scanned_0001.pdf.txt**
- Personal Protection Order
- Emily Watson v. Andrew Pigors
- Judge: Jenny L. McNeill
- Contains respondent info, protective terms, conditions

**court_docs_ppo_cust_scanned_0004.pdf.txt**
- Domestic Relations Case Inventory
- Andrew James Pigors v. Emily Ann Watson
- 14th Circuit Court, Muskegon County
- Filed: 4/1/2024
- Contains case classification, family member info

**court_docs_ppo_cust_scanned_0007.pdf.txt**
- Amended Protective Custody Order
- Emily Watson v. Andrew Pigors
- Contains custody and protective conditions

---

## 🔍 Other Resources

| Resource | Path | Status |
|----------|------|--------|
| **OCR Text Files** | `08_TEXT/` | ✅ Contains 31+ files |
| **Stub Metadata** | `01_FILINGS/TRIAL_14TH/` | ❌ Metadata only |
| **JSON Data** | `09_DATA/SCANNED*.json` | ✅ May have metadata |
| **PDF Originals** | (searched I:\, C:\, F:\, G:\) | ❌ Not found |
| **Database** | `litigation_context.db` | Check for references |
| **OCR Tool** | PyMuPDF (fitz) | Install if needed |

---

## 🎯 Action Items

1. **Use the 08_TEXT directory** for all extracted court document text
2. **Do NOT use** the 01_FILINGS/TRIAL_14TH directory (it's metadata only)
3. **If you need originals**: Check `12_ARCHIVES/` or the I:\ drive
4. **For Python access**: `import fitz` requires `pip install PyMuPDF`

---

**Status**: ✅ All scanned PPO documents have been located and cataloged
