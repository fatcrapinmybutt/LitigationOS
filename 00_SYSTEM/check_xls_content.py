"""Check actual XLS content including the single cell."""
import xlrd, os

XLS = r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\shady enhanced redacted ledger$$$ conv_10aa496d.xls"
wb = xlrd.open_workbook(XLS)
sh = wb.sheet_by_index(0)
print(f"Sheet: {sh.name}, {sh.nrows}r x {sh.ncols}c")
for ri in range(sh.nrows):
    for ci in range(sh.ncols):
        v = sh.cell(ri, ci)
        print(f"  [{ri},{ci}] type={v.ctype} val={repr(v.value)}")

# Also check file size
size = os.path.getsize(XLS)
print(f"\nFile size: {size} bytes")

# Check for other shady ledger files nearby
import glob
pattern = r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\SHADY\*ledger*"
for f in glob.glob(pattern):
    print(f"Found: {f} ({os.path.getsize(f)} bytes)")
