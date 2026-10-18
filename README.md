# Farsçadan — statik site

Farsça İran basınından yapay zekâ destekli Türkçe çeviriler. Tamamen statik: admin paneli, sunucu kodu, giriş yok. İçerik yalnızca bu klasördeki dosyalarla yönetilir.

Gereksinim: Python 3.9+ (standart kütüphane). Pillow, derlemede görsel `width`/`height` değerleri için (yoksa atlanır) ve `rutin/kart_uret.py` için kullanılır.

Site iki dillidir: **Türkçe kökte**, **İngilizce `/en/` altında**. Arayüz metinleri `build.py` içindeki `T` sözlüğündedir (dil başına bir anahtar seti).

## Klasörler

| Yol | Açıklama |
|-----|----------|
| `site.json` | Site ayarları |
| `content/haberler/*.md` | Türkçe haber dosyaları (format: `ICERIK_SOZLESMESI.md`) |
| `content/en/haberler/*.md` | İngilizce haberler; dosya adı Türkçe karşılığıyla aynı (bkz. sözleşmenin “İngilizce sürüm” bölümü) |
| `content/sozluk/*.md` | Türkçe sözlük maddeleri (format: sözleşmenin “Sözlük” bölümü) |
| `content/en/sozluk/*.md` | İngilizce sözlük maddeleri; slug Türkçe karşılığıyla aynı |
| `rutin/kart_uret.py` | Çerçeve kartı (1200×675 PNG) üretici |
| `static/` | CSS, favicon, görseller → olduğu gibi `public/` köküne kopyalanır |
| `build.py` | Site üreticisi |
| `check_links.py` | İç bağlantı, `lang`, hreflang ve XML/sitemap doğrulayıcı |
| `public/` | Çıktı (her derlemede silinip yeniden üretilir; elle düzenlemeyin) |

## Haber ekleme

1. Görseli `static/img/YYYY-MM-DD-<slug>.jpg` olarak koyun (özgür lisanslı, en fazla 1200 px).
2. `content/haberler/YYYY-MM-DD-<slug>.md` dosyasını `ICERIK_SOZLESMESI.md`'deki front matter ile oluşturun. Sayfa adresi dosya adından gelir: `haber/YYYY-MM-DD-<slug>/`.
3. Derleyin ve bağlantıları kontrol edin.

Zorunlu alanlar: `baslik`, `ozet`, `tarih`, `kategori`, `kaynak_adi`, `kaynak_url`. Eksik alanlı ya da geçersiz kategorili dosyalar uyarıyla atlanır; görsel dosyası bulunamazsa haber görselsiz yayımlanır.

Kategori `Analiz` özgün haftalık analizler içindir (“Haftanın Çerçevesi”, sözleşmenin “Özgün içerik” bölümü). Analiz yazıları kartta ve haberde ayırt edici **ANALİZ / ANALYSIS** etiketiyle gösterilir. JSON-LD türü `AnalysisNewsArticle` olur. Kaynak kutusunda “Farsçadan özgün analizi” yazar ve “Özgün haberi oku” bağlantısı çıkmaz. `ek_kaynaklar` “Bu haftanın kaynakları” listesi olur: Farsçadan haber adresleri başlıklarıyla ve göreli bağlantıyla basılır. Kapanış notu da çeviri notu yerine analiz notudur.

`_` ile başlayan dosyalar (ör. `_ornek-1.md`, `sozluk/_test.md`) ve `static/` içindeki `_` ile başlayan dosyalar üretim derlemesinde **atlanır**.

## Çıktı yapısı

| Türkçe | İngilizce | Not |
|--------|-----------|-----|
| `/` | `/en/` | Ana sayfa |
| `haber/<slug>/` | `en/haber/<slug>/` | Aynı slug; iki dilde varsa hreflang ile eşlenir |
| `kategori/<slug>/` | `en/kategori/<slug>/` | Aynı ASCII slug; adlar İngilizce gösterilir (Security, Economy…) |
| `konu/<etiket-slug>/` | `en/konu/<etiket-slug>/` | Her etiket için konu sayfası (≥ 1 haber). **3'ten az haberli** konular `noindex, follow` alır ve `sitemap.xml`'e girmez (ince sayfa denetimi, `TOPIC_MIN`) |
| `kategori/analiz/` | `en/kategori/analiz/` | Analiz kategorisi. Herhangi bir kategori boşsa sayfası `noindex` alır ve sitemap dışında kalır |
| `sozluk/` | `en/glossary/` | Sözlük A–Z dizini (harf atlama, terim + özet, `DefinedTermSet` JSON-LD). Dilde hiç madde yoksa `noindex` |
| `sozluk/<slug>/` | `en/glossary/<slug>/` | Madde sayfası (aşağıya bakın) |
| `konular/` | `en/topics/` | Konu dizini (etiket + haber sayısı), alt menüden bağlı. Tüm etiketler listelenir; 3'ten az haberliler küçük gösterilir |
| `hakkimizda/`, `yayin-ilkeleri/`, `editor/`, `iletisim/` (+`tesekkurler/`), `gizlilik/` | `en/about/`, `en/editorial-standards/`, `en/editor/`, `en/contact/` (+`thanks/`), `en/privacy/` | Statik sayfalar |
| `feed.xml` | `en/feed.xml` | RSS |

