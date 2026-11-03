#!/usr/bin/env python3
"""Günün X taslaklarını (rutin/kayit/x-<tarih>.md) otomatik paylaşır (02.11).

Kullanım: python3 rutin/x_taslak_paylas.py sabah|aksam [YYYY-MM-DD] [--prova]
  sabah → "Günün Özeti" (özet görseliyle) + ilk 2 haber gönderisi (kart görseli varsa)
  aksam → sıradaki 2 haber gönderisi
Kural (04.11, kullanıcı): HİÇBİR tweet bağlantı içermez (uzantısız); site bağlantısı profilde.
Günlük tavan x_paylas.py'de (6).
Paylaşılanlar: ~/farscadan/state/x-paylasilan-<tarih>.txt (aynı gönderi iki kez atılmaz).
"""
import datetime as dt
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.expanduser("~/farscadan/state")


def yerel(url):
    m = re.search(r"farscadan\.com/(x/\S+\.(?:png|jpg))", url or "")
    if not m:
        return None
    p = os.path.join(ROOT, "static", m.group(1))
    return p if os.path.exists(p) else None


def temizle(metin):
    """04.11 kullanıcı kuralı: tweet'ler uzantısız — bağlantı, alan adı ve 'Haberlerin tamamı:' kalıntıları silinir."""
    metin = re.sub(r"\s*(?:Haberlerin tamamı|Tamamı|Ayrıntılar)\s*:?\s*(?=https?://|www\.|[\w-]+\.com)", " ", metin)
    metin = re.sub(r"\s*(?:https?://\S+|www\.\S+|\b[\w-]+\.(?:com|net|org|ir|tr|io|co)\b\S*)", "", metin, flags=re.I)
    metin = re.sub(r"[ \t]{2,}", " ", metin)
    return re.sub(r"\n{3,}", "\n\n", metin).strip()


def ayristir(yol):
    t = open(yol, encoding="utf-8").read()
    ozet, gonderiler = None, []
    m = re.search(r"## Günün Özeti[^\n]*\n+(.*?)(?=\n## |\Z)", t, re.S)
    if m:
        blok = m.group(1).strip()
        g = re.search(r"^Görsel:\s*(\S+)", blok, re.M)
        metin = re.sub(r"^Görsel:.*$", "", blok, flags=re.M).strip()
        metin = temizle(metin)
        ozet = {"metin": metin, "gorsel": yerel(g.group(1)) if g else None}
    m = re.search(r"## Gönderiler\s*\n(.*?)(?=\n## |\Z)", t, re.S)
    if m:
        for parca in re.split(r"\n(?=\d+\.\s)", "\n" + m.group(1).strip()):
            parca = parca.strip()
            if not re.match(r"\d+\.\s", parca):
                continue
            no = parca.split(".", 1)[0]
            g = re.search(r"^Görsel:\s*(\S+)", parca, re.M)
            metin = re.sub(r"^Görsel:.*$", "", parca, flags=re.M)
            metin = re.sub(r"^\d+\.\s*", "", metin.strip())
            metin = temizle(metin)
            gonderiler.append({"no": no, "metin": metin, "gorsel": yerel(g.group(1)) if g else None})
    return ozet, gonderiler


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    mod = a[0] if a else "sabah"
    gun = a[1] if len(a) > 1 else dt.date.today().isoformat()
    prova = "--prova" in sys.argv
    yol = os.path.join(ROOT, "rutin", "kayit", "x-%s.md" % gun)
    if not os.path.exists(yol):
        sys.exit("taslak dosyası yok: %s" % yol)
    ozet, gonderiler = ayristir(yol)
    os.makedirs(STATE, exist_ok=True)
    kayit = os.path.join(STATE, "x-paylasilan-%s.txt" % gun)
    yapildi = set(open(kayit).read().split()) if os.path.exists(kayit) else set()
    plan = []
    if mod == "sabah" and ozet and "ozet" not in yapildi:
        plan.append(("ozet", ozet))
    kalan = [g for g in gonderiler if g["no"] not in yapildi]
    plan += [(g["no"], g) for g in kalan[:2]]
    if not plan:
        print("paylaşılacak yeni taslak yok")
        return
    for anahtar, g in plan:
        cmd = [sys.executable, os.path.join(ROOT, "rutin", "x_paylas.py"), "--gonder", g["metin"]]
        if g["gorsel"]:
            cmd += ["--gorsel", g["gorsel"]]
        if prova:
            cmd.append("--prova")
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(("[%s] " % anahtar) + (r.stdout + r.stderr).strip())
        if not prova and "GONDERILDI" in r.stdout:
            with open(kayit, "a") as f:
                f.write(anahtar + "\n")
        elif not prova and "tavan dolu" in (r.stdout + r.stderr):
            break


if __name__ == "__main__":
    main()
