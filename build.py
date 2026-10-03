#!/usr/bin/env python3
"""Farsçadan statik site üreticisi.

Kullanım:
    python3 build.py           # üretim: '_' ile başlayan içerikleri atlar
    python3 build.py --ornek   # test: '_ornek-*.md' örnek haberleri de dahil eder

Yalnızca Python standart kütüphanesi kullanılır. Çıktı: public/ (her derlemede silinip yeniden üretilir).
"""
import datetime as dt
import email.utils
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "content", "haberler")
STATIC_DIR = os.path.join(ROOT, "static")
PUBLIC_DIR = os.path.join(ROOT, "public")

CATEGORIES = [
    ("Güvenlik", "guvenlik"),
    ("Ekonomi", "ekonomi"),
    ("Diplomasi", "diplomasi"),
    ("İç Politika", "ic-politika"),
    ("Toplum", "toplum"),
    ("Türkiye", "turkiye"),
]
CAT_SLUG = dict(CATEGORIES)

MONTHS_TR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
             "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

FOOTER_NOTE = ("Bu haber Farsça kaynaktan yapay zekâ desteğiyle çevrilmiştir. "
               "Haberin sorumluluğu ilgili yayın organına aittir. "
               "Hata bildirimi için İletişim sayfasını kullanın.")

REQUIRED = ["baslik", "ozet", "tarih", "kategori", "kaynak_adi", "kaynak_url"]

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print("UYARI: " + msg, file=sys.stderr)


def esc(s):
    return html.escape(str(s or ""), quote=True)


def tr_date(d):
    return "%d %s %d" % (d.day, MONTHS_TR[d.month - 1], d.year)


# ---------------------------------------------------------------- markdown

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITAL_RE = re.compile(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])")


def is_external(url, base_url):
    if not re.match(r"^https?://", url, re.I):
        return False
    host = re.sub(r"^https?://", "", base_url, flags=re.I).split("/")[0].lower()
    url_host = re.sub(r"^https?://", "", url, flags=re.I).split("/")[0].lower()
    return url_host not in (host, "www." + host)


def safe_url(url):
    u = url.strip()
    if re.match(r"^(https?:|mailto:|#|/|\.)", u, re.I) or re.match(r"^[\w\-./]+$", u):
        return u
    return "#"


def emphasis(escaped):
    escaped = BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = ITAL_RE.sub(r"<em>\1</em>", escaped)
    return escaped


def inline(text, base_url):
    out = []
    pos = 0
    for m in LINK_RE.finditer(text):
        out.append(emphasis(esc(text[pos:m.start()])))
        label, url = m.group(1), safe_url(m.group(2))
        attrs = ' href="%s"' % esc(url)
        if is_external(url, base_url):
            attrs += ' rel="noopener" target="_blank"'
        out.append("<a%s>%s</a>" % (attrs, emphasis(esc(label))))
        pos = m.end()
    out.append(emphasis(esc(text[pos:])))
    return "".join(out)


def md_blocks(src, base_url):
    """Markdown alt kümesini HTML blok listesine çevirir: [(tür, html), ...]."""
    blocks = []
    para, quote, items, rows = [], [], [], []

    def flush():
        if para:
            blocks.append(("p", "<p>%s</p>" % inline(" ".join(para), base_url)))
            para.clear()
        if quote:
            inner, cur = [], []
            for q in quote + [""]:
                if q.strip():
                    cur.append(q.strip())
                elif cur:
                    inner.append("<p>%s</p>" % inline(" ".join(cur), base_url))
                    cur = []
            blocks.append(("quote", "<blockquote>%s</blockquote>" % "".join(inner)))
            quote.clear()
        if items:
            lis = "".join("<li>%s</li>" % inline(i, base_url) for i in items)
            blocks.append(("ul", "<ul>%s</ul>" % lis))
            items.clear()
        if rows:
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows
                     if not re.match(r"^\|?\s*:?-{3,}", r)]
            head, body = cells[0], cells[1:]
            th = "".join("<th>%s</th>" % inline(c, base_url) for c in head)
            trs = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c, base_url) for c in r)
                          for r in body)
            blocks.append(("table", '<div class="tablo"><table><thead><tr>%s</tr></thead>'
                                    '<tbody>%s</tbody></table></div>' % (th, trs)))
            rows.clear()

    for raw in src.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush()
            continue
        if s.startswith("### "):
            flush()
            blocks.append(("h", "<h3>%s</h3>" % inline(s[4:].strip(), base_url)))
        elif s.startswith("## "):
            flush()
            blocks.append(("h", "<h2>%s</h2>" % inline(s[3:].strip(), base_url)))
        elif s.startswith(">"):
            if para or items:
                flush()
            quote.append(s[1:].lstrip() if len(s) > 1 else "")
        elif s.startswith("|") and s.endswith("|"):
            if para or quote or items:
                flush()
            rows.append(s)
        elif s.startswith("- "):
            if para or quote or rows:
                flush()
            items.append(s[2:].strip())
        else:
            if quote or items or rows:
                flush()
            para.append(s)
    flush()
    return blocks


def md_to_html(src, base_url, ad_after_para=None, ad_comment=""):
    out, pcount = [], 0
    for kind, h in md_blocks(src, base_url):
        out.append(h)
        if kind == "p":
            pcount += 1
            if ad_after_para and pcount == ad_after_para:
                out.append(ad_comment)
    return "\n".join(out)


# ---------------------------------------------------------------- content

def parse_front_matter(text, fname):
    text = text.lstrip("﻿")
    if not text.startswith("---"):
        raise ValueError("%s: front matter ('---') bulunamadı" % fname)
    parts = re.split(r"^---[ \t]*$", text, maxsplit=2, flags=re.M)
    if len(parts) < 3:
        raise ValueError("%s: front matter kapanmamış" % fname)
    meta = {}
    for line in parts[1].split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        meta[k.strip()] = v
    return meta, parts[2].strip("\n")


def parse_ek_kaynaklar(val):
    out = []
    for chunk in (val or "").split(";;"):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "|" in chunk:
            name, url = chunk.rsplit("|", 1)
        else:
            name, url = chunk, ""
        name, url = name.strip(), url.strip()
        m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", name)
        ad, yon = (m.group(1), m.group(2)) if m else (name, "")
        out.append({"ad": ad, "yonelim": yon, "url": url})
    return out


