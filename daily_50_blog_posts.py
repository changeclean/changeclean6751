from pathlib import Path
from datetime import datetime
import csv, random, re, hashlib

ROOT = Path(__file__).resolve().parent
SITE = ROOT / 'generated_site'
OUT = SITE / 'cleaning-story'
ASSETS = SITE / 'assets'
REGIONS = ROOT / 'regions.csv'
COUNT = 50

SERVICES = ['입주청소','이사청소','아파트청소','빌라청소','오피스텔청소']
OPENINGS = [
    '어제는 {region} {dong} {service} 현장에 다녀왔습니다. 집 전체를 먼저 둘러본 뒤 창틀과 수납장, 주방과 욕실처럼 먼지가 남기 쉬운 곳부터 작업 순서를 잡았습니다.',
    '이번 {region} {dong} 현장은 {service} 작업으로 방문했습니다. 비어 있는 공간이라도 창틀 레일과 수납장 안쪽에는 잔먼지가 남아 있어 공간별로 확인하면서 청소를 진행했습니다.',
    '{dong}에서 {service} 작업을 진행했습니다. 현관에서 방과 거실, 주방, 욕실 순으로 상태를 확인하고 손이 많이 가는 곳부터 하나씩 정리했습니다.'
]
MIDDLES = [
    '주방은 싱크대와 상·하부장 안쪽을 확인하고 후드 주변까지 닦았습니다. 욕실은 수전과 거울, 타일, 배수구 주변을 중심으로 정리했습니다.',
    '창틀은 레일 사이와 모서리에 남은 먼지를 확인했고 몰딩 위쪽과 수납장 내부처럼 평소 눈에 잘 들어오지 않는 부분도 함께 닦았습니다.',
    '방과 거실은 위쪽 먼지를 먼저 정리한 다음 바닥으로 내려오는 순서로 진행했습니다. 마지막에는 처음부터 다시 둘러보면서 빠진 곳이 없는지 확인했습니다.'
]
ENDS = [
    '공간별 작업을 마친 뒤 바닥과 물자국을 다시 확인하고 현장을 마무리했습니다. 입주 날짜가 정해져 있다면 지역과 평수, 희망 날짜를 알려주시면 상담이 가능합니다.',
    '마지막 검수까지 마치고 작업을 끝냈습니다. 같은 평수라도 창 개수와 수납공간, 오염 상태에 따라 작업량이 달라질 수 있어 현장 상황을 함께 확인하고 있습니다.',
    '전체 작업 후 주방과 욕실, 창틀을 한 번 더 확인했습니다. 아파트뿐 아니라 빌라와 오피스텔, 원룸도 지역과 평수에 맞춰 상담하고 있습니다.'
]

def slugify(s):
    return re.sub(r'[^a-z0-9-]+','-',s.lower()).strip('-')

def load_regions():
    with REGIONS.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def assets():
    return sorted([p.name for p in ASSETS.glob('site_*.webp')])

def pick_images(seed, files, n=5):
    r = random.Random(seed)
    return r.sample(files, min(n, len(files)))

