from pathlib import Path
import urllib.request, json, csv, re, shutil, random, html

ROOT=Path(__file__).parent
OUT=ROOT/"generated_site"
ASSETS=ROOT/"assets"
TEMPLATE=(ROOT/"template.html").read_text(encoding="utf-8")
DATA_URL="https://raw.githubusercontent.com/vuski/admdongkor/master/ver20260701/HangJeongDong_ver20260701.geojson"
DATA_FILE=ROOT/"HangJeongDong_ver20260701.geojson"
REGIONS_FILE=ROOT/"regions_서울인천경기_전체동.csv"
INTENTS=[("입주청소","movein-cleaning"),("이사청소","moving-cleaning"),("청소업체","cleaning-company"),("입주청소 가격","movein-cleaning-price"),("아파트청소","apartment-cleaning"),("원룸청소","oneroom-cleaning"),("오피스텔청소","officetel-cleaning"),("거주청소","occupied-cleaning"),("사무실청소","office-cleaning"),("청소견적","cleaning-estimate")]

def safe_ascii(text): return "r-"+"-".join(format(ord(c),"x") for c in text if not c.isspace())
def fetch_regions():
    if not DATA_FILE.exists(): urllib.request.urlretrieve(DATA_URL,DATA_FILE)
    data=json.loads(DATA_FILE.read_text(encoding="utf-8")); rows=[]; seen=set()
    for ft in data.get("features",[]):
        name=(ft.get("properties",{}).get("adm_nm") or "").strip()
        if not (name.startswith("서울특별시 ") or name.startswith("인천광역시 ") or name.startswith("경기도 ")): continue
        parts=name.split()
        if len(parts)<3 or not parts[-1].endswith("동"): continue
        key=(parts[0]," ".join(parts[1:-1]),parts[-1])
        if key not in seen: seen.add(key); rows.append(key)
    rows.sort()
    with open(REGIONS_FILE,"w",newline="",encoding="utf-8-sig") as f:
        w=csv.writer(f); w.writerow(["시도","시군구","동"]); w.writerows(rows)
    return rows

def build_neighbors(rows):
    d={}
    for s,g,x in rows: d.setdefault((s,g),[]).append(x)
    return d

def replace_first(pattern,repl,text): return re.sub(pattern,repl,text,count=1,flags=re.S)
def region_url(sido,gugun,dong,intent_slug="movein-cleaning"):
    return f'/{safe_ascii(f"{sido} {gugun} {dong}")}/{intent_slug}/'

def service_links(sido,gugun,dong):
    desc={"입주청소":"입주 전 전체 청소","이사청소":"이사 전후 청소","청소업체":"지역 청소업체 정보","입주청소 가격":"청소비용 안내","아파트청소":"아파트 청소 정보","원룸청소":"원룸 청소 정보","오피스텔청소":"오피스텔 청소","거주청소":"거주중 청소","사무실청소":"사무공간 청소","청소견적":"견적문의 안내"}
    return ''.join(f'<a href="{region_url(sido,gugun,dong,slug)}"><b>{html.escape(dong)} {html.escape(label)}</b>{desc[label]}</a>' for label,slug in INTENTS)

def short_sido(sido):
    return {"서울특별시":"서울","인천광역시":"인천","경기도":"경기"}.get(sido,sido)

def local_dongs(dong,nearby,n=5):
    ds=[dong]+[x for x in nearby if x!=dong]
    if not ds: ds=[dong]
    while len(ds)<n: ds+=ds
    return ds[:n]

def live_rows(sido,dong,nearby):
    ds=local_dongs(dong,nearby,5)
    names=["최*석","김*영","박*민","이*희","정*훈"]
    jobs=["입주청소 · 34평","이사청소 · 25평","입주청소 · 32평","거주청소 · 41평","이사청소 · 28평"]
    times=["3분 전","8분 전","14분 전","21분 전","27분 전"]
    city=short_sido(sido)
    return ''.join(f'<div class="row"><b>{names[i]}</b><span>{html.escape(city)} {html.escape(ds[i])}</span><span>{jobs[i]}</span><span class="ago">{times[i]}</span></div>' for i in range(5))

