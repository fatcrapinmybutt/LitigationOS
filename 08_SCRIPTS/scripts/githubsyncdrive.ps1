# === CONFIGURATION ===
$sourceDrive = "F:\\"                                   # Your F drive root
$gitRepoPath = "F:\\GitRepo\\fredprime"                 # Git repo on F drive
$gitRemoteURL = "https://github.com/YOUR-USER/YOUR-REPO.git"  # Replace this with your GitHub repo URL

# === INITIAL SETUP (RUN ONCE) ===
if (!(Test-Path $gitRepoPath)) {
    Write-Host "Creating Git repo directory on F: drive..."
    New-Item -ItemType Directory -Path $gitRepoPath -Force | Out-Null
    git init $gitRepoPath
    Set-Location $gitRepoPath
    git remote add origin $gitRemoteURL
    git branch -M main
} else {
    Set-Location $gitRepoPath
}

# === MIRROR FILES FROM F:\ TO GIT REPO SUBDIR ===
# Sync F:\ contents EXCLUDING the Git folder itself
Write-Host "Syncing F:\ to $gitRepoPath..."
robocopy "$sourceDrive" "$gitRepoPath" /MIR /XD "$gitRepoPath" /XF *.mp4 *.zip *.exe *.iso *.bak *.tmp *.log /XD node_modules venv > $null

# === GIT AUTO-COMMIT & PUSH ===
Write-Host "Staging changes..."
git add .

# Timestamp for unique commit messages
$timeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
git commit -m "Auto-sync from F drive at $timeStamp" 2>$null

Write-Host "Pushing to GitHub..."
git push origin main

Write-Host "`n✅ Sync complete."
