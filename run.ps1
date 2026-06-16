# run.ps1 — bootstrap the Apex case-study environment on Windows (PowerShell).
# Native Windows, no WSL. Run from the repo root:  .\run.ps1
# If you get an execution-policy error, run this once in the same terminal:
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "=== Apex case study - environment bootstrap (Windows) ==="

# 1. Folder scaffold (idempotent)
foreach ($d in "clean","analysis","qa","deliverables") {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}
Write-Host "[ok] folders: clean/ analysis/ qa/ deliverables/"

# 2. Verify raw inputs present
$missing = $false
foreach ($f in "raw\Apex_Core_Database.xlsx","raw\Apex_Transaction_Ledger.xlsx",
                "raw\Case_Study.pdf","raw\Data_Dictionary.pdf") {
    if (-not (Test-Path $f)) { Write-Host "[MISSING] $f"; $missing = $true }
}
if ($missing) { Write-Host "Aborting: raw files missing"; exit 1 }
Write-Host "[ok] all 4 raw files present"

# 3. Verify config + briefs present
foreach ($f in "definitions.yaml","decisions_log.md","ORCHESTRATOR_README.md",
                "KICKOFF_PROMPT.md","AGENT_1_BRIEF.md","AGENT_2_BRIEF.md","AGENT_3_BRIEF.md") {
    if (-not (Test-Path $f)) { Write-Host "[MISSING] $f"; exit 1 }
}
Write-Host "[ok] config + briefs present"

# 4. Resolve a Python launcher (py preferred on Windows, else python)
$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue)       { $pythonCmd = "py" }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $pythonCmd = "python" }
else { Write-Host "[FAIL] Python not found on PATH. Install Python 3 from python.org and re-run."; exit 1 }
Write-Host "[ok] python launcher: $pythonCmd"

# 5. Validate definitions.yaml parses (uses stdlib if pyyaml present; soft-skips otherwise)
& $pythonCmd -c @"
try:
    import yaml
    yaml.safe_load(open('definitions.yaml'))
    print('[ok] definitions.yaml is valid YAML')
except ImportError:
    print('[skip] pyyaml not installed yet; will be available after deps install')
except Exception as e:
    print('[FAIL] definitions.yaml:', e); raise SystemExit(1)
"@

# 6. Virtual env + libs
if (-not (Test-Path ".venv")) { & $pythonCmd -m venv .venv }
$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) { Write-Host "[FAIL] venv creation failed."; exit 1 }
& $venvPy -m pip install --upgrade pip -q
& $venvPy -m pip install -q pandas numpy openpyxl scikit-learn matplotlib python-pptx pyarrow lifelines kmodes pyyaml
Write-Host "[ok] python deps installed in .venv"

Write-Host ""
Write-Host "=== Bootstrap complete. Next step: ==="
Write-Host "Open this repo in Claude Code and paste the contents of KICKOFF_PROMPT.md."
Write-Host "To use the venv manually:  .\.venv\Scripts\Activate.ps1"
