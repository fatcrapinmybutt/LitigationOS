# ============================================================================
# MASTER SEARCH INTERFACE - Unified Legal Research System
# ============================================================================
# Natural language search across all litigation indexes
# Version: 1.0 | Created: 2026-02-15
# ============================================================================

param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$Query,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("all", "case", "judicial", "evidence", "analysis", "citation")]
    [string]$Source = "all",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("CRITICAL", "HIGH", "MEDIUM", "LOW", "all")]
    [string]$Priority = "all",
    
    [Parameter(Mandatory=$false)]
    [string]$Case = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Judge = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Interactive,
    
    [Parameter(Mandatory=$false)]
    [switch]$Detailed,
    
    [Parameter(Mandatory=$false)]
    [switch]$ExportResults,
    
    [Parameter(Mandatory=$false)]
    [int]$MaxResults = 50
)

# ============================================================================
# Configuration
# ============================================================================

$MasterIndexPath = "C:\Users\andre\LITIGATIONOS_MASTER\MASTER_FILE_INDEX.json"
$JudicialLexiconPath = "C:\Users\andre\LITIGATIONOS_MASTER\00_JUDICIAL_REFERENCE_LIBRARY\_LEXICON_JUDICIAL.json"
$CasesIndexPath = "C:\Users\andre\LITIGATIONOS_MASTER\02_CASE_FILES\_CASES_INDEX.json"

# ============================================================================
# Helper Functions
# ============================================================================

function Show-Banner {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       MASTER SEARCH INTERFACE - LitigationOS v1.0          ║" -ForegroundColor Cyan
    Write-Host "║     Unified Intelligence Hub for Legal Research            ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Load-MasterIndex {
    try {
        $index = Get-Content $MasterIndexPath -Raw | ConvertFrom-Json
        return $index
    }
    catch {
        Write-Host "ERROR: Could not load master index from: $MasterIndexPath" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        exit 1
    }
}

function Load-JudicialLexicon {
    try {
        if (Test-Path $JudicialLexiconPath) {
            $lexicon = Get-Content $JudicialLexiconPath -Raw | ConvertFrom-Json
            return $lexicon
        }
    }
    catch {
        Write-Host "WARNING: Could not load judicial lexicon" -ForegroundColor Yellow
    }
    return $null
}

function Parse-NaturalLanguage {
    param([string]$Query)
    
    $queryLower = $Query.ToLower()
    $keywords = @()
    $filters = @{
        Case = ""
        Judge = ""
        Priority = "all"
        Type = "all"
    }
    
    # Extract case references
    if ($queryLower -match "custody case|custody") {
        $filters.Case = "pigors_v_watson_custody"
        $keywords += "custody"
    }
    if ($queryLower -match "ppo case|ppo|protection order") {
        $filters.Case = "pigors_v_watson_ppo"
        $keywords += "ppo"
    }
    if ($queryLower -match "housing case|shady oaks") {
        $filters.Case = "pigors_v_shady_oaks"
        $keywords += "housing"
    }
    if ($queryLower -match "criminal|perjury") {
        $filters.Case = "criminal_watson_family"
        $keywords += "criminal"
    }
    
    # Extract judge references
    if ($queryLower -match "judge mcneill|mcneill") {
        $filters.Judge = "jenny_mcneill"
        $keywords += "judge_mcneill"
    }
    
    # Extract priority
    if ($queryLower -match "critical|urgent|emergency") {
        $filters.Priority = "CRITICAL"
    }
    elseif ($queryLower -match "high priority|important") {
        $filters.Priority = "HIGH"
    }
    
    # Extract document types
    if ($queryLower -match "emergency motion|ex parte") {
        $keywords += "emergency_motion", "ex_parte"
        $filters.Type = "emergency_motions"
    }
    if ($queryLower -match "evidence|proof") {
        $keywords += "evidence"
        $filters.Type = "evidence"
    }
    if ($queryLower -match "court form|form") {
        $keywords += "court_forms"
        $filters.Type = "court_forms"
    }
    
    # Extract legal citations
    if ($queryLower -match "mcr\s*3\.207|3\.207") {
        $keywords += "MCR 3.207", "ex_parte"
    }
    if ($queryLower -match "mcr\s*3\.707|3\.707") {
        $keywords += "MCR 3.707", "ppo"
    }
    if ($queryLower -match "mcl\s*750\.422|750\.422") {
        $keywords += "MCL 750.422", "perjury"
    }
    
    # Extract common legal terms
    $legalTerms = @{
        "parenting time" = "parenting_time"
        "parental alienation" = "parental_alienation"
        "best interest" = "best_interest"
        "judicial bias" = "judicial_bias"
        "false allegations" = "false_allegations"
        "192 day|192-day" = "192_day_suspension"
    }
    
    foreach ($term in $legalTerms.Keys) {
        if ($queryLower -match $term) {
            $keywords += $legalTerms[$term]
        }
    }
    
    # Extract any remaining keywords
    $commonWords = @("show", "find", "get", "what", "where", "which", "all", "the", "a", "an", "for", "to", "in", "on", "at", "do", "i", "have", "is", "are", "related", "about", "mention", "regarding")
    $words = $queryLower -split '\s+' | Where-Object { 
        $_.Length -gt 2 -and $commonWords -notcontains $_ 
    }
    $keywords += $words
    
    return @{
        Keywords = ($keywords | Select-Object -Unique)
        Filters = $filters
        OriginalQuery = $Query
    }
}

