#!/usr/bin/env python3
"""Farsçadan statik site üreticisi (Türkçe kök + İngilizce /en/).

Kullanım:
    python3 build.py           # üretim: '_' ile başlayan içerikleri atlar
    python3 build.py --ornek   # test: '_ornek-*.md' örnek haberleri de dahil eder

Python standart kütüphanesi kullanılır (Pillow varsa görsel boyutları için). Çıktı: public/
(her derlemede silinip yeniden üretilir).

Diller:
    tr  → kök dizin           content/haberler/*.md       → haber/<slug>/
    en  → en/ alt dizini      content/en/haberler/*.md    → en/haber/<slug>/
İki dildeki haberler aynı dosya adı (slug) ile eşleşir.
"""
import datetime as dt
import email.utils
import html
import json
import os
import re
import shutil
import sys
from urllib.parse import quote

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIRS = {
    "tr": os.path.join(ROOT, "content", "haberler"),
    "en": os.path.join(ROOT, "content", "en", "haberler"),
}
STATIC_DIR = os.path.join(ROOT, "static")
PUBLIC_DIR = os.path.join(ROOT, "public")

LANGS = ("tr", "en")
PFX = {"tr": "", "en": "en/"}  # dil kök öneki (public/ içinde)

CATEGORIES = [
    ("Güvenlik", "guvenlik"),
    ("Ekonomi", "ekonomi"),
    ("Diplomasi", "diplomasi"),
    ("İç Politika", "ic-politika"),
    ("Toplum", "toplum"),
    ("Türkiye", "turkiye"),
]
CAT_SLUG = dict(CATEGORIES)
CAT_EN = {"Güvenlik": "Security", "Ekonomi": "Economy", "Diplomasi": "Diplomacy",
          "İç Politika": "Domestic Politics", "Toplum": "Society", "Türkiye": "Turkey"}

MONTHS = {
    "tr": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
           "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}

# Statik sayfalar: anahtar → dil başına public/ içindeki yol
ROUTES = {
    "home": {"tr": "", "en": "en/"},
    "about": {"tr": "hakkimizda/", "en": "en/about/"},
    "standards": {"tr": "yayin-ilkeleri/", "en": "en/editorial-standards/"},
    "editor": {"tr": "editor/", "en": "en/editor/"},
    "contact": {"tr": "iletisim/", "en": "en/contact/"},
    "thanks": {"tr": "iletisim/tesekkurler/", "en": "en/contact/thanks/"},
    "privacy": {"tr": "gizlilik/", "en": "en/privacy/"},
    "topics": {"tr": "konular/", "en": "en/topics/"},
    "feed": {"tr": "feed.xml", "en": "en/feed.xml"},
}

# Arayüz metinleri (tek sözlük, dile göre)
T = {
    "tr": {
        "html_lang": "tr", "og_locale": "tr_TR", "skip": "İçeriğe geç",
        "home": "Ana sayfa", "about": "Hakkımızda", "contact": "İletişim",
        "standards": "Yayın İlkeleri", "editor": "Editörlük", "privacy": "Gizlilik",
        "topics": "Konular", "rss": "RSS",
        "nav_main": "Ana menü", "nav_footer": "Alt menü", "nav_lang": "Dil seçimi",
        "ai_note": "İçerikler yapay zekâ desteğiyle çevrilmekte ve insan editoryal denetimi altında yayımlanmaktadır.",
        "cookie_aria": "Çerez bildirimi",
        "cookie_text": "Bu site, temel işlevler ve olası reklam/ölçüm hizmetleri için çerezler kullanabilir. Ayrıntılar için ",
        "cookie_link": "Gizlilik Politikası", "cookie_ok": "Anladım",
        "all": "Tümü", "cats_aria": "Kategoriler",
        "empty": "Bu bölümde henüz haber yayımlanmadı. Yeni çeviriler eklendikçe burada görünecek.",
        "latest": "Son haberler",
        "cat_lead": "%s kategorisindeki çeviri haberler.",
        "cat_desc": "%s: İran Farsça basınından %s haberlerinin Türkçe çevirileri.",
        "by": "Yazan:", "oversight": "Editoryal denetim:", "editors": "Farsçadan Editörlüğü",
        "source_lbl": "Kaynak:", "source_h": "Kaynak", "image": "Görsel:", "image_src": "Kaynak",
        "read_orig": "Özgün haberi oku (Farsça) →",
        "extra_sources": "Olayı işleyen diğer kaynaklar",
        "tags_aria": "Etiketler", "related": "İlgili haberler",
        "note_pre": ("Bu haber Farsça kaynaktan yapay zekâ desteğiyle çevrilmiştir. "
                     "Haberin sorumluluğu ilgili yayın organına aittir. Hata bildirimi için "),
        "note_link": "İletişim", "note_post": " sayfasını kullanın.",
        "share": "Paylaş", "share_on": "%s ile paylaş", "copy": "Bağlantıyı kopyala", "copied": "Kopyalandı",
        "topic_lead": "“%s” konusundaki haberler (%d).",
        "topic_desc": "%s: “%s” konusundaki haberler. İran Farsça basınından Türkçe çeviriler.",
        "topics_lead": "Haberlerde geçen tüm konu etiketleri ve haber sayıları.",
        "topics_desc": "%s konu dizini: İran Farsça basınından çevrilen haberlerin etiketleri.",
        "src_note": "Kaynak",
    },
    "en": {
        "html_lang": "en", "og_locale": "en_US", "skip": "Skip to content",
        "home": "Home", "about": "About", "contact": "Contact",
        "standards": "Editorial Standards", "editor": "Editorial Oversight", "privacy": "Privacy",
        "topics": "Topics", "rss": "RSS",
        "nav_main": "Main menu", "nav_footer": "Footer menu", "nav_lang": "Language",
        "ai_note": "Stories are translated with AI assistance and published under human editorial oversight.",
        "cookie_aria": "Cookie notice",
        "cookie_text": "This site may use cookies for basic functionality and for possible advertising and analytics services. For details, see our ",
        "cookie_link": "Privacy Policy", "cookie_ok": "Got it",
        "all": "All", "cats_aria": "Categories",
        "empty": "No stories have been published in this section yet. New translations will appear here as they are added.",
        "latest": "Latest stories",
        "cat_lead": "Translated stories in %s.",
        "cat_desc": "%s: English translations of %s stories from Iran's Persian-language press.",
        "by": "By", "oversight": "Editorial oversight:", "editors": "Farsçadan Editors",
        "source_lbl": "Source:", "source_h": "Source", "image": "Image:", "image_src": "Source",
        "read_orig": "Read the original (Persian) →",
        "extra_sources": "Other outlets covering this story",
        "tags_aria": "Tags", "related": "Related stories",
        "note_pre": ("This article was translated from Persian-language sources with AI assistance "
                     "under human editorial oversight. Responsibility for the reporting lies with the "
                     "original outlet. To report an error, please use our "),
        "note_link": "Contact", "note_post": " page.",
        "share": "Share", "share_on": "Share on %s", "copy": "Copy link", "copied": "Copied",
        "topic_lead": "Stories about “%s” (%d).",
        "topic_desc": "%s: stories about “%s”, translated from Iran's Persian-language press.",
        "topics_lead": "Every topic tag used in our stories, with the number of stories.",
        "topics_desc": "%s topic index: tags for stories translated from Iran's Persian-language press.",
        "src_note": "Source",
    },
}
EN_TAGLINE = "Iran's Persian-language press, in English and Turkish"
EN_DESCRIPTION = ("AI-assisted English translations of selected stories from Iran's Persian-language "
                  "press. Every story notes the outlet's political orientation.")

REQUIRED = ["baslik", "ozet", "tarih", "kategori", "kaynak_adi", "kaynak_url"]

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print("UYARI: " + msg, file=sys.stderr)


def esc(s):
    return html.escape(str(s or ""), quote=True)


def fmt_date(d, lang):
    if lang == "en":
        return "%s %d, %d" % (MONTHS["en"][d.month - 1], d.day, d.year)
    return "%d %s %d" % (d.day, MONTHS["tr"][d.month - 1], d.year)


def tr_date(d):
    return fmt_date(d, "tr")


def cat_name(cat, lang):
    return CAT_EN.get(cat, cat) if lang == "en" else cat


def tagline(cfg, lang):
    return EN_TAGLINE if lang == "en" else cfg.get("tagline", "")


def description(cfg, lang):
    return EN_DESCRIPTION if lang == "en" else cfg["description"]


_SLUG_MAP = str.maketrans({"ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i", "İ": "i",
                           "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
                           "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u", "Û": "u"})


def slugify(s):
    s = s.translate(_SLUG_MAP).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


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
    para, quote_, items, rows = [], [], [], []

    def flush():
        if para:
            blocks.append(("p", "<p>%s</p>" % inline(" ".join(para), base_url)))
            para.clear()
        if quote_:
            inner, cur = [], []
            for q in quote_ + [""]:
                if q.strip():
                    cur.append(q.strip())
                elif cur:
                    inner.append("<p>%s</p>" % inline(" ".join(cur), base_url))
                    cur = []
            blocks.append(("quote", "<blockquote>%s</blockquote>" % "".join(inner)))
            quote_.clear()
        if items:
            lis = "".join("<li>%s</li>" % inline(i, base_url) for i in items)
            blocks.append(("ul", "<ul>%s</ul>" % lis))
            items.clear()
        if rows:
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows
                     if not re.match(r"^\|?\s*:?-{3,}", r)]
            head_, body = cells[0], cells[1:]
            th = "".join("<th>%s</th>" % inline(c, base_url) for c in head_)
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
            quote_.append(s[1:].lstrip() if len(s) > 1 else "")
        elif s.startswith("|") and s.endswith("|"):
            if para or quote_ or items:
                flush()
            rows.append(s)
        elif s.startswith("- "):
            if para or quote_ or rows:
                flush()
            items.append(s[2:].strip())
        else:
            if quote_ or items or rows:
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


