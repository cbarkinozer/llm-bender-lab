"""Materialize the original agent-authored training pilot; no external API calls."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'experiments/turkish-capability/lfm3-1.7b/sft-expansion-v01'

# capability, domain, subskills, instruction, original passage/input, answer,
# required facts (review metadata only). All scenarios are synthetic.
EXAMPLES = [
('faithful_summary','public_services','modality,condition','Metni tek cümlede özetle.',
'Kurgusal Çınarlı Belediyesi, pazar günleri iki mahalle arasında ücretsiz servis başlatmayı önerdi. Öneri henüz oylanmadı. Kabul edilirse servisler ekim ayında başlayacak; mevcut hafta içi seferleri değişmeyecek.',
'Çınarlı Belediyesi, henüz oylanmamış bir öneriyle ekimden itibaren pazar günleri iki mahalle arasında ücretsiz servis başlatmayı planlıyor; hafta içi seferleri değişmeyecek.',
['Öneri henüz oylanmadı.','Başlangıç kabul koşuluna bağlı.','Pazar servisi ücretsiz; hafta içi değişmiyor.']),
('faithful_summary','education','numbers,main_point','Metni iki cümlede özetle.',
'Kurgusal Mavi Okulun kitap değişim gününe 60 öğrenci katıldı. Öğrenciler toplam 180 kitap getirdi ve bunların 150 tanesi yeni okuyucularla buluştu. Kalan 30 kitap okul kütüphanesine bağışlandı. Etkinlik için öğrencilerden ücret alınmadı.',
'Mavi Okulun ücretsiz kitap değişim gününe 60 öğrenci 180 kitap getirdi. Kitapların 150 tanesi el değiştirdi, kalan 30 tanesi okul kütüphanesine bağışlandı.',
['60 öğrenci, 180 kitap.','150 kitap el değiştirdi; 30 kitap bağışlandı.','Etkinlik ücretsizdi.']),
('faithful_summary','research','association,uncertainty','Bulguyu ve sınırlılığını iki cümlede özetle.',
'Kurgusal bir araştırmada 240 yetişkinin uyku günlükleri dört hafta incelendi. Düzenli yürüdüğünü bildirenlerin ortalama uyku süresi daha uzundu. Katılımcılar rastgele gruplara ayrılmadı ve yürüyüş süreleri cihazla ölçülmedi. Araştırmacılar, bu gözlemin yürüyüşün uykuyu uzattığını kanıtlamadığını belirtti.',
'240 yetişkinin dört haftalık günlüklerinde düzenli yürüyüş bildirenlerin daha uzun uyuduğu gözlendi. Rastgele gruplama ve cihazla ölçüm yapılmadığı için bu ilişki, yürüyüşün uykuyu uzattığını kanıtlamıyor.',
['240 yetişkin, dört hafta.','Gözlenen ilişki nedensellik kanıtı değil.','Rastgele gruplama ve cihaz ölçümü yok.']),
('faithful_summary','workplace','attribution,negation','Metni tek cümlede özetle.',
'Kurgusal Kuzey Atölyesinde müdür Ece, cuma günü uzaktan çalışma önerisinin görüşüldüğünü söyledi. Personel temsilcisi Bora ise çalışanların henüz görüş bildirmediğini belirtti. Toplantıda karar alınmadı ve mevcut çalışma düzeni sürdürüldü.',
'Kuzey Atölyesinde cuma günü uzaktan çalışma önerisi görüşüldü ancak Bora çalışanların henüz görüş bildirmediğini belirtti; karar alınmadığı için mevcut düzen sürdü.',
['Öneri görüşüldü, kabul edilmedi.','Çalışan görüşünün bulunmadığını Bora söyledi.','Mevcut düzen sürdü.']),
('faithful_summary','infrastructure','dates,exception','Duyuruyu tam iki maddeyle özetle.',
'Kurgusal Göl Sokakta boru yenileme nedeniyle salı günü 09.00 ile 13.00 arasında su kesilecek. Kesinti yalnızca 1 ile 18 numaralı binaları kapsıyor. Sokaktaki sağlık birimi ayrı hattan beslendiği için etkilenmeyecek. Çalışma erken biterse su belirtilen saatten önce verilebilecek.',
'- Salı günü 09.00–13.00 arasında Göl Sokaktaki 1–18 numaralı binalarda boru yenileme nedeniyle su kesilecek; ayrı hattan beslenen sağlık birimi etkilenmeyecek.\n- Çalışma erken tamamlanırsa su 13.00’ten önce verilebilecek.',
['Salı 09.00–13.00, 1–18 numaralar.','Sağlık birimi istisna.','Erken tamamlanırsa erken su verilebilir.']),
('faithful_summary','culture','ordinary,main_point','Metni tek cümlede özetle.',
'Kurgusal Renk Evi, kullanılmayan kumaşlardan çanta yapmayı öğreten bir atölye düzenledi. Katılımcılar malzemelerini evden getirdi ve etkinlik sonunda yaptıkları çantaları yanlarında götürdü. Atölyeyi iki gönüllü yürüttü.',
'Renk Evinde iki gönüllünün yürüttüğü atölyede katılımcılar evden getirdikleri kullanılmayan kumaşlarla çanta yapıp çantalarını yanlarında götürdü.',
['Kullanılmayan kumaşlardan çanta yapıldı.','Malzemeleri katılımcılar getirdi.','İki gönüllü yürüttü; çantalar katılımcılarda kaldı.']),
('faithful_summary','commerce','denominator,numbers','Raporu iki cümlede özetle.',
'Kurgusal Ada Kooperatifinin mart ayındaki 200 siparişinin 180 tanesi zamanında teslim edildi. Nisan ayında 250 siparişin 220 tanesi zamanında ulaştı. Zamanında teslim edilen sipariş sayısı artsa da bunların tüm siparişlere oranı yüzde 90’dan yüzde 88’e düştü.',
'Ada Kooperatifinde zamanında teslim edilen sipariş sayısı martta 180 iken nisanda 220 oldu. Ancak toplam sipariş 200’den 250’ye çıktığı için zamanında teslim oranı yüzde 90’dan yüzde 88’e düştü.',
['Zamanında teslim sayısı 180→220.','Toplam sipariş 200→250.','Oran %90→%88; artış diye sunma.']),
('faithful_summary','environment','conditions,scope','Metni kısa bir paragrafla özetle.',
'Kurgusal bir fidanlık, 400 yerli fidanı mahalle derneklerine ücretsiz verecek. Her dernek en fazla 20 fidan alabilecek ve fidanların bakımını bir yıl üstlenecek. Başvurular 12 mayısta kapanacak. Dağıtım, başvuru sırasına göre stok bitene kadar yapılacak; başvuru yapmak fidan alınacağını garanti etmiyor.',
'Fidanlık, bir yıllık bakım sorumluluğunu üstlenen mahalle derneklerine dernek başına en fazla 20 olmak üzere toplam 400 yerli fidanı ücretsiz dağıtacak. Başvurular 12 mayısta kapanacak; dağıtım başvuru sırasına ve stoka bağlı olduğu için her başvuruya fidan garantisi yok.',
['400 fidan, dernek başına en çok 20.','Ücretsiz, bir yıl bakım koşulu.','12 Mayıs; sıra ve stok, garanti yok.']),
('faithful_summary','transport','temporal,negation','Metni tek cümlede özetle.',
'Kurgusal Kıyı Vapurunun motor arızası giderildi ve gemi dün deneme seferini tamamladı. Ancak yolcu taşıma izni henüz yenilenmedi. İşletme, izin çıkana kadar aynı hatta yedek geminin çalışacağını duyurdu.',
'Kıyı Vapurunun arızası giderilip deneme seferi tamamlandı ancak yolcu taşıma izni henüz yenilenmediği için hatta yedek gemi çalışacak.',
['Tamir ve deneme tamam.','Yolcu izni henüz yok.','İzin çıkana kadar yedek gemi.']),
('faithful_summary','technology','mechanism,limitation','Açıklamayı iki cümlede özetle.',
'Kurgusal Not Sepeti uygulaması, kullanıcı çevrimdışıyken notları cihazda saklıyor. İnternet bağlantısı kurulduğunda yalnızca kullanıcının eşitleme için seçtiği notlar sunucuya gönderiliyor. Seçilmeyen notlar cihazda kalıyor. Cihaz bozulursa eşitlenmemiş notlar sunucudan geri getirilemiyor.',
'Not Sepeti, çevrimdışı notları cihazda tutuyor ve bağlantı kurulunca yalnızca kullanıcının seçtiği notları sunucuyla eşitliyor. Eşitlenmemiş notlar cihaz bozulduğunda sunucudan geri alınamıyor.',
['Yalnızca seçili notlar eşitleniyor.','Diğerleri yerelde.','Eşitlenmeyenler sunucudan kurtarılamaz.']),
('faithful_summary','sports','entities,attribution','Haberi tek cümlede özetle.',
'Kurgusal Bahar Koşusunda kadınlar yarışını Deniz Arı, erkekler yarışını Deniz Ak kazandı. Organizasyon sorumlusu Selin, parkurun önceki yılla aynı olduğunu söyledi. Dereceler henüz yayımlanmadığı için bir parkur rekoru açıklanmadı.',
'Bahar Koşusunu kadınlarda Deniz Arı, erkeklerde Deniz Ak kazandı; Selin parkurun değişmediğini söylerken dereceler yayımlanmadığından parkur rekoru açıklanmadı.',
['Kadınlar Deniz Arı; erkekler Deniz Ak.','Parkur aynı bilgisi Selin’e ait.','Rekor açıklanmadı.']),
('faithful_summary','agriculture','comparison,uncertainty','Metni iki cümlede özetle.',
'Kurgusal bir serada yeni sulama yöntemi iki bölmenin birinde denendi. Deneme bölmesi aynı dönemde yüzde 15 daha az su kullandı. İki bölmede farklı domates çeşitleri yetiştirildiği için üretici, verim farkının yalnızca sulamaya bağlanamayacağını belirtti. Deneme gelecek mevsim aynı çeşitlerle tekrarlanacak.',
'Seradaki yeni sulama yöntemi denenen bölme yüzde 15 daha az su kullandı ancak farklı domates çeşitleri nedeniyle verim farkı yalnızca sulamaya bağlanamıyor. Deneme gelecek mevsim aynı çeşitlerle tekrarlanacak.',
['Su kullanımı %15 az.','Verim farkının nedeni kesin değil; çeşitler farklı.','Aynı çeşitlerle tekrar planı.']),
('faithful_summary','logistics','cause,partial_completion','Metni tek cümlede özetle.',
'Kurgusal Kutu Dağıtım merkezindeki elektrik kesintisi paket ayrıştırmayı iki saat durdurdu. Akşam vardiyasıyla biriken paketlerin çoğu işlendi, fakat uzak bölgelere gidecek 40 paket ertesi güne kaldı. Şirket bu 40 paketin alıcılarına gecikme bildirimi gönderdi.',
'Elektrik kesintisi Kutu Dağıtımda ayrıştırmayı iki saat durdurdu; akşam vardiyası birikimin çoğunu giderse de uzak bölgelere gidecek 40 paket ertesi güne kaldı ve alıcılara bildirim yapıldı.',
['Elektrik kesintisi iki saat durdurdu.','Çoğu işlendi, 40 paket kaldı.','Alıcılara bildirildi.']),
('faithful_summary','community','ordinary,procedure','Duyuruyu tam üç maddeyle özetle.',
'Kurgusal Komşu Masası, cumartesi 11.00’de mahalle evinde ortak yemek düzenliyor. Katılanların paylaşabilecekleri bir yemek getirmesi isteniyor. Kap ve çatal sağlayan ekip, alerjen bilgisinin yemeğin yanına yazılmasını rica ediyor. Katılım için ön kayıt gerekmiyor.',
'- Ortak yemek cumartesi 11.00’de mahalle evinde yapılacak; ön kayıt gerekmiyor.\n- Katılımcılardan paylaşabilecekleri bir yemek getirmeleri isteniyor.\n- Kap ve çatal ekipten; yemeklerin yanına alerjen bilgisi yazılması rica ediliyor.',
['Cumartesi 11.00, mahalle evi, kayıt yok.','Yemek getirme isteği.','Kap çatal ekipten; alerjen etiketi.']),
('faithful_summary','finance','eligibility,exception','Metni kısa bir paragrafla özetle.',
'Kurgusal Meslek Birliği, bu yıl ilk kez iş yeri açan üyelerine eğitim ücretinde yüzde 30 indirim uygulayacak. İndirim yalnızca birliğin kendi eğitimleri için geçerli olacak; dış kurumların seminerleri kapsama girmiyor. Başvuru sırasında açılış belgesi istenecek ve indirim geriye dönük uygulanmayacak.',
'Meslek Birliği, açılış belgesi sunan ve bu yıl ilk kez iş yeri açan üyelerine kendi eğitimlerinde yüzde 30 indirim sağlayacak. Dış kurum seminerleri kapsam dışında ve geçmiş ödemelere indirim uygulanmayacak.',
['Bu yıl ilk kez açan üyeler ve belge.','%30 yalnızca kendi eğitimleri.','Dış seminer ve geriye dönük uygulama yok.']),
('faithful_summary','accessibility','scope,remaining_gap','Metni iki cümlede özetle.',
'Kurgusal Kent Arşivinin girişine rampa yapıldı ve zemin kattaki danışmaya sesli yönlendirme eklendi. Üst kattaki okuma salonuna çıkan asansör ise bakım nedeniyle kapalı. Arşiv yönetimi, üst kattaki belgelerin talep üzerine zemin kata getirileceğini açıkladı.',
'Kent Arşivinin girişine rampa ve zemin kattaki danışmaya sesli yönlendirme eklendi ancak üst kata çıkan asansör bakımda. Üst kattaki belgeler talep üzerine zemin kata getirilecek.',
['Rampa ve sesli yönlendirme.','Asansör kapalı; tam erişim iddiası yok.','Belgeler istekle aşağı getirilecek.']),
('faithful_summary','energy','baseline,units','Metni tek cümlede özetle.',
'Kurgusal bir apartmanda ortak alan aydınlatmaları yenilendi. Aynı uzunluktaki iki ölçüm döneminde elektrik tüketimi 500 kilovatsaatten 350 kilovatsaate düştü. Bu ölçüm yalnızca ortak alanları kapsıyor; dairelerin tüketimi hesaba katılmadı.',
'Apartmanda aydınlatma yenilemesinden sonra eşit uzunluktaki dönemlerde ortak alan tüketimi 500’den 350 kilovatsaate düştü; ölçüme dairelerin tüketimi dahil edilmedi.',
['500→350 kilovatsaat, eşit dönemler.','Yalnız ortak alan, daireler hariç.']),
('faithful_summary','arts','temporal,refund','Metni iki cümlede özetle.',
'Kurgusal Taş Sahnenin cuma akşamı yapılacak açık hava gösterisi fırtına tahmini nedeniyle iptal edildi. Gösteri için yeni tarih belirlenmedi. Bilet sahipleri, satın aldıkları kanaldan yedi gün içinde iade isteyebilecek. Cumartesi günkü kapalı salon gösterisi programlandığı gibi yapılacak.',
'Taş Sahnenin cuma günkü açık hava gösterisi fırtına tahmini nedeniyle iptal edildi ve yeni tarih belirlenmedi; bilet sahipleri satın alma kanalından yedi gün içinde iade isteyebilecek. Cumartesi günkü kapalı salon gösterisi değişmedi.',
['Cuma açık hava iptal; yeni tarih yok.','Yedi günde aynı kanaldan iade başvurusu.','Cumartesi kapalı salon sürüyor.']),
('faithful_summary','education','detail,coverage','Metni 3–4 cümlelik bir paragrafla özetle; temel uygulama ayrıntılarını koru.',
'Kurgusal Ufuk Öğrenme Merkezi, yetişkinler için altı haftalık ücretsiz okuma grubu açıyor. Grup salı ve perşembe akşamları toplanacak. Her toplantının ilk bölümünde kısa bir metin birlikte okunacak, ikinci bölümünde katılımcılar metni kendi sözleriyle anlatacak. Amaç sınava hazırlamak değil, gündelik metinleri anlamayı ve anlatmayı desteklemek. Merkez basılı metinleri sağlayacak; katılımcıların bilgisayar getirmesine gerek yok. Kontenjan 12 kişi ve kayıtlar başvuru sırasına göre alınacak. Devam zorunluluğu bulunmuyor ancak kayıt yaptırıp katılamayacak kişilerin merkeze haber vermesi isteniyor.',
'Ufuk Öğrenme Merkezi, yetişkinlerin gündelik metinleri anlamasını ve anlatmasını desteklemek için altı haftalık ücretsiz bir okuma grubu açıyor; çalışma sınava hazırlık amacı taşımıyor. Salı ve perşembe akşamları önce kısa bir metin birlikte okunacak, ardından katılımcılar metni kendi sözleriyle anlatacak; basılı metinleri merkez sağlayacak ve bilgisayar gerekmeyecek. Başvuru sırasına göre alınacak 12 katılımcı için devam zorunluluğu yok. Kayıt yaptırıp katılamayacak kişilerin merkeze haber vermesi isteniyor.',
['Altı hafta ücretsiz, yetişkin gündelik okuma; sınav değil.','Salı perşembe, birlikte okuma ve yeniden anlatma.','Metin merkezden, bilgisayar yok.','12 kişi sıra ile; devam zorunlu değil, gelemeyen haber verir.']),
('faithful_summary','repair','sequence,conditions','Süreci tek cümlede özetle.',
'Kurgusal Onar Evi, küçük ev aletlerini önce ücretsiz inceliyor. İncelemeden sonra arızayı ve tahmini ücreti yazılı bildiriyor. Müşteri onay verirse onarıma başlanıyor; onay vermeyen müşteriden inceleme ücreti alınmıyor. Parça beklenmesi gerekiyorsa teslim tarihi ayrıca kararlaştırılıyor.',
'Onar Evi ücretsiz incelemenin ardından arıza ve tahmini ücreti yazılı bildiriyor, yalnızca müşteri onayıyla onarıma başlıyor ve parça beklenirse teslim tarihini ayrıca kararlaştırıyor.',
['İnceleme ücretsiz; ret halinde de ücret yok.','Yazılı arıza ve tahmini ücret, sonra onay.','Parça bekleme halinde tarih ayrıca.']),
('grounded_qa','inventory','arithmetic,units','Kaç defter kaldı? Yalnızca sayı ve birimle yanıtla.',
'Kurgusal bir atölyede 72 defter vardı. Sabah 18, öğleden sonra 24 defter dağıtıldı. Yeni defter gelmedi.',
'30 defter',['72−18−24=30 defter.']),
('grounded_qa','schedule','entity,time','Prova hangi gün ve saat kaçta? Tek cümleyle yanıtla.',
'Kurgusal Korunun konseri pazar günü 19.00’da, son provası ise cumartesi 16.30’da yapılacak.',
'Prova cumartesi günü 16.30’da yapılacak.',['Konser ile provayı karıştırma.']),
('grounded_qa','library','exception,answerable','Atlas kitabını en geç ne zaman geri vermeli? Kısa yanıtla.',
'Kurgusal Gezgin Kütüphanesinde kitaplar normalde 14 gün ödünç verilir. Yeni çıkan kitaplarda süre 7 gündür. Atlas bugün yeni çıkan bir kitap aldı.',
'Bugünden itibaren 7 gün içinde.',['Yeni kitap istisnası: 7 gün.']),
('grounded_qa','manufacturing','unanswerable','Metne göre arızaya ne sebep oldu?',
'Kurgusal bir üretim hattı saat 10.20’de durdu. Ekip iki sensörü değiştirdi ve hat 11.10’da yeniden çalıştı. İnceleme raporu henüz tamamlanmadı; arızanın nedeni belirtilmedi.',
'Metinde arızanın nedeni belirtilmiyor.',['Sensör değişimi nedenin kanıtı değil.']),
('grounded_qa','volunteering','multi_fact','Hangi iki koşulu sağlayanlar başvurabilir?',
'Kurgusal Koru Gönüllüleri ekibine başvurmak için 18 yaşını doldurmuş olmak ve cumartesi sabahları iki saat ayırabilmek gerekiyor. Önceden bahçecilik deneyimi aranmıyor.',
'18 yaşını doldurmuş ve cumartesi sabahları iki saat ayırabilecek kişiler başvurabilir.',['İki zorunlu koşul.','Deneyim koşulu ekleme.']),
('grounded_qa','delivery','conditional,negation','Siparişin yarın kesin teslim edileceği söylenebilir mi? Gerekçesiyle tek cümlede yanıtla.',
'Kurgusal dağıtıcı, köprü akşama kadar açılırsa siparişi yarın getireceğini bildirdi. Köprünün açılıp açılmadığı henüz bilinmiyor.',
'Hayır, yarın teslimat köprünün akşama kadar açılması koşuluna bağlı ve bu koşulun sağlandığı henüz bilinmiyor.',['Teslim kesin değil; köprü koşulu bilinmiyor.']),
('grounded_qa','museum','unanswerable,date','Sergi hangi yıl açıldı?',
'Kurgusal Deniz İzleri sergisi 4 haziranda açıldı. Haberde serginin yılı verilmedi; yalnızca hafta sonları ziyaret edilebildiği belirtildi.',
'Metinde serginin açıldığı yıl belirtilmiyor.',['Günü yıldan ayır; yıl uydurma.']),
('grounded_qa','recycling','comparison,arithmetic','İki grubun topladığı miktarlar arasındaki fark kaç kilogram? Yalnızca sonucu yaz.',
'Kurgusal bir toplama gününde Lale grubu 48 kilogram, Çam grubu 35 kilogram kağıt topladı. Ölçümler aynı tartıyla yapıldı.',
'13 kilogram',['48−35=13; toplam değil fark.']),
('translation','everyday','negation,tense','Aşağıdaki İngilizce cümleyi Türkçeye çevir. Yalnızca çeviriyi yaz.',
'I have not sent the revised invitation yet.',
'Düzenlenmiş davetiyeyi henüz göndermedim.',['Olumsuzluk ve henüz; geçmiş tamamlanma.']),
('translation','workplace','condition,quantity','Türkçeye çevir; açıklama ekleme.',
'If the supplier confirms today, we can deliver all twelve chairs on Friday.',
'Tedarikçi bugün onay verirse on iki sandalyenin tamamını cuma günü teslim edebiliriz.',['Bugün onay koşulu; 12; cuma; olasılık.']),
('translation','travel','contrast,entities','Türkçeye çevir. Yalnızca çeviri metnini ver.',
'Mina left her blue suitcase at the station, not at the hotel.',
'Mina mavi valizini otelde değil, istasyonda bıraktı.',['Mina, mavi valiz, istasyon; otel değil.']),
('translation','technology','modality,negation','Aşağıdaki mesajı doğal Türkçeye çevir.',
'You can read saved messages offline, but new messages will not arrive until you reconnect.',
'Kaydedilmiş mesajları çevrimdışıyken okuyabilirsiniz ancak yeniden bağlanana kadar yeni mesajlar gelmez.',['Kayıtlı okunabilir; yeniler bağlantıya kadar gelmez.']),
('translation','everyday','polysemy,requested_explanation','Cümleyi Türkçeye çevir, ardından “light” sözcüğünün burada hangi anlamda kullanıldığını bir cümleyle açıkla.',
'This bag is light enough for a child to carry.',
'Bu çanta bir çocuğun taşıyabileceği kadar hafif.\n“Light” burada ağırlığın az olduğunu, yani “hafif” anlamını ifade ediyor.',
['Çanta çocuk taşıyabilecek kadar hafif.','İstenen açıklama var; ışık anlamı değil.']),
('translation','research','uncertainty,causality','Türkçeye çevir; yorum yapma.',
'The results suggest a possible link, but they do not prove that one change caused the other.',
'Sonuçlar olası bir bağlantıya işaret ediyor ancak bir değişikliğin diğerine neden olduğunu kanıtlamıyor.',
['Olasılık; nedensellik kanıtlanmıyor.']),
('instruction_control','events','json,extraction','Bilgileri yalnızca geçerli bir JSON nesnesi olarak yaz. Anahtarlar ad, gun ve ucret_tl olsun; ücret sayı olsun.',
'Kurgusal etkinliğin adı Kil Buluşması, günü perşembe, katılım ücreti 75 TL.',
'{"ad":"Kil Buluşması","gun":"perşembe","ucret_tl":75}',
['Üç doğru alan, 75 sayısal; çit ve açıklama yok.']),
('instruction_control','organization','bullets,ordering','İşleri verilen sırayı koruyarak tam üç maddeyle yaz. Başlık ekleme.',
'Önce dosyaları yedekle. Ardından eski kopyaları karşılaştır. Son olarak yinelenen kopyaları ayır.',
'- Dosyaları yedekle.\n- Eski kopyaları karşılaştır.\n- Yinelenen kopyaları ayır.',
['Üç madde ve sıra; ek iş yok.']),
('instruction_control','learning','requested_detail,explanation','Bir konuyu öğrenirken aralıklı tekrarın nasıl uygulanabileceğini 4 cümleyle açıkla. Somut bir çalışma örneği ver.',
'',
'Aralıklı tekrar, öğrendiğin bilgiyi tek oturumda sürekli okumak yerine farklı günlerde yeniden hatırlamayı denemektir. Örneğin bugün öğrendiğin on kelimeyi yarın, birkaç gün sonra ve ertesi hafta kendini sınayarak tekrar edebilirsin. Zorlandığın kelimeleri daha sık, kolay hatırladıklarını daha seyrek gözden geçirebilirsin. Her tekrarda önce cevabı hatırlamaya çalışıp ardından doğruluğunu kontrol edebilirsin.',
['Dört cümle; somut kelime ve gün örneği.','Her zaman kısa yanıt ilkesi öğretme; kullanıcı açıklama istiyor.']),
('instruction_control','planning','multi_turn,context','Bunu yalnızca pazartesinin etkinliği kalacak şekilde kısalt. Başlık yazma.',
'',
'Pazartesi: Çizim atölyesi.',
['Son kullanıcı pazartesiyi seçiyor.','Önceki bağlamdaki etkinliği koru.']),
('minimal_correction','everyday','spelling,minimal_edit','Yalnızca düzeltilmiş cümleyi yaz; anlamını değiştirme.',
'Yarın ki toplantıya bende katılacağım.',
'Yarınki toplantıya ben de katılacağım.',['Yarınki birleşik, ben de ayrı; diğer içerik aynı.']),
('minimal_correction','everyday','unchanged_control,negation','Yazım yanlışı varsa düzelt. Yoksa cümleyi aynen yaz. Açıklama ekleme.',
'Bu akşam dışarı çıkmayacağım.',
'Bu akşam dışarı çıkmayacağım.',['Zaten doğru, olumsuzluğu ve yazımı aynen koru.']),
]


def main():
    rows = []
    for n, (cap, domain, skills, instruction, context, target, facts) in enumerate(EXAMPLES, 1):
        messages = [{'role': 'user', 'content': instruction + ('\n\n' + context if context else '')}]
        if n == 38:
            messages = [
                {'role': 'user', 'content': 'Kurgusal programda pazartesi çizim atölyesi, salı müzik dinletisi var. İkisini listele.'},
                {'role': 'assistant', 'content': 'Pazartesi: Çizim atölyesi.\nSalı: Müzik dinletisi.'},
                *messages,
            ]
        row = dict(id=f'tr-sft-pilot-{n:03d}', capability=cap, subskills=skills.split(','),
            source_family=f'pilot-original-{n:03d}', scenario_group=f'pilot-original-{n:03d}',
            split='train', domain=domain, source_context=context,
            source_provenance={'kind':'original_synthetic', 'author':'Codex agent in this session',
                'date':'2026-11-13', 'external_source':None,
                'note':'Fictional scenarios; not an external factual source or benchmark transformation.'},
            messages=messages, target=target,
            target_authoring_provenance='Agent-authored final answer; no external teacher API or hidden reasoning trace.',
            review_status='draft_pending_independent_semantic_and_human_review',
            rubric={'required_facts':facts, 'general_checks':['Supported meaning and complete requested coverage',
                'Entity/number/negation/modality fidelity', 'Requested format and natural Turkish',
                'No unrelated continuation or commentary; acceptable equivalent wording allowed']})
        payload = json.dumps({'messages':messages,'target':target}, ensure_ascii=False, sort_keys=True)
        row['content_sha256'] = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        rows.append(row)
    assert len(rows) == 40
    OUT.mkdir(exist_ok=True)
    (OUT/'pilot-train-draft.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    blocks = ['TURKISH SFT PILOT — 40 TRAINING-ONLY DRAFTS\n'
        'Targets are proposals, not human-approved labels. All scenarios are original synthetic examples.\n'
        'Rubrics are review metadata and must not be serialized into training messages.\n']
    for row in rows:
        block = f"{row['id']} | {row['capability']} | {row['domain']}\n"
        block += '\n\n'.join(f"{m['role'].upper()}:\n{m['content']}" for m in row['messages'])
        block += '\n\nTARGET:\n'+row['target']+'\n\nREQUIRED FACTS / REVIEW NOTES:\n'
        block += '\n'.join('- '+s for s in row['rubric']['required_facts'])
        blocks.append(block)
    (OUT/'PILOT-REVIEW.txt').write_text('\n\n----\n\n'.join(blocks)+'\n',encoding='utf-8')
    print(f'Wrote {len(rows)} training-only drafts and full review text.')


if __name__ == '__main__':
    main()