function Search-Index {
    param(
        [object]$Index,
        [object]$ParsedQuery,
        [string]$Source,
        [string]$Priority,
        [string]$Case,
        [string]$Judge,
        [int]$MaxResults
    )
    
    $results = @()
    $searchIndex = $Index.search_index
    
    # Override filters from parameters
    if ($Case) { $ParsedQuery.Filters.Case = $Case }
    if ($Judge) { $ParsedQuery.Filters.Judge = $Judge }
    if ($Priority -ne "all") { $ParsedQuery.Filters.Priority = $Priority }
    
    # Search by keyword
    if ($Source -eq "all" -or $Source -eq "case" -or $Source -eq "evidence") {
        foreach ($keyword in $ParsedQuery.Keywords) {
            $keywordKey = $keyword -replace '\s+', '_'
            if ($searchIndex.by_keyword.PSObject.Properties.Name -contains $keywordKey) {
                $result = $searchIndex.by_keyword.$keywordKey
                $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "keyword" -Force
                $result | Add-Member -NotePropertyName "keyword" -NotePropertyValue $keyword -Force
                $results += $result
            }
        }
    }
    
    # Search by case
    if ($ParsedQuery.Filters.Case -or $Source -eq "case") {
        $caseToSearch = if ($ParsedQuery.Filters.Case) { $ParsedQuery.Filters.Case } else { $null }
        if ($caseToSearch -and $searchIndex.by_case.PSObject.Properties.Name -contains $caseToSearch) {
            $result = $searchIndex.by_case.$caseToSearch
            $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "case" -Force
            $results += $result
        }
        elseif (!$caseToSearch) {
            # Return all cases
            foreach ($case in $searchIndex.by_case.PSObject.Properties) {
                $result = $case.Value
                $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "case" -Force
                $result | Add-Member -NotePropertyName "case_id" -NotePropertyValue $case.Name -Force
                $results += $result
            }
        }
    }
    
    # Search by judge
    if ($ParsedQuery.Filters.Judge -or $Judge) {
        $judgeKey = if ($Judge) { $Judge } else { $ParsedQuery.Filters.Judge }
        if ($judgeKey -and $searchIndex.by_judge.PSObject.Properties.Name -contains $judgeKey) {
            $result = $searchIndex.by_judge.$judgeKey
            $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "judge" -Force
            $results += $result
        }
    }
    
    # Search by document type
    if ($ParsedQuery.Filters.Type -ne "all") {
        $typeKey = $ParsedQuery.Filters.Type
        if ($searchIndex.by_document_type.PSObject.Properties.Name -contains $typeKey) {
            $result = $searchIndex.by_document_type.$typeKey
            $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "document_type" -Force
            $result | Add-Member -NotePropertyName "doc_type" -NotePropertyValue $typeKey -Force
            $results += $result
        }
    }
    
    # Search citations
    if ($Source -eq "all" -or $Source -eq "citation") {
        foreach ($keyword in $ParsedQuery.Keywords) {
            # Search MCR citations
            foreach ($rule in $Index.legal_citations.michigan_court_rules) {
                if ($rule.citation -match $keyword -or $rule.title -match $keyword) {
                    $result = $rule | Select-Object *
                    $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "citation" -Force
                    $result | Add-Member -NotePropertyName "citation_type" -NotePropertyValue "MCR" -Force
                    $results += $result
                }
            }
            
            # Search MCL citations
            foreach ($law in $Index.legal_citations.michigan_compiled_laws) {
                if ($law.citation -match $keyword -or $law.title -match $keyword) {
                    $result = $law | Select-Object *
                    $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "citation" -Force
                    $result | Add-Member -NotePropertyName "citation_type" -NotePropertyValue "MCL" -Force
                    $results += $result
                }
            }
        }
    }
    
    # Filter by priority
    if ($ParsedQuery.Filters.Priority -ne "all") {
        $results = $results | Where-Object { 
            $_.priority -eq $ParsedQuery.Filters.Priority 
        }
    }
    
    # Remove duplicates and limit results
    $results = $results | Select-Object -First $MaxResults -Unique
    
    return $results
}