def load_articles(include_samples, lang="tr"):
    arts = []
    cdir = CONTENT_DIRS[lang]
    label = "en/" if lang == "en" else ""
    if not os.path.isdir(cdir):
        return arts
    for fname in sorted(os.listdir(cdir)):
        if not fname.endswith(".md"):
            continue
        if fname.startswith("_") and not include_samples:
            continue
        if fname.startswith(".") or fname.upper().startswith("README"):
            continue
        shown = label + fname
        path = os.path.join(cdir, fname)
        try:
            with open(path, encoding="utf-8") as f:
                meta, body = parse_front_matter(f.read(), shown)
        except Exception as e:
            warn("%s atlandı: %s" % (shown, e))
            continue
        missing = [k for k in REQUIRED if not meta.get(k)]
        if missing:
            warn("%s atlandı: eksik alan(lar): %s" % (shown, ", ".join(missing)))
            continue
        if meta["kategori"] not in CAT_SLUG:
            warn("%s atlandı: geçersiz kategori '%s'" % (shown, meta["kategori"]))
            continue
        try:
            date = dt.datetime.fromisoformat(meta["tarih"])
        except ValueError:
            try:
                date = dt.datetime.strptime(meta["tarih"][:10], "%Y-%m-%d")
            except ValueError:
                warn("%s atlandı: tarih okunamadı '%s'" % (shown, meta["tarih"]))
                continue
        if date.tzinfo is None:
            date = date.replace(tzinfo=dt.timezone(dt.timedelta(hours=3)))
        stem = fname[:-3]
        slug = stem.lstrip("_")
        slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
        if len(meta["ozet"]) > 160:
            warn("%s: özet 160 karakteri aşıyor (%d)" % (shown, len(meta["ozet"])))
        gorsel = meta.get("gorsel", "").lstrip("/")
        if gorsel and not os.path.isfile(os.path.join(STATIC_DIR, gorsel)):
            warn("%s: görsel bulunamadı: static/%s (görselsiz yayımlanıyor)" % (shown, gorsel))
            gorsel = ""
        tags = []
        for t in meta.get("etiketler", "").split(","):
            t = t.strip()
            if t and slugify(t):
                tags.append(t)
        arts.append({
            "file": shown,
            "lang": lang,
            "slug": slug,
            "meta": meta,
            "body": body,
            "date": date,
            "cat": meta["kategori"],
            "cat_slug": CAT_SLUG[meta["kategori"]],
            "gorsel": gorsel,
            "ek": parse_ek_kaynaklar(meta.get("ek_kaynaklar", "")),
            "tags": tags,
        })
    seen = set()
    for a in arts:
        if a["slug"] in seen:
            warn("Yinelenen slug: %s (%s)" % (a["slug"], a["file"]))
        seen.add(a["slug"])
    arts.sort(key=lambda a: a["date"], reverse=True)
    return arts


def collect_topics(arts):
    """Etiket slug'ı → {'name', 'slug', 'arts'} (haberler yeniden eskiye)."""
    topics = {}
    for a in arts:  # arts zaten yeniden eskiye sıralı
        for t in a["tags"]:
            s = slugify(t)
            tp = topics.setdefault(s, {"name": t, "slug": s, "arts": []})
            if a not in tp["arts"]:
                tp["arts"].append(a)
    return topics


# ---------------------------------------------------------------- layout

class Page:
    def __init__(self, path, lang="tr"):
        # path: çıktı yolu public/ içinde, ör. "haber/x/index.html" veya "en/haber/x/index.html"
        self.path = path
        self.lang = lang
        depth = path.count("/")
        self.p = "../" * depth  # kök dizine göreli önek

    def url(self, target):
        """public/ köküne göre bir yola göreli bağlantı."""
        return self.p + target if target else (self.p or "./")

    def l(self, target):
        """Sayfanın dil köküne göre bir yola göreli bağlantı (ör. 'haber/x/')."""
        return self.url(PFX[self.lang] + target)

    def r(self, key, lang=None):
        """Statik sayfa anahtarına (ROUTES) göreli bağlantı."""
        return self.url(ROUTES[key][lang or self.lang])


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


def head(cfg, page, title, description_, canonical_rel, og_type="website",
         image=None, extra="", seo_title=None, alts=None):
    lang = page.lang
    t = T[lang]
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
    hreflang = ""
    if alts:
        hreflang = "".join('<link rel="alternate" hreflang="%s" href="%s">\n'
                           % (lg, esc(abs_url(cfg, alts[lg]))) for lg in LANGS)
        hreflang += ('<link rel="alternate" hreflang="x-default" href="%s">\n'
                     % esc(abs_url(cfg, alts["tr"])))
        other = [T[lg]["og_locale"] for lg in LANGS if lg != lang]
        hreflang += "".join('<meta property="og:locale:alternate" content="%s">\n' % o for o in other)
    return """<!doctype html>
<html lang="{hl}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
{rb}<link rel="canonical" href="{c}">
{hreflang}<meta property="og:site_name" content="{sn}">
<meta property="og:locale" content="{loc}">
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
<link rel="alternate" type="application/rss+xml" title="{sn}{fl}" href="{feed}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&amp;display=swap">
<link rel="stylesheet" href="{p}css/site.css">
{ads}{an}{extra}</head>
<body>
<a class="skip" href="#icerik">{skip}</a>
""".format(hl=t["html_lang"], t=esc(full_title), d=esc(description_), c=esc(canonical),
           sn=esc(cfg["site_name"]), loc=t["og_locale"], hreflang=hreflang,
           ot=og_type, ti=esc(title), tc="summary_large_image" if image else "summary",
           img=img_meta, p=page.p, ads=ads, an=analytics, extra=extra, skip=esc(t["skip"]),
           feed=page.r("feed"), fl=" (English)" if lang == "en" else "",
           xs=('<meta name="twitter:site" content="@%s">\n' % esc(cfg["x_hesap"])) if cfg.get("x_hesap") else "",
           rb="" if 'name="robots"' in extra else
              '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">\n')


