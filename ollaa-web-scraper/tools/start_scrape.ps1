# Starts the owner-approved multi-day scrape (tools/run_until_done.py --live) if it is not
# already running. Run by the Windows task "OllaaWebScrape" each time the owner logs in
# (owner approved, 15 Nov 2026), so a restart of the laptop does not end the scrape.
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

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) { Say "python not found"; exit 1 }
$day = Get-Date -Format "yyyy-MM-dd"
$cmd = "cmd.exe /c `"`"$python`" -u -W ignore tools\run_until_done.py --live >> saved_pages\run_until_done_$day.log 2>> saved_pages\run_until_done_$day.err`""
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd; CurrentDirectory = $wd }
Say "started (result $($r.ReturnValue), pid $($r.ProcessId))"
