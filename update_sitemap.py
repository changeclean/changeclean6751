from pathlib import Path
from datetime import datetime
from urllib.parse import quote
import html

ROOT = Path(__file__).resolve().parent
SITE = ROOT / 'generated_site'
BASE = 'https://changeclean6751.netlify.app'


def url_for(path: Path):
    rel = path.relative_to(SITE).as_posix()
    if rel == 'index.html':
        return BASE + '/'
    if rel.endswith('/index.html'):
        rel = rel[:-10]
    return BASE + '/' + quote(rel, safe='/~-._')


def main():
    pages = sorted(SITE.rglob('index.html'))
    today = datetime.now().strftime('%Y-%m-%d')
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        loc = html.escape(url_for(p))
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d')
        lines += ['  <url>', f'    <loc>{loc}</loc>', f'    <lastmod>{mtime}</lastmod>', '  </url>']
    lines.append('</urlset>')
    (SITE / 'sitemap.xml').write_text('\n'.join(lines), encoding='utf-8')
    (SITE / 'robots.txt').write_text(
        'User-agent: *\nAllow: /\n\nSitemap: ' + BASE + '/sitemap.xml\n', encoding='utf-8'
    )
    print(f'[OK] sitemap: {len(pages):,} URLs / {today}')

if __name__ == '__main__':
    main()