def lang_switch(page, switch_rel):
    """Başlıktaki "TR | EN" seçici. switch_rel: diğer dildeki karşılık (public/ köküne göre)."""
    out = []
    for lg in LANGS:
        label = lg.upper()
        if lg == page.lang:
            out.append('<span class="ls-cur" lang="%s" aria-current="true">%s</span>' % (lg, label))
        else:
            name = "Türkçe" if lg == "tr" else "English"
            out.append('<a href="%s" hreflang="%s" lang="%s" title="%s">%s</a>'
                       % (page.url(switch_rel), lg, lg, name, label))
    return ('<nav class="lang-switch" aria-label="%s">%s</nav>'
            % (esc(T[page.lang]["nav_lang"]), '<span class="ls-sep" aria-hidden="true">|</span>'.join(out)))


def header(cfg, page, active="", switch_rel=None):
    t = T[page.lang]
    if switch_rel is None:
        switch_rel = ROUTES["home"]["en" if page.lang == "tr" else "tr"]
    links = [(page.r("home"), t["home"], "home")]
    links += [(page.l("kategori/%s/" % s), cat_name(n, page.lang), s) for n, s in CATEGORIES]
    links += [(page.r("about"), t["about"], "hakkimizda"), (page.r("contact"), t["contact"], "iletisim")]
    nav = []
    for href, label, key in links:
        cur = ' aria-current="page"' if key == active else ""
        nav.append('<li><a href="%s"%s>%s</a></li>' % (href, cur, esc(label)))
    return """<header class="site-header">
  <div class="wrap header-inner">
    <a class="wordmark" href="{home}"><span class="wm-mark" aria-hidden="true">F</span><span class="wm-text">{sn}</span></a>
    <div class="header-side">
      <p class="tagline">{tag}</p>
      {ls}
    </div>
  </div>
  <nav class="site-nav" aria-label="{navl}"><ul class="wrap">{nav}</ul></nav>
</header>
<main id="icerik">
""".format(home=page.r("home"), sn=esc(cfg["site_name"]), tag=esc(tagline(cfg, page.lang)),
           nav="".join(nav), navl=esc(t["nav_main"]), ls=lang_switch(page, switch_rel))


def footer(cfg, page):
    t = T[page.lang]
    return """</main>
<footer class="site-footer">
  <div class="wrap">
    <nav aria-label="{navf}"><ul class="footer-links">
      <li><a href="{st}">{st_l}</a></li>
      <li><a href="{ed}">{ed_l}</a></li>
      <li><a href="{tp}">{tp_l}</a></li>
      <li><a href="{pr}">{pr_l}</a></li>
      <li><a href="{co}">{co_l}</a></li>
      <li><a href="{feed}">RSS</a></li>
      <li><a href="https://x.com/farscadancom" rel="noopener me" target="_blank">X (@farscadancom)</a></li>
    </ul></nav>
    <p class="ai-note">{ai}</p>
    <p class="copy">© 2026 {sn}</p>
  </div>
</footer>
<div class="cookie" id="cookie" role="region" aria-label="{ca}" hidden>
  <p>{ct}<a href="{pr}">{cl}</a>.</p>
  <button type="button" id="cookie-ok">{ok}</button>
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
""".format(sn=esc(cfg["site_name"]), navf=esc(t["nav_footer"]),
           st=page.r("standards"), st_l=esc(t["standards"]),
           ed=page.r("editor"), ed_l=esc(t["editor"]),
           tp=page.r("topics"), tp_l=esc(t["topics"]),
           pr=page.r("privacy"), pr_l=esc(t["privacy"]),
           co=page.r("contact"), co_l=esc(t["contact"]),
           feed=page.r("feed"), ai=esc(t["ai_note"]),
           ca=esc(t["cookie_aria"]), ct=esc(t["cookie_text"]), cl=esc(t["cookie_link"]),
           ok=esc(t["cookie_ok"]))


def write(rel, content):
    path = os.path.join(PUBLIC_DIR, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def render(cfg, page, title, desc, canonical_rel, body, active="", switch_rel=None, alts=None, **kw):
    write(page.path, head(cfg, page, title, desc, canonical_rel, alts=alts, **kw)
          + header(cfg, page, active, switch_rel) + body + footer(cfg, page))


# ---------------------------------------------------------------- components

def card(a, page, size="card"):
    m = a["meta"]
    lang = page.lang
    href = page.l("haber/%s/" % a["slug"])
    if a["gorsel"]:
        img = ('<img src="%s" alt="%s" loading="lazy" decoding="async">'
               % (page.url(a["gorsel"]), esc(m.get("gorsel_alt", m["baslik"]))))
    else:
        img = '<div class="noimg" aria-hidden="true">F</div>'
    fields = dict(h=href, cu=page.l("kategori/%s/" % a["cat_slug"]),
                  cat=esc(cat_name(a["cat"], lang)), src=esc(m["kaynak_adi"]), t=esc(m["baslik"]),
                  oz=esc(m["ozet"]), iso=a["date"].isoformat(), d=fmt_date(a["date"], lang))
    if size == "hero":
        return """<article class="hero">
  <a class="hero-media" href="{h}" tabindex="-1" aria-hidden="true">{img}</a>
  <div class="hero-body">
    <p class="kicker"><a href="{cu}">{cat}</a> · <span class="src">{src}</span></p>
    <h2 class="hero-title"><a href="{h}">{t}</a></h2>
    <p class="dek">{oz}</p>
    <p class="meta"><time datetime="{iso}">{d}</time></p>
  </div>
</article>""".format(img=img.replace(' loading="lazy"', ''), **fields)
    return """<article class="card">
  <a class="card-media" href="{h}" tabindex="-1" aria-hidden="true">{img}</a>
  <p class="kicker"><a href="{cu}">{cat}</a> · <span class="src">{src}</span></p>
  <h3 class="card-title"><a href="{h}">{t}</a></h3>
  <p class="card-dek">{oz}</p>
  <p class="meta"><time datetime="{iso}">{d}</time></p>
</article>""".format(img=img, **fields)


def chips(page, active=None):
    t = T[page.lang]
    out = ['<li><a class="chip%s" href="%s">%s</a></li>'
           % (" is-active" if active is None else "", page.r("home"), esc(t["all"]))]
    for n, s in CATEGORIES:
        out.append('<li><a class="chip%s" href="%s">%s</a></li>'
                   % (" is-active" if active == s else "", page.l("kategori/%s/" % s),
                      esc(cat_name(n, page.lang))))
    return '<nav aria-label="%s"><ul class="chips">%s</ul></nav>' % (esc(t["cats_aria"]), "".join(out))


def empty_state(lang="tr"):
    return '<p class="empty">%s</p>' % esc(T[lang]["empty"])


SVG = {
    "whatsapp": ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">'
                 '<path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 1.8a8.2 8.2 0 1 1-4.3 15.2l-.3-.2-2.9.8.8-2.8-.2-.3A8.2 8.2 0 0 1 12 3.8z"/>'
                 '<path fill="currentColor" d="M9.1 7.2c-.2-.5-.4-.5-.6-.5h-.5c-.2 0-.5.1-.7.3-.3.3-.9.9-.9 2.2s1 2.6 1.1 2.7c.1.2 1.9 3 4.7 4.1 2.3.9 2.8.7 3.3.7.5-.1 1.6-.7 1.8-1.3.2-.6.2-1.2.2-1.3-.1-.1-.3-.2-.6-.3l-1.9-.9c-.3-.1-.5-.1-.7.1l-.9 1.1c-.2.2-.3.2-.6.1-.3-.1-1.2-.4-2.2-1.4-.8-.7-1.4-1.6-1.5-1.9-.2-.3 0-.4.1-.6l.4-.5.3-.5c.1-.2 0-.4 0-.5l-.8-2.1z"/></svg>'),
    "x": ('<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false">'
          '<path fill="currentColor" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>'),
    "telegram": ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">'
                 '<path fill="currentColor" d="M21.9 4.3l-3.2 15.1c-.2 1-.9 1.3-1.8.8l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.3-5 9.1-8.2c.4-.4-.1-.6-.6-.2L6.2 13l-4.8-1.5c-1-.3-1-1 .2-1.5L20.6 2.7c.9-.3 1.6.2 1.3 1.6z"/></svg>'),
    "link": ('<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false" fill="none" '
             'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.5 1.5"/>'
             '<path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.5-1.5"/></svg>'),
}

