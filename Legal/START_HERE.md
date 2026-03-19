# START_HERE — CAPSTONE_PORTFOLIO_STACK_v2026-01-23.9

## Goal: one desktop icon does everything
You download the ZIP to Downloads. You keep ONE launcher on your Desktop.
You double-click the Desktop launcher. It moves/copies, extracts, and starts Studio.

### Step 1 (once): Put launcher on Desktop
Download this file and move it to Desktop:
`CAPSTONE_DESKTOP_ONECLICK_v2026-01-23.9.cmd`

### Step 2 (every time): Download the pack ZIP
It will land in:
`C:\Users\andre\Downloads\CAPSTONE_PORTFOLIO_STACK_*.zip`

### Step 3: Double-click the Desktop launcher
It will:
- find newest `CAPSTONE_PORTFOLIO_STACK_*.zip` in Downloads
- copy to `F:\CAPSTONE\Packs\_INCOMING\`
- extract to `F:\CAPSTONE\Packs\<ZIPBASE>\`
- run: `<ZIPBASE>\scripts\00_LAUNCH_STUDIO.cmd`

### Logs
If anything fails, open:
`F:\CAPSTONE\Packs\desktop_bootstrap_v2026-01-23.9.log`
