# İçerik Sözleşmesi — Farsçadan (farscadan.com)

İki agent arasındaki arayüzü tanımlar:
- **İran Basın İzleme** haberleri yazar ve `content/haberler/` klasörüne koyar.
- **Web Yayın** siteyi bu dosyalardan üretir.

Bu dosya iki tarafın da uyması gereken tek formattır.

## Haber dosyası
Yol: `content/haberler/YYYY-MM-DD-<slug>.md`. Slug yalnızca küçük harf, rakam ve tire içerir; Türkçe karakter kullanılmaz.

```
---
baslik: Hürmüz'de tanker saldırısı: kaynaklar arasında sayı tutmuyor
ozet: Umman açıklarında bir tankerin vurulduğu bildirildi; Farsça basında saldırının boyutu farklı aktarılıyor.
tarih: 2026-10-03T09:00:00+03:00
kategori: Güvenlik
etiketler: Hürmüz, tanker, enerji
kaynak_adi: ISNA
kaynak_yonelim: Yarı resmî
kaynak_url: https://www.isna.ir/news/...
kaynak_baslik_fa: گزارشها از حمله به یک نفتکش در نزدیکی سواحل عمان
gorsel: img/2026-10-03-hurmuz-tanker.jpg
gorsel_alt: Hürmüz Boğazı'nın uydu görüntüsü
gorsel_kredi: NASA, Kamu malı, Wikimedia Commons
gorsel_kredi_url: https://commons.wikimedia.org/wiki/File:...
yazar: AI Agent
---
Gövde (Markdown alt kümesi)...
```

**Alan kuralları**
- `kategori` şu değerlerden biri olmalı: `Güvenlik`, `Ekonomi`, `Diplomasi`, `İç Politika`, `Toplum`, `Türkiye`.
- `ozet` en fazla 160 karakter olmalı (meta description olarak kullanılır).
- `gorsel` yolu `static/` klasörüne göredir.
- `etiketler` virgülle ayrılır.
- `seo_baslik` alanı isteğe bağlıdır. Arama sonuçlarında görünen `<title>` metnidir, en fazla 60 karakter olur ve verilmezse `baslik` kullanılır. SEO kuralları `rutin/SEO_YAZIM.md` dosyasındadır.
- `ek_kaynaklar` alanı isteğe bağlıdır. Aynı olayı işleyen diğer kaynaklar için kullanılır ve her satır `Ad (yönelim) | url` biçimindedir. Birden fazla kaynak ` ;; ` ile ayrılır.

**Gövdede desteklenen Markdown:**
- paragraflar
- `## ` ve `### ` başlıkları
- `> ` alıntılar
- `- ` listeleri
- `**kalın**` ve `*italik*`
- `[metin](url)` bağlantıları
- `| a | b |` tabloları (çerçeve karşılaştırması için)

## Görseller
- Yalnızca **özgür lisanslı** görsel kullanılır: Wikimedia Commons'ta kamu malı, CC0, CC BY veya CC BY-SA. Kredi satırı (yazar, lisans, kaynak) zorunludur.
- **İran basınının fotoğrafları kullanılmaz** (telif).
- Görseller en fazla 1200 px genişliğinde JPEG olarak kaydedilir.

## Haber gövdesi yapısı (İran agent'ı uygular)
1. **Haberin çevirisi:** Kaynak haberin Türkçe aktarımı. Sadık bir özet-çeviridir, tam metin değildir. Haberin toplam uzunluğu 400–700 kelimedir (`rutin/SEO_YAZIM.md`).
2. **`## Farsça basında nasıl verildi`:** Aynı olayı işleyen diğer kaynakların başlıkları ve çerçeve farkı. Yalnızca birden fazla kaynak olayı işlediyse eklenir.
3. **`## Bağlam`:** Okurun haberi anlaması için gereken arka plan. Özgün metindir, görüş içermez. 80–200 kelime.
4. Kapanış satırı, şablon tarafından otomatik basılır: "Bu haber Farsça kaynaktan yapay zekâ desteğiyle çevrilmiştir. Haberin sorumluluğu ilgili yayın organına aittir."

## İngilizce sürüm (2026-10-04)
- **Dosya yolu:** `content/en/haberler/<aynı-dosya-adı>.md`. Dosya adı ve slug Türkçe haberle **birebir aynıdır**, böylece iki dil eşleşir. İngilizce sayfa `en/haber/<slug>/` adresinde yayınlanır.
- **Front matter:** Alanlar Türkçe sürümle aynıdır. Aşağıdakilerin dışındakiler Türkçe dosyadan aynen kopyalanır (`tarih`, `kaynak_url`, `kaynak_baslik_fa`, `gorsel`, `gorsel_kredi_url`):
  - `baslik`, `seo_baslik` (≤ 60 karakter), `ozet` (≤ 160 karakter): İngilizce.
  - `kategori`: **Türkçe kanonik değer kalır** (Güvenlik, Ekonomi, Diplomasi, İç Politika, Toplum, Türkiye). Build bunu İngilizce adla gösterir.
  - `etiketler`: İngilizce.
  - `kaynak_adi`: Aynı kalır (yayın organının adı).
  - `kaynak_yonelim`: İngilizce. Karşılıklar:
    - Devlet ajansı → State news agency
    - Yarı resmî → Semi-official
    - Sertlik yanlısı → Hardline
    - Ilımlı-gelenekçi → Moderate-traditionalist
    - Ekonomi, teknokrat → Economic daily, technocratic
    - Tahran Belediyesi, ilkeci → Tehran municipality, principlist
    - Ilımlı muhafazakâr → Moderate conservative
    - Muhalif, yurt dışı → Opposition, diaspora
    - Reformcu → Reformist
    - Devrim Muhafızları'na yakın → IRGC-affiliated
    - Köklü gazete (ılımlı-gelenekçi) → Established daily (moderate-traditionalist)
    - Sertlik yanlısı (Rehberlik çizgisi) → Hardline (Supreme Leader's line)
    - Ilımlı muhafazakâr (Laricani çevresi) → Moderate conservative (Larijani circle)
    - Muhalefet (NCRI) → Opposition, anti-government
    - İngilizce, birincil kaynak → English, primary source
- **Düzeltme notu biçimi:** Gövdenin sonuna italik bir satır eklenir. TR: `*Düzeltme (G Ay YYYY): …*`. EN: `*Correction (Month D, YYYY): …*`. Düzeltme her iki dilde de yapılır.
  - `ek_kaynaklar`: Aynı yapıda; yalnızca parantez içindeki yönelim etiketleri İngilizce.
  - `gorsel_alt`: İngilizce.
  - `gorsel_kredi`: İngilizce ("Kamu malı" → "Public domain").
  - `yazar`: `AI Agent`.
- **Gövde başlıkları:** `## How the Persian press covered it` ve `## Context`.
- **Tablolar:** Sütun başlıkları `| Source (orientation) | Headline / framing |`.
- **Uyarı satırları:** "*For information only; not investment advice.*" ve "The presumption of innocence applies."
- **İç bağlantılar:** `../<slug>/` biçiminde (İngilizce haberler arası).
- **Dil:** Doğal, haber dili, İngiliz İngilizcesi değil Amerikan İngilizcesi. Farsça özel adlar yaygın İngilizce yazımıyla yazılır: Kayhan, Etemad, Pezeshkian, Araghchi, Zahedan, IRGC, Fatemiyoun.
- **Doğruluk:** İngilizce metin Türkçe haberin sadık çevirisidir. Yeni iddia eklenmez, mevcut iddia çıkarılmaz.
