#!/usr/bin/env python3
"""Farsçadan haftalık e-posta bülteni (31.10): haftanın analizi + önemli haberler.

Kullanım:
  python3 rutin/bulten.py [YYYY-MM-DD]            → önizleme: rutin/kayit/bulten-<tarih>.md yazar, göndermez
  python3 rutin/bulten.py [YYYY-MM-DD] --gonder   → Buttondown API ile abonelere gönderir (bir kez)
  python3 rutin/bulten.py [YYYY-MM-DD] --taslak   → Buttondown'da taslak oluşturur (göndermez)

Tarih: haftanın son günü (pazar), varsayılan bugün. Kapsam: o gün dahil son 7 gün.
"Önemli haberler": önce haftanın analizinin bağlantı verdiği haberler (analizdeki sırayla),
sonra eksik kalırsa Türkiye kategorisi ve en yeni haberler; en fazla 8 haber.
API anahtarı yalnızca Keychain'de: security add-generic-password -a farscadan -s farscadan-buttondown -w
Çıkış kodları: 0 tamam, 2 bu hafta haber yok, 3 zaten gönderilmiş, 4 API anahtarı yok, 5 API hatası.
"""
import datetime as dt
import glob
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://farscadan.com"
API = "https://api.buttondown.com/v1/emails"
EN_FAZLA = 8
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def oku(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", t, re.S)
    meta = {}
    for line in (m.group(1) if m else "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] == '"':
                v = v[1:-1]
            meta[k.strip()] = v
    meta["_slug"] = os.path.basename(path)[:-3]
    meta["_body"] = m.group(2) if m else t
    return meta


def link(slug, kampanya):
    return "%s/haber/%s/?utm_source=bulten&utm_medium=email&utm_campaign=%s" % (BASE, slug, kampanya)


def gun_araligi(bas, son):
    if bas.month == son.month:
        return "%d–%d %s" % (bas.day, son.day, AYLAR[son.month - 1])
    return "%d %s–%d %s" % (bas.day, AYLAR[bas.month - 1], son.day, AYLAR[son.month - 1])


def topla(son):
    bas = son - dt.timedelta(days=6)
    arts, analiz = [], None
    for f in glob.glob(os.path.join(ROOT, "content", "haberler", "*.md")):
        if os.path.basename(f).startswith("_"):
            continue
        try:
            d = dt.date.fromisoformat(os.path.basename(f)[:10])
        except ValueError:
            continue
        if not (bas <= d <= son):
            continue
        m = oku(f)
        if m.get("kategori") == "Analiz":
            if analiz is None or m["_slug"] > analiz["_slug"]:
                analiz = m
        else:
            arts.append(m)
    arts.sort(key=lambda m: m.get("tarih", m["_slug"]), reverse=True)
    return bas, arts, analiz


def sec(arts, analiz):
    """Önce analizin bağlantı verdiği haberler, sonra Türkiye ve en yeniler; konu çeşitliliği için kategori başına en fazla 2."""
    by_slug = {m["_slug"]: m for m in arts}
    aday = []
    if analiz:
        for s in re.findall(r"(?:\.\./|/haber/)(\d{4}-\d{2}-\d{2}-[a-z0-9-]+)/", analiz["_body"]):
            if s in by_slug and by_slug[s] not in aday:
                aday.append(by_slug[s])
    # Türk okur için Türkiye haberleri (en fazla 2) analiz bağlantılarının ilk 6'sından hemen sonra gelir
    aday = aday[:6] + [a for a in arts if a.get("kategori") == "Türkiye"][:2] + aday[6:] + arts
    secilen, sayac = [], {}
    for sinir in (2, 3):
        for m in aday:
            if len(secilen) >= EN_FAZLA:
                break
            k = m.get("kategori", "")
            if m not in secilen and sayac.get(k, 0) < sinir:
                secilen.append(m)
                sayac[k] = sayac.get(k, 0) + 1
    return secilen


def olustur(son):
    bas, arts, analiz = topla(son)
    if not arts:
        return None
    kampanya = "haftalik-" + son.isoformat()
    secilen = sec(arts, analiz)
    aralik = gun_araligi(bas, son)
    ana = analiz["baslik"] if analiz else "Haftanın önemli haberleri"
    ana = re.sub(r"^Haftanın Çerçevesi\s*\([^)]*\):\s*", "", ana)
    konu = "Farsçadan Haftalık (%s): %s" % (aralik, ana)
    s = ["Merhaba,", "",
         "İran'ın Farsça basınında %s haftası. Başlıklara tıklayınca haberin tamamı sitemizde açılır." % aralik, ""]
    if analiz:
        s += ["## Haftanın Çerçevesi", "",
              "**[%s](%s)**" % (analiz["baslik"], link(analiz["_slug"], kampanya)), "",
              analiz.get("ozet", ""), "",
              "[Analizin tamamını okuyun →](%s)" % link(analiz["_slug"], kampanya), ""]
    s += ["## Haftanın önemli haberleri", ""]
    for m in secilen:
        s.append("- **[%s](%s)**  " % (m["baslik"], link(m["_slug"], kampanya)))
        s.append("  %s *(%s)*" % (m.get("ozet", ""), m.get("kaynak_adi", "")))
        s.append("")
    s += ["---", "",
          "Bu hafta toplam %d haber yayımladık. Hepsi: [farscadan.com](%s/?utm_source=bulten&utm_medium=email&utm_campaign=%s) · X: [@farscadan](https://x.com/farscadan)"
          % (len(arts), BASE, kampanya), "",
          "*Farsçadan, İran'ın Farsça basınından seçilmiş haberlerin yapay zekâ destekli Türkçe çevirilerini yayımlar; "
          "içerikler Farsçadan Editörlüğü'nün denetimi altındadır. Her haberde kaynağın yönelimi belirtilir.*"]
    return konu, "\n".join(s), len(secilen), bool(analiz)


def anahtar():
    try:
        return subprocess.run(["security", "find-generic-password", "-a", "farscadan", "-s", "farscadan-buttondown", "-w"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def gonder(konu, govde, durum):
    key = anahtar()
    if not key:
        print("HATA: Keychain'de farscadan-buttondown anahtarı yok")
        sys.exit(4)
    req = urllib.request.Request(API, method="POST",
                                 data=json.dumps({"subject": konu, "body": govde, "status": durum}).encode("utf-8"),
                                 headers={"Authorization": "Token " + key, "Content-Type": "application/json",
                                          # 02.11: about_to_send bu başlığı ister (anahtar başına bir kez; her seferinde göndermek zararsız)
                                          "X-Buttondown-Live-Dangerously": "true"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            cevap = json.loads(r.read().decode("utf-8") or "{}")
            return cevap.get("id", "?"), cevap.get("status", durum)
    except urllib.error.HTTPError as e:
        print("HATA: Buttondown %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:500]))
        sys.exit(5)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    son = dt.date.fromisoformat(args[0]) if args else dt.date.today()
    sonuc = olustur(son)
    if not sonuc:
        print("bu hafta haber yok:", son)
        sys.exit(2)
    konu, govde, adet, analiz_var = sonuc
    kayit = os.path.join(ROOT, "rutin", "kayit", "bulten-%s.md" % son.isoformat())
    gonderildi = os.path.exists(kayit) and "Gönderim: gönderildi" in open(kayit, encoding="utf-8").read()
    durum = "about_to_send" if "--gonder" in sys.argv else ("draft" if "--taslak" in sys.argv else None)
    if durum == "about_to_send" and gonderildi:
        print("bu hafta zaten gönderildi:", kayit)
        sys.exit(3)
    satir = "Gönderim: önizleme (gönderilmedi)"
    if durum:
        eid, st = gonder(konu, govde, durum)
        satir = ("Gönderim: gönderildi (Buttondown %s, %s, %s)" if durum == "about_to_send"
                 else "Gönderim: taslak oluşturuldu (Buttondown %s, %s, %s)") % (eid, st, dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
    with open(kayit, "w", encoding="utf-8") as f:
        f.write("# Haftalık Bülten — %s\n\n%s\nKonu: %s\nHaber: %d · Analiz: %s\n\n---\n\n%s\n"
                % (son.isoformat(), satir, konu, adet, "var" if analiz_var else "yok", govde))
    print(satir)
    print("Konu:", konu)
    print("Kayıt:", kayit)


if __name__ == "__main__":
    main()
