# Runs one day's share of the owner-approved scrape (tools/run_until_done.py --live --once)
# if it is not already running. Run by the Windows task "OllaaWebScrape" once a day at a
# fixed time (owner, 16 Nov 2026; if the laptop was off then, Windows runs it as soon as it
# can). Each run adds a line to saved_pages/daily_log.csv.
# It never starts after a stop: if SCRAPE_STOPPED.txt or SCRAPE_FINISHED.txt exists, or a
# run log says "STOPPED for good", it does nothing. Reads no passwords; writes only logs.
$ErrorActionPreference = "Stop"
$wd = Split-Path -Parent $PSScriptRoot
$pages = Join-Path $wd "saved_pages"
$note = Join-Path $pages "start_scrape.log"
function Say($msg) { Add-Content -Path $note -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm') $msg" -Encoding utf8 }

$running = Get-CimInstance Win32_Process | Where-Object { $_.Name -like "python*" -and $_.CommandLine -match "run_until_done\.py" }
if ($running) { Say "already running (pid $($running.ProcessId -join ', ')); nothing to do"; exit 0 }

foreach ($marker in "SCRAPE_STOPPED.txt", "SCRAPE_FINISHED.txt") {
    if (Test-Path (Join-Path $pages $marker)) { Say "not starting: $marker exists"; exit 0 }
}
$stoppedLog = Get-ChildItem $pages -Filter "run_until_done_*.log" | Where-Object { Select-String -Path $_.FullName -Pattern "STOPPED for good" -Quiet }
if ($stoppedLog) {
    Set-Content -Path (Join-Path $pages "SCRAPE_STOPPED.txt") -Value "found 'STOPPED for good' in $($stoppedLog[0].Name)" -Encoding utf8
    Say "not starting: $($stoppedLog[0].Name) says STOPPED for good"
    exit 0
}

# Right after log-in the internet may not be connected yet (16 Nov 2026 the run stopped
# because betdelala.com could not be found). Wait up to 15 minutes for it; if it never
# comes, do nothing (this is not a stop: the next log-in tries again).
$online = $false
for ($i = 0; $i -lt 30; $i++) {
    try { [System.Net.Dns]::GetHostAddresses("betdelala.com") | Out-Null; $online = $true; break } catch { Start-Sleep -Seconds 30 }
}
if (-not $online) { Say "no internet after 15 minutes; not starting this time"; exit 0 }

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { Say "python not found"; exit 1 }
$day = Get-Date -Format "yyyy-MM-dd"
$cmd = "cmd.exe /c `"`"$python`" -u -W ignore tools\run_until_done.py --live --once >> saved_pages\run_until_done_$day.log 2>> saved_pages\run_until_done_$day.err`""
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $wd }
Say "started (result $($r.ReturnValue), pid $($r.ProcessId))"