def load_articles(include_samples):
    arts = []
    if not os.path.isdir(CONTENT_DIR):
        return arts
    for fname in sorted(os.listdir(CONTENT_DIR)):
        if not fname.endswith(".md"):
            continue
        if fname.startswith("_") and not include_samples:
            continue
        if fname.startswith(".") or fname.upper().startswith("README"):
            continue
        path = os.path.join(CONTENT_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                meta, body = parse_front_matter(f.read(), fname)
        except Exception as e:
            warn("%s atlandı: %s" % (fname, e))
            continue
        missing = [k for k in REQUIRED if not meta.get(k)]
        if missing:
            warn("%s atlandı: eksik alan(lar): %s" % (fname, ", ".join(missing)))
            continue
        if meta["kategori"] not in CAT_SLUG:
            warn("%s atlandı: geçersiz kategori '%s'" % (fname, meta["kategori"]))
            continue
        try:
            date = dt.datetime.fromisoformat(meta["tarih"])
        except ValueError:
            try:
                date = dt.datetime.strptime(meta["tarih"][:10], "%Y-%m-%d")
            except ValueError:
                warn("%s atlandı: tarih okunamadı '%s'" % (fname, meta["tarih"]))
                continue
        if date.tzinfo is None:
            date = date.replace(tzinfo=dt.timezone(dt.timedelta(hours=3)))
        stem = fname[:-3]
        slug = stem.lstrip("_")
        slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
        if len(meta["ozet"]) > 160:
            warn("%s: özet 160 karakteri aşıyor (%d)" % (fname, len(meta["ozet"])))
        gorsel = meta.get("gorsel", "").lstrip("/")
        if gorsel and not os.path.isfile(os.path.join(STATIC_DIR, gorsel)):
            warn("%s: görsel bulunamadı: static/%s (görselsiz yayımlanıyor)" % (fname, gorsel))
            gorsel = ""
        arts.append({
            "file": fname,
            "slug": slug,
            "meta": meta,
            "body": body,
            "date": date,
            "cat": meta["kategori"],
            "cat_slug": CAT_SLUG[meta["kategori"]],
            "gorsel": gorsel,
            "ek": parse_ek_kaynaklar(meta.get("ek_kaynaklar", "")),
            "tags": [t.strip() for t in meta.get("etiketler", "").split(",") if t.strip()],
        })
    seen = set()
    for a in arts:
        if a["slug"] in seen:
            warn("Yinelenen slug: %s (%s)" % (a["slug"], a["file"]))
        seen.add(a["slug"])
    arts.sort(key=lambda a: a["date"], reverse=True)
    return arts


# ---------------------------------------------------------------- layout

class Page:
    def __init__(self, path):
        # path: çıktı yolu public/ içinde, ör. "haber/x/index.html"
        self.path = path
        depth = path.count("/")
        self.p = "../" * depth  # kök dizine göreli önek

    def url(self, target):
        return self.p + target if target else (self.p or "./")


def adsense_active(cfg):
    """AdSense kimliği; `adsense_baslangic` (YYYY-MM-DD, İstanbul) gelmeden boş döner."""
    client = cfg.get("adsense_client", "").strip()
    start = cfg.get("adsense_baslangic", "").strip()
    if client and start:
        today = dt.datetime.now(dt.timezone(dt.timedelta(hours=3))).date().isoformat()
        if today < start:
            return ""
    return client


def image_size(rel):
    """static/ altındaki görselin (genişlik, yükseklik) değeri; Pillow yoksa None."""
    try:
        from PIL import Image
        with Image.open(os.path.join(STATIC_DIR, rel)) as im:
            return im.size
    except Exception:
        return None


def abs_url(cfg, rel):
    return cfg["base_url"].rstrip("/") + "/" + rel.lstrip("/")


def head(cfg, page, title, description, canonical_rel, og_type="website",
         image=None, extra="", seo_title=None):
    t0 = seo_title or title
    full_title = t0 if t0 == cfg["site_name"] else "%s — %s" % (t0, cfg["site_name"])
    canonical = abs_url(cfg, canonical_rel)
    ads = ""
    client = adsense_active(cfg)
    if client:
        if not client.startswith("ca-"):
            client = "ca-" + client
        ads = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/'
               'adsbygoogle.js?client=%s" crossorigin="anonymous"></script>\n' % esc(client))
    analytics = ""
    ga = cfg.get("analytics", "").strip()
    if ga:
        analytics = (
            '<script async src="https://www.googletagmanager.com/gtag/js?id=%s"></script>\n'
            '<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}'
            'gtag("js",new Date());gtag("config",%s);</script>\n' % (esc(ga), json.dumps(ga)))
    img_meta = ""
    if image:
        img_meta = ('<meta property="og:image" content="%s">\n'
                    '<meta name="twitter:image" content="%s">\n' % (esc(image), esc(image)))
    return """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
{rb}<link rel="canonical" href="{c}">
<meta property="og:site_name" content="{sn}">
<meta property="og:locale" content="tr_TR">
<meta property="og:type" content="{ot}">
<meta property="og:title" content="{ti}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{c}">
<meta name="twitter:card" content="{tc}">
{xs}
<meta name="twitter:title" content="{ti}">
<meta name="twitter:description" content="{d}">
{img}<meta name="color-scheme" content="light dark">
<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/rss+xml" title="{sn}" href="{p}feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&amp;display=swap">
<link rel="stylesheet" href="{p}css/site.css">
{ads}{an}{extra}</head>
<body>
<a class="skip" href="#icerik">İçeriğe geç</a>
""".format(t=esc(full_title), d=esc(description), c=esc(canonical), sn=esc(cfg["site_name"]),
           ot=og_type, ti=esc(title), tc="summary_large_image" if image else "summary",
           img=img_meta, p=page.p, ads=ads, an=analytics, extra=extra,
           xs=('<meta name="twitter:site" content="@%s">\n' % esc(cfg["x_hesap"])) if cfg.get("x_hesap") else "",
           rb="" if 'name="robots"' in extra else
              '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">\n')


