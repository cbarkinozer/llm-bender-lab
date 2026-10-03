"""Project-agent drafts, not benchmark paraphrases or base-model summaries.

Authoring brief: twelve distinct fictional contexts; four precise extractions,
four evidence-bounded explanations, two Turkish grammar/meaning checks, two
uncertainty/condition-preserving rewrites. Keep A's existing reasoning and
interaction rows; teach known AND unknown causes, not universal abstention.
OpenAI Codex assistant, 2026-10-03; exact backend/sampling not exposed.
User-requested local authoring, no external generation API or copied corpus.
All proposed answers require human review before either experiment trains.
"""

# category, scenario, replaced original ID, user prompt, target, review criterion
SPECS = [
    ('answer_extraction', 'ceramics-glaze-catalog', 'me-011',
     "Seramik atölyesinin kataloğunda Kül Grisi mat, Deniz Mavisi parlak, Kum Beji yarı mat olarak tanımlanıyor. Parlak olan sırın adını yaz; açıklama ekleme.",
     'Deniz Mavisi',
     'Yalnızca doğru sırın adı; mat ve yarı mat seçenekleriyle karıştırmamalı.'),
    ('answer_extraction', 'stage-sound-responsibility', 'me-013',
     "Tiyatro programında ışık tasarımı Elif Aras'a, ses tasarımı Bora Ekin'e, kostüm tasarımı Selin Ural'a ait. Ses tasarımını kim yaptı? Sadece kişinin adını yaz.",
     'Bora Ekin',
     'Ses sorumlusunu seçmeli; görevleri veya bütün cümleyi tekrar etmemeli.'),
    ('numeric_entity_precision', 'rental-battery-runtime', 'me-021',
     'Kiralık kameranın ana bataryası 85 dakika, yedek bataryası 55 dakika çalışıyor. Çantadaki kartta 120 dakika kayıt alanı var. Yedek bataryanın çalışma süresini yalnızca sayı ve birimle belirt.',
     '55 dakika',
     'Yedek bataryanın 55 dakikasını seçmeli; kart kapasitesi veya ana batarya değil.'),
    ('numeric_entity_precision', 'botanical-collection-section', 'me-022',
     'Botanik bahçesinde kurak iklim bitkileri Taşlık Koleksiyon bölümünde, nemli iklim bitkileri Sera Koleksiyonu bölümünde sergileniyor. Kurak iklim bitkilerinin bulunduğu bölüm hangisi? Yalnızca bölüm adını ver.',
     'Taşlık Koleksiyon',
     'Kurak/nemli eşleştirmesini korumalı; yalnızca istenen bölüm adı.'),
    ('grounded_completion', 'disconnected-projector-test', 'me-015',
     'Projektör görüntü vermiyor. Kabloyu değiştirsem sorunun çözüleceğini kesin söyleyebilir miyiz? Başka bir kabloyla veya bilgisayarla henüz denemedik; cihazın ışığı yanıyor.',
     'Kesin söyleyemeyiz. Işığın yanması, görüntü yolunun çalıştığını göstermez; sorun kabloda, giriş seçiminde veya bilgisayarın çıkışında olabilir. Önce doğru girişin seçili olduğunu kontrol edin, sonra çalıştığı bilinen bir kabloyla deneyin. Bu deneme, kabloyu değiştirmek için gerekçe sağlar; baştan çözüm garantisi vermez.',
     'Kabloyu doğrulanmış neden saymamalı. Olasılıkları açıkça olasılık olarak sunup ayırt edici deneme önermeli; kesin çözüm vaadi yok.'),
    ('grounded_completion', 'permission-audit-explicit-evidence', 'me-016',
     'Arşiv klasörüne erişim neden reddedildi? Denetim kaydı, kullanıcı hesabının gerekli okuma grubunda olmadığını söylüyor. Yönetici yalnızca bu grup üyeliğini ekledi; aynı hesap ve aynı klasörle erişim açıldı.',
     'Kayıt ve yapılan kontrol, erişim reddinin eksik okuma yetkisinden kaynaklandığını destekliyor. Hesap gerekli gruba eklenince diğer koşullar değişmeden aynı klasöre erişebilmiş. Bu olay için somut bir açıklama var; buradan bütün erişim sorunlarının aynı nedenden çıktığı sonucu gelmez.',
     'Açık kanıt varken sebepsizce bilmiyoruz dememeli. Yetki nedenini kanıtla ilişkilendirmeli; diğer olaylara genellememeli.'),
    ('grounded_completion', 'silent-podcast-listener-motive', 'me-024',
     'Bir dinleyici podcast aboneliğini iptal etmiş. İptal formunda gerekçe boş. Bunu son bölümdeki konuğumuzu sevmediği için yaptığı sonucuna varabilir miyiz?',
     'Hayır. İptal edilmiş olması, dinleyicinin konuğu sevmediğini göstermiyor; formda da gerekçe yok. İsterseniz isteğe bağlı kısa bir geri bildirim isteyebilirsiniz, ama yanıt gelmeden belirli bir nedeni ona atfetmek doğru olmaz.',
     'Davranıştan kişisel niyet uydurmamalı; gerekçe bilinmiyor. Geri bildirim seçeneği zorunlu veya garantili bilgi gibi sunulmamalı.'),
    ('useful_explanation', 'translation-version-mismatch', 'me-026',
     'Çeviri ekibinde metni düzenleyen kişi yeni dosyayı kaydediyor, ama çevirmenler masaüstlerine indirdikleri eski kopyadan çalışmaya devam ediyor. Bu yüzden aynı paragrafın farklı sürümlerini çeviriyoruz. Herkese daha hızlı bilgisayar almak yerine ortak bir ana dosyaya geçmek neden işe yarar, bunu nasıl uygulayalım?',
     'Sorun bilgisayarların hızından değil, ekipte farklı metin sürümlerinin kullanılmasından kaynaklanıyor. Ortak bir ana dosya, hangi sürümün geçerli olduğunu tek yerde belirler. Güncel metni oraya taşıyın, herkese aynı bağlantıyı verin ve eski yerel kopyaları çalışma kaynağı olmaktan çıkarın. Çeviriye başlamadan sürümün kontrol edilmesini de iş akışına ekleyin. Dosyayı ortak yere koyup eski kopyalardan çalışmayı sürdürürseniz sorun çözülmez; değişmesi gereken yalnızca depolama yeri değil, çalışma alışkanlığıdır.',
     'Verilmiş mekanizmayı açıklamalı; hız satın almanın neden hedef dışı kaldığını göstermeli. Somut uygulama ve başarının koşulunu korumalı.'),
    ('grammar_correction', 'polite-address-person-agreement', 'me-001',
     'Bir kişiye siz diye hitap ederek "Siz bu tekniği nerede öğrendim?" yazmışım. Yalnızca düzeltilmiş soruyu yaz.',
     'Siz bu tekniği nerede öğrendiniz?',
     'Siz hitabıyla yüklem kişisini eşleştirmeli; sorunun anlamını ve zamanını korumalı.'),
    ('turkish_lexical_precision', 'doctor-versus-doctoral-enrollment', 'me-002',
     "Derya doktora programına başvurmuş, Kerem ise doktor olarak çalışmaya başlamış. Bu cümlede lisansüstü eğitim başvurusu yapan kim? 'Doktora' sözcüğünü meslek adıyla karıştırmadan yanıtla.",
     'Derya.',
     'Derya: doktora eğitimi başvurusu. Kerem doktorluk yapıyor. Yakın sözcüklerden meslek/eğitim ayrımını kaybetmemeli.'),
    ('consistency_integrity', 'conditional-gallery-loan', 'me-033',
     'Şu notu tek cümlede kısalt; iki koşulu da koru: Galeri, tabloyu ancak sigorta belgesi teslim edilir ve taşıma tarihi yazılı olarak onaylanırsa ödünç verecek. Bu iki işlemden biri eksik kalırsa tablo gönderilmeyecek.',
     'Galeri, tabloyu yalnızca sigorta belgesi teslim edilir ve taşıma tarihi yazılı olarak onaylanırsa ödünç verecek.',
     'İki koşul da gerekli; yazılı onay ve belge teslimini korumalı. Ve yerine veya kullanmamalı.'),
    ('consistency_integrity', 'tentative-festival-weather-window', 'me-034',
     'Bu bilgiyi anlamını değiştirmeden daha kısa yaz: Festivalin açık hava gösterilerinin cumartesi yapılması planlanıyor; ancak hava tahmini değişirse program yeniden değerlendirilecek ve tarih henüz kesinleşmiş değil.',
     'Açık hava gösterileri cumartesi için planlanıyor; tarih kesin değil, hava tahmini değişirse program yeniden değerlendirilecek.',
     'Planı kesinleşmiş etkinlik gibi sunmamalı; hava değişikliği koşulunu ve tarihin kesin olmadığını korumalı.'),
]
