"""Write the 40-prompt native Turkish writing probe (authored by hand, no external source, no license issue).

Each row: id, category, prompt, optional automatic constraint check. Output is committed (small, original text):
experiments/turkish-capability/lfm3-1.7b/eval-v2/writing-prompts-tr.jsonl
Constraint kinds: max_words N, exact_sentences N, bullets N (lines starting with - * or a number), must_include [words].
"""
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'experiments/turkish-capability/lfm3-1.7b/eval-v2/writing-prompts-tr.jsonl'

PARAGRAPHS = {
    'su': 'Türkiye\'de son yıllarda barajlardaki doluluk oranı mevsimlere göre büyük dalgalanma gösteriyor. Kış aylarında yağışların '
          'azalması, tarımsal sulamanın yaz aylarında artması ve kentlerdeki tüketimin yükselmesi su kaynakları üzerindeki baskıyı '
          'artırıyor. Uzmanlar, damla sulama gibi verimli yöntemlerin yaygınlaştırılmasının ve şebeke kayıplarının azaltılmasının '
          'kısa vadede en etkili çözümler olduğunu söylüyor.',
    'bisiklet': 'Belediye, şehir merkezinde yeni bir bisiklet yolu açtığını duyurdu. Yol, tren garını üniversite kampüsüne bağlıyor ve '
                'toplam on iki kilometre uzunluğunda. Bisiklet yolunun yanında park yerleri ve tamir istasyonları da kuruldu. '
                'Yetkililer, ilk altı ayda günlük kullanıcı sayısının üç bini aşmasını bekliyor.',
    'kitap': 'Kütüphanenin yeni dönem üyelik koşulları değişti. Artık öğrenciler kimlik kartlarını göstererek ücretsiz üye olabiliyor, '
             'diğer yetişkinler ise yıllık yüz yirmi lira ödüyor. Üyeler aynı anda altı kitap alabiliyor ve kitapları en fazla yirmi '
             'bir gün tutabiliyor. Süresi geçen her gün için elli kuruş gecikme cezası uygulanıyor.',
    'uyku': 'Uyku araştırmacıları, yetişkinlerin çoğunun gece yedi ile dokuz saat arasında uykuya ihtiyaç duyduğunu belirtiyor. '
            'Düzensiz uyku saatleri, yatmadan önce ekran kullanımı ve akşam geç saatlerde alınan kafein uykunun kalitesini düşüren '
            'başlıca etkenler arasında sayılıyor. Her gün aynı saatte yatıp kalkmak ise en basit ve etkili alışkanlıklardan biri olarak görülüyor.',
    'enerji': 'Bir şirket, fabrikasının çatısına güneş enerjisi panelleri kurarak elektrik faturasını yüzde otuz azalttı. '
              'Yatırımın maliyeti yaklaşık dört yılda geri dönecek. Şirket yetkilileri, ikinci aşamada depolama bataryaları ekleyerek '
              'geceleri de kendi enerjisini kullanmayı planladıklarını açıkladı.',
    'kahve': 'Türk kahvesi, 2013 yılında UNESCO tarafından somut olmayan kültürel miras listesine alındı. Kahve, cezvede kısık ateşte '
             'pişirilir ve genellikle şekerle birlikte, küçük fincanlarda sunulur. Kahvenin yanında verilen su ve lokum da geleneğin bir parçasıdır. '
             'Fincanın dibinde kalan telveden fal bakmak ise sohbetin eğlenceli bir bölümü sayılır.',
}