def header(cfg, page, active=""):
    links = [("", "Ana sayfa", "home")]
    links += [("kategori/%s/" % s, n, s) for n, s in CATEGORIES]
    links += [("hakkimizda/", "Hakkımızda", "hakkimizda"), ("iletisim/", "İletişim", "iletisim")]
    nav = []
    for target, label, key in links:
        cur = ' aria-current="page"' if key == active else ""
        nav.append('<li><a href="%s"%s>%s</a></li>' % (page.url(target), cur, esc(label)))
    return """<header class="site-header">
  <div class="wrap header-inner">
    <a class="wordmark" href="{home}"><span class="wm-mark" aria-hidden="true">F</span><span class="wm-text">{sn}</span></a>
    <p class="tagline">{tag}</p>
  </div>
  <nav class="site-nav" aria-label="Ana menü"><ul class="wrap">{nav}</ul></nav>
</header>
<main id="icerik">
""".format(home=page.url(""), sn=esc(cfg["site_name"]), tag=esc(cfg.get("tagline", "")),
           nav="".join(nav))


def footer(cfg, page):
    return """</main>
<footer class="site-footer">
  <div class="wrap">
    <nav aria-label="Alt menü"><ul class="footer-links">
      <li><a href="{p}yayin-ilkeleri/">Yayın İlkeleri</a></li>
      <li><a href="{p}editor/">Editörlük</a></li>
      <li><a href="{p}gizlilik/">Gizlilik</a></li>
      <li><a href="{p}iletisim/">İletişim</a></li>
      <li><a href="{p}feed.xml">RSS</a></li>
      <li><a href="https://x.com/farscadancom" rel="noopener me" target="_blank">X (@farscadancom)</a></li>
    </ul></nav>
    <p class="ai-note">İçerikler yapay zekâ desteğiyle çevrilmekte ve insan editoryal denetimi altında yayımlanmaktadır.</p>
    <p class="copy">© 2026 {sn}</p>
  </div>
</footer>
<div class="cookie" id="cookie" role="region" aria-label="Çerez bildirimi" hidden>
  <p>Bu site, temel işlevler ve olası reklam/ölçüm hizmetleri için çerezler kullanabilir. Ayrıntılar için <a href="{p}gizlilik/">Gizlilik Politikası</a>.</p>
  <button type="button" id="cookie-ok">Anladım</button>
</div>
<script>
(function(){{var k="farscadan_cerez_ok",b=document.getElementById("cookie");
var seen=false;try{{seen=localStorage.getItem(k)==="1";}}catch(e){{}}
if(!seen&&b){{b.hidden=false;}}
var btn=document.getElementById("cookie-ok");
if(btn)btn.addEventListener("click",function(){{try{{localStorage.setItem(k,"1");}}catch(e){{}}b.hidden=true;}});}})();
</script>
</body>
</html>
""".format(p=page.p, sn=esc(cfg["site_name"]))


def write(rel, content):
    path = os.path.join(PUBLIC_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- components

def card(a, page, size="card"):
    m = a["meta"]
    href = page.url("haber/%s/" % a["slug"])
    if a["gorsel"]:
        img = ('<img src="%s" alt="%s" loading="lazy" decoding="async">'
               % (page.url(a["gorsel"]), esc(m.get("gorsel_alt", m["baslik"]))))
    else:
        img = '<div class="noimg" aria-hidden="true">F</div>'
    if size == "hero":
        return """<article class="hero">
  <a class="hero-media" href="{h}" tabindex="-1" aria-hidden="true">{img}</a>
  <div class="hero-body">
    <p class="kicker"><a href="{cu}">{cat}</a> · <span class="src">{src}</span></p>
    <h2 class="hero-title"><a href="{h}">{t}</a></h2>
    <p class="dek">{oz}</p>
    <p class="meta"><time datetime="{iso}">{d}</time></p>
  </div>
</article>""".format(h=href, img=img.replace(' loading="lazy"', ''), cu=page.url("kategori/%s/" % a["cat_slug"]),
                     cat=esc(a["cat"]), src=esc(m["kaynak_adi"]), t=esc(m["baslik"]),
                     oz=esc(m["ozet"]), iso=a["date"].isoformat(), d=tr_date(a["date"]))
    return """<article class="card">
  <a class="card-media" href="{h}" tabindex="-1" aria-hidden="true">{img}</a>
  <p class="kicker"><a href="{cu}">{cat}</a> · <span class="src">{src}</span></p>
  <h3 class="card-title"><a href="{h}">{t}</a></h3>
  <p class="card-dek">{oz}</p>
  <p class="meta"><time datetime="{iso}">{d}</time></p>
</article>""".format(h=href, img=img, cu=page.url("kategori/%s/" % a["cat_slug"]),
                     cat=esc(a["cat"]), src=esc(m["kaynak_adi"]), t=esc(m["baslik"]),
                     oz=esc(m["ozet"]), iso=a["date"].isoformat(), d=tr_date(a["date"]))


def chips(page, active=None):
    out = ['<li><a class="chip%s" href="%s">Tümü</a></li>'
           % (" is-active" if active is None else "", page.url(""))]
    for n, s in CATEGORIES:
        out.append('<li><a class="chip%s" href="%s">%s</a></li>'
                   % (" is-active" if active == s else "", page.url("kategori/%s/" % s), esc(n)))
    return '<nav aria-label="Kategoriler"><ul class="chips">%s</ul></nav>' % "".join(out)


def empty_state():
    return ('<p class="empty">Bu bölümde henüz haber yayımlanmadı. '
            'Yeni çeviriler eklendikçe burada görünecek.</p>')


# ---------------------------------------------------------------- pages

def build_index(cfg, arts):
    page = Page("index.html")
    body = ['<div class="wrap wide">', chips(page)]
    if arts:
        body.append(card(arts[0], page, "hero"))
        if len(arts) > 1:
            body.append('<h2 class="section-title">Son haberler</h2>')
            body.append('<div class="grid">%s</div>' % "".join(card(a, page) for a in arts[1:]))
    else:
        body.append(empty_state())
    body.append("</div>")
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "WebSite",
        "name": cfg["site_name"], "url": abs_url(cfg, ""), "inLanguage": "tr",
        "description": cfg["description"],
    }, ensure_ascii=False).replace("<", "\\u003c")
    extra = '<script type="application/ld+json">%s</script>\n' % jsonld
    img = abs_url(cfg, arts[0]["gorsel"]) if arts and arts[0]["gorsel"] else None
    write(page.path, head(cfg, page, cfg["site_name"], cfg["description"], "", image=img, extra=extra)
          + header(cfg, page, "home")
          + '<h1 class="sr-only">%s — %s</h1>\n' % (esc(cfg["site_name"]), esc(cfg.get("tagline", "")))
          + "\n".join(body) + footer(cfg, page))