COPY_SCRIPT = """<script>
(function(){try{var bs=document.querySelectorAll(".share-copy");
function done(b){var s=b.querySelector(".share-txt");if(!s)return;var o=b.getAttribute("data-label");s.textContent=b.getAttribute("data-done");setTimeout(function(){s.textContent=o;},2000);}
function fb(t){var ok=false;try{var a=document.createElement("textarea");a.value=t;a.setAttribute("readonly","");a.style.position="absolute";a.style.left="-9999px";document.body.appendChild(a);a.select();ok=document.execCommand("copy");document.body.removeChild(a);}catch(e){}return ok;}
for(var i=0;i<bs.length;i++){bs[i].hidden=false;bs[i].addEventListener("click",function(){var b=this,u=b.getAttribute("data-url");try{if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(u).then(function(){done(b);},function(){if(fb(u))done(b);});}else if(fb(u)){done(b);}}catch(e){if(fb(u))done(b);}});}}catch(e){}})();
</script>
"""


def share_block(cfg, title, url, lang):
    t = T[lang]
    q = lambda s: quote(s, safe="")  # noqa: E731
    via = cfg.get("x_hesap", "").strip()
    links = [
        ("whatsapp", "WhatsApp", "https://wa.me/?text=%s%%20%s" % (q(title), q(url))),
        ("x", "X", "https://x.com/intent/post?text=%s&url=%s%s"
         % (q(title), q(url), ("&via=" + q(via)) if via else "")),
        ("telegram", "Telegram", "https://t.me/share/url?url=%s&text=%s" % (q(url), q(title))),
    ]
    out = ['<div class="share" role="group" aria-label="%s">' % esc(t["share"]),
           '<span class="share-label" aria-hidden="true">%s</span>' % esc(t["share"])]
    for key, name, href in links:
        out.append('<a class="share-btn share-%s" href="%s" rel="noopener" target="_blank" '
                   'aria-label="%s">%s<span class="share-txt">%s</span></a>'
                   % (key, esc(href), esc(t["share_on"] % name), SVG[key], esc(name)))
    out.append('<button type="button" class="share-btn share-copy" data-url="%s" data-label="%s" '
               'data-done="%s" hidden>%s<span class="share-txt" aria-live="polite">%s</span></button>'
               % (esc(url), esc(t["copy"]), esc(t["copied"]), SVG["link"], esc(t["copy"])))
    out.append("</div>")
    return "".join(out)


# ---------------------------------------------------------------- pages

def build_index(cfg, arts, lang):
    t = T[lang]
    page = Page(PFX[lang] + "index.html", lang)
    body = ['<div class="wrap wide">', chips(page)]
    if arts:
        body.append(card(arts[0], page, "hero"))
        if len(arts) > 1:
            body.append('<h2 class="section-title">%s</h2>' % esc(t["latest"]))
            body.append('<div class="grid">%s</div>' % "".join(card(a, page) for a in arts[1:]))
    else:
        body.append(empty_state(lang))
    body.append("</div>")
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "WebSite",
        "name": cfg["site_name"], "url": abs_url(cfg, ROUTES["home"][lang]), "inLanguage": lang,
        "description": description(cfg, lang),
    }, ensure_ascii=False).replace("<", "\\u003c")
    extra = '<script type="application/ld+json">%s</script>\n' % jsonld
    img = abs_url(cfg, arts[0]["gorsel"]) if arts and arts[0]["gorsel"] else None
    other = "en" if lang == "tr" else "tr"
    render(cfg, page, cfg["site_name"], description(cfg, lang), ROUTES["home"][lang],
           '<h1 class="sr-only">%s — %s</h1>\n' % (esc(cfg["site_name"]), esc(tagline(cfg, lang)))
           + "\n".join(body),
           active="home", switch_rel=ROUTES["home"][other], alts=ROUTES["home"],
           image=img, extra=extra)


def build_category(cfg, arts, name, slug, lang):
    t = T[lang]
    page = Page(PFX[lang] + "kategori/%s/index.html" % slug, lang)
    items = [a for a in arts if a["cat_slug"] == slug]
    disp = cat_name(name, lang)
    body = ['<div class="wrap wide">', chips(page, slug),
            '<header class="page-head"><h1>%s</h1><p class="lead">%s</p></header>'
            % (esc(disp), esc(t["cat_lead"] % disp))]
    if items:
        body.append('<div class="grid">%s</div>' % "".join(card(a, page) for a in items))
    else:
        body.append(empty_state(lang))
    body.append("</div>")
    desc = t["cat_desc"] % (cfg["site_name"], disp)
    alts = {lg: PFX[lg] + "kategori/%s/" % slug for lg in LANGS}
    other = "en" if lang == "tr" else "tr"
    render(cfg, page, disp, desc, alts[lang], "\n".join(body), active=slug,
           switch_rel=alts[other], alts=alts)


def related_for(a, arts, n=3):
    same = [x for x in arts if x is not a and x["cat_slug"] == a["cat_slug"]]
    other = [x for x in arts if x is not a and x["cat_slug"] != a["cat_slug"]]
    return (same + other)[:n]


REL_LINK_RE = re.compile(r"\]\(\.\./([a-z0-9-]+)/\)")


def fix_cross_links(body, own_slugs, other_slugs, lang):
    """Haber gövdesindeki '../<slug>/' bağlantısı bu dilde yoksa diğer dildeki habere yönlendirilir."""
    other_pfx = PFX["en" if lang == "tr" else "tr"]

    def sub(m):
        s = m.group(1)
        if s in own_slugs or s not in other_slugs:
            return m.group(0)
        return "](%s%shaber/%s/)" % ("../" * (2 + PFX[lang].count("/")), other_pfx, s)
    return REL_LINK_RE.sub(sub, body)


def build_article(cfg, a, arts, counterpart, topics_slug, other_slugs):
    lang = a["lang"]
    t = T[lang]
    other = "en" if lang == "tr" else "tr"
    page = Page(PFX[lang] + "haber/%s/index.html" % a["slug"], lang)
    m = a["meta"]
    base = cfg["base_url"]
    ad_mid = "<!-- AD_SLOT: article-inline (2. paragraftan sonra; adsense_client ayarlanınca manuel reklam birimi buraya eklenebilir) -->"
    own_slugs = {x["slug"] for x in arts}
    body_html = md_to_html(fix_cross_links(a["body"], own_slugs, other_slugs, lang), base,
                           ad_after_para=2, ad_comment=ad_mid)

    fig = ""
    if a["gorsel"]:
        credit = esc(m.get("gorsel_kredi", ""))
        cu = m.get("gorsel_kredi_url", "")
        if cu:
            credit_html = ('%s <a href="%s" rel="noopener" target="_blank">%s</a>'
                           % (esc(t["image"]), esc(safe_url(cu)), credit or esc(t["image_src"])))
        else:
            credit_html = "%s %s" % (esc(t["image"]), credit) if credit else ""
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
  <h2 id="kaynak-baslik">{h}</h2>
  <p class="source-name"><strong>{ad}</strong>{yon}</p>
  {fa}
  <p><a href="{u}" rel="noopener" target="_blank">{ro}</a></p>
