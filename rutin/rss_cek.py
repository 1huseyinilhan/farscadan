#!/usr/bin/env python3
"""Farsça basın RSS'lerini çeker, son N saatin haberlerini tek JSON'a yazar.

Kullanım: python3 rss_cek.py [saat=20] [cikti=feeds.json]
Kaynak listesi ve yönelim etiketleri: ../skills/GUNLUK_BULTEN.md → Kaynak Havuzu.
"""
import json, re, sys, html, subprocess, urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

KAYNAKLAR = {
    "irna":         ("https://www.irna.ir/rss",            "Devlet ajansı (hükümet)"),
    "isna":         ("https://www.isna.ir/rss",            "Yarı resmî (üniversite/ılımlı)"),
    "hamshahri":    ("https://www.hamshahrionline.ir/rss", "Tahran Belediyesi (ilkeci)"),
    "kayhan":       ("https://kayhan.ir/fa/rss/allnews",   "Sertlik yanlısı (Rehberlik çizgisi)"),
    "donya":        ("https://donya-e-eqtesad.com/feeds/", "Ekonomi gazetesi (teknokrat)"),
    "ettelaat":     ("https://www.ettelaat.com/rss",       "Köklü gazete (ılımlı-gelenekçi)"),
    "khabaronline": ("https://www.khabaronline.ir/rss",    "Ilımlı muhafazakâr (Laricani çevresi)"),
    "iranintl":     ("https://www.iranintl.com/fa/feed",   "Muhalif, yurt dışı (Londra)"),
}

def cek(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()
    except Exception:
        # Bazı .ir sunucularında Python SSL zinciri hata verir; curl yedeği
        return subprocess.run(["curl", "-sL", "-m", "20", "-A", "Mozilla/5.0", url],
                              capture_output=True, check=True).stdout

def temiz(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(s or ""))).strip()

def tarih(s):
    try:
        d = parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None

def main():
    saat = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    cikti = sys.argv[2] if len(sys.argv) > 2 else "feeds.json"
    sinir = datetime.now(timezone.utc) - timedelta(hours=saat)
    sonuc, durum = [], {}
    for ad, (url, yonelim) in KAYNAKLAR.items():
        try:
            kok = ET.fromstring(cek(url))
            n = 0
            for it in kok.iter("item"):
                d = tarih(it.findtext("pubDate"))
                if d and d < sinir:
                    continue
                sonuc.append({"kaynak": ad, "yonelim": yonelim,
                              "baslik": temiz(it.findtext("title")),
                              "ozet": temiz(it.findtext("description"))[:600],
                              "link": (it.findtext("link") or "").strip(),
                              "tarih": d.isoformat() if d else None})
                n += 1
            durum[ad] = f"ok ({n})"
        except Exception as e:
            durum[ad] = f"HATA: {type(e).__name__}"
    json.dump({"durum": durum, "haberler": sonuc}, open(cikti, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(durum, ensure_ascii=False))

if __name__ == "__main__":
    main()