function Format-Results {
    param(
        [array]$Results,
        [object]$ParsedQuery,
        [switch]$Detailed
    )
    
    if ($Results.Count -eq 0) {
        Write-Host ""
        Write-Host "No results found for: " -NoNewline -ForegroundColor Yellow
        Write-Host $ParsedQuery.OriginalQuery -ForegroundColor White
        Write-Host ""
        Write-Host "Try:" -ForegroundColor Cyan
        Write-Host "  - Broader search terms" -ForegroundColor Gray
        Write-Host "  - Different keywords" -ForegroundColor Gray
        Write-Host "  - Use -Interactive mode for guided search" -ForegroundColor Gray
        Write-Host ""
        return
    }
    
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host " SEARCH RESULTS: " -NoNewline -ForegroundColor Green
    Write-Host $ParsedQuery.OriginalQuery -ForegroundColor White
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host " Found: $($Results.Count) results" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    
    $groupedResults = $Results | Group-Object -Property search_type
    
    foreach ($group in $groupedResults) {
        $typeName = switch ($group.Name) {
            "keyword" { "📋 KEYWORD MATCHES" }
            "case" { "⚖️  CASE FILES" }
            "judge" { "👨‍⚖️  JUDGE INFORMATION" }
            "document_type" { "📄 DOCUMENT TYPES" }
            "citation" { "📖 LEGAL CITATIONS" }
            default { "🔍 OTHER RESULTS" }
        }
        
        Write-Host $typeName -ForegroundColor Yellow
        Write-Host ("─" * 63) -ForegroundColor DarkGray
        
        foreach ($result in $group.Group) {
            switch ($result.search_type) {
                "case" {
                    $priorityColor = switch ($result.priority) {
                        "CRITICAL" { "Red" }
                        "HIGH" { "Yellow" }
                        "MEDIUM" { "Cyan" }
                        default { "White" }
                    }
                    
                    Write-Host "  Case: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.case_id -ForegroundColor White
                    if ($result.case_number) {
                        Write-Host "  Number: " -NoNewline -ForegroundColor Gray
                        Write-Host $result.case_number -ForegroundColor White
                    }
                    Write-Host "  Status: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.status -ForegroundColor White
                    Write-Host "  Priority: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.priority -ForegroundColor $priorityColor
                    if ($result.deadline) {
                        Write-Host "  Deadline: " -NoNewline -ForegroundColor Gray
                        Write-Host $result.deadline -ForegroundColor Red
                    }
                    if ($result.directory) {
                        Write-Host "  Location: " -NoNewline -ForegroundColor Gray
                        Write-Host $result.directory -ForegroundColor Cyan
                    }
                    if ($Detailed -and $result.keywords) {
                        Write-Host "  Keywords: " -NoNewline -ForegroundColor Gray
                        Write-Host ($result.keywords -join ", ") -ForegroundColor DarkCyan
                    }
                }
                
                "keyword" {
                    Write-Host "  Keyword: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.keyword -ForegroundColor White
                    if ($result.case_id) {
                        Write-Host "  Case: " -NoNewline -ForegroundColor Gray
                        Write-Host $result.case_id -ForegroundColor Cyan
                    }
                    if ($result.case_ids) {
                        Write-Host "  Cases: " -NoNewline -ForegroundColor Gray
                        Write-Host ($result.case_ids -join ", ") -ForegroundColor Cyan
                    }
                    Write-Host "  Documents: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.document_count -ForegroundColor White
                    if ($result.priority) {
                        Write-Host "  Priority: " -NoNewline -ForegroundColor Gray
                        Write-Host $result.priority -ForegroundColor Yellow
                    }
                    if ($Detailed -and $result.related_terms) {
                        Write-Host "  Related: " -NoNewline -ForegroundColor Gray
                        Write-Host ($result.related_terms -join ", ") -ForegroundColor DarkCyan
                    }
                }
                
                "citation" {
                    Write-Host "  Citation: " -NoNewline -ForegroundColor Gray
                    Write-Host "$($result.citation_type) $($result.citation)" -ForegroundColor White
                    Write-Host "  Title: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.title -ForegroundColor Cyan
                    Write-Host "  Relevance: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.relevance -ForegroundColor White
                    if ($result.case_references) {
                        Write-Host "  Cases: " -NoNewline -ForegroundColor Gray
                        Write-Host ($result.case_references -join ", ") -ForegroundColor Cyan
                    }
                }
                
                "judge" {
                    Write-Host "  Judge: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.full_name -ForegroundColor White
                    Write-Host "  Court: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.court -ForegroundColor Cyan
                    Write-Host "  Cases: " -NoNewline -ForegroundColor Gray
                    Write-Host ($result.case_ids -join ", ") -ForegroundColor Cyan
                    Write-Host "  Documents: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.document_count -ForegroundColor White
                }
                
                "document_type" {
                    Write-Host "  Type: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.doc_type -ForegroundColor White
                    Write-Host "  Count: " -NoNewline -ForegroundColor Gray
                    Write-Host $result.count -ForegroundColor White
                    if ($result.location) {
                        Write-Host "  Location: " -NoNewline -ForegroundColor Gray
                        Write-Host $result.location -ForegroundColor Cyan
                    }
                    if ($result.deadline) {
                        Write-Host "  Deadline: " -NoNewline -ForegroundColor Gray
                        Write-Host $result.deadline -ForegroundColor Red
                    }
                }
            }
            Write-Host ""
        }
    }
}

