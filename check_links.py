#!/usr/bin/env python3
"""public/ içindeki tüm iç bağlantıları doğrular; sitemap.xml ve feed.xml'i XML olarak ayrıştırır.

Kullanım: python3 check_links.py   (önce python3 build.py çalıştırılmalı)
Çıkış kodu: 0 = sorun yok, 1 = hata var.
"""
import os
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.scripts = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if a.get(key) is not None:
                self.refs.append((tag, a[key]))
        if tag == "script":
            self.scripts.append(a)


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


def main():
    if not os.path.isdir(PUBLIC):
        print("public/ yok; önce build.py çalıştırın.")
        return 1
    errors, checked, pages = [], 0, 0
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
            if "lang=\"tr\"" not in src:
                errors.append("%s: lang=\"tr\" eksik" % rel)
    for x in ("sitemap.xml", "feed.xml"):
        p = os.path.join(PUBLIC, x)
        try:
            ET.parse(p)
        except Exception as e:  # noqa
            errors.append("%s: geçersiz XML: %s" % (x, e))
    for x in ("robots.txt", ".nojekyll", "404.html", "favicon.svg", "css/site.css"):
        if not os.path.exists(os.path.join(PUBLIC, x)):
            errors.append("eksik dosya: %s" % x)
    print("%d sayfa, %d iç bağlantı kontrol edildi, %d hata." % (pages, checked, len(errors)))
    for e in errors:
        print("  - " + e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
