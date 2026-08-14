# نافذة تسجيل الدخول إلى GitHub
$gh = "C:\Users\m122s\Tools\gh\gh.exe"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host " تسجيل الدخول إلى GitHub" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1) ستنزل قائمة: اختر [GitHub.com] ثم Enter" -ForegroundColor White
Write-Host "2) اختر [HTTPS] ثم Enter" -ForegroundColor White
Write-Host "3) اختر [Login with a web browser] ثم Enter" -ForegroundColor White
Write-Host "4) سيظهر رمز - انسخه" -ForegroundColor White
Write-Host "5) افتح الرابط والصق الرمز واضغط Authorize" -ForegroundColor White
Write-Host "6) ارجع لهذه النافذة وانتظر [Logged in as]" -ForegroundColor Yellow
Write-Host ""

& $gh auth login

Write-Host ""
$check = & $gh auth status 2>&1
if ($check -match "Logged in to github.com") {
    Write-Host "نجاح! ارجع للمحادثة واكتب: تم" -ForegroundColor Green
} else {
    Write-Host "لم يكتمل بعد - أعد المحاولة باتباع الخطوات بحذر" -ForegroundColor Red
}
Read-Host "اضغط Enter للإغلاق"