function Show-InteractiveMenu {
    param([object]$Index)
    
    $continue = $true
    
    while ($continue) {
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host " INTERACTIVE SEARCH MENU" -ForegroundColor Cyan
        Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "1. Search by natural language query" -ForegroundColor White
        Write-Host "2. Browse all cases" -ForegroundColor White
        Write-Host "3. View critical deadlines" -ForegroundColor White
        Write-Host "4. Search by case" -ForegroundColor White
        Write-Host "5. Search by judge" -ForegroundColor White
        Write-Host "6. Search legal citations (MCR/MCL)" -ForegroundColor White
        Write-Host "7. View emergency motions" -ForegroundColor White
        Write-Host "8. Browse evidence files" -ForegroundColor White
        Write-Host "9. Show quick queries examples" -ForegroundColor White
        Write-Host "0. Exit" -ForegroundColor Gray
        Write-Host ""
        
        $choice = Read-Host "Select option (0-9)"
        
        switch ($choice) {
            "1" {
                $query = Read-Host "Enter your search query"
                $parsed = Parse-NaturalLanguage -Query $query
                $results = Search-Index -Index $Index -ParsedQuery $parsed -Source "all" -Priority "all" -MaxResults $MaxResults
                Format-Results -Results $results -ParsedQuery $parsed -Detailed:$Detailed
            }
            "2" {
                $results = $Index.search_index.by_case.PSObject.Properties | ForEach-Object {
                    $case = $_.Value
                    $case | Add-Member -NotePropertyName "case_id" -NotePropertyValue $_.Name -Force
                    $case | Add-Member -NotePropertyName "search_type" -NotePropertyValue "case" -Force
                    $case
                }
                $parsed = @{ OriginalQuery = "All cases"; Keywords = @(); Filters = @{} }
                Format-Results -Results $results -ParsedQuery $parsed -Detailed:$true
            }
            "3" {
                Write-Host ""
                Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
                Write-Host " CRITICAL DEADLINES" -ForegroundColor Red
                Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Red
                foreach ($deadline in $Index.quick_access.critical_deadlines) {
                    Write-Host ""
                    Write-Host "  Deadline: " -NoNewline -ForegroundColor Gray
                    Write-Host $deadline.deadline -ForegroundColor Red
                    Write-Host "  Task: " -NoNewline -ForegroundColor Gray
                    Write-Host $deadline.description -ForegroundColor White
                    Write-Host "  Location: " -NoNewline -ForegroundColor Gray
                    Write-Host $deadline.location -ForegroundColor Cyan
                }
                Write-Host ""
            }
            "4" {
                Write-Host ""
                Write-Host "Available cases:" -ForegroundColor Cyan
                $caseList = $Index.search_index.by_case.PSObject.Properties.Name
                for ($i = 0; $i -lt $caseList.Count; $i++) {
                    Write-Host "  $($i+1). $($caseList[$i])" -ForegroundColor White
                }
                $caseChoice = Read-Host "Select case number"
                if ($caseChoice -match '^\d+$' -and [int]$caseChoice -gt 0 -and [int]$caseChoice -le $caseList.Count) {
                    $selectedCase = $caseList[[int]$caseChoice - 1]
                    $result = $Index.search_index.by_case.$selectedCase
                    $result | Add-Member -NotePropertyName "case_id" -NotePropertyValue $selectedCase -Force
                    $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "case" -Force
                    $parsed = @{ OriginalQuery = "Case: $selectedCase"; Keywords = @(); Filters = @{} }
                    Format-Results -Results @($result) -ParsedQuery $parsed -Detailed:$true
                }
            }
            "5" {
                $results = $Index.search_index.by_judge.PSObject.Properties | ForEach-Object {
                    $judge = $_.Value
                    $judge | Add-Member -NotePropertyName "search_type" -NotePropertyValue "judge" -Force
                    $judge
                }
                $parsed = @{ OriginalQuery = "All judges"; Keywords = @(); Filters = @{} }
                Format-Results -Results $results -ParsedQuery $parsed -Detailed:$true
            }
            "6" {
                $citationType = Read-Host "Search MCR or MCL? (Enter 'MCR' or 'MCL')"
                $citationQuery = Read-Host "Enter citation number or keyword"
                
                $results = @()
                if ($citationType -eq "MCR") {
                    $results = $Index.legal_citations.michigan_court_rules | Where-Object {
                        $_.citation -match $citationQuery -or $_.title -match $citationQuery
                    } | ForEach-Object {
                        $_ | Add-Member -NotePropertyName "search_type" -NotePropertyValue "citation" -Force
                        $_ | Add-Member -NotePropertyName "citation_type" -NotePropertyValue "MCR" -Force
                        $_
                    }
                }
                elseif ($citationType -eq "MCL") {
                    $results = $Index.legal_citations.michigan_compiled_laws | Where-Object {
                        $_.citation -match $citationQuery -or $_.title -match $citationQuery
                    } | ForEach-Object {
                        $_ | Add-Member -NotePropertyName "search_type" -NotePropertyValue "citation" -Force
                        $_ | Add-Member -NotePropertyName "citation_type" -NotePropertyValue "MCL" -Force
                        $_
                    }
                }
                
                $parsed = @{ OriginalQuery = "$citationType $citationQuery"; Keywords = @(); Filters = @{} }
                Format-Results -Results $results -ParsedQuery $parsed -Detailed:$true
            }
            "7" {
                $result = $Index.search_index.by_document_type.emergency_motions
                $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "document_type" -Force
                $result | Add-Member -NotePropertyName "doc_type" -NotePropertyValue "emergency_motions" -Force
                $parsed = @{ OriginalQuery = "Emergency motions"; Keywords = @(); Filters = @{} }
                Format-Results -Results @($result) -ParsedQuery $parsed -Detailed:$true
            }
            "8" {
                $result = $Index.search_index.by_document_type.evidence
                $result | Add-Member -NotePropertyName "search_type" -NotePropertyValue "document_type" -Force
                $result | Add-Member -NotePropertyName "doc_type" -NotePropertyValue "evidence" -Force
                $parsed = @{ OriginalQuery = "Evidence files"; Keywords = @(); Filters = @{} }
                Format-Results -Results @($result) -ParsedQuery $parsed -Detailed:$true
            }
            "9" {
                Write-Host ""
                Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
                Write-Host " QUICK QUERY EXAMPLES" -ForegroundColor Cyan
                Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Cyan
                Write-Host ""
                Write-Host "Natural language examples:" -ForegroundColor Yellow
                Write-Host "  • Show all files related to the custody case" -ForegroundColor White
                Write-Host "  • Find MCR 3.207 references" -ForegroundColor White
                Write-Host "  • What evidence do I have for parental alienation?" -ForegroundColor White
                Write-Host "  • Which files mention Judge McNeill?" -ForegroundColor White
                Write-Host "  • Show all emergency motions" -ForegroundColor White
                Write-Host "  • Find documents about the 192-day suspension" -ForegroundColor White
                Write-Host "  • Show PPO case files" -ForegroundColor White
                Write-Host "  • What are the critical deadlines?" -ForegroundColor White
                Write-Host ""
            }
            "0" {
                $continue = $false
            }
            default {
                Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            }
        }
        
        if ($continue) {
            Write-Host ""
            Read-Host "Press Enter to continue"
        }
    }
}

