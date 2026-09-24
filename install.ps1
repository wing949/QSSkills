# ============================================================
# 🏗️ CSA Takeoff Suite — One-Click Installer (Windows PowerShell)
# ============================================================

$ErrorActionPreference = "Stop"

$PLUGIN_NAME = "csa-takeoff-suite"
$TARGET_DIR = "$env:USERPROFILE\.gemini\config\plugins\$PLUGIN_NAME"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " 🏗️  CSA TAKEOFF SUITE — HE SINH THAI MULTI-AGENT BOQ" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Kiem tra Python
Write-Host "[1/3] Kiem tra moi truong Python..." -ForegroundColor Yellow
try {
    $pyVer = python --version 2>&1
    Write-Host "  -> Python da san sang: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "  [LOI] Khong tim thay Python. Vui long cai dat Python 3.10+ va tich vao 'Add Python to PATH'!" -ForegroundColor Red
    exit 1
}

# 2. Cai dat thu vien phu thuoc
Write-Host "[2/3] Cai dat thu vien Python (openpyxl, ezdxf, pymupdf, matplotlib, pillow)..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
if (Test-Path "$PSScriptRoot\requirements.txt") {
    python -m pip install -r "$PSScriptRoot\requirements.txt" --quiet
} else {
    python -m pip install openpyxl ezdxf pymupdf matplotlib pillow --quiet
}
Write-Host "  -> Thu vien Python da duoc cai dat day du!" -ForegroundColor Green

# 3. Kiem tra / Copy plugin vao thu muc Antigravity/Gemini Config neu can
Write-Host "[3/3] Kiem tra duong dan plugin Antigravity..." -ForegroundColor Yellow
$currentPath = (Get-Item -Path $PSScriptRoot).FullName
if ($currentPath -ne $TARGET_DIR) {
    Write-Host "  -> Dang sao chep plugin vao: $TARGET_DIR" -ForegroundColor Cyan
    if (-not (Test-Path "$env:USERPROFILE\.gemini\config\plugins")) {
        New-Item -ItemType Directory -Path "$env:USERPROFILE\.gemini\config\plugins" -Force | Out-Null
    }
    Copy-Item -Path $currentPath -Destination $TARGET_DIR -Recurse -Force
    Write-Host "  -> Da sao chep thanh cong vao thu muc plugin!" -ForegroundColor Green
} else {
    Write-Host "  -> Plugin da nam dung thu muc Global: $TARGET_DIR" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " [THANH CONG] He sinh thai CSA Takeoff Suite da san sang!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