ROWS = [
    # explanations
    ('explain', 'Fotosentez nedir? Bir ortaokul öğrencisine anlatır gibi açıkla.', None),
    ('explain', 'Enflasyon neden fiyatların artmasına yol açar? Gündelik bir örnekle anlat.', None),
    ('explain', 'Bir internet sitesine girdiğimizde arka planda neler olur? Teknik terimleri en aza indirerek anlat.', None),
    ('explain', 'Bulutlar neden yağmur yağdırır? Kısa ve anlaşılır bir açıklama yaz.', None),
    ('explain', 'Bir bankanın faiz oranı ile bir yatırım fonunun getirisi arasındaki farkı basit bir dille açıkla.', None),
    ('explain', 'Yapay zekâ modelleri metin yazmayı nasıl öğrenir? Programcı olmayan birine anlat.', None),
    ('explain', 'Mevsimler neden oluşur? Dünyanın eğikliğinden bahsederek açıkla.', None),
    ('explain', 'Bir kişinin kredi notu neye göre belirlenir ve nasıl yükseltilir?', None),
    # emails, letters
    ('email', 'Kiracı olduğun evdeki kombi bozuldu. Ev sahibine durumu bildiren, kibar ama net bir e-posta yaz.', None),
    ('email', 'Müdürüne gelecek hafta iki gün izin istediğini bildiren resmî bir e-posta yaz. İzin gerekçesi: kardeşinin düğünü.', None),
    ('email', 'Aldığın bir ürünün yanlış rengini fark ettin. Müşteri hizmetlerine değişim talebini anlatan bir mesaj yaz.', None),
    ('email', 'Bir iş görüşmesinden sonra görüşmeyi yapan kişiye teşekkür eden kısa bir e-posta yaz.', None),
    ('email', 'Komşularına, cumartesi akşamı evinde küçük bir doğum günü kutlaması yapacağını ve biraz gürültü olabileceğini nazikçe duyuran bir not yaz.', None),
    ('email', 'Üniversitedeki hocana, ödev teslim tarihini bir gün uzatmasını rica eden bir e-posta yaz. Hastalandığını belirt.', None),
    # summaries
    ('summary', f'Aşağıdaki metni iki cümleyle özetle.\n\n{PARAGRAPHS["su"]}', dict(exact_sentences=2)),
    ('summary', f'Aşağıdaki haberi tek cümleyle özetle.\n\n{PARAGRAPHS["bisiklet"]}', dict(exact_sentences=1)),
    ('summary', f'Aşağıdaki metindeki önemli bilgileri üç madde halinde yaz.\n\n{PARAGRAPHS["kitap"]}', dict(bullets=3)),
    ('summary', f'Aşağıdaki metni en fazla otuz kelimeyle özetle.\n\n{PARAGRAPHS["uyku"]}', dict(max_words=30)),
    ('summary', f'Aşağıdaki haberin başlığını yaz ve ardından iki cümlelik bir özet ver.\n\n{PARAGRAPHS["enerji"]}', None),
    ('summary', f'Aşağıdaki metinden yola çıkarak "Türk kahvesi neden kültürel miras sayılıyor?" sorusunu yanıtla.\n\n{PARAGRAPHS["kahve"]}', None),
    # rewriting
    ('rewrite', 'Şu cümleyi daha resmî bir dille yeniden yaz: "Abi, toplantıyı biraz erteleyebilir miyiz, işim çıktı."', None),
    ('rewrite', 'Şu cümleyi sade ve kısa hale getir: "Tarafımızca gerçekleştirilen değerlendirme neticesinde söz konusu başvurunun kabul edilmesine karar verilmiştir."', None),
    ('rewrite', 'Şu paragrafı daha akıcı hale getir: "Hava soğuktu. Biz dışarı çıktık. Dışarıda kimse yoktu. Biz yürüdük. Yürürken konuştuk."', None),
    ('rewrite', 'Şu cümledeki yazım ve anlatım hatalarını düzelt: "Dün akşam arkadaşlarla bulusup yemeğe gittik ama yer bulamadıgımız için eve geri dönmek zorunda kaldık."', None),
    # creative
    ('creative', 'Yağmurlu bir pazar sabahını anlatan, beş cümlelik kısa bir paragraf yaz.', dict(exact_sentences=5)),
    ('creative', 'Kedisini kaybeden bir çocuğun hikâyesini üç kısa paragrafta anlat. Hikâye mutlu bitsin.', None),
    ('creative', 'İstanbul\'da vapurla yapılan bir yolculuğu anlatan kısa bir şiir yaz.', None),
    ('creative', 'Yeni açılan bir kitapçı için iki cümlelik, akılda kalıcı bir reklam metni yaz.', dict(exact_sentences=2)),
    # constrained instructions
    ('constraint', 'Sağlıklı beslenmek için beş öneriyi madde işaretleriyle yaz.', dict(bullets=5)),
    ('constraint', 'İstanbul\'u ilk kez ziyaret edecek biri için en fazla elli kelimelik bir tavsiye yaz.', dict(max_words=50)),
    ('constraint', 'Ankara hakkında tam üç cümle yaz.', dict(exact_sentences=3)),
    ('constraint', '"Zaman" kelimesini en az bir kez kullanarak iki cümlelik bir söz yaz.', dict(exact_sentences=2, must_include=['zaman'])),
    ('constraint', 'Bir ofis çalışanı için dört maddelik bir sabah rutini öner.', dict(bullets=4)),
    ('constraint', 'Yeni bir dil öğrenmenin faydalarını en fazla kırk kelimeyle anlat.', dict(max_words=40)),
    # advice and discussion
    ('advice', 'İlk kez bir bilgisayar satın alacak biri hangi noktalara dikkat etmeli?', None),
    ('advice', 'Sınavdan önceki gece nasıl bir hazırlık yapmak daha verimli olur?', None),
    ('advice', 'Evde bitki yetiştirmeye yeni başlayanlara birkaç öneri ver.', None),
    ('advice', 'Bir arkadaşınla yaşadığın küçük bir tartışmadan sonra barışmak için ne yapabilirsin?', None),
    # translation
    ('translate', 'Şu cümleyi Türkçeye çevir: "The meeting has been moved to Thursday because several colleagues will be traveling on Wednesday."', None),
    ('translate', 'Şu cümleyi Türkçeye çevir: "If you have any questions about the new policy, please contact the human resources department."', None),
]


def main():
    rows = []
    for i, (category, prompt, check) in enumerate(ROWS, 1):
        rows.append(dict(id=f'wr-tr-{i:02d}', category=category, prompt=prompt, check=check))
    assert len(rows) == 40, len(rows)
    OUT.write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n', encoding='utf-8', newline='\n')
    print(len(rows), OUT.name, hashlib.sha256(OUT.read_bytes()).hexdigest()[:16])


if __name__ == '__main__':
    main()