def build_category(cfg, arts, name, slug):
    page = Page("kategori/%s/index.html" % slug)
    items = [a for a in arts if a["cat_slug"] == slug]
    body = ['<div class="wrap wide">', chips(page, slug),
            '<header class="page-head"><h1>%s</h1><p class="lead">%s kategorisindeki çeviri haberler.</p></header>'
            % (esc(name), esc(name))]
    if items:
        body.append('<div class="grid">%s</div>' % "".join(card(a, page) for a in items))
    else:
        body.append(empty_state())
    body.append("</div>")
    desc = "%s: İran Farsça basınından %s haberlerinin Türkçe çevirileri." % (cfg["site_name"], name)
    write(page.path, head(cfg, page, name, desc, "kategori/%s/" % slug)
          + header(cfg, page, slug) + "\n".join(body) + footer(cfg, page))


def related_for(a, arts, n=3):
    same = [x for x in arts if x is not a and x["cat_slug"] == a["cat_slug"]]
    other = [x for x in arts if x is not a and x["cat_slug"] != a["cat_slug"]]
    return (same + other)[:n]


def build_article(cfg, a, arts):
    page = Page("haber/%s/index.html" % a["slug"])
    m = a["meta"]
    base = cfg["base_url"]
    ad_mid = "<!-- AD_SLOT: article-inline (2. paragraftan sonra; adsense_client ayarlanınca manuel reklam birimi buraya eklenebilir) -->"
    body_html = md_to_html(a["body"], base, ad_after_para=2, ad_comment=ad_mid)

    fig = ""
    if a["gorsel"]:
        credit = esc(m.get("gorsel_kredi", ""))
        cu = m.get("gorsel_kredi_url", "")
        if cu:
            credit_html = ('Görsel: <a href="%s" rel="noopener" target="_blank">%s</a>'
                           % (esc(safe_url(cu)), credit or "Kaynak"))
        else:
            credit_html = "Görsel: %s" % credit if credit else ""
        if not m.get("gorsel_kredi"):
            warn("%s: gorsel_kredi eksik" % a["file"])
        sz = image_size(a["gorsel"])
        fig = """<figure class="lead-figure">
  <img src="{src}" alt="{alt}"{dims} decoding="async" fetchpriority="high">
  <figcaption>{cap}</figcaption>
</figure>""".format(src=page.url(a["gorsel"]), alt=esc(m.get("gorsel_alt") or m["baslik"]), cap=credit_html,
                    dims=(' width="%d" height="%d"' % sz) if sz else "")

    fa = m.get("kaynak_baslik_fa", "")
    yon = m.get("kaynak_yonelim", "")
    kaynak = """<aside class="source-box" aria-labelledby="kaynak-baslik">
  <h2 id="kaynak-baslik">Kaynak</h2>
  <p class="source-name"><strong>{ad}</strong>{yon}</p>
  {fa}
  <p><a href="{u}" rel="noopener" target="_blank">Özgün haberi oku (Farsça) →</a></p>
</aside>""".format(
        ad=esc(m["kaynak_adi"]),
        yon=(' <span class="label">%s</span>' % esc(yon)) if yon else "",
        fa=('<p class="fa-title" dir="rtl" lang="fa">%s</p>' % esc(fa)) if fa else "",
        u=esc(safe_url(m["kaynak_url"])))

    ek = ""
    if a["ek"]:
        lis = []
        for e in a["ek"]:
            name = esc(e["ad"])
            if e["url"]:
                name = '<a href="%s" rel="noopener" target="_blank">%s</a>' % (esc(safe_url(e["url"])), name)
            lab = (' <span class="label">%s</span>' % esc(e["yonelim"])) if e["yonelim"] else ""
            lis.append("<li>%s%s</li>" % (name, lab))
        ek = ('<section class="extra-sources"><h2>Olayı işleyen diğer kaynaklar</h2><ul>%s</ul></section>'
              % "".join(lis))

    tags = ""
    if a["tags"]:
        tags = '<ul class="tags" aria-label="Etiketler">%s</ul>' % "".join(
            "<li>%s</li>" % esc(t) for t in a["tags"])

    rel = related_for(a, arts)
    related = ""
    if rel:
        related = ('<section class="related" aria-labelledby="ilgili"><h2 id="ilgili" class="section-title">İlgili haberler</h2>'
                   '<div class="grid grid-3">%s</div></section>' % "".join(card(x, page) for x in rel))

    canonical_rel = "haber/%s/" % a["slug"]
    img_abs = abs_url(cfg, a["gorsel"]) if a["gorsel"] else None
    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": m["baslik"][:110],
        "description": m["ozet"],
        "datePublished": a["date"].isoformat(),
        "dateModified": a["date"].isoformat(),
        "inLanguage": "tr",
        "articleSection": a["cat"],
        "keywords": ", ".join(a["tags"]),
        "mainEntityOfPage": {"@type": "WebPage", "@id": abs_url(cfg, canonical_rel)},
        "author": {"@type": "Organization", "name": m.get("yazar") or "AI Agent"},
        "editor": {"@type": "Organization", "name": "Farsçadan Editörlüğü", "url": abs_url(cfg, "editor/")},
        "publisher": {"@type": "Organization", "name": cfg["site_name"],
                      "sameAs": ["https://x.com/%s" % cfg["x_hesap"]] if cfg.get("x_hesap") else [],
                      "logo": {"@type": "ImageObject", "url": abs_url(cfg, "img/logo.png")}},
        "isBasedOn": safe_url(m["kaynak_url"]),
    }
    if img_abs:
        ld["image"] = [img_abs]
    mod = a.get("modified") or a["date"]
    ld["dateModified"] = mod.isoformat()
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Ana sayfa", "item": abs_url(cfg, "")},
        {"@type": "ListItem", "position": 2, "name": a["cat"],
         "item": abs_url(cfg, "kategori/%s/" % a["cat_slug"])},
        {"@type": "ListItem", "position": 3, "name": m["baslik"], "item": abs_url(cfg, canonical_rel)}]}
    jsonld = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
    jsonbc = json.dumps(crumbs, ensure_ascii=False).replace("<", "\\u003c")
    tag_meta = "".join('<meta property="article:tag" content="%s">\n' % esc(t) for t in a["tags"])
    extra = ('<meta property="article:published_time" content="%s">\n'
             '<meta property="article:modified_time" content="%s">\n'
             '<meta property="article:section" content="%s">\n%s'
             '<script type="application/ld+json">%s</script>\n'
             '<script type="application/ld+json">%s</script>\n'
             % (a["date"].isoformat(), mod.isoformat(), esc(a["cat"]), tag_meta, jsonld, jsonbc))

    article = """<div class="wrap">
<article class="article">
  <header class="article-head">
    <p class="kicker"><a href="{cu}">{cat}</a></p>
    <h1 class="article-title">{t}</h1>
    <p class="dek">{oz}</p>
    <p class="byline">Yazan: <span class="author">{author}</span> · Editoryal denetim: <a href="{ed}">Farsçadan Editörlüğü</a> · <time datetime="{iso}">{d}</time> · Kaynak: {src}</p>
  </header>
  {fig}
  <div class="article-body">
{body}
  </div>
  {kaynak}
  {ek}
  {tags}
  <p class="disclaimer">{note_pre}<a href="{il}">İletişim</a>{note_post}</p>
  <!-- AD_SLOT: article-bottom (haber sonu reklam alanı; şimdilik boş) -->
</article>
<!-- AD_SLOT: sidebar (geniş ekran yan sütun reklam alanı; şimdilik boş) -->
</div>
<div class="wrap wide">{related}</div>
""".format(cu=page.url("kategori/%s/" % a["cat_slug"]), cat=esc(a["cat"]), t=esc(m["baslik"]),
           oz=esc(m["ozet"]), author=esc(m.get("yazar") or "AI Agent"), iso=a["date"].isoformat(),
           d=tr_date(a["date"]), src=esc(m["kaynak_adi"]), fig=fig, ed=page.url("editor/"), body=body_html, kaynak=kaynak,
           ek=ek, tags=tags,
           note_pre=esc(FOOTER_NOTE.split("İletişim sayfasını")[0]),
           il=page.url("iletisim/"),
           note_post=esc(" sayfasını" + FOOTER_NOTE.split("İletişim sayfasını")[1]),
           related=related)
    write(page.path, head(cfg, page, m["baslik"], m["ozet"], canonical_rel, og_type="article",
                          image=img_abs, extra=extra, seo_title=m.get("seo_baslik") or None)
          + header(cfg, page, a["cat_slug"]) + article + footer(cfg, page))


