#!/usr/bin/env python3
"""Günün Özeti görseli: günün haber başlıkları + kısa açıklamaları (X paylaşımı için).

Kullanım: python3 rutin/ozet_karti.py [YYYY-MM-DD] [--lang tr|en]
Çıktı:    static/x/ozet/<tarih>.png  (en: <tarih>-en.png), 1080x1350 (4:5)
Kaynak:   content/haberler/<tarih>-*.md (en: content/en/haberler/), tarih alanına göre yeniden eskiye.
Çıkış kodu 2: o gün haber yok.
"""
import datetime as dt
import glob
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1350
BG, GOLD, WHITE, MUTED, LINE = (15, 95, 92), (241, 211, 155), (255, 255, 255), (200, 226, 223), (60, 130, 126)
FD = "/System/Library/Fonts/Supplemental/"
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
TXT = {
    "tr": {"kicker": "GÜNÜN ÖZETİ", "sub": "İran'ın Farsça basınından bugün", "more": "Haberlerin tamamı"},
    "en": {"kicker": "TODAY IN BRIEF", "sub": "From Iran's Persian-language press today", "more": "Full stories at"},
}


def font(name, size):
    try:
        return ImageFont.truetype(FD + name, size)
    except OSError:
        return ImageFont.load_default()


def front_matter(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---", t, re.S)
    meta = {}
    for line in (m.group(1) if m else "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta


def wrap(draw, text, fnt, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while draw.textlength(last + "…", font=fnt) > width and " " in last:
            last = last.rsplit(" ", 1)[0]
        lines[-1] = last.rstrip(".,;:") + "…"
    return lines


def tarih_yazi(d, lang):
    if lang == "en":
        return d.strftime("%A, %B ") + str(d.day) + d.strftime(", %Y")
    return "%d %s %d, %s" % (d.day, AYLAR[d.month - 1], d.year, GUNLER[d.weekday()])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    lang = "en" if "--lang" in sys.argv and sys.argv[sys.argv.index("--lang") + 1] == "en" else "tr"
    gun = args[0] if args else dt.date.today().isoformat()
    d = dt.date.fromisoformat(gun)
    src = os.path.join(ROOT, "content", "en" if lang == "en" else "", "haberler")
    files = [f for f in glob.glob(os.path.join(src, gun + "-*.md")) if not os.path.basename(f).startswith("_")]
    if not files:
        print("bu tarihte haber yok:", gun)
        sys.exit(2)
    items = sorted((front_matter(f) for f in files), key=lambda m: m.get("tarih", ""), reverse=True)[:6]

    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)
    f_word, f_kick, f_date = font("Georgia Bold.ttf", 44), font("Arial Bold.ttf", 26), font("Georgia.ttf", 30)
    f_sub, f_head, f_desc = font("Georgia Italic.ttf", 26), font("Georgia Bold.ttf", 33), font("Arial.ttf", 23)
    f_num, f_foot = font("Georgia Bold.ttf", 28), font("Arial Bold.ttf", 26)
    M = 70

    # Üst bant: logo + başlık + tarih
    dr.rounded_rectangle([M, 62, M + 56, 118], radius=12, fill=GOLD)
    dr.text((M + 28, 90), "F", font=font("Georgia Bold.ttf", 38), fill=BG, anchor="mm")
    dr.text((M + 76, 90), "Farsçadan", font=f_word, fill=WHITE, anchor="lm")
    dr.text((W - M, 90), TXT[lang]["kicker"], font=f_kick, fill=GOLD, anchor="rm")
    dr.text((M, 168), tarih_yazi(d, lang), font=f_date, fill=WHITE)
    dr.text((M, 210), TXT[lang]["sub"], font=f_sub, fill=MUTED)
    dr.rectangle([M, 262, W - M, 265], fill=GOLD)

    # Haberler
    top, bottom = 295, H - 120
    slot = (bottom - top) / max(len(items), 1)
    for i, m in enumerate(items):
        y = top + i * slot
        cx, cy = M + 22, y + 26
        dr.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], outline=GOLD, width=3)
        dr.text((cx, cy), str(i + 1), font=f_num, fill=GOLD, anchor="mm")
        x, w = M + 70, W - M - (M + 70)
        hl = wrap(dr, m.get("baslik", "").strip('"'), f_head, w, 2)
        for j, line in enumerate(hl):
            dr.text((x, y + j * 40), line, font=f_head, fill=WHITE)
        dy = y + len(hl) * 40 + 8
        for j, line in enumerate(wrap(dr, m.get("ozet", ""), f_desc, w, 2)):
            dr.text((x, dy + j * 30), line, font=f_desc, fill=MUTED)
        if i < len(items) - 1:
            dr.line([x, y + slot - 14, W - M, y + slot - 14], fill=LINE, width=1)

    # Alt bant
    dr.rectangle([M, H - 100, W - M, H - 98], fill=GOLD)
    dr.text((M, H - 55), TXT[lang]["more"] + "  farscadan.com" + ("/en" if lang == "en" else ""), font=f_foot, fill=GOLD, anchor="lm")
    dr.text((W - M, H - 55), "@farscadancom", font=font("Arial.ttf", 24), fill=MUTED, anchor="rm")

    out_dir = os.path.join(ROOT, "static", "x", "ozet")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, gun + ("-en" if lang == "en" else "") + ".png")
    im.save(out, optimize=True)
    print(out)


if __name__ == "__main__":
    main()
