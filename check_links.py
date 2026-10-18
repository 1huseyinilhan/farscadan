#!/usr/bin/env python3
"""public/ içindeki tüm iç bağlantıları doğrular; sitemap.xml, news-sitemap.xml, feed.xml ve
en/feed.xml'i XML olarak ayrıştırır. Ayrıca:
  - en/ altındaki sayfalarda lang="en", diğerlerinde lang="tr" olmalı;
  - hreflang alternatiflerinin hedefleri public/ içinde var olmalı ve karşılıklı olmalı;
  - sitemap.xml'deki her <loc> (ve xhtml:link) adresinin dosyası var olmalı;
  - sitemap.xml'de robots noindex taşıyan sayfa olmamalı;
  - konu sayfaları: 3'ten az haberli olan noindex, en az 3 haberli olan indekslenebilir olmalı;
  - sözlük (sozluk/, en/glossary/): dizinler var, madde sayfalarında DefinedTerm JSON-LD'si ve
    dizine işaret eden inDefinedTermSet var; iki dilde de bulunan maddelerde hreflang eşi var;
  - Analiz kategorisi sayfaları var; Analiz yazılarında AnalysisNewsArticle var ve
    "Özgün haberi oku" bağlantısı yok.

Kullanım: python3 check_links.py   (önce python3 build.py çalıştırılmalı)
Çıkış kodu: 0 = sorun yok, 1 = hata var.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")
PFX_GL = {"tr": "sozluk", "en": os.path.join("en", "glossary")}


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.scripts = []
        self.ids = set()
        self.alternates = []  # (hreflang, href)
        self.html_lang = None
        self.robots = ""
        self.jsonld = []
        self._in_ld = False
        self.cards = 0
        self.texts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alternates.append((a["hreflang"], a.get("href") or ""))
        if "id" in a:
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if a.get(key) is not None:
                self.refs.append((tag, a[key]))
        if tag == "script":
            self.scripts.append(a)
            self._in_ld = a.get("type") == "application/ld+json"
            if self._in_ld:
                self.jsonld.append("")
        if tag == "meta" and a.get("name") == "robots":
            self.robots = (a.get("content") or "").lower()
        if tag == "article" and "card" in (a.get("class") or "").split():
            self.cards += 1

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_ld = False

    def handle_data(self, data):
        if self._in_ld:
            self.jsonld[-1] += data


def is_external(u):
    s = urlsplit(u)
    return bool(s.scheme) or u.startswith("//")


def resolve(html_file, ref):
    path = unquote(urlsplit(ref).path)
    if not path:
        return html_file  # yalnızca #parça veya ?sorgu
    if path.startswith("/"):
        target = os.path.join(PUBLIC, path.lstrip("/"))
    else:
        target = os.path.normpath(os.path.join(os.path.dirname(html_file), path))
    if path.endswith("/") or os.path.isdir(target):
        target = os.path.join(target, "index.html")
    return target


def load_base():
    try:
        with open(os.path.join(ROOT, "site.json"), encoding="utf-8") as f:
            return json.load(f).get("base_url", "https://farscadan.com").rstrip("/") + "/"
    except Exception:  # noqa
        return "https://farscadan.com/"


def abs_to_file(base, url):
    """Sitenin mutlak URL'sini public/ içindeki dosyaya çevirir; site dışıysa None."""
    if not url.startswith(base):
        return None
    rel = unquote(urlsplit(url[len(base):]).path)
    target = os.path.join(PUBLIC, rel)
    if rel == "" or rel.endswith("/") or os.path.isdir(target):
        target = os.path.join(target, "index.html")
    return os.path.normpath(target)


