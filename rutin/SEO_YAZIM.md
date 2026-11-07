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

## 5. Gövde (550–900 kelime; Bağlam dahil)
1. **Giriş paragrafı (40–60 kelime):** 5N1K'ya cevap verir. Anahtar kelime ilk cümlede geçer. Haberin kaynağı adıyla anılır ("ISNA'nın aktardığına göre…").
2. **Haberin çevirisi:** Kaynak haberin sadık özet-çevirisi. Tam metin değildir, kendi cümlelerinle yazılır. Kısa doğrudan alıntılar tırnak içinde verilir. Rakam, isim ve tarihler kaynakla birebir aynı olur.
3. **`## Farsça basında nasıl verildi`:** Aynı olayı işleyen diğer kaynakların başlıkları ve çerçeve farkı. Gerekirse tablo kullanılır (`| Kaynak (yönelim) | Başlık / çerçeve |`). Yalnızca ≥ 2 kaynak varsa yazılır.
4. **`## Bağlam`** (kullanıcı kararı 2026-11-07: günde 5 haber kalır, her habere daha fazla özgün Bağlam): sitenin asıl özgün katkısı ve AdSense/Google kalite değerlendirmesinde belirleyici bölüm. **250–400 kelime**, aşağıdaki kalın girişli alt bloklarla yazılır. En az 3 blok zorunlu; Türkiye bağlantısı varsa "Türkiye boyutu" da zorunlu.
   - **Arka plan:** Olayın geçmişi, 3–5 maddelik tarihli zaman çizelgesi (`- **12 Haziran 2025:** …`). En az bir madde Farsçadan'daki önceki habere bağlantı verir (varsa).
   - **Kim kimdir / kavram:** Haberdeki kişi, kurum ya da kavramın 1–2 cümlelik tanımı; Farsça terimin Latin harfli okunuşu ve Türkçe karşılığı (ör. *Majles-e Khobregan* — Uzmanlar Meclisi). Türkçe kaynaklarda bulunmayan bilgi tercih edilir.
   - **Rakamlarla:** Konuyu ölçen en az 2 sayı (kur, ihracat, bütçe, nüfus, kayıp, oy vb.), her biri kaynak ve tarihle. Sayılar WebSearch ile doğrulanır, kaynak `ek_kaynaklar`'a eklenir.
   - **Türkiye boyutu:** Ticaret, enerji, sınır, göç veya diplomasi bağlantısı; somut veriyle. Bağlantı yoksa blok yazılmaz, uydurulmaz.
   - **Sırada ne var:** Yalnızca açıklanmış/takvimli gelişmeler (oturum, son tarih, ziyaret, oylama). Tahmin yazılmaz.
   - **Yasaklar:** Görüş ve yorum ("örüntü", "geçiştiriyor", "mesaj veriyor" gibi niyet okumaları), haber gövdesinin tekrarı, kaynaksız sayı, genel geçer dolgu cümleleri. Her olgu bir kaynağa dayanır; en az bir doğrulama kaynağı İran dışı/uluslararasıdır (Reuters, AP, IAEA, IMF, TÜİK, resmî açıklama).
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
