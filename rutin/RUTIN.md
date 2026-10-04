# Farsçadan — Günlük Yayın Rutini

Bu dosya bulut rutininin (ve yerel elle çalıştırmanın) adım adım akışıdır. Çalışma dizini, `farscadan` deposunun **`kaynak`** dalıdır.

## Roller
- **İran Basın İzleme agent'ı (sen, 1–5. adımlar):** Haberleri seçer, çevirir ve yazar.
- **Web Yayın agent'ı (sen, 6–7. adımlar):** Siteyi derler, kontrol eder ve yayınlar.

## Hedef
Her gün **5 yeni haber.** Hepsi `rutin/SEO_YAZIM.md` ve `ICERIK_SOZLESMESI.md` kurallarına uyar ve `yazar: AI Agent` olur.

## Adımlar

### 0. Hazırlık
- `git checkout kaynak && git pull --rebase origin kaynak` (oturum başka bir dalda açıldıysa önce `git fetch origin kaynak`)
- **Bugün rutin zaten çalıştı mı?** `rutin/kayit/YYYY-MM-DD.md` dosyası (bugünün tarihi, Europe/Istanbul) varsa ve "Yayın sonucu: başarılı" satırını içeriyorsa dur ve "bugün zaten yayınlandı" diye raporla. Kurulum günü (2026-10-03) elle eklenen 10 haber bu sayıma girmez. Kayıt dosyası yoksa ya da başarısız bir çalıştırmayı gösteriyorsa yeni 5 haber yazılır.
- Son 7 günün haber başlıklarını ve etiketlerini listele. Bu liste tekrarı önlemek ve iç bağlantı vermek için kullanılır.

### 1. Kaynakları çek
- `python3 rutin/rss_cek.py 24 /tmp/feeds.json`
  - Çıktıdaki `durum` satırında kaynakların en az 5'i "ok" olmalı.
  - Daha azı çalışıyorsa WebSearch ile tamamla: tarih damgalı sorgular, örneğin `site:isna.ir`, `site:irna.ir`, "Iran news October 4 2026".
  - Erişilemeyen kaynakları rapora yaz.

### 2. 5 olay seç
- Seçim `SEO_YAZIM.md` §1'e göre yapılır.
  - Öncelik: Türkiye bağlantısı > çok kaynaklı olay > ekonomi, güvenlik, diplomasi.
  - Kategori çeşitliliği gözetilir: aynı kategoriden en fazla 2 haber.
  - Son 7 günde aynı açıdan yazılmış bir olay seçilmez.
- Her olay için 1 ana kaynak ve 1–3 ek kaynak belirle.

### 3. Tam metni oku
- Haber sayfalarını `curl -sL -A "Mozilla/5.0"` ile çek ve `<p>` paragraflarını çıkar.
- IRNA ve ISNA sayfalarında gövde `<p>` içinde gelmez. Bu kaynaklar için RSS özetini ve diğer kaynakları kullan.
- Türkiye'ye veya yaptırımlara ilişkin iddiaları İngilizce birincil kaynakla doğrula (WebSearch).

### 4. Yaz
- Her haber `content/haberler/YYYY-MM-DD-<anahtar-kelimeler>.md` dosyasına yazılır. Biçim `ICERIK_SOZLESMESI.md`'deki front matter ve isteğe bağlı `seo_baslik` alanıdır.
- `tarih`: bugünün tarihi ve rutin saati, `+03:00` ile. 5 haberin saatleri 10'ar dakika arayla verilir. En önemli haber en yeni saati alır ve ana sayfada en üstte görünür.
- Kalite barı, her haber için:
  - [ ] `seo_baslik` ≤ 60 karakter, `ozet` 120–155 karakter
  - [ ] Gövde 400–700 kelime; "Bağlam" bölümü var; ≥ 2 kaynak varsa "Farsça basında nasıl verildi" bölümü var
  - [ ] Her iddia atfedilmiş; çelişkiler "teyit edilmedi" ile işaretli
  - [ ] Görsel özgür lisanslı ve kredili

### 4b. İngilizce sürüm (2026-10-04)
- Yazılan her Türkçe haberin İngilizcesi `content/en/haberler/<aynı-dosya-adı>.md` dosyasına yazılır. Kurallar `ICERIK_SOZLESMESI.md` dosyasının "İngilizce sürüm" bölümündedir: kategori Türkçe kanonik değer olarak kalır, yönelim etiketleri tablodaki karşılıklarla yazılır.
- İngilizce metin Türkçe haberin sadık çevirisidir; yeni iddia eklenmez.

### 5. Görseller
- `SEO_YAZIM.md` §7'ye göre her haber için 1 görsel bulunur.
- Wikimedia isteklerinin arasında ≥ 8 saniye beklenir.

### 6. Derle, kontrol et, yayınla
- `bash rutin/yayinla.sh "Günlük yayın YYYY-MM-DD: 5 haber"`
  - Betik sırasıyla şunları yapar: kaynak dalını commit'leyip gönderir, `build.py` ile derler, `check_links.py` ile kontrol eder, `public/` çıktısını `main` dalına gönderir. GitHub Pages siteyi 1–2 dakikada günceller.
