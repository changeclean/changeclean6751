@echo off
cd /d "%~dp0"
echo ========================================
echo CHANGE CLEAN - DAILY 50 BLOG POSTS
echo ========================================
python daily_50_blog_posts.py
if errorlevel 1 (
  echo.
  echo [ERROR] Generation failed.
  pause
  exit /b 1
)
echo.
echo [OK] 50 blog pages generated.
echo.
echo Git add/commit/push starting...
git add generated_site/cleaning-story
git commit -m "daily 50 cleaning stories"
if errorlevel 1 echo [INFO] Nothing new to commit or commit skipped.
git push origin main
echo.
echo [DONE]
pause