def static_page(cfg, rel_dir, title, description, inner, active=""):
    page = Page(rel_dir + "index.html")
    html_ = ('<div class="wrap"><article class="prose">\n<h1>%s</h1>\n%s\n</article></div>\n'
             % (esc(title), inner))
    write(page.path, head(cfg, page, title, description, rel_dir)
          + header(cfg, page, active) + html_ + footer(cfg, page))
    return page


def build_static_pages(cfg):
    sn = esc(cfg["site_name"])

    # Editörlük
    page = Page("editor/index.html")
    static_page(cfg, "editor/", "Editörlük",
                "%s haberleri nasıl denetlenir: editoryal süreç ve sorumluluk." % cfg["site_name"], """
<p class="lead">{sn} haberleri yapay zekâ ile çevrilir ve <strong>insan editoryal denetimi</strong> altında yayımlanır.</p>
<h2>Editör kimdir?</h2>
<p>{sn} Editörlüğü, Farsça mütercim-tercümanlık eğitimi almış ve daha önce haber sitesi genel yayın yönetmenliği yapmış bir editör tarafından yürütülür. Editör; kaynak seçimini, yayın ilkelerini, yönelim etiketlerini ve düzeltmeleri belirler.</p>
<h2>Denetim nasıl işler?</h2>
<ul>
<li><strong>Kurallar:</strong> Her haber, editörün belirlediği yazım ve yayın ilkelerine göre hazırlanır: kaynağa atıf, yönelim etiketi, çelişkili iddiaların “teyit edilmedi” olarak işaretlenmesi, görüş içermeme.</li>
<li><strong>Haftalık inceleme:</strong> Türkiye’yi doğrudan ilgilendiren ve hassas konulu haberler editör tarafından her hafta tek tek okunur ve onaylanır; gerekirse düzeltilir.</li>
<li><strong>Doğrulama:</strong> Türkiye’ye veya yaptırımlara ilişkin iddialar yayın öncesinde İngilizce birincil kaynaklarla karşılaştırılır.</li>
<li><strong>Düzeltmeler:</strong> Okur bildirimleri editör tarafından incelenir; anlamı değiştiren düzeltmeler haberin sonunda tarihli not olarak belirtilir.</li>
</ul>
<p>Hata bildirmek için <a href="{p}iletisim/">İletişim</a> sayfasındaki formu kullanabilirsiniz. Yayın ilkelerimiz: <a href="{p}yayin-ilkeleri/">Yayın İlkeleri</a>.</p>
""".format(sn=sn, p=page.p), "hakkimizda")

    # Hakkımızda
    page = Page("hakkimizda/index.html")
    static_page(cfg, "hakkimizda/", "Hakkımızda",
                "%s nedir, haberler nasıl seçilir ve çevrilir?" % cfg["site_name"], """
<p class="lead">{sn}, İran'ın Farsça basınında çıkan haberleri Türkçe okurlara aktaran, yapay zekâ destekli bir çeviri haber sitesidir.</p>
<h2>Ne yapıyoruz?</h2>
<p>İran'da ve İran dışında Farsça yayın yapan çok sayıda haber kuruluşunu düzenli olarak izliyoruz. Gündemi belirleyen haberleri seçiyor, Türkçeye özet-çeviri olarak aktarıyoruz. Amacımız, Türkçe okurların İran'daki tartışmayı doğrudan Farsça kaynaklardan izleyebilmesidir.</p>
<h2>Kaynaklar ve yönelim etiketleri</h2>
<p>Haberleri tek bir bakış açısından değil, yelpazenin farklı noktalarından seçiyoruz:</p>
<ul>
<li><strong>Devlet ve resmî</strong> yayın organları,</li>
<li><strong>muhafazakâr / sert çizgi</strong> yayınlar,</li>
<li><strong>reformcu</strong> gazeteler,</li>
<li><strong>ekonomi</strong> basını,</li>
<li>yurt dışındaki <strong>diaspora ve muhalif</strong> Farsça yayınlar.</li>
</ul>
<p>Her haberin altında kaynağın adı, <strong>yönelim etiketi</strong>, Farsça özgün başlığı ve özgün habere bağlantı yer alır. Böylece okur, haberi hangi çerçeveden okuduğunu bilir.</p>
<h2>Görüş yayımlamıyoruz</h2>
<p>{sn} köşe yazısı ya da yorum yayımlamaz. Haberlerde aktarılan iddia ve değerlendirmeler ilgili yayın organına aittir. Arka plan bilgisi verdiğimiz “Bağlam” bölümleri olgulara dayanır ve görüş içermez.</p>
<h2>Çeviriyi kim yapıyor?</h2>
<p>Çeviriler yapay zekâ ile yapılır; bu nedenle haberlerde imza olarak <strong>“AI Agent”</strong> yer alır. Süreç insan editoryal denetimi altında yürütülür: kaynak seçimi, yayın ilkeleri ve düzeltmeler editörün sorumluluğundadır. Ayrıntılar: <a href="{p}editor/">Editörlük</a>.</p>
<h2>Düzeltme politikası</h2>
<p>Çeviri ya da bilgi hatalarını ciddiye alıyoruz. Bir hata fark ederseniz <a href="{p}iletisim/">İletişim</a> sayfasındaki formdan “Hata bildirimi” konusunu seçerek bize yazın. Doğrulanan hatalar en kısa sürede düzeltilir; anlamı değiştiren düzeltmeler haberin sonunda not olarak belirtilir.</p>
<p>Ayrıntılı ilkelerimiz için <a href="{p}yayin-ilkeleri/">Yayın İlkeleri</a> sayfasına bakabilirsiniz.</p>
""".format(sn=sn, p=page.p), "hakkimizda")

    page = Page("yayin-ilkeleri/index.html")
    static_page(cfg, "yayin-ilkeleri/", "Yayın İlkeleri",
                "%s editoryal ilkeleri: tarafsızlık, yönelim etiketleri, doğrulanmamış iddialar, görsel lisansları ve düzeltmeler." % cfg["site_name"], """
<p class="lead">{sn}'ın haber seçimi, çevirisi ve yayımı aşağıdaki ilkelere göre yapılır.</p>
<h2>1. Tarafsızlık</h2>
<p>Haberleri olduğu gibi aktarırız; taraf tutmayız, görüş eklemeyiz. Farklı yönelimlerden kaynakları dengeli biçimde izleriz ve aynı olay farklı biçimlerde verildiğinde bu farkı “Farsça basında nasıl verildi” bölümünde gösteririz.</p>
<h2>2. Yönelim etiketleri</h2>
<p>Her haberde kaynağın yönelimi (ör. resmî, yarı resmî, muhafazakâr, reformcu, ekonomi, diaspora muhalif) etiketle belirtilir. Etiket, kaynağın genel yayın çizgisini tanımlar; haberin doğruluğu hakkında bir hüküm değildir.</p>
<h2>3. Doğrulanmamış iddialar</h2>
<p>Bağımsız olarak doğrulanamayan iddialar “iddia edildi”, “kaynağa göre” gibi ifadelerle açıkça işaretlenir. Kaynaklar arasında rakam ya da olay örgüsü farkı varsa bu belirtilir.</p>
<h2>4. Özet-çeviri</h2>
<p>Kaynak metnin tamamını yeniden yayımlamayız. Haberin özünü sadık bir özet-çeviriyle aktarır, her zaman özgün habere bağlantı veririz. Haberin sorumluluğu ilgili yayın organına aittir.</p>
<h2>5. Yapay zekâ ve insan denetimi</h2>
<p>Çeviriler yapay zekâ ile üretilir ve “AI Agent” imzasıyla yayımlanır. Kaynak seçimi, ilkeler ve düzeltmeler insan editoryal denetimi altındadır.</p>
<h2>6. Görseller</h2>
<p>Yalnızca özgür lisanslı görseller kullanılır (kamu malı, CC0, CC BY, CC BY-SA). Her görselin altında yazar, lisans ve kaynak bağlantısı bulunur. İran basınına ait fotoğraflar kullanılmaz.</p>
<h2>7. Düzeltmeler</h2>
<p>Hatalar <a href="{p}iletisim/">İletişim</a> sayfası üzerinden bildirilebilir. Doğrulanan hatalar düzeltilir; anlamı değiştiren düzeltmeler haberin sonunda not olarak gösterilir.</p>
""".format(sn=sn, p=page.p))

    # İletişim
    endpoint = cfg.get("form_endpoint", "").strip()
    if endpoint:
        form = """<form class="contact-form" action="https://formsubmit.co/{ep}" method="POST">
  <input type="hidden" name="_subject" value="Farsçadan iletişim">
  <input type="hidden" name="_captcha" value="true">
  <input type="hidden" name="_template" value="table">
  <input type="hidden" name="_next" value="{next}">
  <p class="hp" aria-hidden="true"><label>Bu alanı boş bırakın <input type="text" name="_honey" tabindex="-1" autocomplete="off"></label></p>
  <p><label for="f-ad">Ad</label><input id="f-ad" type="text" name="ad" required autocomplete="name"></p>
  <p><label for="f-eposta">E-posta</label><input id="f-eposta" type="email" name="e-posta" required autocomplete="email"></p>
  <p><label for="f-konu">Konu</label><select id="f-konu" name="konu" required>
    <option>Genel</option><option>Hata bildirimi</option><option>Reklam/İş birliği</option></select></p>
  <p><label for="f-mesaj">Mesaj</label><textarea id="f-mesaj" name="mesaj" rows="7" required></textarea></p>
  <p class="form-note">Gönderdiğiniz bilgiler yalnızca mesajınıza yanıt vermek için kullanılır. Ayrıntılar: <a href="{p}gizlilik/">Gizlilik</a>.</p>
  <p><button type="submit">Gönder</button></p>
</form>""".format(ep=esc(endpoint), next=esc(abs_url(cfg, "iletisim/tesekkurler/")), p="../")
    else:
        form = '<p class="notice">İletişim formu yakında aktif olacak.</p>'
    static_page(cfg, "iletisim/", "İletişim",
                "%s ile iletişim: genel sorular, hata bildirimi, reklam ve iş birliği." % cfg["site_name"], """
<p class="lead">Sorularınız, hata bildirimleriniz ve iş birliği önerileriniz için aşağıdaki formu kullanabilirsiniz.</p>
<p>Bir çeviride hata gördüyseniz konu olarak “Hata bildirimi”ni seçin ve haberin bağlantısını mesajınıza ekleyin.</p>
{form}
""".format(form=form), "iletisim")

    page = Page("iletisim/tesekkurler/index.html")
    static_page(cfg, "iletisim/tesekkurler/", "Teşekkürler",
                "Mesajınız alındı.", """
<p class="lead">Mesajınız bize ulaştı. İlginiz için teşekkür ederiz.</p>
<p>Hata bildirimleri öncelikle incelenir. <a href="{p}">Ana sayfaya dön</a></p>
""".format(p=page.p))

    page = Page("gizlilik/index.html")
    static_page(cfg, "gizlilik/", "Gizlilik Politikası",
                "%s gizlilik politikası ve KVKK kapsamında aydınlatma metni: çerezler, reklam, iletişim formu." % cfg["site_name"], """
<p class="meta">Son güncelleme: 3 Ekim 2026</p>
<p class="lead">Bu politika, {sn} (farscadan.com) web sitesini ziyaret ettiğinizde hangi verilerin işlendiğini, 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) kapsamında açıklar.</p>
<h2>1. Hesap sistemi yoktur</h2>
<p>{sn}'da üyelik, giriş ya da kullanıcı hesabı bulunmaz. Siteyi okumak için herhangi bir kişisel bilgi vermeniz gerekmez.</p>
<h2>2. Çerezler ve yerel depolama</h2>
<p>Çerezler, ziyaret ettiğiniz sitelerin tarayıcınıza kaydettiği küçük metin dosyalarıdır. Sitemiz kendi başına yalnızca çerez bildirimini kapattığınızı hatırlamak için tarayıcınızın yerel depolama alanını (localStorage) kullanır; bu bilgi cihazınızdan dışarı gönderilmez.</p>
<p>Yazı tipleri Google Fonts üzerinden yüklenir; bu sırada IP adresiniz teknik olarak Google'a iletilebilir.</p>
<h2>3. Üçüncü taraf reklam ve ölçüm hizmetleri</h2>
<p>Sitemizde ileride Google AdSense gibi üçüncü taraf reklam hizmetleri ve ziyaret istatistikleri için ölçüm araçları kullanılabilir. Bu durumda:</p>
<ul>
<li>Google dahil üçüncü taraf sağlayıcılar, kullanıcının bu web sitesine veya diğer web sitelerine yaptığı önceki ziyaretlere dayalı reklamlar yayınlamak için çerezler kullanır.</li>
<li>Google'ın reklam çerezlerini kullanması, Google'ın ve iş ortaklarının kullanıcılara bu siteye ve/veya internetteki diğer sitelere yaptıkları ziyaretlere dayalı reklamlar sunmasını sağlar.</li>
<li>Kişiselleştirilmiş reklamcılığı <a href="https://adssettings.google.com/" rel="noopener" target="_blank">Google Reklam Ayarları</a> sayfasından devre dışı bırakabilirsiniz. Üçüncü taraf sağlayıcıların kişiselleştirilmiş reklamcılık için kullandığı çerezleri <a href="https://www.aboutads.info/choices/" rel="noopener" target="_blank">www.aboutads.info</a> adresinden devre dışı bırakabilirsiniz.</li>
<li>Google'ın bu verileri nasıl kullandığı hakkında bilgi için: <a href="https://policies.google.com/technologies/ads" rel="noopener" target="_blank">https://policies.google.com/technologies/ads</a>.</li>
</ul>
<p>Tarayıcınızın ayarlarından çerezleri silebilir veya engelleyebilirsiniz; bu durumda bazı özellikler beklendiği gibi çalışmayabilir.</p>
<h2>4. İletişim formu</h2>
<p>İletişim formunu kullandığınızda adınız, e-posta adresiniz, seçtiğiniz konu ve mesajınız, form hizmeti sağlayıcısı <strong>FormSubmit</strong> (formsubmit.co) aracılığıyla bize e-posta olarak iletilir. Bu veriler yalnızca mesajınıza yanıt vermek ve hata bildirimlerini değerlendirmek amacıyla, açık rızanıza ve meşru menfaate dayanılarak işlenir; pazarlama amacıyla kullanılmaz ve üçüncü kişilere satılmaz. FormSubmit, hizmeti sağlamak için bu verileri kendi sunucularında işleyebilir; bu nedenle verileriniz yurt dışına aktarılabilir.</p>
<h2>5. Sunucu kayıtları</h2>
<p>Site statik olarak barındırılır. Barındırma hizmeti sağlayıcısı, güvenlik ve işletim amacıyla IP adresi, tarayıcı türü ve erişim zamanı gibi standart teknik kayıtları tutabilir.</p>
<h2>6. Saklama süresi</h2>
<p>İletişim formu yoluyla gelen mesajlar, talebin sonuçlandırılması için gereken süre boyunca ve yasal yükümlülüklerin gerektirdiği süre kadar saklanır.</p>
<h2>7. KVKK kapsamındaki haklarınız</h2>
<p>KVKK'nın 11. maddesi uyarınca kişisel verilerinizin işlenip işlenmediğini öğrenme, bilgi talep etme, düzeltilmesini veya silinmesini isteme, itiraz etme ve zarara uğramanız hâlinde giderilmesini talep etme haklarına sahipsiniz. Başvurularınızı <a href="{p}iletisim/">İletişim</a> sayfasındaki form üzerinden iletebilirsiniz.</p>
<h2>8. Değişiklikler</h2>
<p>Bu politika gerektiğinde güncellenebilir. Güncel sürüm her zaman bu sayfada yayımlanır.</p>
""".format(sn=sn, p=page.p))