def gallery_dongs(dong,nearby,n=8):
    # 현재 동 + 같은 시군구의 인근 동을 사진별로 분산한다.
    ds=[x for x in nearby if x!=dong]
    if dong not in ds: ds.append(dong)
    if not ds: ds=[dong]
    while len(ds)<n: ds+=ds
    return ds[:n]

def replace_gallery_images(t,chosen,gallery_names):
    m=re.search(r'(<section class="sec" id="works">)(.*?)(</section>)',t,flags=re.S)
    if not m: return t
    block=m.group(2)
    i=0
    def repl_img(mm):
        nonlocal i
        if i>=len(chosen): return mm.group(0)
        p=chosen[i]
        alt=html.escape(f"{gallery_names[i]} 청소 작업사진")
        i+=1
        return f'<img src="/assets/{p.name}" alt="{alt}" loading="lazy">'
    block=re.sub(r'<img\b[^>]*>',repl_img,block,count=min(8,len(chosen)),flags=re.I)
    return t[:m.start()]+m.group(1)+block+m.group(3)+t[m.end():]

def make_page(sido,gugun,dong,intent,intent_slug,nearby,imgs):
    t=TEMPLATE; full=f"{sido} {gugun} {dong}"
    t=t.replace("인천 부평구",f"{sido} {gugun}").replace("부평구",gugun).replace("부평동",dong)
    t=replace_first(r"<title>.*?</title>",f"<title>{html.escape(dong)} {html.escape(intent)} | {html.escape(gugun)} 체인지클린</title>",t)
    t=replace_first(r'<meta name="description" content=".*?">',f'<meta name="description" content="{html.escape(full)} {html.escape(intent)} 체인지클린. 청소 현장, 청소범위, 평당 11,000원, 빠른 견적문의.">',t)
    t=replace_first(r"<h1>.*?</h1>",f"<h1>{html.escape(dong)} {html.escape(intent)}<br>지역 전문 청소 서비스</h1>",t)

    hero_ds=local_dongs(dong,nearby,5)
    hero_regions='·'.join(html.escape(x) for x in hero_ds)
    t=re.sub(r'<p class="lead">.*?</p>',f'<p class="lead">{hero_regions} 등 지역별 청소 정보를 확인하고 청소 현장과 청소 범위를 살펴본 뒤 간편하게 견적을 문의할 수 있습니다.</p>',t,count=1,flags=re.S)
    t=replace_first(r'<div class="roller" id="roller">.*?</div></div></div></section>', '<div class="roller" id="roller">'+live_rows(sido,dong,nearby)+'</div></div></div></section>', t)

    area_dongs=[dong]+[x for x in nearby if x!=dong][:7]
    area_html=''.join(f'<a href="{region_url(sido,gugun,x)}">{html.escape(x)} 입주청소</a>' for x in area_dongs)
    t=replace_first(r'<div class="area">.*?</div>',f'<div class="area">{area_html}</div>',t)

    # 사진 내용(주방/욕실 등)을 추측하지 않고 같은 시군구의 인근 동 작업사진으로 표시한다.
    gnames=gallery_dongs(dong,nearby,8)
    cap_i=iter(range(8))
    def cap(m):
        i=next(cap_i)
        return f'<figcaption><b>{html.escape(gnames[i])} 청소 작업사진</b><span>{html.escape(gugun)} 인근지역 청소 현장</span></figcaption>'
    t=re.sub(r"<figcaption>.*?</figcaption>",cap,t,count=8,flags=re.S)

    if imgs:
        rnd=random.Random(full+"|"+intent)
        chosen=rnd.sample(imgs,min(8,len(imgs)))
        while len(chosen)<8: chosen+=chosen
        t=replace_gallery_images(t,chosen[:8],gnames)

    t=replace_first(r'<div class="links">.*?</div></div></section>', '<div class="links">'+service_links(sido,gugun,dong)+'</div></div></section>', t)
    t=re.sub(r'action="https://formspree\.io/f/[^"]+"','action="https://formspree.io/f/mvzlylrr"',t)
    return t

