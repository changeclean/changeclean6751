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
echo Updating sitemap.xml and robots.txt...
python update_sitemap.py
if errorlevel 1 (
  echo [ERROR] Sitemap update failed.
  pause
  exit /b 1
)

echo.
echo Git add/commit/push starting...
git add generated_site/cleaning-story generated_site/sitemap.xml generated_site/robots.txt
git commit -m "daily 50 cleaning stories and sitemap"
if errorlevel 1 echo [INFO] Nothing new to commit or commit skipped.
git push origin main

echo.
echo [DONE] Netlify will deploy automatically from GitHub.
pause