def build_404(cfg):
    # 404 sayfası herhangi bir yoldan sunulabildiği için göreli bağlantı yerine base_url kullanılır.
    base = cfg["base_url"].rstrip("/") + "/"

    class AbsPage(Page):
        def __init__(self):
            self.path = "404.html"
            self.p = base

    page = AbsPage()
    inner = ('<div class="wrap"><article class="prose"><h1>Sayfa bulunamadı</h1>'
             '<p class="lead">Aradığınız sayfa taşınmış ya da kaldırılmış olabilir.</p>'
             '<p><a href="%s">Ana sayfaya dön</a></p></article></div>' % base)
    write("404.html", head(cfg, page, "Sayfa bulunamadı", cfg["description"], "404.html",
                           extra='<meta name="robots" content="noindex">\n')
          + header(cfg, page) + inner + footer(cfg, page))


def xml_esc(s):
    return html.escape(str(s), quote=True)


def build_feeds(cfg, arts):
    urls = [("", None), ("hakkimizda/", None), ("yayin-ilkeleri/", None), ("iletisim/", None),
            ("gizlilik/", None)]
    urls += [("kategori/%s/" % s, None) for _, s in CATEGORIES]
    urls += [("haber/%s/" % a["slug"], a["date"]) for a in arts]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for rel, d in urls:
        sm.append("  <url><loc>%s</loc>%s</url>" % (
            xml_esc(abs_url(cfg, rel)),
            "<lastmod>%s</lastmod>" % d.date().isoformat() if d else ""))
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")

    # Google News site haritası: son 48 saatteki haberler
    limit = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=48)
    ns = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
    for a in [x for x in arts if x["date"] >= limit][:1000]:
        ns.append("  <url><loc>%s</loc><news:news><news:publication><news:name>%s</news:name>"
                  "<news:language>tr</news:language></news:publication>"
                  "<news:publication_date>%s</news:publication_date><news:title>%s</news:title>"
                  "</news:news></url>" % (xml_esc(abs_url(cfg, "haber/%s/" % a["slug"])),
                                          xml_esc(cfg["site_name"]), a["date"].isoformat(),
                                          xml_esc(a["meta"]["baslik"])))
    ns.append("</urlset>")
    write("news-sitemap.xml", "\n".join(ns) + "\n")

    write("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s\nSitemap: %s\n"
          % (abs_url(cfg, "sitemap.xml"), abs_url(cfg, "news-sitemap.xml")))

    now = arts[0]["date"] if arts else dt.datetime.now(dt.timezone.utc)
    items = []
    for a in arts[:20]:
        m = a["meta"]
        link = abs_url(cfg, "haber/%s/" % a["slug"])
        items.append("""  <item>
    <title>{t}</title>
    <link>{l}</link>
    <guid isPermaLink="true">{l}</guid>
    <pubDate>{d}</pubDate>
    <category>{c}</category>
    <dc:creator>{au}</dc:creator>
    <description>{o}</description>
  </item>""".format(t=xml_esc(m["baslik"]), l=xml_esc(link), d=email.utils.format_datetime(a["date"]),
                    c=xml_esc(a["cat"]), au=xml_esc(m.get("yazar") or "AI Agent"),
                    o=xml_esc("%s (Kaynak: %s)" % (m["ozet"], m["kaynak_adi"]))))
    feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>{sn}</title>
  <link>{home}</link>
  <description>{d}</description>
  <language>tr</language>
  <lastBuildDate>{lb}</lastBuildDate>
  <atom:link href="{self}" rel="self" type="application/rss+xml"/>
{items}
</channel>
</rss>
""".format(sn=xml_esc(cfg["site_name"]), home=xml_esc(abs_url(cfg, "")), d=xml_esc(cfg["description"]),
           lb=email.utils.format_datetime(now), self=xml_esc(abs_url(cfg, "feed.xml")),
           items="\n".join(items))
    write("feed.xml", feed)


def copy_static(include_samples):
    def ignore(d, names):
        return [n for n in names if n.startswith(".") or (n.startswith("_") and not include_samples)]
    shutil.copytree(STATIC_DIR, PUBLIC_DIR, ignore=ignore, dirs_exist_ok=True)


def main():
    include_samples = "--ornek" in sys.argv[1:]
    with open(os.path.join(ROOT, "site.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    for k, v in (("site_name", "Farsçadan"), ("base_url", "https://farscadan.com"),
                 ("description", ""), ("tagline", "")):
        cfg.setdefault(k, v)

    if os.path.isdir(PUBLIC_DIR):
        shutil.rmtree(PUBLIC_DIR)
    os.makedirs(PUBLIC_DIR)
    copy_static(include_samples)

    arts = load_articles(include_samples)
    build_index(cfg, arts)
    for name, slug in CATEGORIES:
        build_category(cfg, arts, name, slug)
    for a in arts:
        build_article(cfg, a, arts)
    build_static_pages(cfg)
    build_404(cfg)
    build_feeds(cfg, arts)

    write(".nojekyll", "")
    client = adsense_active(cfg)
    if client:
        pub = client[3:] if client.startswith("ca-") else client
        write("ads.txt", "google.com, %s, DIRECT, f08c47fec0942fa0\n" % pub)

    print("Derleme tamam: %d haber, %d uyarı%s → %s" % (
        len(arts), len(WARNINGS), " (örnekler dahil)" if include_samples else "", PUBLIC_DIR))


if __name__ == "__main__":
    main()
