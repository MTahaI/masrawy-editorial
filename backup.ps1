# سكربت النسخ الاحتياطي الآلي — نظام التحرير
# التشغيل:  powershell -ExecutionPolicy Bypass -File D:\masrawy-backup\backup.ps1
# أو إنشاء اختصار على سطح المكتب للتشغيل بنقرة.

$ErrorActionPreference = "Stop"
$base = "D:\masrawy-backup"
$configSrc = "C:\Users\m122s\.config\opencode"
$projectSrc = "D:\مصراوي"
$toolsSrc = "C:\Users\m122s\Tools"

Write-Host "=== نسخ احتياطي لنظام التحرير ===" -ForegroundColor Cyan

# 1) تحديث الملفات
Write-Host "[1/4] تحديث الملفات..." -ForegroundColor Yellow
Copy-Item "$configSrc\opencode.jsonc" "$base\config\opencode.jsonc" -Force
Copy-Item "$configSrc\rules\*" "$base\rules\" -Force -Recurse
Copy-Item "$configSrc\skills\buriedsignals" "$base\skills\" -Recurse -Force
Get-ChildItem "$configSrc\skills" -Directory | Where-Object { $_.Name -notmatch 'buriedsignals|__pycache__' } | ForEach-Object {
    Copy-Item $_.FullName "$base\skills\" -Recurse -Force
}
Copy-Item "$projectSrc\*" "$base\project\" -Recurse -Force -ErrorAction SilentlyContinue
if (Test-Path "$toolsSrc\local-rag-mcp\config.py") { Copy-Item "$toolsSrc\local-rag-mcp\config.py" "$base\tools\local-rag-config.py" -Force }
if (Test-Path "$toolsSrc\Modelfile-ctx") { Copy-Item "$toolsSrc\Modelfile-ctx" "$base\tools\Modelfile-ctx" -Force }
Write-Host "      تم تحديث الملفات" -ForegroundColor Green

# 2) فحص أمني: رفض المتابعة إذا وُجد سر
Write-Host "[2/4] فحص أمني..." -ForegroundColor Yellow
$leak = Get-ChildItem $base -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch '\.git\\' } | ForEach-Object {
    $m = Select-String -Path $_.FullName -Pattern 'AIza[0-9A-Za-z_-]{20,}|AQ\.Ab[0-9A-Za-z_-]+|sk-[A-Za-z0-9]{20,}' -ErrorAction SilentlyContinue
    if ($m) { $_.FullName }
}
if ($leak) {
    Write-Host "⚠️  تم رصد أسرار في الملفات التالية — أوقفت الرفع. نظّفها وأعد المحاولة:" -ForegroundColor Red
    $leak | ForEach-Object { Write-Host "      $_" -ForegroundColor Red }
    exit 1
}
Write-Host "      لا توجد أسرار — آمن للرفع" -ForegroundColor Green

# 3) بناء نسخة ZIP محلية (النسخة الثانية من قاعدة 3-2-1)
Write-Host "[3/4] بناء ZIP محلي..." -ForegroundColor Yellow
$zipName = "masrawy-backup_$(Get-Date -Format 'yyyyMMdd_HHmm').zip"
$zipPath = "D:\masrawy-backup-zips\$zipName"
New-Item -ItemType Directory -Path "D:\masrawy-backup-zips" -Force | Out-Null
Compress-Archive -Path "$base\*" -DestinationPath $zipPath -Force
Get-ChildItem "D:\masrawy-backup-zips\*.zip" | Where-Object { $_.Name -ne $zipName } | Sort-Object LastWriteTime -Descending | Select-Object -Skip 5 | Remove-Item -Force
Write-Host "      ZIP: $zipName" -ForegroundColor Green

# 4) الدفع إلى GitHub (يتطلب gh مصادقًا)
Write-Host "[4/4] الدفع إلى GitHub..." -ForegroundColor Yellow
Set-Location $base
git add -A 2>$null
$changed = git status --porcelain
if ($changed) {
    git commit -m "نسخة احتياطية $(Get-Date -Format 'yyyy-MM-dd HH:mm')" 2>&1 | Out-Null
    git push origin main 2>&1 | ForEach-Object { Write-Host "      $_" }
    Write-Host "      تم الرفع إلى GitHub" -ForegroundColor Green
} else {
    Write-Host "      لا تغييرات — لا حاجة للرفع" -ForegroundColor Green
}

Write-Host "=== اكتمل النسخ الاحتياطي ===" -ForegroundColor Cyan
