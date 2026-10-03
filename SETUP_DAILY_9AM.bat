@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ==============================================
echo  CHANGE CLEAN - DAILY 09:00 AUTO SETUP
echo ==============================================
echo.

set "TASKNAME=ChangeClean_Daily50_Blog_9AM"
set "RUNFILE=%~dp0RUN_DAILY_50_BLOG_AUTO.bat"

schtasks /Delete /TN "%TASKNAME%" /F >nul 2>&1
schtasks /Create /TN "%TASKNAME%" /TR "\"%RUNFILE%\"" /SC DAILY /ST 09:00 /F

if errorlevel 1 (
  echo.
  echo [ERROR] 작업 스케줄 등록에 실패했습니다.
  echo 이 파일을 마우스 오른쪽 버튼 - 관리자 권한으로 실행해보세요.
  pause
  exit /b 1
)

echo.
echo [OK] 매일 오전 9시 자동 실행 등록 완료
echo 작업 이름: %TASKNAME%
echo 실행 파일: %RUNFILE%
echo.
schtasks /Query /TN "%TASKNAME%" /FO LIST /V
pause