</aside>""".format(
        h=esc(t["source_h"]), ro=esc(t["read_orig"]),
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
        ek = ('<section class="extra-sources"><h2>%s</h2><ul>%s</ul></section>'
              % (esc(t["extra_sources"]), "".join(lis)))

    tags = ""
    if a["tags"]:
        lis = []
        for tg in a["tags"]:
            s = slugify(tg)
            if s in topics_slug:
                lis.append('<li><a href="%s">%s</a></li>' % (page.l("konu/%s/" % s), esc(tg)))
            else:
                lis.append("<li>%s</li>" % esc(tg))
        tags = '<ul class="tags" aria-label="%s">%s</ul>' % (esc(t["tags_aria"]), "".join(lis))

    rel = related_for(a, arts)
    related = ""
    if rel:
        related = ('<section class="related" aria-labelledby="ilgili"><h2 id="ilgili" class="section-title">%s</h2>'
                   '<div class="grid grid-3">%s</div></section>' % (esc(t["related"]), "".join(card(x, page) for x in rel)))

    canonical_rel = PFX[lang] + "haber/%s/" % a["slug"]
    canonical_abs = abs_url(cfg, canonical_rel)
    img_abs = abs_url(cfg, a["gorsel"]) if a["gorsel"] else None
    disp_cat = cat_name(a["cat"], lang)
    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": m["baslik"][:110],
        "description": m["ozet"],
        "datePublished": a["date"].isoformat(),
        "dateModified": a["date"].isoformat(),
        "inLanguage": lang,
        "articleSection": disp_cat,
        "keywords": ", ".join(a["tags"]),
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_abs},
        "author": {"@type": "Organization", "name": m.get("yazar") or "AI Agent"},
        "editor": {"@type": "Organization", "name": t["editors"], "url": abs_url(cfg, ROUTES["editor"][lang])},
        "publisher": {"@type": "Organization", "name": cfg["site_name"],
                      "sameAs": ["https://x.com/%s" % cfg["x_hesap"]] if cfg.get("x_hesap") else [],
                      "logo": {"@type": "ImageObject", "url": abs_url(cfg, "img/logo.png")}},
        "isBasedOn": safe_url(m["kaynak_url"]),
    }
    if counterpart:
        ld["translationOfWork" if lang == "en" else "workTranslation"] = {
            "@type": "NewsArticle", "@id": abs_url(cfg, PFX[other] + "haber/%s/" % a["slug"]),
            "inLanguage": other}
    if img_abs:
        ld["image"] = [img_abs]
    mod = a.get("modified") or a["date"]
    ld["dateModified"] = mod.isoformat()
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": t["home"], "item": abs_url(cfg, ROUTES["home"][lang])},
        {"@type": "ListItem", "position": 2, "name": disp_cat,
         "item": abs_url(cfg, PFX[lang] + "kategori/%s/" % a["cat_slug"])},
        {"@type": "ListItem", "position": 3, "name": m["baslik"], "item": canonical_abs}]}
    jsonld = json.dumps(ld, ensure_ascii=False).replace("<", "\\u003c")
    jsonbc = json.dumps(crumbs, ensure_ascii=False).replace("<", "\\u003c")
    tag_meta = "".join('<meta property="article:tag" content="%s">\n' % esc(x) for x in a["tags"])
    extra = ('<meta property="article:published_time" content="%s">\n'
             '<meta property="article:modified_time" content="%s">\n'
             '<meta property="article:section" content="%s">\n%s'
             '<script type="application/ld+json">%s</script>\n'
             '<script type="application/ld+json">%s</script>\n'
             % (a["date"].isoformat(), mod.isoformat(), esc(disp_cat), tag_meta, jsonld, jsonbc))

    share = share_block(cfg, m["baslik"], canonical_abs, lang)
    article = """<div class="wrap">
<article class="article">
  <header class="article-head">
    <p class="kicker"><a href="{cu}">{cat}</a></p>
    <h1 class="article-title">{t}</h1>
    <p class="dek">{oz}</p>
    <p class="byline">{by} <span class="author">{author}</span> · {ov} <a href="{ed}">{eds}</a> · <time datetime="{iso}">{d}</time> · {sl} {src}</p>
  </header>
  {share}
  {fig}
  <div class="article-body">
{body}
  </div>
  {share}
  {kaynak}
  {ek}
  {tags}
  <p class="disclaimer">{note_pre}<a href="{il}">{nl}</a>{note_post}</p>
  <!-- AD_SLOT: article-bottom (haber sonu reklam alanı; şimdilik boş) -->
</article>
<!-- AD_SLOT: sidebar (geniş ekran yan sütun reklam alanı; şimdilik boş) -->
</div>
<div class="wrap wide">{related}</div>
{copy}""".format(cu=page.l("kategori/%s/" % a["cat_slug"]), cat=esc(disp_cat), t=esc(m["baslik"]),
                 oz=esc(m["ozet"]), author=esc(m.get("yazar") or "AI Agent"), iso=a["date"].isoformat(),
                 by=esc(t["by"]), ov=esc(t["oversight"]), eds=esc(t["editors"]), sl=esc(t["source_lbl"]),
                 d=fmt_date(a["date"], lang), src=esc(m["kaynak_adi"]), fig=fig, ed=page.r("editor"),
                 body=body_html, kaynak=kaynak, ek=ek, tags=tags, share=share,
                 note_pre=esc(t["note_pre"]), il=page.r("contact"), nl=esc(t["note_link"]),
                 note_post=esc(t["note_post"]), related=related, copy=COPY_SCRIPT)
    alts = None
    if counterpart:
        alts = {lg: PFX[lg] + "haber/%s/" % a["slug"] for lg in LANGS}
        switch_rel = alts[other]
    else:
        switch_rel = ROUTES["home"][other]
    render(cfg, page, m["baslik"], m["ozet"], canonical_rel, article, active=a["cat_slug"],
           switch_rel=switch_rel, alts=alts, og_type="article", image=img_abs, extra=extra,
           seo_title=m.get("seo_baslik") or None)


def build_topics(cfg, topics, lang):
    """konu/<slug>/ sayfaları + konular/ (en/topics/) dizini."""
    t = T[lang]
    other = "en" if lang == "tr" else "tr"
    for s, tp in topics.items():
        page = Page(PFX[lang] + "konu/%s/index.html" % s, lang)
        body = ('<div class="wrap wide"><header class="page-head"><p class="kicker"><a href="%s">%s</a></p>'
                '<h1>%s</h1><p class="lead">%s</p></header><div class="grid">%s</div></div>\n'
                % (page.r("topics"), esc(t["topics"]), esc(tp["name"]),
                   esc(t["topic_lead"] % (tp["name"], len(tp["arts"]))),
                   "".join(card(a, page) for a in tp["arts"])))
        render(cfg, page, tp["name"], t["topic_desc"] % (cfg["site_name"], tp["name"]),
               PFX[lang] + "konu/%s/" % s, body, switch_rel=ROUTES["topics"][other])
    page = Page(ROUTES["topics"][lang] + "index.html", lang)
    items = sorted(topics.values(), key=lambda x: x["slug"])
    lis = "".join('<li><a href="%s">%s <span class="count">%d</span></a></li>'
                  % (page.l("konu/%s/" % tp["slug"]), esc(tp["name"]), len(tp["arts"])) for tp in items)
    inner = ('<p class="lead">%s</p>\n<ul class="topic-list">%s</ul>' % (esc(t["topics_lead"]), lis)
             if items else empty_state(lang))
    static_page(cfg, lang, "topics", t["topics"], t["topics_desc"] % cfg["site_name"], inner)


def static_page(cfg, lang, key, title, desc, inner, active=""):
    page = Page(ROUTES[key][lang] + "index.html", lang)
    other = "en" if lang == "tr" else "tr"
    html_ = ('<div class="wrap"><article class="prose">\n<h1>%s</h1>\n%s\n</article></div>\n'
             % (esc(title), inner))
    render(cfg, page, title, desc, ROUTES[key][lang], html_, active=active,
           switch_rel=ROUTES[key][other], alts=ROUTES[key])
    return page


def contact_form(cfg, page, lang):
    endpoint = cfg.get("form_endpoint", "").strip()
    if not endpoint:
        return '<p class="notice">%s</p>' % (
            "İletişim formu yakında aktif olacak." if lang == "tr" else "The contact form will be available soon.")
    if lang == "tr":
        return """<form class="contact-form" action="https://formsubmit.co/{ep}" method="POST">
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
  <p class="form-note">Gönderdiğiniz bilgiler yalnızca mesajınıza yanıt vermek için kullanılır. Ayrıntılar: <a href="{priv}">Gizlilik</a>.</p>
  <p><button type="submit">Gönder</button></p>
