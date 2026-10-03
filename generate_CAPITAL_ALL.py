from pathlib import Path
import urllib.request, json, csv, re, shutil, random, html, sys, time

ROOT=Path(__file__).parent
OUT=ROOT/"generated_site"
ASSETS=ROOT/"assets"
TEMPLATE=(ROOT/"template.html").read_text(encoding="utf-8")

DATA_URL="https://raw.githubusercontent.com/vuski/admdongkor/master/ver20260701/HangJeongDong_ver20260701.geojson"
DATA_FILE=ROOT/"HangJeongDong_ver20260701.geojson"
REGIONS_FILE=ROOT/"regions_서울인천경기_전체동.csv"

INTENTS=[
("입주청소","movein-cleaning"),
("이사청소","moving-cleaning"),
("청소업체","cleaning-company"),
("입주청소 가격","movein-cleaning-price"),
("아파트청소","apartment-cleaning"),
("원룸청소","oneroom-cleaning"),
("오피스텔청소","officetel-cleaning"),
("거주청소","occupied-cleaning"),
("사무실청소","office-cleaning"),
("청소견적","cleaning-estimate"),
]

def safe_ascii(text):
    # 안정적인 영문/숫자 URL 키
    return "r-"+"-".join(format(ord(c),"x") for c in text if not c.isspace())

def fetch_regions():
    print("[1/4] 2026-07-01 최신 행정동 자료 확인중...")
    if not DATA_FILE.exists():
        print("      최초 1회 최신 행정동 파일 다운로드중...")
        urllib.request.urlretrieve(DATA_URL, DATA_FILE)
    data=json.loads(DATA_FILE.read_text(encoding="utf-8"))
    rows=[]
    seen=set()
    for ft in data.get("features",[]):
        prop=ft.get("properties",{})
        name=(prop.get("adm_nm") or "").strip()
        if not name:
            continue
        # 서울특별시 / 인천광역시 / 경기도만
        if not (name.startswith("서울특별시 ") or name.startswith("인천광역시 ") or name.startswith("경기도 ")):
            continue
        parts=name.split()
        if len(parts)<3:
            continue
        sido=parts[0]
        dong=parts[-1]
        # 사용자가 요청한 '동 단위'만: 읍/면 제외
        if not dong.endswith("동"):
            continue
        gugun=" ".join(parts[1:-1])
        key=(sido,gugun,dong)
        if key in seen: continue
        seen.add(key)
        rows.append(key)
    rows.sort()
    with open(REGIONS_FILE,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["시도","시군구","동"]); w.writerows(rows)
    return rows

def build_neighbors(rows):
    by_gu={}
    for sido,gugun,dong in rows:
        by_gu.setdefault((sido,gugun),[]).append(dong)
    return by_gu

def replace_first(pattern,repl,text):
    return re.sub(pattern,repl,text,count=1,flags=re.S)

def make_page(sido,gugun,dong,intent,intent_slug,nearby,imgs):
    t=TEMPLATE
    full=f"{sido} {gugun} {dong}"

    # 지역/검색의도
    t=t.replace("인천 부평구",f"{sido} {gugun}")
    t=t.replace("부평구",gugun)
    t=t.replace("부평동",dong)
    t=replace_first(r"<title>.*?</title>",
        f"<title>{html.escape(dong)} {html.escape(intent)} | {html.escape(gugun)} 체인지클린</title>",t)
    t=replace_first(r'<meta name="description" content=".*?">',
        f'<meta name="description" content="{html.escape(full)} {html.escape(intent)} 체인지클린. 청소 현장, 청소범위, 평당 11,000원, 빠른 견적문의.">',t)
    t=replace_first(r"<h1>.*?</h1>",
        f"<h1>{html.escape(dong)} {html.escape(intent)}<br>지역 전문 청소 서비스</h1>",t)

    # '청소 현장' 캡션: 현재동 + 같은 구 인근동 + 건물유형 로테이션
    buildings=["아파트","빌라","오피스텔","아파트","빌라","주택","오피스텔","아파트"]
    places=[dong]+[x for x in nearby if x!=dong]
    if not places: places=[dong]
    while len(places)<8: places += places
    caps=iter([(places[i],buildings[i]) for i in range(8)])
    def cap(m):
        nd,b=next(caps)
        return f'<figcaption><b>{html.escape(nd)} {b} 청소</b><span>{html.escape(gugun)} {b} 청소 현장</span></figcaption>'
    t=re.sub(r"<figcaption>.*?</figcaption>",cap,t,flags=re.S)

    # 검색의도 10종 실제 내부링크
    link_html=[]
    region_key=safe_ascii(full)
    for label,sl in INTENTS:
        link_html.append(
            f'<a href="/{region_key}/{sl}/"><b>{html.escape(dong)} {html.escape(label)}</b>{html.escape(label)} 정보</a>'
        )
    t=replace_first(r'<div class="links">.*?</div></div></section>',
                    '<div class="links">'+"".join(link_html)+'</div></div></section>',t)

    # 299장 이미지 풀에서 페이지별 8장 결정적 로테이션
    if imgs:
        rnd=random.Random(full+"|"+intent)
        chosen=rnd.sample(imgs,min(8,len(imgs)))
        while len(chosen)<8: chosen+=chosen
        # 기존 8개 이미지 src를 순서대로 교체
        for p in chosen[:8]:
            t=re.sub(r'src="(?:assets/|/assets/)[^"]+\.(?:jpg|jpeg|png|webp)"',
                     f'src="/assets/{p.name}"',t,count=1,flags=re.I)

    # Formspree 확정
    t=re.sub(r'action="https://formspree\.io/f/[^"]+"',
             'action="https://formspree.io/f/mvzlylrr"',t)
    return t

def main():
    rows=fetch_regions()
    print(f"      서울·인천·경기 동 단위: {len(rows):,}개")
    print(f"      예상 생성 페이지: {len(rows)*len(INTENTS):,}개")

    by_gu=build_neighbors(rows)
    imgs=sorted([p for p in ASSETS.iterdir()
                 if p.suffix.lower() in {".jpg",".jpeg",".png",".webp"}])
    print(f"[2/4] 청소 이미지 풀: {len(imgs):,}장")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(ASSETS,OUT/"assets")

    print("[3/4] 전체 페이지 생성중...")
    count=0
    for sido,gugun,dong in rows:
        nearby=by_gu.get((sido,gugun),[])
        key=safe_ascii(f"{sido} {gugun} {dong}")
        for intent,islug in INTENTS:
            d=OUT/key/islug
            d.mkdir(parents=True,exist_ok=True)
            (d/"index.html").write_text(
                make_page(sido,gugun,dong,intent,islug,nearby,imgs),
                encoding="utf-8"
            )
            count+=1
            if count%1000==0:
                print(f"      생성: {count:,} / {len(rows)*10:,}")

    # 홈
    shutil.copy2(ROOT/"index.html",OUT/"index.html")

    # sitemap
    urls=[]
    for sido,gugun,dong in rows:
        key=safe_ascii(f"{sido} {gugun} {dong}")
        for _,islug in INTENTS:
            urls.append(f"/{key}/{islug}/")
    (OUT/"urls.txt").write_text("\n".join(urls),encoding="utf-8")

    print("[4/4] 완료")
    print("="*55)
    print(f"지역(동): {len(rows):,}개")
    print(f"검색의도: 10종")
    print(f"총 페이지: {count:,}개")
    print(f"이미지 풀: {len(imgs):,}장")
    print("출력 폴더:",OUT)
    print("="*55)

if __name__=="__main__":
    main()
