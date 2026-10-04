#!/usr/bin/env python3
"""Çerçeve kartı üretici: haberin "aynı olay, farklı manşet" tablosundan 1200×675 PNG kart.

Kullanım:
    python3 rutin/kart_uret.py <slug> [--lang tr|en]

Girdi : content/haberler/<slug>.md  (tr)  veya  content/en/haberler/<slug>.md  (en)
Çıktı : static/x/kart/<slug>.png    (tr)  veya  static/x/kart/<slug>-en.png    (en)
Çıkış kodları: 0 = kart üretildi, 1 = dosya/argüman hatası, 2 = haberde karşılaştırma tablosu yok.

Gereksinim: Pillow. Yazı tipleri macOS Supplemental (Georgia, Arial); yoksa Pillow varsayılanı.
"""
import os
import re
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    print("Pillow gerekli: pip3 install Pillow", file=sys.stderr)
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "static", "x", "kart")

W, H = 1200, 675
PAD_X, PAD_Y = 64, 48
BG = (15, 95, 92)          # #0f5f5c
WHITE = (255, 255, 255)
GOLD = (241, 211, 155)     # #f1d39b
GOLD_SOFT = (241, 211, 155, 190)
LINE = (255, 255, 255, 46)

FONT_DIR = "/System/Library/Fonts/Supplemental"
FONTS = {
    "serif_bold": "Georgia Bold.ttf",
    "serif": "Georgia.ttf",
    "sans_bold": "Arial Bold.ttf",
    "sans": "Arial.ttf",
}
KICKER = {"tr": "AYNI OLAY, FARKLI MANŞET", "en": "SAME STORY, DIFFERENT HEADLINES"}

_warned = set()


def font(kind, size):
    path = os.path.join(FONT_DIR, FONTS[kind])
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        if kind not in _warned:
            print("UYARI: yazı tipi bulunamadı (%s); varsayılan kullanılıyor" % path, file=sys.stderr)
            _warned.add(kind)
        try:
            return ImageFont.load_default(size=size)  # Pillow ≥ 10.1
        except TypeError:
            return ImageFont.load_default()


def clean(text):
    """Markdown işaretlerini temizler (tırnaklar kalır)."""
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    t = t.replace("**", "").replace("__", "")
    t = re.sub(r"(?<!\w)\*(\S.*?\S|\S)\*(?!\w)", r"\1", t)
    t = t.replace("`", "")
    t = re.sub(r"\s+", " ", t).strip()
    return smart_quotes(t)


def smart_quotes(t):
    """Düz tırnakları tipografik tırnağa çevirir: "x" → “x”, Trump's → Trump’s."""
    t = re.sub(r'(^|[\s(\[{—–-])"', "\\1\u201c", t)
    t = t.replace('"', "\u201d")
    t = re.sub(r"(^|[\s(\[{—–-])'", "\\1\u2018", t)
    return t.replace("'", "\u2019")


def read_article(slug, lang):
    sub = ("content", "en", "haberler") if lang == "en" else ("content", "haberler")
    path = os.path.join(ROOT, *sub, slug + ".md")
    if not os.path.isfile(path):
        print("Haber dosyası yok: %s" % os.path.relpath(path, ROOT), file=sys.stderr)
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        text = f.read().lstrip("﻿")
    parts = re.split(r"^---[ \t]*$", text, maxsplit=2, flags=re.M)
    if len(parts) < 3:
        print("Front matter okunamadı: %s" % path, file=sys.stderr)
        sys.exit(1)
    meta = {}
    for line in parts[1].split("\n"):
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            meta[k.strip()] = v
    return meta, parts[2]


def find_table(body):
    """İlk karşılaştırma tablosunun veri satırları: [(kaynak, yönelim, başlık), ...]."""
    block, tables = [], []
    for raw in body.split("\n") + [""]:
        s = raw.strip()
        if s.startswith("|") and s.endswith("|"):
            block.append(s)
        elif block:
            tables.append(block)
            block = []
    for tb in tables:
        cells = [[c.strip() for c in r.strip("|").split("|")] for r in tb
                 if not re.match(r"^\|?\s*:?-{3,}", r)]
        if len(cells) < 2 or len(cells[0]) < 2:
            continue
        rows = []
        for r in cells[1:]:
            if len(r) < 2:
                continue
            src = clean(r[0])
            m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", src)
            name, ori = (m.group(1), m.group(2)) if m else (src, "")
            head = clean(" ".join(r[1:]))
            if name and head:
                rows.append((name, ori, head))
        if rows:
            return rows
    return []