</form>""".format(ep=esc(endpoint), next=esc(abs_url(cfg, ROUTES["thanks"]["tr"])), priv=page.r("privacy"))
    return """<form class="contact-form" action="https://formsubmit.co/{ep}" method="POST">
  <input type="hidden" name="_subject" value="Farsçadan contact (English)">
  <input type="hidden" name="_captcha" value="true">
  <input type="hidden" name="_template" value="table">
  <input type="hidden" name="_next" value="{next}">
  <p class="hp" aria-hidden="true"><label>Leave this field empty <input type="text" name="_honey" tabindex="-1" autocomplete="off"></label></p>
  <p><label for="f-ad">Name</label><input id="f-ad" type="text" name="name" required autocomplete="name"></p>
  <p><label for="f-eposta">Email</label><input id="f-eposta" type="email" name="email" required autocomplete="email"></p>
  <p><label for="f-konu">Subject</label><select id="f-konu" name="subject" required>
    <option>General</option><option>Error report</option><option>Advertising/Partnership</option></select></p>
  <p><label for="f-mesaj">Message</label><textarea id="f-mesaj" name="message" rows="7" required></textarea></p>
  <p class="form-note">The information you send is used only to reply to your message. Details: <a href="{priv}">Privacy</a>.</p>
  <p><button type="submit">Send</button></p>
