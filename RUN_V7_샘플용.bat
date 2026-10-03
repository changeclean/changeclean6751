@echo off
chcp 65001 > nul
echo ==========================================
echo CHANGE CLEAN MOMO V7 FULL GENERATOR
echo ==========================================
python generate_all.py
echo.
echo 생성 완료. generated_site 폴더를 확인하세요.
pause