def wrap(draw, text, fnt, width, max_lines):
    """Kelime kaydırma; satır sınırını aşarsa son satır '…' ile kısaltılır."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    # Tek kelime bile sığmıyorsa harf harf kısalt
    lines = [fit(draw, ln, fnt, width) if draw.textlength(ln, font=fnt) > width else ln for ln in lines]
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        lines = lines[:max_lines]
        lines[-1] = ellipsize(draw, last + " " + "x", fnt, width, force=True)
    return lines


def fit(draw, text, fnt, width):
    while text and draw.textlength(text + "…", font=fnt) > width:
        text = text[:-1]
    return text + "…"


def ellipsize(draw, text, fnt, width, force=False):
    words = text.split()
    if force:
        words = words[:-1]
    while words:
        cand = " ".join(words).rstrip(",;:.–—-") + "…"
        if draw.textlength(cand, font=fnt) <= width:
            return cand
        words = words[:-1]
    return fit(draw, text, fnt, width)


def render(meta, rows, lang, out_path):
    img = Image.new("RGB", (W, H), BG)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    d = ImageDraw.Draw(img)
    inner = W - 2 * PAD_X

    # Wordmark: altın kare içinde "F" + "Farsçadan"
    y = PAD_Y
    mark = 40
    d.rounded_rectangle((PAD_X, y, PAD_X + mark, y + mark), radius=8, fill=GOLD)
    fm = font("serif_bold", 28)
    bb = d.textbbox((0, 0), "F", font=fm)
    d.text((PAD_X + (mark - (bb[2] - bb[0])) / 2 - bb[0], y + (mark - (bb[3] - bb[1])) / 2 - bb[1]),
           "F", font=fm, fill=BG)
    fw = font("serif_bold", 32)
    bb = d.textbbox((0, 0), "Farsçadan", font=fw)
    d.text((PAD_X + mark + 14, y + (mark - (bb[3] - bb[1])) / 2 - bb[1]), "Farsçadan", font=fw, fill=WHITE)

    # Kicker (sağ üst, harf aralıklı)
    fk = font("sans_bold", 17)
    kick = KICKER[lang]
    spacing = 2.2
    kw = sum(d.textlength(ch, font=fk) for ch in kick) + spacing * (len(kick) - 1)
    kx = W - PAD_X - kw
    bbk = d.textbbox((0, 0), "A", font=fk)
    ky = y + (mark - (bbk[3] - bbk[1])) / 2 - bbk[1]
    for ch in kick:
        d.text((kx, ky), ch, font=fk, fill=GOLD)
        kx += d.textlength(ch, font=fk) + spacing

    # Başlık (en fazla 2 satır)
    y = PAD_Y + mark + 34
    ft = font("serif_bold", 40)
    title = clean(meta.get("baslik", ""))
    for ln in wrap(d, title, ft, inner, 2):
        d.text((PAD_X, y), ln, font=ft, fill=WHITE)
        y += 50
    y += 14
    od.line((PAD_X, y, W - PAD_X, y), fill=(241, 211, 155, 150), width=2)
    y += 22

    # Satırlar: sol sütun kaynak + yönelim (altın), sağ sütun manşet (beyaz, ≤ 2 satır)
    rows = rows[:3]
    col = 270
    gap = 28
    fs_name = font("sans_bold", 20)
    fs_ori = font("sans", 16)
    fh = font("serif", 26)
    foot_top = H - PAD_Y - 22
    avail = foot_top - 18 - y
    row_h = min(116, avail // max(1, len(rows)))
    for i, (name, ori, head) in enumerate(rows):
        ry = y + i * row_h
        nl = wrap(d, name, fs_name, col - 10, 1)[0]
        d.text((PAD_X, ry + 4), nl, font=fs_name, fill=GOLD)
        if ori:
            ol = wrap(d, ori, fs_ori, col - 10, 2)
            oy = ry + 32
            for ln in ol:
                od.text((PAD_X, oy), ln, font=fs_ori, fill=GOLD_SOFT)
                oy += 21
        hy = ry
        for ln in wrap(d, head, fh, inner - col - gap, 2):
            d.text((PAD_X + col + gap, hy), ln, font=fh, fill=WHITE)
            hy += 35
        if i < len(rows) - 1:
            ly = ry + row_h - 16
            od.line((PAD_X, ly, W - PAD_X, ly), fill=LINE, width=1)

    # Alt bilgi
    ff = font("sans_bold", 20)
    bb = d.textbbox((0, 0), "farscadan.com", font=ff)
    d.text((PAD_X, H - PAD_Y - (bb[3] - bb[1]) - bb[1]), "farscadan.com", font=ff, fill=GOLD)
    fx = font("sans", 17)
    handle = "@farscadancom"
    bbh = d.textbbox((0, 0), handle, font=fx)
    od.text((W - PAD_X - (bbh[2] - bbh[0]) - bbh[0], H - PAD_Y - (bbh[3] - bbh[1]) - bbh[1]),
            handle, font=fx, fill=(255, 255, 255, 170))

    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    lang = "tr"
    if "--lang" in argv:
        i = argv.index("--lang")
        lang = argv[i + 1] if i + 1 < len(argv) else ""
        args = [a for a in args if a != lang]
    elif any(a.startswith("--lang=") for a in argv):
        lang = [a for a in argv if a.startswith("--lang=")][0].split("=", 1)[1]
    if len(args) != 1 or lang not in ("tr", "en"):
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 1
    slug = args[0].strip("/").split("/")[-1]
    if slug.endswith(".md"):
        slug = slug[:-3]
    meta, body = read_article(slug, lang)
    rows = find_table(body)
    if not rows:
        print("Tablo yok: %s (%s) haberinde karşılaştırma tablosu bulunamadı; kart üretilmedi." % (slug, lang))
        return 2
    out = os.path.join(OUT_DIR, slug + ("-en" if lang == "en" else "") + ".png")
    render(meta, rows, lang, out)
    print("Kart üretildi: %s (%d satır, %s)" % (os.path.relpath(out, ROOT), min(3, len(rows)), lang))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