# ============================================================================
# Main Execution
# ============================================================================

Show-Banner

# Load master index
$masterIndex = Load-MasterIndex

# Interactive mode
if ($Interactive) {
    Show-InteractiveMenu -Index $masterIndex
    exit 0
}

# Command-line query
if (-not $Query) {
    Write-Host "ERROR: No query provided. Use -Query parameter or -Interactive mode." -ForegroundColor Red
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Cyan
    Write-Host "  .\SEARCH_INTERFACE.ps1 -Query 'custody case'" -ForegroundColor Gray
    Write-Host "  .\SEARCH_INTERFACE.ps1 -Query 'MCR 3.207'" -ForegroundColor Gray
    Write-Host "  .\SEARCH_INTERFACE.ps1 -Interactive" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Parse and execute query
$parsedQuery = Parse-NaturalLanguage -Query $Query
$results = Search-Index -Index $masterIndex -ParsedQuery $parsedQuery -Source $Source -Priority $Priority -Case $Case -Judge $Judge -MaxResults $MaxResults
Format-Results -Results $results -ParsedQuery $parsedQuery -Detailed:$Detailed

# Export results if requested
if ($ExportResults -and $results.Count -gt 0) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $exportPath = "C:\Users\andre\LITIGATIONOS_MASTER\search_results_$timestamp.json"
    $results | ConvertTo-Json -Depth 10 | Out-File -FilePath $exportPath -Encoding UTF8
    Write-Host ""
    Write-Host "Results exported to: " -NoNewline -ForegroundColor Green
    Write-Host $exportPath -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Search complete." -ForegroundColor Green
Write-Host ""