def page(row, service, imgs, day, idx):
    sido, sigungu, dong = row['시도'], row['시군구'], row['동']
    region = f'{sido} {sigungu}'
    rnd = random.Random(f'{day}-{dong}-{service}-{idx}')
    opening = rnd.choice(OPENINGS).format(region=region,dong=dong,service=service)
    mid1, mid2 = rnd.sample(MIDDLES, 2)
    end = rnd.choice(ENDS)
    title = f'어제 다녀온 {dong} {service} 현장'
    # 항상 사이트 루트 assets를 사용. 상세페이지 깊이와 무관하게 이미지가 깨지지 않는다.
    im = [f'/assets/{x}' for x in imgs]
    near = [x for x in load_regions() if x['시군구']==sigungu and x['동']!=dong][:4]
    near_html = ''.join(f'<a href="/">{x["동"]} 입주청소</a>' for x in near)
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | 체인지클린</title><meta name="description" content="{region} {dong} {service} 청소 현장 기록. 체인지클린 청소 작업과 현장 사진을 확인하세요."><style>*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:#f5f6f7;color:#17232d;font-family:Arial,'Noto Sans KR',sans-serif;line-height:1.85}}.w{{max-width:900px;margin:auto;padding:0 18px}}header{{height:68px;background:#fff;border-bottom:1px solid #e6e8ea;position:sticky;top:0;z-index:20}}.nav{{height:100%;display:flex;align-items:center;justify-content:space-between}}.logo{{font-size:25px;font-weight:900;color:#113d5c}}.phone{{font-weight:900}}.post{{background:#fff;margin:28px auto;border:1px solid #e1e5e8;border-radius:18px;padding:34px 38px}}.cat{{font-size:13px;color:#267296;font-weight:800}}h1{{font-size:36px;line-height:1.3;margin:8px 0 4px}}.date{{font-size:14px;color:#8a949c;margin-bottom:28px}}p{{font-size:16px;margin:18px 0}}h2{{font-size:24px;margin:36px 0 12px}}.photo{{display:block;width:100%;max-height:560px;object-fit:cover;border-radius:13px;margin:22px 0 28px}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:22px 0}}.two img{{width:100%;height:310px;object-fit:cover;border-radius:12px}}.note{{margin:28px 0;padding:18px 20px;background:#f1f7f9;border-radius:12px}}.near{{margin-top:38px;padding-top:24px;border-top:1px solid #e3e7e9}}.near a{{display:inline-block;text-decoration:none;background:#f2f6f8;border:1px solid #dce5e9;border-radius:999px;padding:8px 13px;margin:4px;color:#263943;font-weight:700}}.quote{{background:#103e5d;color:#fff;border-radius:16px;padding:26px;margin-top:28px}}.quote h2{{margin-top:0}}form{{display:grid;grid-template-columns:1fr 1fr;gap:9px}}input,textarea{{font:inherit;padding:12px;border:0;border-radius:8px}}textarea{{grid-column:1/-1;min-height:90px}}.btn{{background:#ffd02c;border:0;border-radius:9px;padding:13px 17px;font-weight:900}}.floating{{position:fixed;right:20px;bottom:20px;display:flex;flex-direction:column;gap:9px;z-index:30}}.float{{padding:13px 18px;border-radius:999px;text-decoration:none;font-weight:900;box-shadow:0 5px 18px #0003;text-align:center}}.call{{background:#1688d4;color:#fff}}.estimate{{background:#ffd02c;color:#111}}@media(max-width:700px){{.post{{padding:25px 20px}}h1{{font-size:29px}}.two{{grid-template-columns:1fr}}.two img{{height:280px}}form{{grid-template-columns:1fr}}textarea{{grid-column:auto}}}}</style></head><body><header><div class="w nav"><div class="logo">체인지클린</div><div class="phone">☎ 1688-6751</div></div></header><main class="w"><article class="post"><div class="cat">체인지클린 청소일지</div><h1>{title}</h1><div class="date">{day}</div><p>{opening}</p><p>{mid1}</p><img class="photo" src="{im[0]}" alt="{dong} {service} 청소 현장" loading="lazy"><p>{mid2}</p><div class="two"><img src="{im[1]}" alt="{dong} 청소 현장" loading="lazy"><img src="{im[2]}" alt="{dong} 청소 작업" loading="lazy"></div><div class="note">입주·이사청소는 같은 평수라도 창 개수와 수납공간, 오염 상태에 따라 현장에서 손이 가는 부분이 달라질 수 있습니다.</div><h2>마지막으로 전체를 다시 확인했습니다</h2><p>{end}</p><div class="two"><img src="{im[3]}" alt="{dong} 청소 마무리" loading="lazy"><img src="{im[4]}" alt="{dong} 청소 완료" loading="lazy"></div><div class="near"><b>{sigungu} 주변 청소</b><br>{near_html}</div><section class="quote" id="quote"><h2>간편견적 문의</h2><p>지역 · 평수 · 청소 종류 · 희망 날짜를 남겨주세요.</p><form action="https://formspree.io/f/mvzlylrr" method="POST"><input name="name" placeholder="성함" required><input name="phone" placeholder="연락처" required><input name="area" placeholder="지역 / 평수"><input name="service" placeholder="입주청소 / 이사청소 등"><textarea name="message" placeholder="희망 날짜 또는 요청사항"></textarea><button class="btn" type="submit">간편견적 보내기</button></form></section></article></main><div class="floating"><a class="float call" href="tel:16886751">☎ 전화상담</a><a class="float estimate" href="#quote">⚡ 간편견적</a></div></body></html>'''

def main():
    rows, files = load_regions(), assets()
    if len(files) < 5: raise SystemExit('assets/site_*.webp 이미지가 5장 이상 필요합니다.')
    day = datetime.now().strftime('%Y-%m-%d')
    daykey = datetime.now().strftime('%Y%m%d')
    made = 0
    skipped = 0
    for i in range(COUNT):
        row = rows[i % len(rows)]
        service = SERVICES[(i // len(rows) + i) % len(SERVICES)]
        seed = int(hashlib.md5(f'{daykey}-{i}-{row["동"]}-{service}'.encode()).hexdigest()[:8],16)
        imgs = pick_images(seed, files)
        slug = f'{daykey}-{i+1:02d}-{slugify(row["동"])}-{slugify(service)}'
        if slug.endswith('-'): slug += hashlib.md5(f'{row["동"]}{service}'.encode()).hexdigest()[:8]
        dest = OUT / slug
        # 같은 날 재실행해도 같은 50개를 덮어쓰거나 중복 생성하지 않는다.
        if (dest / 'index.html').exists():
            skipped += 1
            continue
        dest.mkdir(parents=True, exist_ok=True)
        (dest/'index.html').write_text(page(row,service,imgs,day,i),encoding='utf-8')
        made += 1
    print(f'[OK] 신규 {made}개 생성 / 기존 {skipped}개 건너뜀: {OUT}')

if __name__ == '__main__': main()
