# Farsçadan — statik site

Farsça İran basınından yapay zekâ destekli Türkçe çeviriler. Tamamen statik: admin paneli, sunucu kodu, giriş yok. İçerik yalnızca bu klasördeki dosyalarla yönetilir.

Gereksinim: Python 3.9+ (yalnızca standart kütüphane). Pillow yalnızca örnek görseli üretmek için kullanıldı; derleme için gerekmez.

## Klasörler

| Yol | Açıklama |
|-----|----------|
| `site.json` | Site ayarları |
| `content/haberler/*.md` | Haber dosyaları (format: `ICERIK_SOZLESMESI.md`) |
| `static/` | CSS, favicon, görseller → olduğu gibi `public/` köküne kopyalanır |
| `build.py` | Site üreticisi |
| `check_links.py` | İç bağlantı + XML doğrulayıcı |
| `public/` | Çıktı (her derlemede silinip yeniden üretilir; elle düzenlemeyin) |

## Haber ekleme

1. Görseli `static/img/YYYY-MM-DD-<slug>.jpg` olarak koyun (özgür lisanslı, en fazla 1200 px).
2. `content/haberler/YYYY-MM-DD-<slug>.md` dosyasını `ICERIK_SOZLESMESI.md`'deki front matter ile oluşturun. Sayfa adresi dosya adından gelir: `haber/YYYY-MM-DD-<slug>/`.
3. Derleyin ve bağlantıları kontrol edin.

Zorunlu alanlar: `baslik`, `ozet`, `tarih`, `kategori`, `kaynak_adi`, `kaynak_url`. Eksik alanlı ya da geçersiz kategorili dosyalar uyarıyla atlanır; görsel dosyası bulunamazsa haber görselsiz yayımlanır.

`_` ile başlayan dosyalar (ör. `_ornek-1.md`) ve `static/` içindeki `_` ile başlayan dosyalar üretim derlemesinde **atlanır**.

## Derleme ve önizleme

```sh
python3 build.py              # üretim derlemesi
python3 build.py --ornek      # _ornek-*.md test haberleri dahil
python3 check_links.py        # iç bağlantılar, sitemap.xml ve feed.xml doğrulaması
python3 -m http.server -d public 8000   # http://localhost:8000
```

Tüm iç bağlantılar göreli olduğundan site bir alt yoldan da çalışır (ör. `https://kullanici.github.io/farscadan/`). Mutlak adresler (canonical, OG, sitemap, RSS, iletişim formu yönlendirmesi ve `404.html` içindeki bağlantılar) `base_url` ile üretilir.

## site.json anahtarları

| Anahtar | Açıklama |
|---------|----------|
| `site_name` | Site adı (“Farsçadan”) |
| `tagline` | Başlık altındaki slogan |
| `base_url` | Mutlak URL kökü, sonda `/` olmadan (`https://farscadan.com`) |
| `description` | Ana sayfa meta açıklaması ve RSS açıklaması |
| `language` | `tr` |
| `form_endpoint` | FormSubmit uç noktası (e-posta adresi ya da FormSubmit'in verdiği rastgele kimlik). Boşsa iletişim sayfasında “İletişim formu yakında aktif olacak” yazar. E-posta adresi sayfada görünmemesi için FormSubmit'in rastgele kimliği tercih edilmeli. |
| `adsense_client` | Boşsa hiçbir reklam kodu üretilmez. `pub-XXXX` veya `ca-pub-XXXX` girilirse `<head>`'e AdSense otomatik reklam betiği eklenir ve `ads.txt` üretilir. |
| `analytics` | Boşsa ölçüm kodu yok. GA4 ölçüm kimliği (`G-XXXX`) girilirse gtag betiği eklenir. |

## Reklam yerleri

Haber şablonunda `<!-- AD_SLOT: ... -->` yorumları vardır (2. paragraftan sonra, haber sonu, yan sütun). Şu an hiçbir şey göstermezler; manuel reklam birimi eklemek istenirse `build.py` içindeki bu yorumlar değiştirilir.

## Yayın (GitHub Pages)

`public/` klasörünün içeriği yayımlanır (`.nojekyll` dahildir). Özel alan adı bağlanınca `static/CNAME` dosyasına `farscadan.com` yazmak yeterlidir.