def make_home(rows):
    t=(ROOT/"index.html").read_text(encoding="utf-8")
    lookup={dong:(sido,gugun) for sido,gugun,dong in rows}
    preferred=["부평동","산곡동","청천동","갈산동","삼산동","부개동"]
    home_dongs=[x for x in preferred if x in lookup]
    if not home_dongs: home_dongs=[d for _,_,d in rows[:6]]
    area=''.join(f'<a href="{region_url(lookup[x][0],lookup[x][1],x)}">{html.escape(x)} 입주청소</a>' for x in home_dongs)
    t=replace_first(r'<div class="area">.*?</div>',f'<div class="area">{area}</div>',t)
    base_dong="부평동" if "부평동" in lookup else home_dongs[0]
    sido,gugun=lookup[base_dong]
    t=replace_first(r'<div class="links">.*?</div></div></section>', '<div class="links">'+service_links(sido,gugun,base_dong)+'</div></div></section>', t)
    return t

def validate_links():
    broken=[]
    for page in OUT.rglob("*.html"):
        text=page.read_text(encoding="utf-8",errors="ignore")
        for href in re.findall(r'href="(/[^"]+/)"',text):
            if href.startswith(("/assets/","//")): continue
            target=OUT/href.strip("/")/"index.html"
            if not target.exists(): broken.append((page.relative_to(OUT).as_posix(),href))
    return broken

def validate_gallery_images():
    bad=[]
    for page in OUT.rglob("*.html"):
        if page == OUT/"index.html": continue
        text=page.read_text(encoding="utf-8",errors="ignore")
        m=re.search(r'<section class="sec" id="works">(.*?)</section>',text,flags=re.S)
        if not m: continue
        srcs=re.findall(r'<img\b[^>]*src="([^"]+)"',m.group(1),flags=re.I)
        if len(srcs)!=8 or any(not x.startswith("/assets/") for x in srcs):
            bad.append((page.relative_to(OUT).as_posix(),srcs))
    return bad

def main():
    rows=fetch_regions(); by_gu=build_neighbors(rows)
    imgs=sorted([p for p in ASSETS.iterdir() if p.suffix.lower() in {".jpg",".jpeg",".png",".webp"}])
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True); shutil.copytree(ASSETS,OUT/"assets")
    count=0
    for sido,gugun,dong in rows:
        nearby=by_gu.get((sido,gugun),[]); key=safe_ascii(f"{sido} {gugun} {dong}")
        for intent,islug in INTENTS:
            d=OUT/key/islug; d.mkdir(parents=True,exist_ok=True)
            (d/"index.html").write_text(make_page(sido,gugun,dong,intent,islug,nearby,imgs),encoding="utf-8"); count+=1
    (OUT/"index.html").write_text(make_home(rows),encoding="utf-8")
    urls=[region_url(s,g,d,sl) for s,g,d in rows for _,sl in INTENTS]
    (OUT/"urls.txt").write_text("\n".join(urls),encoding="utf-8")
    broken=validate_links(); bad_images=validate_gallery_images()
    if broken:
        print(f"[오류] 내부링크 {len(broken):,}개가 실제 페이지와 연결되지 않습니다.")
        for page,href in broken[:20]: print(" -",page,"->",href)
        raise SystemExit(1)
    if bad_images:
        print(f"[오류] 갤러리 이미지 경로 이상 {len(bad_images):,}페이지")
        for page,srcs in bad_images[:20]: print(" -",page,srcs)
        raise SystemExit(1)
    print(f"[완료] {count:,}개 생성 / 내부링크 0개 오류 / 갤러리 이미지 경로 0개 오류")
if __name__=="__main__": main()
