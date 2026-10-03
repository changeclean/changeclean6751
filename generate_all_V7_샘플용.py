from pathlib import Path
import csv,re,shutil,random,html

ROOT=Path(__file__).parent
TEMPLATE=(ROOT/"template.html").read_text(encoding="utf-8")
OUT=ROOT/"generated_site"
ASSETS=ROOT/"assets"
OUT.mkdir(exist_ok=True)

INTENTS=[
("입주청소","movein-cleaning"),("이사청소","moving-cleaning"),
("청소업체","cleaning-company"),("입주청소 가격","movein-cleaning-price"),
("아파트청소","apartment-cleaning"),("원룸청소","oneroom-cleaning"),
("오피스텔청소","officetel-cleaning"),("거주청소","occupied-cleaning"),
("사무실청소","office-cleaning"),("청소견적","cleaning-estimate")
]

def slug(x):
    # URL은 영문 의도 + 안정적인 지역코드 형태. 한글 지역명은 본문/H1/title에 유지.
    return re.sub(r'[^a-z0-9-]+','-',x.lower()).strip('-')

def region_code(sido,gugun,dong):
    # 한글 URL 문제를 피하기 위해 유니코드 코드포인트 기반 안정적 ASCII 키
    raw=f"{sido}-{gugun}-{dong}"
    return "r-"+"-".join(format(ord(c),"x") for c in raw if c!=" ")

def make_page(sido,gugun,dong,intent,intent_slug,nearby):
    t=TEMPLATE
    full=f"{sido} {gugun} {dong}"
    # 기준 샘플의 지역/의도 텍스트 치환
    t=t.replace("인천 부평구",f"{sido} {gugun}")
    t=t.replace("부평구",gugun)
    t=t.replace("부평동",dong)
    t=t.replace("입주청소·이사청소",f"{intent}·청소")
    t=t.replace("입주·이사청소",intent)
    # title/meta/H1을 현재 검색의도 중심으로 보강
    t=re.sub(r'<title>.*?</title>',f'<title>{html.escape(full)} {html.escape(intent)} | 체인지클린</title>',t,count=1,flags=re.S)
    t=re.sub(r'<meta name="description" content=".*?">',f'<meta name="description" content="{html.escape(full)} {html.escape(intent)} 체인지클린. 청소 현장, 청소범위, 비용안내와 간편견적.">',t,count=1,flags=re.S)
    t=re.sub(r'<h1>.*?</h1>',f'<h1>{html.escape(dong)} {html.escape(intent)}<br>지역 전문 청소 서비스</h1>',t,count=1,flags=re.S)

    # 청소현장 캡션: 현재동 + 인근동 + 건물유형 로테이션
    buildings=["아파트","빌라","오피스텔","아파트","빌라","주택","오피스텔","아파트"]
    names=[dong]+nearby
    while len(names)<8: names+=names
    cap_iter=iter([(names[i],buildings[i]) for i in range(8)])
    def repl(m):
        nd,b=next(cap_iter)
        return f'<figcaption><b>{html.escape(nd)} {b} 청소</b><span>인근지역 {b} 청소 현장</span></figcaption>'
    t=re.sub(r'<figcaption>.*?</figcaption>',repl,t,flags=re.S)

    # 샘플용 죽은 지역 링크는 전체 생성 URL 체계로 교체
    links=[]
    for label,sl in INTENTS:
        href=f"/{region_code(sido,gugun,dong)}/{sl}/"
        links.append(f'<a href="{href}"><b>{html.escape(dong)} {html.escape(label)}</b>{html.escape(label)} 정보</a>')
    t=re.sub(r'<div class="links">.*?</div></div></section>',
             '<div class="links">'+"".join(links)+'</div></div></section>',t,count=1,flags=re.S)

    # 이미지 8장 페이지별 결정적 로테이션
    imgs=sorted([p for p in ASSETS.iterdir() if p.suffix.lower() in {".jpg",".jpeg",".png",".webp"}])
    if imgs:
        rnd=random.Random(full+intent)
        chosen=rnd.sample(imgs,min(8,len(imgs)))
        if len(chosen)<8: chosen=(chosen*8)[:8]
        for i,p in enumerate(chosen[:8],1):
            t=re.sub(r'src="assets/site_\d+\.(?:jpg|jpeg|png|webp)"',
                     f'src="/assets/{p.name}"',t,count=1,flags=re.I)
    return t

rows=[]
with open(ROOT/"regions.csv",encoding="utf-8-sig") as f:
    rows=list(csv.DictReader(f))

# 공용 assets
dst_assets=OUT/"assets"
if dst_assets.exists(): shutil.rmtree(dst_assets)
shutil.copytree(ASSETS,dst_assets)

count=0
for r in rows:
    sido,gugun,dong=r["시도"].strip(),r["시군구"].strip(),r["동"].strip()
    nearby=[x["동"].strip() for x in rows if x["시군구"].strip()==gugun and x["동"].strip()!=dong][:7]
    if not nearby: nearby=[dong]
    for intent,islug in INTENTS:
        d=OUT/region_code(sido,gugun,dong)/islug
        d.mkdir(parents=True,exist_ok=True)
        (d/"index.html").write_text(make_page(sido,gugun,dong,intent,islug,nearby),encoding="utf-8")
        count+=1

# 메인 인덱스
(ROOT/"generated_site"/"index.html").write_text(TEMPLATE,encoding="utf-8")
print(f"완료: {count:,}페이지 생성")
print("지역 수:",len(rows)," / 지역당 검색의도:",len(INTENTS))
print("출력:",ROOT/"generated_site")
