from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import quote
from email.utils import format_datetime
import html, re

ROOT = Path(__file__).resolve().parent
SITE = ROOT / 'generated_site'
BASE = 'https://changeclean6751.netlify.app'
RSS_LIMIT = 100


def url_for(path: Path):
    rel = path.relative_to(SITE).as_posix()
    if rel == 'index.html':
        return BASE + '/'
    if rel.endswith('/index.html'):
        rel = rel[:-10]
    return BASE + '/' + quote(rel, safe='/~-._')


def extract_tag(text, tag, default=''):
    m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', text, flags=re.I | re.S)
    if not m:
        return default
    return re.sub(r'<[^>]+>', '', m.group(1)).strip()


def update_rss():
    story_root = SITE / 'cleaning-story'
    posts = list(story_root.glob('*/index.html')) if story_root.exists() else []
    posts.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    posts = posts[:RSS_LIMIT]

    now = format_datetime(datetime.now(timezone.utc))
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        '<channel>',
        '  <title>체인지클린 청소일지</title>',
        f'  <link>{BASE}/</link>',
        '  <description>체인지클린 입주·이사청소 현장 기록과 청소 정보</description>',
        '  <language>ko-KR</language>',
        f'  <lastBuildDate>{now}</lastBuildDate>',
    ]

    for p in posts:
        text = p.read_text(encoding='utf-8', errors='ignore')
        title = extract_tag(text, 'title', '체인지클린 청소일지').split(' | ')[0]
        desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', text, flags=re.I)
        desc = desc_m.group(1).strip() if desc_m else '체인지클린 청소 현장 기록'
        loc = url_for(p)
        pub = format_datetime(datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc))
        lines += [
            '  <item>',
            f'    <title>{html.escape(title)}</title>',
            f'    <link>{html.escape(loc)}</link>',
            f'    <guid isPermaLink="true">{html.escape(loc)}</guid>',
            f'    <description>{html.escape(desc)}</description>',
            f'    <pubDate>{pub}</pubDate>',
            '  </item>',
        ]

    lines += ['</channel>', '</rss>']
    (SITE / 'rss.xml').write_text('\n'.join(lines), encoding='utf-8')
    return len(posts)


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
    rss_count = update_rss()
    print(f'[OK] sitemap: {len(pages):,} URLs / RSS: {rss_count} items / {today}')

if __name__ == '__main__':
    main()