- `build.py` uyarı verirse (eksik alan, geçersiz kategori, özet > 160 karakter) dosyayı düzelt ve betiği yeniden çalıştır.
- `check_links.py` hata verirse **yayınlama.** Hatayı düzeltmeyi bir kez dene, olmazsa rapora yaz.

### 6b. Çerçeve kartı (X görseli)
- Bugünün haberlerinden **karşılaştırma tablosu olan** birini seç. Türkiye haberi varsa ve tablosu varsa onu tercih et.
- Kartı iki dilde üret: `python3 rutin/kart_uret.py <slug>` ve `python3 rutin/kart_uret.py <slug> --lang en`. Kartlar `static/x/kart/` klasörüne yazılır.
- Kartları yayınlamak için `bash rutin/yayinla.sh "Çerçeve kartı <slug>"` komutunu tekrar çalıştır. Yayınlanan kart adresi: `https://farscadan.com/x/kart/<slug>.png`.
- Bugün tablolu haber yoksa kart üretme ve bunu rapora yaz.

### 7. Canlı kontrol
- GitHub Pages dağıtımı genelde 1–2 dakika sürer, ama 8 dakikaya kadar uzayabilir (03.10'da görüldü). 404 alınırsa 30 saniyede bir yeniden dene, en fazla **10 dakika** bekle. Ancak bu sürenin sonunda hâlâ 404 alınıyorsa "başarısız" yaz.
- `curl -s -o /dev/null -w "%{http_code}" https://farscadan.com/haber/<slug>/` komutunu 5 haberin hepsi için çalıştır. Hepsi 200 dönmeli.
- `https://farscadan.com/news-sitemap.xml` yeni haberleri içermeli.

### 8. Raporla
- `rutin/kayit/YYYY-MM-DD.md` dosyasına kısa bir kayıt yaz (ilk satırlardan biri tam olarak `Yayın sonucu: başarılı` ya da `Yayın sonucu: başarısız — <neden>` olmalı) ve kaynak dalına commit'le (betiği yeniden çalıştırmaya gerek yok; `git add`, `git commit`, `git push origin HEAD:kaynak` yeterli). Kayıtta şunlar bulunur:
  - Seçilen 5 haber (başlık ve URL)
  - Kaynak erişim durumu
  - Uyarılar
  - Yayın sonucu
  - Toplam haber sayısı (AdSense eşiği için)
- Rapor kişisel veri içermez. Bu depo herkese açıktır.

### 8b. X (@farscadancom) paylaşım taslakları
- Yayından sonra `rutin/kayit/x-YYYY-MM-DD.md` dosyasına bugünün 5 haberi için **paylaşıma hazır 5 gönderi** yaz. Kartlı haberin gönderisinde "Görsel: https://farscadan.com/x/kart/<slug>.png" satırı da bulunur. Kurallar:
  - Her gönderi ≤ 270 karakter: haberin en çarpıcı olgusu (kaynağa atıfla, ör. "Kayhan'a göre…") + haber bağlantısı (`https://farscadan.com/haber/<slug>/`).
  - En fazla 2 hashtag (ör. #İran, #Hürmüz). Görüş, emoji yığını ve clickbait yok.
  - Türkiye kategorisindeki haber varsa onun gönderisi ilk sıraya konur.
  - Gönderinin sonunda kaynağın yönelim etiketi parantez içinde verilir: "(Kayhan, sertlik yanlısı)".
- Dosya kaynak dalına commit'lenir. Paylaşımı site sahibi yapar.

### 9. Pazar günleri: haftalık editör listesi (editör katmanı, 2026-10-03)
- Pazar çalıştırmasında, yayın tamamlandıktan sonra `rutin/kayit/editor-YYYY-MM-DD.md` dosyasını yaz. Tarih o pazarın tarihidir.
- **Kapsam:** Son 7 günde yayınlanan haberlerden şunlar:
  - `kategori: Türkiye` olanlar
  - Hassas konulu olanlar: soykırım, din, Kürt meselesi, suçlama veya yargılama, ölüm ve çatışma bilançosu, Türk kişi ve kurumları hakkındaki iddialar
- **Her satırda:** başlık, canlı bağlantı, hassasiyet nedeni (tek cümle), `[ ] Onaylandı` kutusu.
- Editör (site sahibi) listeyi okur. Düzeltme isterse bir sonraki oturumda haber güncellenir ve sonuna "*Düzeltme (tarih): …*" notu eklenir.
- Bu dosya kaynak dalına commit'lenir. Kişisel veri içermez.

## Asla
- Token, şifre veya e-posta adresini hiçbir dosyaya yazma.
- `main` dalını elle düzenleme. `main` yalnızca `yayinla.sh` ile güncellenir.
- Eski haberleri silme veya üzerine yazma. Düzeltme gerekiyorsa haberi güncelle ve gövdenin sonuna "*Düzeltme (tarih): …*" notu ekle.
- İran basınının fotoğraflarını kullanma.
- Yorum, görüş veya yatırım tavsiyesi yazma.
