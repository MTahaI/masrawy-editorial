@echo off
chcp 65001 >nul
cd /d D:\masrawy-backup
echo ==================================================
echo   رفع النظام إلى GitHub - masrawy-editorial
echo ==================================================
echo.
echo  [مهم] إذا ظهرت نافذة "Git Credential Manager"
echo  اضغط: Sign in with your browser ثم Authorize
echo.
echo  جاري رفع الملفات...
echo.
git branch -M main
git pull origin main --allow-unrelated-histories --no-edit -X ours
git push -u origin main
echo.
echo ==================================================
echo  النتيجة أعلاه.
echo  لو ظهر السطر: master -^> main ... (راجع الأسطر)
echo  أو: Everything up-to-date = الرفع نجح.
echo  ارجع للمحادثة واكتب: تم الرفع
echo ==================================================
pause
