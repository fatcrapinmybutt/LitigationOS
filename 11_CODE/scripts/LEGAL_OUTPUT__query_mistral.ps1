# Direct Mistral Query for Legal Citations
param(
    [string]$ViolationType,
    [string]$Code
)

$prompt = @"
As a Michigan legal expert, provide case citations for: $ViolationType

Return 3-5 Michigan cases in this EXACT format:

CASE 1: [Case Name v. Case Name], [Citation], [Year]
HOLDING: [One sentence holding]
RELEVANCE: [How it applies to judicial misconduct]

CASE 2: [Case Name v. Case Name], [Citation], [Year]
HOLDING: [One sentence holding]
RELEVANCE: [How it applies to judicial misconduct]

Focus on Michigan Supreme Court and Court of Appeals decisions involving judges.
"@

Write-Host "Querying Mistral for: $ViolationType" -ForegroundColor Cyan
Write-Host ""

# Query Ollama with proper output capture
$response = ollama run mistral $prompt 2>&1 | Out-String

Write-Host $response

# Return the response for parsing
return $response
