@echo off
chcp 65001 > nul
cd /d "%~dp0"

set "LOG=%~dp0daily50_auto.log"
echo.>> "%LOG%"
echo ==================================================>> "%LOG%"
echo START %date% %time%>> "%LOG%"

REM 원격 변경사항 먼저 반영
git pull --rebase origin main >> "%LOG%" 2>&1

REM 오늘자 50개 생성
python daily_50_blog_posts.py >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] generator failed %date% %time%>> "%LOG%"
  exit /b 1
)

REM 생성된 청소일지와 로그를 제외한 사이트 변경사항 업로드
git add generated_site/cleaning-story >> "%LOG%" 2>&1
git commit -m "daily 50 cleaning stories %date%" >> "%LOG%" 2>&1

REM 같은 날짜에 이미 실행되어 새 파일이 없더라도 오류 취급하지 않음
git push origin main >> "%LOG%" 2>&1

echo DONE %date% %time%>> "%LOG%"
exit /b 0
