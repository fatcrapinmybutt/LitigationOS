param(
  [string]$TaskName="WorldFirst_GDrive_Daily",
  [string]$StartTime="03:15"
)
$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot=Resolve-Path (Join-Path $Root "..")
$RunScript=Join-Path $Root "run_pipeline.ps1"
$UserId="$env:USERNAME"
$Date=(Get-Date -Format "yyyy-MM-dd")
$Time="$StartTime:00"
$Xml=@"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>$Date`T$Time</Date>
    <Author>$UserId</Author>
    <Description>Daily Google Drive normalize + inventory + canonical ship</Description>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>$Date`T$Time</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$UserId</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <StartWhenAvailable>true</StartWhenAvailable>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <ExecutionTimeLimit>PT8H</ExecutionTimeLimit>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -File "$RunScript"</Arguments>
      <WorkingDirectory>$ProjectRoot</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@
$Tmp=Join-Path $env:TEMP ($TaskName+".xml")
[IO.File]::WriteAllText($Tmp,$Xml,[Text.Encoding]::Unicode)
schtasks /Create /TN $TaskName /XML $Tmp /F | Out-Null
Remove-Item $Tmp -Force
Write-Host "Installed scheduled task: $TaskName"
