$OutputFile = "C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\run_bisect_stdout.txt"
cd C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai
python tests\_bisect.py 2>&1 | Out-File -FilePath $OutputFile -Encoding UTF8 -Append
"Script completed at $(Get-Date)" | Out-File -FilePath $OutputFile -Encoding UTF8 -Append

# Now read and output the _bisect_out.txt if it exists
if (Test-Path "C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_bisect_out.txt") {
    "=== CONTENTS OF _bisect_out.txt ===" | Out-File -FilePath $OutputFile -Encoding UTF8 -Append
    Get-Content "C:\Users\andre\LitigationOS\00_SYSTEM\legal_ai\tests\_bisect_out.txt" | Out-File -FilePath $OutputFile -Encoding UTF8 -Append
} else {
    "FILE _bisect_out.txt NOT FOUND" | Out-File -FilePath $OutputFile -Encoding UTF8 -Append
}