def main():
    if not os.path.isdir(PUBLIC):
        print("public/ yok; önce build.py çalıştırın.")
        return 1
    base = load_base()
    errors, checked, pages = [], 0, 0
    alt_map = {}  # sayfa dosyası → {hreflang: hedef dosya}
    noindex = set()  # robots noindex taşıyan sayfa dosyaları
    topic_stats = {"tr": [0, 0], "en": [0, 0]}  # [indeksli, noindex]
    gloss_pages = {"tr": {}, "en": {}}  # slug → (dosya, alternates)
    analysis_pages = 0
    for dirpath, _, files in os.walk(PUBLIC):
        for fn in files:
            if not fn.endswith(".html"):
                continue
            pages += 1
            fp = os.path.join(dirpath, fn)
            rel = os.path.relpath(fp, PUBLIC)
            with open(fp, encoding="utf-8") as f:
                src = f.read()
            c = Collector()
            c.feed(src)
            for tag, ref in c.refs:
                if ref.startswith(("mailto:", "tel:", "data:")):
                    continue
                if ref.lower().startswith("javascript:"):
                    errors.append("%s: javascript: bağlantısı: %s" % (rel, ref))
                    continue
                if is_external(ref):
                    continue
                checked += 1
                target = resolve(fp, ref)
                if not target.startswith(PUBLIC):
                    errors.append("%s: public/ dışına çıkan bağlantı: %s" % (rel, ref))
                elif not os.path.isfile(target):
                    errors.append("%s: kırık bağlantı: %s" % (rel, ref))
            # Kaçış kontrolü: içerikten sızmış <script> olmamalı
            for s in c.scripts:
                if not (s.get("type") == "application/ld+json" or "src" in s or not s):
                    errors.append("%s: beklenmeyen script etiketi: %r" % (rel, s))
            if src.count("<script") != len(c.scripts):
                errors.append("%s: script sayısı tutarsız" % rel)
            want = "en" if rel.startswith("en" + os.sep) else "tr"
            if c.html_lang != want:
                errors.append("%s: <html lang> %r, beklenen %r" % (rel, c.html_lang, want))
            if c.alternates:
                amap = {}
                for hl, href in c.alternates:
                    t = abs_to_file(base, href)
                    if t is None:
                        errors.append("%s: hreflang=%s site dışı: %s" % (rel, hl, href))
                    elif not os.path.isfile(t):
                        errors.append("%s: hreflang=%s hedefi yok: %s" % (rel, hl, href))
                    else:
                        amap[hl] = t
                if "x-default" not in amap:
                    errors.append("%s: hreflang x-default eksik" % rel)
                alt_map[os.path.normpath(fp)] = amap
            parts = rel.split(os.sep)
            lg = "en" if parts[0] == "en" else "tr"
            sub = parts[1:] if lg == "en" else parts
            if "noindex" in c.robots:
                noindex.add(os.path.normpath(fp))
            lds = []
            for raw in c.jsonld:
                try:
                    lds.append(json.loads(raw))
                except ValueError as e:
                    errors.append("%s: geçersiz JSON-LD: %s" % (rel, e))
            types = {d.get("@type") for d in lds if isinstance(d, dict)}
            # Konu sayfaları: ince sayfa denetimi
            if len(sub) == 3 and sub[0] == "konu":
                thin = c.cards < 3
                topic_stats[lg][1 if thin else 0] += 1
                if thin and "noindex" not in c.robots:
                    errors.append("%s: %d haberli konu sayfası noindex değil" % (rel, c.cards))
                if not thin and "noindex" in c.robots:
                    errors.append("%s: %d haberli konu sayfası noindex" % (rel, c.cards))
            # Sözlük madde sayfaları
            gdir = "glossary" if lg == "en" else "sozluk"
            if len(sub) == 3 and sub[0] == gdir:
                gloss_pages[lg][sub[1]] = (os.path.normpath(fp), dict(c.alternates))
                dts = [d for d in lds if isinstance(d, dict) and d.get("@type") == "DefinedTerm"]
                if not dts:
                    errors.append("%s: DefinedTerm JSON-LD yok" % rel)
                for d in dts:
                    t = abs_to_file(base, d.get("inDefinedTermSet", ""))
                    want_idx = os.path.normpath(os.path.join(PUBLIC, PFX_GL[lg], "index.html"))
                    if t != want_idx:
                        errors.append("%s: inDefinedTermSet sözlük dizinini göstermiyor: %r"
                                      % (rel, d.get("inDefinedTermSet")))
                if "BreadcrumbList" not in types:
                    errors.append("%s: BreadcrumbList JSON-LD yok" % rel)
            # Analiz yazıları
            if len(sub) == 3 and sub[0] == "haber" and "AnalysisNewsArticle" in types:
                analysis_pages += 1
                if "Özgün haberi oku" in src or "Read the original (Persian)" in src:
                    errors.append("%s: Analiz yazısında 'özgün haberi oku' bağlantısı var" % rel)
    # hreflang karşılıklılığı: A, B'yi alternatif gösteriyorsa B de A'yı göstermeli
    hreflang_pairs = 0
    for page_file, amap in alt_map.items():
        for hl, target in amap.items():
            if hl == "x-default" or target == page_file:
                continue
            hreflang_pairs += 1
            back = alt_map.get(target, {})
            if page_file not in back.values():
                errors.append("%s: hreflang=%s karşılıksız (%s geri bağlamıyor)" % (
                    os.path.relpath(page_file, PUBLIC), hl, os.path.relpath(target, PUBLIC)))
    # Sözlük: iki dilde de var olan maddeler hreflang ile eşlenmeli ve hedefler var olmalı
    gloss_pairs = 0
    for lg, other in (("tr", "en"), ("en", "tr")):
        for slug, (fp, alts) in gloss_pages[lg].items():
            for hl, href in alts.items():
                t = abs_to_file(base, href)
                if t is None or not os.path.isfile(t):
                    errors.append("%s: sözlük hreflang=%s hedefi yok: %s" % (
                        os.path.relpath(fp, PUBLIC), hl, href))
            if slug in gloss_pages[other]:
                gloss_pairs += 1
                want = gloss_pages[other][slug][0]
                if alt_map.get(fp, {}).get(other) != want:
                    errors.append("%s: karşılık madde var ama hreflang=%s eksik/yanlış" % (
                        os.path.relpath(fp, PUBLIC), other))
    sitemap_locs = 0
    for x in ("sitemap.xml", "news-sitemap.xml", "feed.xml", "en/feed.xml"):
        p = os.path.join(PUBLIC, x)
        try:
            tree = ET.parse(p)
        except Exception as e:  # noqa
            errors.append("%s: geçersiz XML: %s" % (x, e))
            continue
        if x.endswith("sitemap.xml"):
            locs = [el.text or "" for el in tree.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
            locs += [el.get("href", "") for el in tree.iter("{http://www.w3.org/1999/xhtml}link")]
            for u in locs:
                t = abs_to_file(base, u)
                if t is None or not os.path.isfile(t):
                    errors.append("%s: sayfası olmayan adres: %s" % (x, u))
                elif t in noindex:
                    errors.append("%s: noindex sayfa site haritasında: %s" % (x, u))
            if x == "sitemap.xml":
                sitemap_locs = len(locs)
    for x in ("robots.txt", ".nojekyll", "404.html", "favicon.svg", "css/site.css",
              "en/index.html", "en/feed.xml", "sozluk/index.html", "en/glossary/index.html",
              "kategori/analiz/index.html", "en/kategori/analiz/index.html"):
        if not os.path.exists(os.path.join(PUBLIC, x)):
            errors.append("eksik dosya: %s" % x)
    print("%d sayfa, %d iç bağlantı, %d hreflang eşi kontrol edildi, %d hata." % (
        pages, checked, hreflang_pairs, len(errors)))
    print("  konu sayfaları: TR %d indeksli / %d noindex, EN %d indeksli / %d noindex; "
          "sitemap %d adres (noindex sayfa: %d)" % (
              topic_stats["tr"][0], topic_stats["tr"][1], topic_stats["en"][0], topic_stats["en"][1],
              sitemap_locs, len(noindex)))
    print("  sözlük: %d TR + %d EN madde sayfası, %d hreflang eşi; analiz yazısı: %d" % (
        len(gloss_pages["tr"]), len(gloss_pages["en"]), gloss_pairs, analysis_pages))
    for e in errors:
        print("  - " + e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
