# Michigan Judicial Reference Lexicon - Query Helper
# Interactive search utility for the judicial reference lexicon

$lexiconPath = Join-Path $PSScriptRoot "_LEXICON_JUDICIAL.json"

if (-not (Test-Path $lexiconPath)) {
    Write-Host "ERROR: Lexicon not found at $lexiconPath" -ForegroundColor Red
    exit
}

Write-Host "Loading Michigan Judicial Reference Lexicon..." -ForegroundColor Cyan
$lexicon = Get-Content $lexiconPath -Raw | ConvertFrom-Json

Write-Host "Loaded $($lexicon.entries.Count) legal files" -ForegroundColor Green
Write-Host ""

function Show-Menu {
    Write-Host "=== MICHIGAN JUDICIAL REFERENCE LEXICON ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Search by MCR Reference (e.g., MCR 3.207)"
    Write-Host "2. Search by Category (Benchbook, FOC, Court Rules, etc.)"
    Write-Host "3. Search by Keywords"
    Write-Host "4. Search by Use Case"
    Write-Host "5. Find Related Files"
    Write-Host "6. Find Duplicates (by hash)"
    Write-Host "7. Browse All Entries"
    Write-Host "8. Show Statistics"
    Write-Host "Q. Quit"
    Write-Host ""
}

function Search-ByMCR {
    Write-Host "Enter MCR reference (e.g., MCR 3.207, 3.207, or just 207):" -ForegroundColor Yellow
    $input = Read-Host
    
    # Normalize input
    if ($input -match "^\d+$") {
        $input = "MCR 3.$input"
    } elseif ($input -match "^(\d+\.\d+)$") {
        $input = "MCR $($matches[1])"
    }
    
    $results = $lexicon.entries | Where-Object { 
        $_.mcr_references -contains $input 
    }
    
    if ($results) {
        Write-Host "`nFound $($results.Count) files referencing $input" -ForegroundColor Green
        foreach ($result in $results) {
            Write-Host "`n[$($result.id)] $($result.file_name)" -ForegroundColor Cyan
            Write-Host "  Path: $($result.original_path)"
            Write-Host "  Category: $($result.category)"
            Write-Host "  Keywords: $($result.keywords -join ', ')"
        }
    } else {
        Write-Host "No files found for $input" -ForegroundColor Red
    }
}

function Search-ByCategory {
    Write-Host "`nAvailable categories:" -ForegroundColor Yellow
    $categories = $lexicon.entries | Select-Object -ExpandProperty category -Unique | Sort-Object
    for ($i = 0; $i -lt $categories.Count; $i++) {
        Write-Host "  $($i+1). $($categories[$i])"
    }
    
    Write-Host "`nSelect category number:" -ForegroundColor Yellow
    $selection = Read-Host
    
    if ($selection -match "^\d+$" -and [int]$selection -le $categories.Count) {
        $category = $categories[[int]$selection - 1]
        $results = $lexicon.entries | Where-Object { $_.category -eq $category }
        
        Write-Host "`nFound $($results.Count) files in category: $category" -ForegroundColor Green
        foreach ($result in $results | Select-Object -First 20) {
            Write-Host "`n[$($result.id)] $($result.file_name)" -ForegroundColor Cyan
            Write-Host "  Path: $($result.original_path)"
            if ($result.description) {
                Write-Host "  Description: $($result.description)"
            }
        }
        
        if ($results.Count -gt 20) {
            Write-Host "`n(Showing first 20 of $($results.Count) results)" -ForegroundColor Yellow
        }
    }
}