</form>""".format(ep=esc(endpoint), next=esc(abs_url(cfg, ROUTES["thanks"]["en"])), priv=page.r("privacy"))


def build_static_pages_tr(cfg):
    sn = esc(cfg["site_name"])
    lang = "tr"
    page = Page(ROUTES["editor"][lang] + "index.html", lang)
    static_page(cfg, lang, "editor", "Editörlük",
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
<p>Hata bildirmek için <a href="{co}">İletişim</a> sayfasındaki formu kullanabilirsiniz. Yayın ilkelerimiz: <a href="{st}">Yayın İlkeleri</a>.</p>
""".format(sn=sn, co=page.r("contact"), st=page.r("standards")), "hakkimizda")

    page = Page(ROUTES["about"][lang] + "index.html", lang)
    static_page(cfg, lang, "about", "Hakkımızda",
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
<p>Çeviriler yapay zekâ ile yapılır; bu nedenle haberlerde imza olarak <strong>“AI Agent”</strong> yer alır. Süreç insan editoryal denetimi altında yürütülür: kaynak seçimi, yayın ilkeleri ve düzeltmeler editörün sorumluluğundadır. Ayrıntılar: <a href="{ed}">Editörlük</a>.</p>
<h2>Düzeltme politikası</h2>
<p>Çeviri ya da bilgi hatalarını ciddiye alıyoruz. Bir hata fark ederseniz <a href="{co}">İletişim</a> sayfasındaki formdan “Hata bildirimi” konusunu seçerek bize yazın. Doğrulanan hatalar en kısa sürede düzeltilir; anlamı değiştiren düzeltmeler haberin sonunda not olarak belirtilir.</p>
<p>Ayrıntılı ilkelerimiz için <a href="{st}">Yayın İlkeleri</a> sayfasına bakabilirsiniz.</p>
""".format(sn=sn, ed=page.r("editor"), co=page.r("contact"), st=page.r("standards")), "hakkimizda")

    page = Page(ROUTES["standards"][lang] + "index.html", lang)
    static_page(cfg, lang, "standards", "Yayın İlkeleri",
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
<p>Hatalar <a href="{co}">İletişim</a> sayfası üzerinden bildirilebilir. Doğrulanan hatalar düzeltilir; anlamı değiştiren düzeltmeler haberin sonunda not olarak gösterilir.</p>
""".format(sn=sn, co=page.r("contact")))

    page = Page(ROUTES["contact"][lang] + "index.html", lang)
    static_page(cfg, lang, "contact", "İletişim",
                "%s ile iletişim: genel sorular, hata bildirimi, reklam ve iş birliği." % cfg["site_name"], """
<p class="lead">Sorularınız, hata bildirimleriniz ve iş birliği önerileriniz için aşağıdaki formu kullanabilirsiniz.</p>
<p>Bir çeviride hata gördüyseniz konu olarak “Hata bildirimi”ni seçin ve haberin bağlantısını mesajınıza ekleyin.</p>
{form}
""".format(form=contact_form(cfg, page, lang)), "iletisim")

    page = Page(ROUTES["thanks"][lang] + "index.html", lang)
    static_page(cfg, lang, "thanks", "Teşekkürler",
                "Mesajınız alındı.", """
<p class="lead">Mesajınız bize ulaştı. İlginiz için teşekkür ederiz.</p>
<p>Hata bildirimleri öncelikle incelenir. <a href="{h}">Ana sayfaya dön</a></p>
""".format(h=page.r("home")))

    page = Page(ROUTES["privacy"][lang] + "index.html", lang)
    static_page(cfg, lang, "privacy", "Gizlilik Politikası",
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
<p>KVKK'nın 11. maddesi uyarınca kişisel verilerinizin işlenip işlenmediğini öğrenme, bilgi talep etme, düzeltilmesini veya silinmesini isteme, itiraz etme ve zarara uğramanız hâlinde giderilmesini talep etme haklarına sahipsiniz. Başvurularınızı <a href="{co}">İletişim</a> sayfasındaki form üzerinden iletebilirsiniz.</p>
<h2>8. Değişiklikler</h2>
<p>Bu politika gerektiğinde güncellenebilir. Güncel sürüm her zaman bu sayfada yayımlanır.</p>
""".format(sn=sn, co=page.r("contact")))


def build_static_pages_en(cfg):
    sn = esc(cfg["site_name"])
    lang = "en"
    page = Page(ROUTES["editor"][lang] + "index.html", lang)
    static_page(cfg, lang, "editor", "Editorial Oversight",
                "How %s stories are reviewed: our editorial process and accountability." % cfg["site_name"], """
<p class="lead">{sn} stories are translated with AI and published under <strong>human editorial oversight</strong>.</p>
<h2>Who is the editor?</h2>
<p>{sn} Editors is run by an editor trained in Persian translation and interpreting who previously served as editor-in-chief of a news website. The editor decides on source selection, editorial standards, orientation labels and corrections.</p>
<h2>How does oversight work?</h2>
<ul>
<li><strong>Rules:</strong> Every story is prepared according to the writing and editorial standards set by the editor: attribution to the source, an orientation label, marking conflicting claims as “unconfirmed,” and no opinion.</li>
<li><strong>Weekly review:</strong> Stories that directly concern Turkey or deal with sensitive subjects are read and approved one by one by the editor every week, and corrected where necessary.</li>
<li><strong>Verification:</strong> Claims about Turkey or about sanctions are checked against primary English-language sources before publication.</li>
<li><strong>Corrections:</strong> Reader reports are reviewed by the editor; corrections that change the meaning of a story are noted with a date at the end of the story.</li>
</ul>
<p>To report an error, please use the form on our <a href="{co}">Contact</a> page. Our editorial standards: <a href="{st}">Editorial Standards</a>.</p>
""".format(sn=sn, co=page.r("contact"), st=page.r("standards")), "hakkimizda")

    page = Page(ROUTES["about"][lang] + "index.html", lang)
    static_page(cfg, lang, "about", "About",
                "What is %s, and how are its stories selected and translated?" % cfg["site_name"], """
<p class="lead">{sn} is an AI-assisted translation news site that brings stories from Iran's Persian-language press to English and Turkish readers.</p>
<h2>What we do</h2>
<p>We regularly monitor a large number of Persian-language news organizations, both inside and outside Iran. We select the stories that shape the agenda and publish them as summary translations. Our aim is to let readers follow the debate in Iran directly through Persian-language sources.</p>
<h2>Sources and orientation labels</h2>
<p>We do not select stories from a single point of view but from different points across the spectrum:</p>
<ul>
<li><strong>state and official</strong> outlets,</li>
<li><strong>conservative and hardline</strong> publications,</li>
<li><strong>reformist</strong> newspapers,</li>
<li>the <strong>economic</strong> press,</li>
<li>Persian-language <strong>diaspora and opposition</strong> outlets based abroad.</li>
</ul>
<p>Each story shows the outlet's name, its <strong>orientation label</strong>, the original Persian headline and a link to the original story, so readers always know through which lens they are reading it.</p>
<h2>We do not publish opinion</h2>
<p>{sn} does not publish columns or commentary. Claims and assessments reported in our stories belong to the original outlet. The “Context” sections, where we provide background, are based on facts and contain no opinion.</p>
<h2>Who does the translation?</h2>
<p>Translations are produced with AI, which is why our stories carry the byline <strong>“AI Agent.”</strong> The process runs under human editorial oversight: source selection, editorial standards and corrections are the editor's responsibility. Details: <a href="{ed}">Editorial Oversight</a>.</p>
<h2>Corrections policy</h2>
<p>We take translation and factual errors seriously. If you notice an error, write to us using the form on our <a href="{co}">Contact</a> page and choose “Error report” as the subject. Verified errors are corrected as quickly as possible; corrections that change the meaning of a story are noted at the end of the story.</p>
<p>For our detailed principles, see our <a href="{st}">Editorial Standards</a>.</p>
""".format(sn=sn, ed=page.r("editor"), co=page.r("contact"), st=page.r("standards")), "hakkimizda")

    page = Page(ROUTES["standards"][lang] + "index.html", lang)
    static_page(cfg, lang, "standards", "Editorial Standards",
                "%s editorial standards: impartiality, orientation labels, unverified claims, image licensing and corrections." % cfg["site_name"], """
<p class="lead">{sn} selects, translates and publishes stories according to the following principles.</p>
<h2>1. Impartiality</h2>
<p>We report stories as they are; we do not take sides or add opinion. We follow outlets of different orientations in a balanced way, and when the same event is reported differently, we show that difference in the “How the Persian press covered it” section.</p>
<h2>2. Orientation labels</h2>
<p>Every story labels the outlet's orientation (for example state, semi-official, conservative, reformist, economic, or diaspora opposition). The label describes the outlet's general editorial line; it is not a judgment on the accuracy of the story.</p>
<h2>3. Unverified claims</h2>
<p>Claims that cannot be independently verified are clearly marked with phrases such as “allegedly” or “according to the outlet.” Where outlets differ on figures or on the sequence of events, we say so.</p>
<h2>4. Summary translation</h2>
<p>We do not republish the full source text. We convey the substance of each story in a faithful summary translation and always link to the original. Responsibility for the reporting lies with the original outlet.</p>
<h2>5. AI and human oversight</h2>
<p>Translations are produced with AI and published under the byline “AI Agent.” Source selection, standards and corrections are subject to human editorial oversight.</p>
<h2>6. Images</h2>
<p>We use only freely licensed images (public domain, CC0, CC BY, CC BY-SA). Every image carries a credit with the author, license and a link to the source. We do not use photographs from the Iranian press.</p>
<h2>7. Corrections</h2>
<p>Errors can be reported through our <a href="{co}">Contact</a> page. Verified errors are corrected; corrections that change the meaning of a story are noted at the end of the story.</p>
""".format(sn=sn, co=page.r("contact")))

    page = Page(ROUTES["contact"][lang] + "index.html", lang)
    static_page(cfg, lang, "contact", "Contact",
                "Contact %s: general questions, error reports, advertising and partnerships." % cfg["site_name"], """
<p class="lead">Please use the form below for questions, error reports and partnership proposals.</p>
<p>If you spot an error in a translation, choose “Error report” as the subject and include the link to the story in your message.</p>
{form}
""".format(form=contact_form(cfg, page, lang)), "iletisim")

    page = Page(ROUTES["thanks"][lang] + "index.html", lang)
    static_page(cfg, lang, "thanks", "Thank you",
                "Your message has been received.", """
<p class="lead">Your message has reached us. Thank you for getting in touch.</p>
<p>Error reports are reviewed first. <a href="{h}">Back to the home page</a></p>
""".format(h=page.r("home")))

    page = Page(ROUTES["privacy"][lang] + "index.html", lang)
    static_page(cfg, lang, "privacy", "Privacy Policy",
                "%s privacy policy and data protection notice under Turkish law (KVKK): cookies, advertising, contact form." % cfg["site_name"], """
<p class="meta">Last updated: October 3, 2026</p>
<p class="lead">This policy explains what data is processed when you visit the {sn} (farscadan.com) website, in accordance with Turkey's Personal Data Protection Law No. 6698 (KVKK).</p>
<h2>1. No account system</h2>
<p>{sn} has no membership, login or user accounts. You do not need to provide any personal information to read the site.</p>
<h2>2. Cookies and local storage</h2>
<p>Cookies are small text files that the websites you visit store in your browser. On its own, our site uses only your browser's local storage (localStorage) to remember that you have dismissed the cookie notice; this information never leaves your device.</p>
<p>Fonts are loaded from Google Fonts; in the process, your IP address may technically be transmitted to Google.</p>
<h2>3. Third-party advertising and analytics services</h2>
<p>Our site may use third-party advertising services such as Google AdSense and analytics tools for visitor statistics. In that case:</p>
<ul>
<li>Third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to this website or other websites.</li>
<li>Google's use of advertising cookies enables it and its partners to serve ads to users based on their visit to this site and/or other sites on the Internet.</li>
<li>You may opt out of personalized advertising by visiting <a href="https://adssettings.google.com/" rel="noopener" target="_blank">Google Ads Settings</a>. You can opt out of third-party vendors' use of cookies for personalized advertising by visiting <a href="https://www.aboutads.info/choices/" rel="noopener" target="_blank">www.aboutads.info</a>.</li>
<li>For information on how Google uses this data, see <a href="https://policies.google.com/technologies/ads" rel="noopener" target="_blank">https://policies.google.com/technologies/ads</a>.</li>
</ul>
<p>You can delete or block cookies in your browser settings; if you do, some features may not work as expected.</p>
<h2>4. Contact form</h2>
<p>When you use the contact form, your name, email address, chosen subject and message are forwarded to us by email through the form service provider <strong>FormSubmit</strong> (formsubmit.co). This data is processed solely to reply to your message and to assess error reports, on the basis of your explicit consent and our legitimate interest; it is not used for marketing and is not sold to third parties. FormSubmit may process this data on its own servers in order to provide the service, so your data may be transferred abroad.</p>
<h2>5. Server logs</h2>
<p>The site is hosted as a static site. The hosting provider may keep standard technical logs, such as IP address, browser type and time of access, for security and operational purposes.</p>
<h2>6. Retention</h2>
<p>Messages received through the contact form are kept for as long as needed to resolve the request and for as long as required by legal obligations.</p>
<h2>7. Your rights under KVKK</h2>
<p>Under Article 11 of KVKK, you have the right to learn whether your personal data is processed, to request information, to ask for it to be corrected or deleted, to object, and to claim compensation if you suffer damage. You can submit requests through the form on our <a href="{co}">Contact</a> page.</p>
<h2>8. Changes</h2>
<p>This policy may be updated when necessary. The current version is always published on this page.</p>
""".format(sn=sn, co=page.r("contact")))


def build_404(cfg):
    # 404 sayfası herhangi bir yoldan sunulabildiği için göreli bağlantı yerine base_url kullanılır.
    base = cfg["base_url"].rstrip("/") + "/"

    class AbsPage(Page):
        def __init__(self):
            self.path = "404.html"
            self.lang = "tr"
            self.p = base

    page = AbsPage()
    inner = ('<div class="wrap"><article class="prose"><h1>Sayfa bulunamadı</h1>'
             '<p class="lead">Aradığınız sayfa taşınmış ya da kaldırılmış olabilir.</p>'
             '<p><a href="%s">Ana sayfaya dön</a></p>'
             '<div lang="en"><h2>Page not found</h2>'
             '<p>The page you are looking for may have been moved or removed.</p>'
             '<p><a href="%sen/">Go to the English home page</a></p></div></article></div>' % (base, base))
    render(cfg, page, "Sayfa bulunamadı", cfg["description"], "404.html", inner,
           extra='<meta name="robots" content="noindex">\n')


def xml_esc(s):
    return html.escape(str(s), quote=True)


def build_feeds(cfg, arts_by_lang, topics_by_lang):
    tr_slugs = {a["slug"] for a in arts_by_lang["tr"]}
    en_slugs = {a["slug"] for a in arts_by_lang["en"]}
    both = tr_slugs & en_slugs
    # (rel, lastmod, alts)
    urls = []
    for key in ("home", "about", "standards", "editor", "contact", "privacy", "topics"):
        for lg in LANGS:
            urls.append((ROUTES[key][lg], None, ROUTES[key]))
    for _, s in CATEGORIES:
        alts = {lg: PFX[lg] + "kategori/%s/" % s for lg in LANGS}
        for lg in LANGS:
            urls.append((alts[lg], None, alts))
    for lg in LANGS:
        for a in arts_by_lang[lg]:
            alts = ({x: PFX[x] + "haber/%s/" % a["slug"] for x in LANGS}
                    if a["slug"] in both else None)
            urls.append((PFX[lg] + "haber/%s/" % a["slug"], a["date"], alts))
    for lg in LANGS:
        for s, tp in sorted(topics_by_lang[lg].items()):
            urls.append((PFX[lg] + "konu/%s/" % s, tp["arts"][0]["date"], None))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for rel, d, alts in urls:
        alt_xml = ""
        if alts:
            alt_xml = "".join('<xhtml:link rel="alternate" hreflang="%s" href="%s"/>'
                              % (lg, xml_esc(abs_url(cfg, alts[lg]))) for lg in LANGS)
            alt_xml += ('<xhtml:link rel="alternate" hreflang="x-default" href="%s"/>'
                        % xml_esc(abs_url(cfg, alts["tr"])))
        sm.append("  <url><loc>%s</loc>%s%s</url>" % (
            xml_esc(abs_url(cfg, rel)),
            "<lastmod>%s</lastmod>" % d.date().isoformat() if d else "", alt_xml))
    sm.append("</urlset>")
    write("sitemap.xml", "\n".join(sm) + "\n")

    # Google News site haritası: son 48 saatteki haberler (iki dil)
    limit = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=48)
    ns = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">']
    recent = []
    for lg in LANGS:
        recent += [x for x in arts_by_lang[lg] if x["date"] >= limit]
    recent.sort(key=lambda a: a["date"], reverse=True)
    for a in recent[:1000]:
        ns.append("  <url><loc>%s</loc><news:news><news:publication><news:name>%s</news:name>"
                  "<news:language>%s</news:language></news:publication>"
                  "<news:publication_date>%s</news:publication_date><news:title>%s</news:title>"
                  "</news:news></url>" % (xml_esc(abs_url(cfg, PFX[a["lang"]] + "haber/%s/" % a["slug"])),
                                          xml_esc(cfg["site_name"]), a["lang"], a["date"].isoformat(),
                                          xml_esc(a["meta"]["baslik"])))
    ns.append("</urlset>")
    write("news-sitemap.xml", "\n".join(ns) + "\n")

    write("robots.txt", "User-agent: *\nAllow: /\n\nSitemap: %s\nSitemap: %s\n"
          % (abs_url(cfg, "sitemap.xml"), abs_url(cfg, "news-sitemap.xml")))

    for lg in LANGS:
        arts = arts_by_lang[lg]
        now = arts[0]["date"] if arts else dt.datetime.now(dt.timezone.utc)
        items = []
        for a in arts[:20]:
            m = a["meta"]
            link = abs_url(cfg, PFX[lg] + "haber/%s/" % a["slug"])
            items.append("""  <item>
    <title>{t}</title>
    <link>{l}</link>
    <guid isPermaLink="true">{l}</guid>
    <pubDate>{d}</pubDate>
    <category>{c}</category>
    <dc:creator>{au}</dc:creator>
    <description>{o}</description>
  </item>""".format(t=xml_esc(m["baslik"]), l=xml_esc(link), d=email.utils.format_datetime(a["date"]),
                    c=xml_esc(cat_name(a["cat"], lg)), au=xml_esc(m.get("yazar") or "AI Agent"),
                    o=xml_esc("%s (%s: %s)" % (m["ozet"], T[lg]["src_note"], m["kaynak_adi"]))))
        feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
<channel>
  <title>{sn}</title>
  <link>{home}</link>
  <description>{d}</description>
  <language>{lg}</language>
  <lastBuildDate>{lb}</lastBuildDate>
  <atom:link href="{self}" rel="self" type="application/rss+xml"/>
{items}
</channel>
</rss>
""".format(sn=xml_esc(cfg["site_name"] + (" (English)" if lg == "en" else "")),
           home=xml_esc(abs_url(cfg, ROUTES["home"][lg])), d=xml_esc(description(cfg, lg)), lg=lg,
           lb=email.utils.format_datetime(now), self=xml_esc(abs_url(cfg, ROUTES["feed"][lg])),
           items="\n".join(items))
        write(ROUTES["feed"][lg], feed)


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

    arts_by_lang = {lg: load_articles(include_samples, lg) for lg in LANGS}
    slugs = {lg: {a["slug"] for a in arts_by_lang[lg]} for lg in LANGS}
    topics_by_lang = {lg: collect_topics(arts_by_lang[lg]) for lg in LANGS}
    for lg in LANGS:
        other = "en" if lg == "tr" else "tr"
        arts = arts_by_lang[lg]
        other_by_slug = {a["slug"]: a for a in arts_by_lang[other]}
        build_index(cfg, arts, lg)
        for name, slug in CATEGORIES:
            build_category(cfg, arts, name, slug, lg)
        for a in arts:
            build_article(cfg, a, arts, other_by_slug.get(a["slug"]), topics_by_lang[lg], slugs[other])
        build_topics(cfg, topics_by_lang[lg], lg)
    build_static_pages_tr(cfg)
    build_static_pages_en(cfg)
    build_404(cfg)
    build_feeds(cfg, arts_by_lang, topics_by_lang)

    write(".nojekyll", "")
    client = adsense_active(cfg)
    if client:
        pub = client[3:] if client.startswith("ca-") else client
        write("ads.txt", "google.com, %s, DIRECT, f08c47fec0942fa0\n" % pub)

    pairs = len(slugs["tr"] & slugs["en"])
    print("Derleme tamam: %d TR + %d EN haber (%d eşli), %d TR + %d EN konu, %d uyarı%s → %s" % (
        len(arts_by_lang["tr"]), len(arts_by_lang["en"]), pairs,
        len(topics_by_lang["tr"]), len(topics_by_lang["en"]), len(WARNINGS),
        " (örnekler dahil)" if include_samples else "", PUBLIC_DIR))


if __name__ == "__main__":
    main()
