# Farsçadan — Haber Yazımı ve SEO Kuralları

Bu kurallar her haber için geçerlidir. Biçim sözleşmesi `ICERIK_SOZLESMESI.md` dosyasındadır; bu dosya onu tamamlar.

## 1. Konu seçimi (arama talebi + özgünlük)
- **Önce Türkiye'ye değen haberler:** Türk şirketleri, ticaret, enerji, sınır, göç, Türkiye hakkındaki iddialar. Türkçe aramada rakibi en az olan ve en çok aranan alan budur.
- **Sonra çok kaynaklı olaylar:** ≥ 2 kamptan kaynağın işlediği olaylar. Bunlar "Farsça basında nasıl verildi" karşılaştırması için gereklidir ve sitenin özgün katkısı budur.
- **Uzun kuyruk fırsatları:** Türkçede karşılığı az aranan ama hiç anlatılmamış İran'a özgü kavramlar, kişiler ve kurumlar (ör. "kalabarg nedir", "Meydari kimdir", "Donya-ye Eghtesad"). Habere 2–3 cümlelik bir açıklama paragrafı eklenir.
- **Tekrar yok:** Önceki günlerde yazılan bir olayı aynı açıdan tekrar yazma. Yeni gelişme varsa yeni haber yazılır ve önceki habere bağlantı verilir.
- **Kapsam dışı:** Spor, magazin, sağlık-yaşam ve dini içerikler. Siyasi sonucu olan spor haberi istisnadır.

## 2. Başlıklar
- `baslik` (H1): Bilgi veren, doğal Türkçe bir cümle, ≤ 90 karakter. Ana anahtar kelime (kişi, kurum, yer veya kavram) başlığın ilk yarısında yer alır.
- `seo_baslik`: Arama sonuçlarında görünen `<title>`, **≤ 60 karakter**, anahtar kelime başta. Site adı otomatik eklenir, sen yazma.
  - Örnek: "Dolar 260 bin tümen: İran Merkez Bankası müdahale sinyali verdi"
- **Yasak:** Clickbait ("Şok!", "Bakın ne oldu"), tamamı büyük harf, soru işaretiyle ilgi çekme.

## 3. Özet (meta description)
- `ozet` 120–155 karakter olur ve anahtar kelimeyi doğal biçimde içerir. Ne olduğunu ve neden önemli olduğunu söyler.

## 4. URL (slug)
- Dosya adı `YYYY-MM-DD-anahtar-kelimeler.md` biçimindedir: 3–6 Türkçe anahtar kelime, yalnızca ASCII (ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u), bağlaç yok.
  - Örnek: `2026-10-04-dolar-tumen-merkez-bankasi-mudahale.md`

## 5. Gövde (400–700 kelime)
1. **Giriş paragrafı (40–60 kelime):** 5N1K'ya cevap verir. Anahtar kelime ilk cümlede geçer. Haberin kaynağı adıyla anılır ("ISNA'nın aktardığına göre…").
2. **Haberin çevirisi:** Kaynak haberin sadık özet-çevirisi. Tam metin değildir, kendi cümlelerinle yazılır. Kısa doğrudan alıntılar tırnak içinde verilir. Rakam, isim ve tarihler kaynakla birebir aynı olur.
3. **`## Farsça basında nasıl verildi`:** Aynı olayı işleyen diğer kaynakların başlıkları ve çerçeve farkı. Gerekirse tablo kullanılır (`| Kaynak (yönelim) | Başlık / çerçeve |`). Yalnızca ≥ 2 kaynak varsa yazılır.
4. **`## Bağlam`:** Okurun haberi anlaması için gereken arka plan. Özgün metin, 80–200 kelime, görüş içermez. Varsa Türkiye bağlantısı burada açıklanır.
5. **İç bağlantı:** Farsçadan'daki ilgili 1–2 habere bağlantı ver: `[metin](../YYYY-MM-DD-slug/)`. Bağlantı göreli olur, haber sayfaları `haber/<slug>/` altındadır. Konu ilk kez işleniyorsa bağlantı zorunlu değil.
6. **Uyarılar:**
   - Döviz, petrol ve borsa haberinin sonuna `*Bu haber bilgilendirme amaçlıdır; yatırım tavsiyesi değildir.*` eklenir.
   - Suçlama haberlerinde şüpheliler yalnızca baş harfleriyle anılır ve "Masumiyet karinesi geçerlidir." cümlesi eklenir.

Ara başlıklar (`##`) açıklayıcı olur ve anahtar kelimeyle ilişkilidir. Anahtar kelime doldurma yapılmaz: aynı ifade en fazla 3–4 kez geçer.

## 6. Etiketler ve kategori
- `etiketler`: 3–6 adet varlık adı veya konu (ör. "Hürmüz Boğazı, tanker, UKMTO"). Daha önce kullanılmış yazımlara uyulur.
- `kategori`: Güvenlik · Ekonomi · Diplomasi · İç Politika · Toplum · Türkiye. Türkiye'ye doğrudan değen haber "Türkiye" kategorisine girer.

## 7. Görsel
- **Kaynak:** Yalnızca Wikimedia Commons'tan kamu malı, CC0, CC BY veya CC BY-SA lisanslı görsel. İran basınının kendi fotoğrafları kullanılmaz. Tasnim'in Commons'a yüklediği CC BY 4.0 fotoğraflar kredi verilerek kullanılabilir.
- **API:** `https://commons.wikimedia.org/w/api.php` adresinde `generator=search`, `gsrsearch=filetype:bitmap <sorgu>`, `prop=imageinfo`, `iiprop=url|extmetadata`, `iiurlwidth=1200` parametreleri kullanılır.
  - User-Agent başlığı gönderilir: `FarscadanBot/0.1 (https://farscadan.com/iletisim/)`.
  - **İstekler arasında ≥ 8 saniye beklenir** (429 hız sınırı).
- **Kayıt:** Görsel 1200 px genişliğe küçültülür ve `static/img/<slug>.jpg` adıyla JPEG (kalite 82) olarak kaydedilir.
  - Pillow yoksa `pip install pillow` ile kurulur. O da olmazsa Commons'un 1200 px küçük görseli (`thumburl`) olduğu gibi indirilir.
- **Kredi:** `gorsel_kredi` = "Yazar, Lisans, Wikimedia Commons" ve `gorsel_kredi_url` = dosya sayfası.
- **Alt metin:** `gorsel_alt` görseli Türkçe ve somut olarak betimler (anahtar kelime doğal biçimde geçebilir).
- **Uygun görsel yoksa:** Konuyla ilgili genel bir görsel kullanılır (ör. harita, uydu görüntüsü, şehir). Görselsiz yayın en son çaredir.

## 8. Doğruluk ve tarafsızlık
- Her iddia bir kaynağa atfedilir. Kaynaklar çelişiyorsa ikisi de yazılır ve "teyit edilmedi" denir.
- Türkiye'ye veya yaptırımlara ilişkin iddialar İngilizce birincil kaynakla (OFAC, Reuters, resmî açıklama) WebSearch üzerinden doğrulanır. Doğrulanan kaynak `ek_kaynaklar` alanına eklenir.
- Farsçadan aktarılan özel adlar resmî yazımla düzeltilir.
- Görüş, yorum ve taraf tutan sıfatlar kullanılmaz. Kaynakların kendi nitelemeleri tırnak içinde ve kaynağa atfedilerek verilir.
- Yazar alanı her zaman `yazar: AI Agent` olur.