function Search-ByKeyword {
    Write-Host "Enter keyword (e.g., parenting time, ex parte, custody):" -ForegroundColor Yellow
    $keyword = Read-Host
    
    $results = $lexicon.entries | Where-Object { 
        $_.keywords -contains $keyword -or 
        $_.file_name -match [regex]::Escape($keyword) -or
        $_.description -match [regex]::Escape($keyword)
    }
    
    if ($results) {
        Write-Host "`nFound $($results.Count) files matching '$keyword'" -ForegroundColor Green
        foreach ($result in $results | Select-Object -First 15) {
            Write-Host "`n[$($result.id)] $($result.file_name)" -ForegroundColor Cyan
            Write-Host "  Path: $($result.original_path)"
            Write-Host "  Category: $($result.category)"
            if ($result.mcr_references) {
                Write-Host "  MCR: $($result.mcr_references -join ', ')"
            }
        }
        
        if ($results.Count -gt 15) {
            Write-Host "`n(Showing first 15 of $($results.Count) results)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No files found matching '$keyword'" -ForegroundColor Red
    }
}

function Search-ByUseCase {
    Write-Host "`nAvailable use cases:" -ForegroundColor Yellow
    $useCases = $lexicon.use_case_map.PSObject.Properties
    
    $i = 1
    foreach ($useCase in $useCases) {
        Write-Host "  $i. $($useCase.Name) - $($useCase.Value.description)"
        $i++
    }
    
    Write-Host "`nSelect use case number:" -ForegroundColor Yellow
    $selection = Read-Host
    
    if ($selection -match "^\d+$" -and [int]$selection -le $useCases.Count) {
        $selectedCase = $useCases[[int]$selection - 1]
        $fileIds = $selectedCase.Value.recommended_files
        
        Write-Host "`nUse Case: $($selectedCase.Name)" -ForegroundColor Cyan
        Write-Host "Description: $($selectedCase.Value.description)"
        Write-Host "Relevant MCR: $($selectedCase.Value.relevant_mcr -join ', ')"
        Write-Host "`nRecommended files: $($fileIds.Count)" -ForegroundColor Green
        
        foreach ($fileId in $fileIds | Select-Object -First 10) {
            $file = $lexicon.entries | Where-Object { $_.id -eq $fileId }
            if ($file) {
                Write-Host "`n[$($file.id)] $($file.file_name)" -ForegroundColor Cyan
                Write-Host "  Path: $($file.original_path)"
            }
        }
        
        if ($fileIds.Count -gt 10) {
            Write-Host "`n(Showing first 10 of $($fileIds.Count) files)" -ForegroundColor Yellow
        }
    }
}

function Find-Related {
    Write-Host "Enter file name (or part of it):" -ForegroundColor Yellow
    $fileName = Read-Host
    
    $file = $lexicon.entries | Where-Object { $_.file_name -match [regex]::Escape($fileName) } | Select-Object -First 1
    
    if ($file) {
        Write-Host "`nFile: $($file.file_name)" -ForegroundColor Cyan
        Write-Host "Path: $($file.original_path)"
        Write-Host "Category: $($file.category)"
        
        if ($file.related_files -and $file.related_files.Count -gt 0) {
            Write-Host "`nRelated files ($($file.related_files.Count)):" -ForegroundColor Green
            
            foreach ($relatedId in $file.related_files | Select-Object -First 10) {
                $related = $lexicon.entries | Where-Object { $_.id -eq $relatedId }
                if ($related) {
                    Write-Host "  - $($related.file_name)"
                    Write-Host "    Path: $($related.original_path)"
                }
            }
        } else {
            Write-Host "`nNo related files found." -ForegroundColor Yellow
        }
    } else {
        Write-Host "File not found matching '$fileName'" -ForegroundColor Red
    }
}

function Find-Duplicates {
    Write-Host "`nFinding duplicate files by hash..." -ForegroundColor Yellow
    
    $duplicates = $lexicon.entries | 
        Where-Object { $_.file_hash } |
        Group-Object file_hash | 
        Where-Object { $_.Count -gt 1 }
    
    if ($duplicates) {
        Write-Host "Found $($duplicates.Count) sets of duplicate files" -ForegroundColor Green
        
        foreach ($dup in $duplicates | Select-Object -First 10) {
            Write-Host "`n=== Duplicate Set ($($dup.Count) files) ===" -ForegroundColor Cyan
            Write-Host "Hash: $($dup.Name.Substring(0, 16))..."
            
            foreach ($file in $dup.Group) {
                Write-Host "  - $($file.file_name)"
                Write-Host "    Path: $($file.original_path)"
                Write-Host "    Size: $([math]::Round($file.file_size_bytes / 1KB, 2)) KB"
            }
        }
        
        if ($duplicates.Count -gt 10) {
            Write-Host "`n(Showing first 10 of $($duplicates.Count) duplicate sets)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "No duplicates found" -ForegroundColor Green
    }
}

function Browse-All {
    Write-Host "Enter number of entries to show (default 20):" -ForegroundColor Yellow
    $count = Read-Host
    if (-not $count) { $count = 20 }
    
    $entries = $lexicon.entries | Select-Object -First $count
    
    foreach ($entry in $entries) {
        Write-Host "`n[$($entry.id)] $($entry.file_name)" -ForegroundColor Cyan
        Write-Host "  Path: $($entry.original_path)"
        Write-Host "  Category: $($entry.category)"
        Write-Host "  Size: $([math]::Round($entry.file_size_bytes / 1KB, 2)) KB"
        if ($entry.keywords) {
            Write-Host "  Keywords: $($entry.keywords -join ', ')"
        }
    }
    
    Write-Host "`n(Showing $count of $($lexicon.entries.Count) total entries)" -ForegroundColor Yellow
}

function Show-Statistics {
    Write-Host "`n=== LEXICON STATISTICS ===" -ForegroundColor Cyan
    Write-Host "Total Files: $($lexicon.entries.Count)"
    Write-Host "Created: $($lexicon.metadata.created)"
    Write-Host "Version: $($lexicon.metadata.version)"
    
    Write-Host "`nCategories:" -ForegroundColor Yellow
    $lexicon.entries | Group-Object category | Sort-Object Count -Descending | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Count) files"
    }
    
    Write-Host "`nFile Types:" -ForegroundColor Yellow
    $lexicon.entries | Group-Object content_type | Sort-Object Count -Descending | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Count) files"
    }
    
    $totalSize = ($lexicon.entries | Measure-Object -Property file_size_bytes -Sum).Sum
    Write-Host "`nTotal Size: $([math]::Round($totalSize / 1MB, 2)) MB" -ForegroundColor Green
    
    if ($lexicon.mcr_catalog) {
        $mcrCount = $lexicon.mcr_catalog.PSObject.Properties.Name.Count
        Write-Host "MCR References: $mcrCount" -ForegroundColor Green
    }
}

# Main loop
do {
    Show-Menu
    $choice = Read-Host "Select option"
    Write-Host ""
    
    switch ($choice.ToUpper()) {
        "1" { Search-ByMCR }
        "2" { Search-ByCategory }
        "3" { Search-ByKeyword }
        "4" { Search-ByUseCase }
        "5" { Find-Related }
        "6" { Find-Duplicates }
        "7" { Browse-All }
        "8" { Show-Statistics }
        "Q" { 
            Write-Host "Goodbye!" -ForegroundColor Cyan
            exit 
        }
        default { Write-Host "Invalid option" -ForegroundColor Red }
    }
    
    Write-Host "`nPress Enter to continue..." -ForegroundColor Gray
    Read-Host
    Clear-Host
    
} while ($true)
