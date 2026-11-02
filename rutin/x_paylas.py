#!/usr/bin/env python3
"""X (@farscadan) otomatik paylaşım — OAuth 1.0a, yalnızca standart kütüphane (02.11).

Kullanım:
  python3 rutin/x_paylas.py --kontrol                      → kimlik doğrulama testi (GET /2/users/me, gönderi atmaz)
  python3 rutin/x_paylas.py --gonder "metin" [--gorsel yol.png] [--prova]
       --prova: hiçbir şey göndermez, yalnızca ne gönderileceğini ve günlük sayacı gösterir.

Anahtarlar yalnızca Keychain'de (hesap: farscadan):
  farscadan-x-api-key, farscadan-x-api-secret, farscadan-x-access-token, farscadan-x-access-secret
Beyan edilen kapsam (geliştirici başvurusu): yalnızca kendi hesabımızda kendi içeriğimizi paylaşmak.
Okuma/DM/otomatik etkileşim YOK. Günlük tavan: GUNLUK_TAVAN gönderi (kredi koruması).
Kayıt: ~/farscadan/state/x-gonderim.log (depo dışında).
"""
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GUNLUK_TAVAN = 6
KAYIT = os.path.expanduser("~/farscadan/state/x-gonderim.log")
API = "https://api.x.com"


def anahtar(ad):
    try:
        return subprocess.run(["security", "find-generic-password", "-a", "farscadan", "-s", ad, "-w"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError:
        sys.exit("HATA: Keychain'de %s yok" % ad)


def q(s):
    return urllib.parse.quote(str(s), safe="~-._")


def oauth_baslik(method, url, params=None):
    ck, cs = anahtar("farscadan-x-api-key"), anahtar("farscadan-x-api-secret")
    tk, ts = anahtar("farscadan-x-access-token"), anahtar("farscadan-x-access-secret")
    o = {"oauth_consumer_key": ck, "oauth_nonce": secrets.token_hex(16), "oauth_signature_method": "HMAC-SHA1",
         "oauth_timestamp": str(int(time.time())), "oauth_token": tk, "oauth_version": "1.0"}
    tum = dict(o)
    tum.update(params or {})
    temel = "&".join([method.upper(), q(url), q("&".join("%s=%s" % (q(k), q(v)) for k, v in sorted(tum.items())))])
    imza = base64.b64encode(hmac.new(("%s&%s" % (q(cs), q(ts))).encode(), temel.encode(), hashlib.sha1).digest()).decode()
    o["oauth_signature"] = imza
    return "OAuth " + ", ".join('%s="%s"' % (q(k), q(v)) for k, v in sorted(o.items()))


def istek(method, url, govde=None, icerik_tipi=None, params=None):
    tam = url + ("?" + urllib.parse.urlencode(params) if params else "")
    h = {"Authorization": oauth_baslik(method, url, params)}
    if icerik_tipi:
        h["Content-Type"] = icerik_tipi
    req = urllib.request.Request(tam, data=govde, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, dict(r.headers), json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")[:800]


def bugunku_sayi():
    if not os.path.exists(KAYIT):
        return 0
    bugun = dt.date.today().isoformat()
    return sum(1 for l in open(KAYIT, encoding="utf-8") if l.startswith(bugun) and " OK " in l)


def kaydet(satir):
    os.makedirs(os.path.dirname(KAYIT), exist_ok=True)
    with open(KAYIT, "a", encoding="utf-8") as f:
        f.write("%s %s\n" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M"), satir))


def gorsel_yukle(yol):
    """v2 medya yükleme (tek parça, multipart/form-data)."""
    sinir = "----frs" + secrets.token_hex(8)
    veri = open(yol, "rb").read()
    tip = "image/png" if yol.lower().endswith(".png") else "image/jpeg"
    parca = (("--%s\r\nContent-Disposition: form-data; name=\"media_category\"\r\n\r\ntweet_image\r\n" % sinir).encode()
             + ("--%s\r\nContent-Disposition: form-data; name=\"media\"; filename=\"%s\"\r\nContent-Type: %s\r\n\r\n"
                % (sinir, os.path.basename(yol), tip)).encode() + veri + ("\r\n--%s--\r\n" % sinir).encode())
    kod, _, cevap = istek("POST", API + "/2/media/upload", parca, "multipart/form-data; boundary=" + sinir)
    if kod not in (200, 201) or not isinstance(cevap, dict):
        sys.exit("HATA: görsel yüklenemedi (%s): %s" % (kod, cevap))
    mid = (cevap.get("data") or {}).get("id") or cevap.get("media_id_string")
    if not mid:
        sys.exit("HATA: medya kimliği yok: %s" % cevap)
    return mid


def main():
    a = sys.argv[1:]
    if "--kontrol" in a:
        kod, h, cevap = istek("GET", API + "/2/users/me")
        print("HTTP", kod)
        print("kullanıcı:", cevap.get("data") if isinstance(cevap, dict) else cevap)
        erisim = {k: v for k, v in h.items() if "access-level" in k.lower()}
        if erisim:
            print("erişim düzeyi:", erisim)
        return
    if "--gonder" not in a:
        sys.exit(__doc__)
    metin = a[a.index("--gonder") + 1]
    gorsel = a[a.index("--gorsel") + 1] if "--gorsel" in a else None
    sayi = bugunku_sayi()
    print("bugün gönderilen: %d / tavan %d" % (sayi, GUNLUK_TAVAN))
    import re
    uzunluk = len(re.sub(r"https?://\S+", "x" * 23, metin))  # X her bağlantıyı 23 karakter sayar
    if uzunluk > 280:
        sys.exit("HATA: metin 280 karakteri aşıyor (%d)" % uzunluk)
    if "--prova" in a:
        print("PROVA — gönderilmedi:\n%s\n[görsel: %s]" % (metin, gorsel or "yok"))
        return
    if sayi >= GUNLUK_TAVAN:
        kaydet("ATLANDI tavan dolu: " + metin[:60].replace("\n", " "))
        sys.exit("günlük tavan dolu, gönderilmedi")
    govde = {"text": metin}
    if gorsel:
        govde["media"] = {"media_ids": [gorsel_yukle(gorsel)]}
    kod, _, cevap = istek("POST", API + "/2/tweets", json.dumps(govde).encode(), "application/json")
    if kod in (200, 201) and isinstance(cevap, dict) and cevap.get("data"):
        tid = cevap["data"]["id"]
        kaydet("OK %s %s" % (tid, metin[:60].replace("\n", " ")))
        print("GONDERILDI https://x.com/i/status/%s" % tid)
    else:
        kaydet("HATA %s %s" % (kod, str(cevap)[:200].replace("\n", " ")))
        sys.exit("HATA: gönderilemedi (%s): %s" % (kod, cevap))


if __name__ == "__main__":
    main()