Etiket slug'ı: ç→c ğ→g ı/İ→i ö→o ş→s ü→u, küçük harf, harf/rakam dışı → `-`.

## Sözlük

Madde dosyası: `content/sozluk/<slug>.md` (EN: `content/en/sozluk/<slug>.md`, aynı slug). Front matter alanları şunlardır: `terim`, `ozet`, `esanlamlar` (virgülle), `farsca`, `kaynaklar` (`Ad | url ;; Ad | url`) ve `guncelleme` (YYYY-MM-DD). Gövde, haberlerle aynı Markdown alt kümesini kullanır. `terim` ya da `ozet` eksikse dosya uyarıyla atlanır.

- **Madde sayfası:** H1 terimdir. `farsca` varsa altında `dir="rtl" lang="fa"` satırı gelir. Ardından özet, gövde, “Kaynaklar” listesi ve “Son güncelleme” gelir. Sayfada `DefinedTerm` (`inDefinedTermSet` = dizin adresi) ve `BreadcrumbList` JSON-LD'si bulunur. `<title>` “X nedir?” / “What is X?” biçimindedir. İki dilde de bulunan maddeler hreflang ile eşlenir; dil seçici sözlükten sözlüğe gider.
- **Eşleşme:** Eşleşme ifadeleri `esanlamlar` ile terimin parantez dışı kısmından oluşur. Karşılaştırma büyük/küçük harfe duyarsızdır ve Türkçe kurallarına uyar (I/ı, İ/i). İfade kelime başında aranır. Türkçede 5 harf ve üzeri ifadeler ek alabilir (kalabargı, Devrim Muhafızları'nın); İngilizcede -s/-es/'s eki kabul edilir. Haber başlığı ve gövdesi taranır; bağlantı adresleri taranmaz.
- **İlgili haberler:** Aynı dilde maddenin geçtiği haberler, yeniden eskiye ve en fazla 12 tanesi kart olarak gösterilir.
- **Haber sayfası:** Haber eşleşen maddeleri ilk geçiş sırasıyla gösteren bir “Kavramlar” / “Key terms” kutusu alır (en fazla 5). Gövdede her maddenin ilk geçişi sözlüğe bağlanır (`a.gloss-link`, haber başına en fazla 3). Mevcut bağlantıların içinde, başlıklarda ve tablolarda bağlantı kurulmaz. JSON-LD'ye `mentions` eklenir.
- Üst menüde “Sözlük”, alt menüde sözlük bağlantısı bulunur. Maddeler `sitemap.xml`'e (`lastmod` = `guncelleme`, xhtml alternatifleriyle) eklenir.

**Site haritası kuralı:** `noindex` üretilen hiçbir sayfa `sitemap.xml`'e girmez. Alternatiflerinden biri `noindex` olan girdiye `xhtml:link` yazılmaz. `build.py` çıktısı dil başına indeksli/noindex konu sayısını ve sözlük madde sayılarını da yazar.

**Dil seçici (TR | EN)** her sayfanın başlığında. Haber iki dilde varsa karşılık habere, tek dildeyse diğer dilin ana sayfasına gider; statik sayfalar, kategoriler ve konu dizini karşılıklarına; tek tek konu sayfaları diğer dilin konu dizinine gider.

**hreflang:** Karşılığı olan her sayfada `tr`, `en` ve `x-default` (→ Türkçe) alternatifleri; `og:locale` `tr_TR`/`en_US`. `sitemap.xml` iki dili ve `xhtml:link` alternatiflerini, `news-sitemap.xml` son 48 saatin iki dildeki haberlerini (`news:language`) içerir. İngilizce haber gövdesindeki `../<slug>/` bağlantısının İngilizcesi yoksa bağlantı Türkçe habere çevrilir.

**Paylaşım düğmeleri:** Her haberde başlığın altında ve gövdenin sonunda WhatsApp, X (`via` = `x_hesap`), Telegram ve “Bağlantıyı kopyala” (küçük satır içi betik; JS yoksa gizli kalır). Üçüncü taraf betik yoktur.

## Çerçeve kartı

```sh
python3 rutin/kart_uret.py <slug>            # → static/x/kart/<slug>.png
python3 rutin/kart_uret.py <slug> --lang en  # → static/x/kart/<slug>-en.png
```

Haberdeki ilk karşılaştırma tablosundan (`| Kaynak (yönelim) | Başlık / çerçeve |`) ilk 3 satırı alır; 1200×675, #0f5f5c zemin, beyaz + altın (#f1d39b) metin, Georgia/Arial (yoksa Pillow varsayılanı). Tablo yoksa çıkış kodu 2.

## Derleme ve önizleme

```sh
python3 build.py              # üretim derlemesi
python3 build.py --ornek      # _ornek-*.md test haberleri dahil
python3 check_links.py        # iç bağlantılar, lang, hreflang, sitemap/news-sitemap ve iki feed doğrulaması;
                              # ayrıca: sitemap'te noindex sayfa yok, konu noindex eşiği (< 3 haber),
                              # sözlük JSON-LD (DefinedTerm/inDefinedTermSet, Breadcrumb) + hreflang eşleri,
                              # Analiz yazılarında AnalysisNewsArticle ve "özgün haberi oku" yokluğu
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
