"""Freeze the fresh bilingual-pilot diagnostic: 35 new underlying tasks x 4 directions (140 prompts) plus a
separate symbolic arithmetic control set. Authored BEFORE any training-data translation; never training data,
never a generation demonstration. References live in a separate file so annotation displays can omit them.

Verify/reproduce: python scripts/datasets/prepare_lfm3_bilingual_pilot_eval.py  (existing files must match byte for byte)
"""
import ast
import datetime
import json
import operator
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import (DIRECTIONS, PILOT, SYSTEM, freeze, json_bytes, jsonl_bytes, sha256_bytes,
                                    with_instruction)

OUT = PILOT / 'eval-v01'


def T(task_id, category, tr, en, ref_tr, ref_en, final, facts_tr, facts_en, rubric, verify=None):
    return dict(task_id=task_id, category=category, tr=tr, en=en, ref_tr=ref_tr, ref_en=ref_en, final=final,
                facts_tr=facts_tr, facts_en=facts_en, rubric=rubric, verify=verify)


def _date_check():
    start = datetime.date(2025, 3, 3)
    assert start.strftime('%A') == 'Monday'
    due = start + datetime.timedelta(days=21)
    assert due.strftime('%A') == 'Monday' and (due.month, due.day) == (3, 24)
    return '24 March, Monday (open)'


def _end_time():
    t = datetime.datetime(2025, 1, 1, 19, 45) + datetime.timedelta(minutes=20) + datetime.timedelta(hours=2, minutes=35)
    return t.strftime('%H:%M')


TASKS = [
    # ---------------- arithmetic (8) ----------------
    T('ar01-ticket-change', 'arithmetic',
      "Bir otobüs bileti 27 TL. Selin 4 bilet alıp satıcıya 200 TL veriyor, ardından para üstünün 30 TL'sini kardeşine veriyor. Selin'in elinde para üstünden kaç TL kalır? Kısa bir hesaplama ve sonucu yaz.",
      "A bus ticket costs 27 TL. Selin buys 4 tickets and hands the seller 200 TL, then gives 30 TL of her change to her brother. How many TL of the change does Selin have left? Give a brief calculation and the result.",
      "4 bilet 4 × 27 = 108 TL tutar. Para üstü 200 − 108 = 92 TL'dir; kardeşine 30 TL verince 92 − 30 = 62 TL kalır.",
      "Four tickets cost 4 × 27 = 108 TL. The change is 200 − 108 = 92 TL; after giving 30 TL to her brother, 62 TL remains.",
      '62', ['108', '92', '62'], ['108', '92', '62'],
      'Final 62 TL; intermediates 108 and 92 if shown. A common error is stopping at 92 or subtracting 30 from 200.',
      lambda: str(200 - 4 * 27 - 30)),
    T('ar02-sequential-discount', 'arithmetic',
      "Bir montun etiket fiyatı 800 TL. Önce %25 indirim yapılıyor, ardından indirimli fiyat üzerinden ayrıca %10 indirim daha uygulanıyor. Son fiyat kaç TL olur? Kısa bir hesaplama ve sonucu yaz.",
      "A coat has a tag price of 800 TL. First a 25% discount is applied, then a further 10% discount is applied to the discounted price. What is the final price in TL? Give a brief calculation and the result.",
      "İlk indirimden sonra fiyat 800 × 0,75 = 600 TL olur. İkinci indirimden sonra 600 × 0,90 = 540 TL kalır.",
      "After the first discount the price is 800 × 0.75 = 600 TL. After the second discount it is 600 × 0.90 = 540 TL.",
      '540', ['600', '540'], ['600', '540'],
      'Final 540 TL. Adding the percentages (35% off = 520 TL) is the typical error and is wrong.',
      lambda: str(Fraction(800) * Fraction(3, 4) * Fraction(9, 10))),
    T('ar03-session-end-time', 'arithmetic',
      "Bir sinema seansı saat 19.45'te başlıyor. Önce 20 dakika reklam gösteriliyor, ardından 2 saat 35 dakikalık film oynatılıyor. Seans saat kaçta biter? Kısa bir hesaplama ve sonucu yaz.",
      "A cinema session starts at 19:45. First 20 minutes of ads are shown, then a film lasting 2 hours 35 minutes is played. At what time does the session end? Give a brief calculation and the result.",
      "Reklamlar 20.05'te biter. Film 2 saat 35 dakika sürdüğü için seans 22.40'ta sona erer.",
      "The ads end at 20:05. Since the film lasts 2 hours 35 minutes, the session ends at 22:40.",
      '22:40', ['20.05', '22.40'], ['20:05', '22:40'],
      'Final time 22:40 (22.40 accepted). Intermediate 20:05 if shown.',
      _end_time),
    T('ar04-ratio-share', 'arithmetic',
      "Üç arkadaş 840 TL'lik bir ödülü 2:3:5 oranında paylaşıyor. En çok parayı alan kişi, en az parayı alandan kaç TL fazla alır? Kısa bir hesaplama ve sonucu yaz.",
      "Three friends share a prize of 840 TL in the ratio 2:3:5. How many TL more does the person with the largest share receive than the person with the smallest share? Give a brief calculation and the result.",
      "Oran toplamı 2 + 3 + 5 = 10, bir pay 840 / 10 = 84 TL'dir. En küçük pay 2 × 84 = 168 TL, en büyük pay 5 × 84 = 420 TL; fark 420 − 168 = 252 TL.",
      "The ratio parts sum to 2 + 3 + 5 = 10, so one part is 840 / 10 = 84 TL. The smallest share is 2 × 84 = 168 TL and the largest is 5 × 84 = 420 TL; the difference is 420 − 168 = 252 TL.",
      '252', ['84', '168', '420', '252'], ['84', '168', '420', '252'],
      'Final difference 252 TL (not the largest share 420 and not the sum 840).',
      lambda: str(Fraction(840, 10) * (5 - 2))),
    T('ar05-net-fill-rate', 'arithmetic',
      "Bir su deposunun kapasitesi 450 litre ve şu anda içinde 120 litre su var. Bir musluk dakikada 15 litre su doldururken depodaki bir kaçak dakikada 5 litre su kaybettiriyor. Depo kaç dakikada dolar? Kısa bir hesaplama ve sonucu yaz.",
      "A water tank has a capacity of 450 litres and currently holds 120 litres. A tap adds 15 litres per minute while a leak in the tank loses 5 litres per minute. How many minutes does it take to fill the tank? Give a brief calculation and the result.",
      "Net doldurma hızı 15 − 5 = 10 litre/dakikadır. Doldurulacak miktar 450 − 120 = 330 litre olduğundan süre 330 / 10 = 33 dakikadır.",
      "The net filling rate is 15 − 5 = 10 litres per minute. The amount still to be filled is 450 − 120 = 330 litres, so it takes 330 / 10 = 33 minutes.",
      '33', ['10', '330', '33'], ['10', '330', '33'],
      'Final 33 minutes. Ignoring the leak gives 22; ignoring the initial 120 L gives 45.',
      lambda: str(Fraction(450 - 120, 15 - 5))),
    T('ar06-percent-up-down', 'arithmetic',
      "Bir ürünün fiyatı 250 TL iken önce %20 zam yapılıyor, ardından yeni fiyatın %20'si kadar indirim uygulanıyor. Ürünün son fiyatı kaç TL olur ve ilk fiyattan farklı mıdır? Kısa bir hesaplama ve sonucu yaz.",
      "A product costs 250 TL. First its price is raised by 20%, then a discount of 20% of the new price is applied. What is the final price in TL, and is it different from the original price? Give a brief calculation and the result.",
      "Zamlı fiyat 250 × 1,20 = 300 TL'dir. %20 indirimle 300 × 0,80 = 240 TL olur. Son fiyat ilk fiyattan farklıdır; 10 TL daha düşüktür.",
      "The raised price is 250 × 1.20 = 300 TL. After the 20% discount it is 300 × 0.80 = 240 TL. The final price differs from the original; it is 10 TL lower.",
      '240', ['300', '240', '10'], ['300', '240', '10'],
      'Final 240 TL and must state it is different (10 TL lower). Claiming it returns to 250 is wrong.',
      lambda: str(Fraction(250) * Fraction(6, 5) * Fraction(4, 5))),
    T('ar07-average-target', 'arithmetic',
      "Bir öğrencinin ilk üç sınavdan aldığı puanlar 70, 85 ve 90'dır. Dört sınavın ortalamasının 85 olması için dördüncü sınavdan en az kaç puan alması gerekir? Kısa bir hesaplama ve sonucu yaz.",
      "A student's scores on the first three exams are 70, 85 and 90. What is the minimum score the student needs on the fourth exam for the average of all four exams to be 85? Give a brief calculation and the result.",
      "Dört sınavın toplamı 4 × 85 = 340 olmalıdır. İlk üçün toplamı 70 + 85 + 90 = 245'tir, dolayısıyla dördüncü sınavdan 340 − 245 = 95 puan gerekir.",
      "The four scores must total 4 × 85 = 340. The first three total 70 + 85 + 90 = 245, so the fourth exam must score 340 − 245 = 95.",
      '95', ['340', '245', '95'], ['340', '245', '95'],
      'Final 95. Averaging the three scores to 81.67 or answering 85 are errors.',
      lambda: str(4 * 85 - (70 + 85 + 90))),
    T('ar08-egg-boxes', 'arithmetic',
      "Bir çiftlikte 270 yumurta var. Yumurtalar 12'lik kutulara dolduruluyor ve yalnızca dolu kutular satılıyor; her kutu 90 TL'ye satılıyor. Satıştan toplam kaç TL gelir elde edilir ve kaç yumurta açıkta kalır? Kısa bir hesaplama ve sonucu yaz.",
      "A farm has 270 eggs. The eggs are packed into boxes of 12 and only full boxes are sold, each box for 90 TL. How many TL of revenue does the sale bring in, and how many eggs are left over? Give a brief calculation and the result.",
      "270 / 12 = 22 kalan 6 olduğundan 22 dolu kutu olur. Gelir 22 × 90 = 1980 TL'dir ve 6 yumurta açıkta kalır.",
      "270 / 12 = 22 remainder 6, so there are 22 full boxes. The revenue is 22 × 90 = 1980 TL and 6 eggs are left over.",
      '1980 TL; 6 eggs', ['22', '1980', '6'], ['22', '1980', '6'],
      'Both values required: revenue 1980 TL and 6 leftover eggs. Rounding boxes up to 23 (2070 TL) is wrong.',
      lambda: f'{(270 // 12) * 90} TL; {270 % 12} eggs'),
    # ---------------- Turkish comprehension (6) ----------------
    T('co01-library-due-date', 'turkish_comprehension',
      "Yalnızca aşağıdaki duyuruya bakarak soruyu yanıtla.\n\nDuyuru: Belediye kütüphanesi hafta içi 09.00–18.00, cumartesi 10.00–14.00 saatleri arasında hizmet verir. Pazar günü kapalıdır. Ödünç alınan kitaplar 21 gün içinde iade edilmelidir.\n\nSoru: Bir kitabı 3 Mart Pazartesi günü ödünç alan kişi kitabı en geç hangi tarihte iade etmelidir ve kütüphane o gün açık mıdır?",
      "Answer the question using only the notice below.\n\nNotice: The municipal library is open 09:00–18:00 on weekdays and 10:00–14:00 on Saturdays. It is closed on Sundays. Borrowed books must be returned within 21 days.\n\nQuestion: By what date must a person who borrowed a book on Monday, 3 March return it, and is the library open that day?",
      "Kitap en geç 24 Mart'ta iade edilmelidir. 3 Mart'tan 21 gün sonrası da Pazartesi'ye denk geldiği için hafta içidir ve kütüphane o gün 09.00–18.00 arasında açıktır.",
      "The book must be returned by 24 March. Since 21 days after Monday, 3 March is also a Monday, it is a weekday and the library is open from 09:00 to 18:00 that day.",
      '24 March, Monday (open)', ['24 Mart', 'açık'], ['24 March', 'open'],
      'Due date 24 March (a Monday, so open). Must not invent holiday information.',
      _date_check),
    T('co02-camp-unstated', 'turkish_comprehension',
      "Aşağıdaki haberi oku ve soruyu yalnızca haberdeki bilgilere dayanarak yanıtla.\n\nHaber: Kaşgar Spor Kulübü, genç sporcular için yaz kampını 15 Temmuz'da başlatacak. Kamp iki hafta sürecek ve katılım ücretsiz olacak; ancak kayıtlar kontenjanla sınırlı. Konaklama ve ulaşım ayrıca belirtilmemiştir.\n\nSoru: Kampa katılanların ulaşım masraflarını kulüp karşılayacak mı?",
      "Read the news item below and answer the question based only on the information in it.\n\nNews item: Kaşgar Sports Club will start its summer camp for young athletes on 15 July. The camp will last two weeks and participation will be free, but registration is limited by quota. Accommodation and transport are not specified separately.\n\nQuestion: Will the club cover the participants' transport costs?",
      "Bu haberden anlaşılamaz. Katılımın ücretsiz olacağı belirtiliyor, ancak ulaşımın nasıl karşılanacağı ayrıca belirtilmemiştir; bu yüzden kulübün ulaşım masraflarını karşılayıp karşılamayacağını bilemeyiz.",
      "This cannot be determined from the news item. It says participation will be free, but how transport is handled is not specified, so we cannot know whether the club will cover transport costs.",
      'not determinable from the text', ['belirtilmemiş', 'bilinemez'], ['not specified', 'cannot'],
      'Must say the text does not establish this. Answering yes (because participation is free) or no is an unsupported claim.',
      None),
    T('co03-rainfall-table', 'turkish_comprehension',
      "Aşağıdaki tabloya göre soruyu yanıtla.\n\nAylık yağış miktarı (mm): Ocak 48, Şubat 36, Mart 52, Nisan 41.\n\nSoru: En yağışlı ay hangisidir ve ilk dört ayın toplam yağışı kaç mm'dir?",
      "Answer the question according to the table below.\n\nMonthly rainfall (mm): January 48, February 36, March 52, April 41.\n\nQuestion: Which month is the rainiest, and what is the total rainfall of the first four months in mm?",
      "En yağışlı ay 52 mm ile Mart'tır. İlk dört ayın toplam yağışı 48 + 36 + 52 + 41 = 177 mm'dir.",
      "The rainiest month is March with 52 mm. The total rainfall of the first four months is 48 + 36 + 52 + 41 = 177 mm.",
      'March; 177 mm', ['Mart', '177'], ['March', '177'],
      'Both parts: March and 177 mm.',
      lambda: f'March; {48 + 36 + 52 + 41} mm'),
    T('co04-branch-hours', 'turkish_comprehension',
      "Metni dikkatle oku ve soruyu yanıtla.\n\nMetin: Bursa şubesi yalnızca randevuyla müşteri kabul eder. İzmir şubesi randevu şartı aramaz, ancak öğle arasında (12.30–13.30) kapalıdır.\n\nSoru: Randevusu olmayan bir müşteri saat 13.00'te bu şubelerden hangisine gidebilir?",
      "Read the text carefully and answer the question.\n\nText: The Bursa branch accepts customers by appointment only. The İzmir branch does not require an appointment but is closed during the lunch break (12:30–13:30).\n\nQuestion: Which of these branches can a customer without an appointment visit at 13:00?",
      "Hiçbirine gidemez. Bursa şubesi yalnızca randevuyla çalışır; İzmir şubesi randevu aramasa da saat 13.00 öğle arasına denk geldiği için kapalıdır.",
      "Neither. The Bursa branch works by appointment only; the İzmir branch does not require one but is closed at 13:00 because that falls within the lunch break.",
      'neither branch', ['Hiçbir', 'öğle arası'], ['Neither', 'lunch'],
      'Answer must be "neither" with both reasons. Naming İzmir (ignoring the lunch break) is the typical error.',
      None),
    T('co05-report-timeline', 'turkish_comprehension',
      "Aşağıdaki notu oku ve soruyu yanıtla.\n\nNot: Proje raporu Salı günü teslim edildi. Danışman raporu Perşembe günü okudu ve Cuma günü geri bildirimini gönderdi. Öğrenci düzeltmeleri geri bildirimden bir gün sonra tamamladı.\n\nSoru: Düzeltmeler hangi gün tamamlandı ve danışman raporu teslimden kaç gün sonra okudu?",
      "Read the note below and answer the question.\n\nNote: The project report was submitted on Tuesday. The advisor read the report on Thursday and sent feedback on Friday. The student finished the corrections one day after the feedback.\n\nQuestion: On which day were the corrections finished, and how many days after submission did the advisor read the report?",
      "Düzeltmeler geri bildirimden bir gün sonra, yani Cumartesi günü tamamlandı. Danışman raporu Salı'dan iki gün sonra, Perşembe günü okudu.",
      "The corrections were finished one day after the feedback, that is on Saturday. The advisor read the report two days after submission, on Thursday.",
      'Saturday; 2 days', ['Cumartesi', 'iki gün'], ['Saturday', 'two days'],
      'Saturday and 2 days.',
      None),
    T('co06-orchard-count', 'turkish_comprehension',
      "Aşağıdaki metne dayanarak soruyu yanıtla.\n\nMetin: Ece'nin bahçesinde 12 elma ağacı ve 8 armut ağacı var. Elma ağaçlarının yarısı bu yıl meyve vermedi. Armut ağaçlarının tamamı meyve verdi.\n\nSoru: Bu yıl bahçedeki kaç ağaç meyve verdi?",
      "Answer the question based on the text below.\n\nText: Ece's garden has 12 apple trees and 8 pear trees. Half of the apple trees did not bear fruit this year. All of the pear trees bore fruit.\n\nQuestion: How many trees in the garden bore fruit this year?",
      "Meyve veren elma ağacı sayısı 12 / 2 = 6'dır. Armut ağaçlarının hepsi, yani 8'i meyve verdiğine göre toplam 6 + 8 = 14 ağaç meyve vermiştir.",
      "The number of apple trees that bore fruit is 12 / 2 = 6. Since all 8 pear trees bore fruit, a total of 6 + 8 = 14 trees bore fruit.",
      '14', ['6', '8', '14'], ['6', '8', '14'],
      'Final 14. Answering 6 (apples only) or 10 are errors.',
      lambda: str(12 // 2 + 8)),
    # ---------------- negation (6) ----------------
    T('ne01-opened-earphones', 'negation',
      "İade koşulları: Ürünler satın alındıktan sonraki 14 gün içinde iade edilebilir; ancak ambalajı açılmış kulaklıklar iade edilemez. Ambalajı açılmış bir kulaklığı 5. günde iade edebilir miyiz? Gerekçeni kısaca yaz.",
      "Return conditions: Products can be returned within 14 days of purchase; however, earphones whose packaging has been opened cannot be returned. Can we return a pair of earphones with opened packaging on day 5? Briefly give your reason.",
      "Hayır. 5. gün 14 günlük süre içinde olsa da ambalajı açılmış kulaklıklar iade edilemez.",
      "No. Although day 5 is within the 14-day period, earphones with opened packaging cannot be returned.",
      'no', ['Hayır', 'ambalaj'], ['No', 'packaging'],
      'Must be no, citing the exception despite being inside the time window.',
      None),
    T('ne02-denied-antecedent', 'negation',
      "Kural: Toplantıya katılmayan çalışan raporu imzalayamaz. Deniz toplantıya katıldı. Bu bilgilere dayanarak Deniz'in raporu imzalayabileceği kesin midir? Gerekçeni kısaca yaz.",
      "Rule: An employee who did not attend the meeting cannot sign the report. Deniz attended the meeting. Based on this information, is it certain that Deniz can sign the report? Briefly give your reason.",
      "Hayır, kesin değildir. Kural yalnızca toplantıya katılmayanların imzalayamayacağını söyler; katılanların imzalayabileceğini garanti etmez, başka koşullar olabilir.",
      "No, it is not certain. The rule only says that those who did not attend cannot sign; it does not guarantee that those who attended can sign, as other conditions may apply.",
      'not certain', ['Hayır', 'kesin değil'], ['No', 'not certain'],
      'Must reject the inference. The rule gives a necessary condition, not a sufficient one.',
      None),
    T('ne03-neither-nor', 'negation',
      "Ayşe'nin evinde ne kedi ne de köpek var. Buna dayanarak Ayşe'nin evinde hiç evcil hayvan olmadığını söyleyebilir miyiz? Gerekçeni kısaca yaz.",
      "Ayşe has neither a cat nor a dog at home. Based on this, can we say that Ayşe has no pets at all at home? Briefly give your reason.",
      "Hayır. Yalnızca kedi ve köpeğin olmadığı belirtiliyor; evde kuş veya balık gibi başka evcil hayvanlar bulunabilir.",
      "No. Only the absence of a cat and a dog is stated; there could be other pets at home, such as a bird or fish.",
      'no', ['Hayır', 'başka'], ['No', 'other'],
      'Must say no; only cat and dog are excluded.',
      None),
    T('ne04-upper-bound', 'negation',
      "Üç sınıfın hiçbirinde 30'dan fazla öğrenci yok. Bu üç sınıftaki toplam öğrenci sayısı en fazla kaç olabilir? Kısa bir hesaplama ve sonucu yaz.",
      "None of three classes has more than 30 students. What is the maximum possible total number of students in these three classes? Give a brief calculation and the result.",
      "Her sınıfta en fazla 30 öğrenci olabileceğinden toplam en fazla 3 × 30 = 90 öğrencidir.",
      "Since each class can have at most 30 students, the total is at most 3 × 30 = 90 students.",
      '90', ['30', '90'], ['30', '90'],
      'Final 90 (a class with exactly 30 is allowed). 87 or 93 would be errors.',
      lambda: str(3 * 30)),
    T('ne05-museum-monday', 'negation',
      "Müze pazartesi hariç her gün açıktır. \"Müze pazartesi günleri kapalı değildir\" ifadesi bu bilgiye göre doğru mudur? Gerekçeni kısaca yaz.",
      "The museum is open every day except Monday. According to this information, is the statement \"The museum is not closed on Mondays\" true? Briefly give your reason.",
      "Hayır, ifade yanlıştır. Müze pazartesi hariç her gün açık olduğuna göre pazartesi günleri kapalıdır.",
      "No, the statement is false. Since the museum is open every day except Monday, it is closed on Mondays.",
      'false', ['yanlış', 'kapalı'], ['false', 'closed'],
      'Must judge the negated statement false because the museum is closed on Mondays.',
      None),
    T('ne06-no-score-below', 'negation',
      "Sınava girenlerin hiçbiri 40'ın altında puan almadı. Ece de sınava girdi. Ece'nin puanı 40'ın altında olabilir mi? Gerekçeni kısaca yaz.",
      "None of the people who took the exam scored below 40. Ece also took the exam. Could Ece's score be below 40? Briefly give your reason.",
      "Hayır. Sınava girenlerin hiçbiri 40'ın altında puan almadığına göre Ece'nin puanı da 40 veya daha yüksektir.",
      "No. Since none of the test-takers scored below 40, Ece's score is also 40 or higher.",
      'no', ['Hayır', '40'], ['No', '40'],
      'Must say no; score is 40 or above (40 included).',
      None),
    # ---------------- semantic roles (5) ----------------
    T('sr01-causative-report', 'semantic_roles',
      "Şu cümleyi oku: \"Müdür, sekreterine raporu avukata göndertti.\" Raporu kim gönderdi, gönderilmesini kim istedi ve rapor kime gitti?",
      "Read this sentence: \"The manager had his secretary send the report to the lawyer.\" Who sent the report, who requested that it be sent, and who received it?",
      "Raporu sekreter gönderdi. Gönderilmesini müdür istedi. Rapor avukata gitti.",
      "The secretary sent the report. The manager requested that it be sent. The lawyer received it.",
      'secretary sent; manager requested; lawyer received', ['sekreter', 'müdür', 'avukat'], ['secretary', 'manager', 'lawyer'],
      'All three roles: sender=secretary, requester=manager, recipient=lawyer. Swapping manager/secretary is the typical error.',
      None),
    T('sr02-passive-package', 'semantic_roles',
      "Şu cümleyi oku: \"Komşu tarafından kapıya bırakılan paketi kardeşim aldı.\" Paketi kapıya kim bıraktı ve paketi kim aldı?",
      "Read this sentence: \"The package left at the door by the neighbour was picked up by my brother.\" Who left the package at the door, and who picked it up?",
      "Paketi kapıya komşu bıraktı. Paketi anlatıcının kardeşi aldı.",
      "The neighbour left the package at the door. The speaker's brother picked it up.",
      'neighbour left; brother picked up', ['komşu', 'kardeş'], ['neighbour', 'brother'],
      'Roles: left=neighbour, picked up=brother (the speaker\'s brother).',
      None),
    T('sr03-instrument-note', 'semantic_roles',
      "Şu cümleyi oku: \"Berk, Ali'nin kalemiyle Deniz'e not yazdı.\" Notu kim yazdı, notu kime yazdı ve kalem kimindi?",
      "Read this sentence: \"Berk wrote Deniz a note with Ali's pen.\" Who wrote the note, to whom was it written, and whose pen was used?",
      "Notu Berk yazdı. Not Deniz'e yazıldı. Kullanılan kalem Ali'nindi.",
      "Berk wrote the note. It was written to Deniz. The pen used was Ali's.",
      'Berk; Deniz; Ali', ['Berk', "Deniz", "Ali"], ['Berk', 'Deniz', 'Ali'],
      'Writer=Berk, addressee=Deniz, pen owner=Ali.',
      None),
    T('sr04-relative-clause', 'semantic_roles',
      "Şu cümleyi oku: \"Ayşe'nin selamladığı kişi Mert'in öğretmeniydi.\" Kim kimi selamladı ve öğretmen kimin öğretmeniydi?",
      "Read this sentence: \"The person Ayşe greeted was Mert's teacher.\" Who greeted whom, and whose teacher was that person?",
      "Ayşe, Mert'in öğretmenini selamladı. Selamlanan kişi Mert'in öğretmeniydi.",
      "Ayşe greeted Mert's teacher. The person greeted was Mert's teacher.",
      'Ayşe greeted Mert\'s teacher', ['Ayşe', 'öğretmen', 'Mert'], ['Ayşe', 'teacher', 'Mert'],
      'Greeter=Ayşe, greeted=the teacher, teacher belongs to Mert. Mert greeting Ayşe is wrong.',
      None),
    T('sr05-ambiguous-pronoun', 'semantic_roles',
      "Şu cümleyi oku: \"Mert, kardeşi Can'a ödevinde yardım etti; sonra o, öğretmene bir teşekkür mektubu yazdı.\" Mektubu kimin yazdığı bu cümleden kesin olarak anlaşılıyor mu?",
      "Read this sentence: \"Mert helped his brother Can with his homework; then he wrote a thank-you letter to the teacher.\" Is it clear from this sentence who wrote the letter?",
      "Hayır, kesin olarak anlaşılmıyor. \"O\" zamiri hem Mert'i hem Can'ı gösterebilir; cümle mektubu kimin yazdığını belirtmiyor.",
      "No, it is not clear. The pronoun \"he\" could refer to either Mert or Can; the sentence does not say who wrote the letter.",
      'ambiguous', ['Hayır', 'Mert', 'Can'], ['No', 'Mert', 'Can'],
      'Must flag the ambiguity (Mert or Can) without picking one as certain.',
      None),
    # ---------------- faithful rewriting (5) ----------------
    T('rw01-course-registration', 'faithful_rewriting',
      "Aşağıdaki duyuruyu en fazla 25 kelimelik tek bir cümleye indir; hiçbir tarihi, sayıyı veya koşulu kaybetme, yeni bilgi ekleme.\n\nDuyuru: Kurs kaydı 15 Mart'a kadar açıktır. Ödeme, kayıttan sonraki 3 gün içinde yapılmazsa kayıt iptal edilir. Kurs ücreti iade edilmez.",
      "Condense the notice below into a single sentence of at most 25 words; do not lose any date, number or condition, and do not add new information.\n\nNotice: Course registration is open until 15 March. If payment is not made within 3 days of registering, the registration is cancelled. The course fee is not refundable.",
      "Kurs kaydı 15 Mart'a kadar açıktır; kayıttan sonraki 3 gün içinde ödeme yapılmazsa kayıt iptal edilir ve ücret iade edilmez.",
      "Course registration is open until 15 March; if payment is not made within 3 days of registering, the registration is cancelled, and the fee is not refundable.",
      'one sentence retaining 15 March, 3 days, cancellation, no refund', ['15 Mart', '3 gün', 'iptal', 'iade'], ['15 March', '3 days', 'cancel', 'refund'],
      'One sentence, at most 25 words, keeping 15 March, 3 days, cancellation and non-refundability. Reject added facts and the refund condition being dropped or reversed.',
      None),
    T('rw02-formal-message', 'faithful_rewriting',
      "Aşağıdaki mesajı anlamını ve bilgilerini koruyarak resmî bir dille yeniden yaz; yeni bilgi ekleme.\n\nMesaj: Abi toplantı 14.30'a kaydı, salon 3 değil 5. Sunumu getirmeyi unutma ama çıktı almana gerek yok.",
      "Rewrite the message below in a formal register, preserving its meaning and information; do not add new information.\n\nMessage: Hey, the meeting has moved to 14:30, and the room is 5, not 3. Don't forget to bring the presentation, but you don't need to print it out.",
      "Toplantı saati 14.30 olarak değiştirilmiştir ve toplantı 3 numaralı salon yerine 5 numaralı salonda yapılacaktır. Sunumu getirmeniz rica olunur; ancak çıktı almanıza gerek yoktur.",
      "The meeting time has been changed to 14:30 and the meeting will take place in room 5 instead of room 3. Please bring the presentation; however, there is no need to print it.",
      'formal; 14:30, room 5 not 3, bring presentation, no printout', ['14.30', '5', 'çıktı'], ['14:30', '5', 'print'],
      'Formal register; keep time 14:30, room 5 (not 3), bring the presentation, no printout needed. The source does not say whether the meeting moved earlier or later, so asserting "postponed" or "brought forward" is an unsupported addition.',
      None),
    T('rw03-simplify-evaporation', 'faithful_rewriting',
      "Aşağıdaki cümleyi 10 yaşındaki bir çocuğun anlayabileceği sade bir dille, bilgi eklemeden yeniden yaz.\n\nCümle: Buharlaşma, sıvı haldeki suyun ısı alarak gaz hâline geçmesidir; deniz ve göl yüzeylerinde sürekli gerçekleşir.",
      "Rewrite the sentence below in simple language that a 10-year-old can understand, without adding information.\n\nSentence: Evaporation is the change of liquid water into a gas by absorbing heat; it takes place continuously on the surfaces of seas and lakes.",
      "Buharlaşmada sıvı su ısınır ve gaza dönüşür. Bu olay denizlerin ve göllerin yüzeyinde hiç durmadan olur.",
      "In evaporation, liquid water warms up and turns into a gas. This keeps happening all the time on the surface of seas and lakes.",
      'simplified, all facts kept', ['sıvı', 'ısı', 'gaz', 'deniz', 'göl', 'sürekli'], ['liquid', 'heat', 'gas', 'sea', 'lake', 'continuous'],
      'Simple language; keeps liquid water, heat, gas, seas and lakes, continuous occurrence; adds no new facts (no sun, clouds, rain).',
      None),
    T('rw04-two-bullets', 'faithful_rewriting',
      "Aşağıdaki notu tam olarak iki madde hâlinde özetle; olumsuzlukları ve sayıları koru, yeni bilgi ekleme.\n\nNot: Servis salı günü çalışmayacak, ancak çarşamba günü normal saatlerde çalışacak. Bilet ücreti 18 TL olarak değişmedi.",
      "Summarise the note below in exactly two bullet points; keep the negations and numbers, and do not add new information.\n\nNote: The shuttle will not run on Tuesday, but it will run at normal times on Wednesday. The ticket fare is unchanged at 18 TL.",
      "- Servis salı günü çalışmayacak; çarşamba günü normal saatlerde çalışacak.\n- Bilet ücreti değişmedi: 18 TL.",
      "- The shuttle will not run on Tuesday; it will run at normal times on Wednesday.\n- The ticket fare is unchanged: 18 TL.",
      'two bullets; Tuesday not running, Wednesday normal, fare 18 TL unchanged', ['salı', 'çalışmayacak', 'çarşamba', '18 TL'], ['Tuesday', 'not run', 'Wednesday', '18 TL'],
      'Exactly two bullets; negation (no service Tuesday) kept; Wednesday normal; 18 TL unchanged. Reject reversed negation.',
      None),
    T('rw05-meeting-one-sentence', 'faithful_rewriting',
      "Aşağıdaki notu bilgi kaybetmeden ve bilgi eklemeden tek bir cümleye indir.\n\nNot: Toplantı çarşamba değil, perşembe yapılacak. Katılamayacak olanlar önceden haber verecek. Gündem 3 maddeden oluşuyor.",
      "Condense the note below into a single sentence without losing or adding information.\n\nNote: The meeting will be held on Thursday, not Wednesday. Those who cannot attend will notify in advance. The agenda consists of 3 items.",
      "Toplantı çarşamba değil perşembe günü yapılacak, katılamayacak olanlar önceden haber verecek ve gündem 3 maddeden oluşuyor.",
      "The meeting will be held on Thursday rather than Wednesday, those who cannot attend will notify in advance, and the agenda has 3 items.",
      'one sentence; Thursday not Wednesday; notify in advance; 3 agenda items', ['perşembe', 'çarşamba', 'önceden', '3'], ['Thursday', 'Wednesday', 'advance', '3'],
      'One sentence keeping Thursday (not Wednesday), advance notice for non-attendees, and 3 agenda items.',
      None),
    # ---------------- output-language control (5) ----------------
    T('ol01-weekend-days', 'output_language_control',
      "Hafta sonunu oluşturan günleri yaz.",
      "Write the days that make up the weekend.",
      "Cumartesi ve Pazar.",
      "Saturday and Sunday.",
      'Saturday and Sunday', ['Cumartesi', 'Pazar'], ['Saturday', 'Sunday'],
      'Content: Saturday and Sunday. Primary check is that the answer is in the requested language only.',
      None),
    T('ol02-main-point', 'output_language_control',
      "Aşağıdaki cümlenin ana fikrini tek kısa cümleyle yaz: \"Toplantı yarın değil, bu cuma yapılacak.\"",
      "Write the main point of the following sentence in one short sentence: \"The meeting will be held this Friday, not tomorrow.\"",
      "Toplantı bu cuma yapılacak.",
      "The meeting will be held this Friday.",
      'meeting this Friday, not tomorrow', ['cuma', 'yarın'], ['Friday', 'tomorrow'],
      'One short sentence in the requested language; Friday kept; must not say the meeting is tomorrow.',
      None),
    T('ol03-weather-data', 'output_language_control',
      "Verilere göre hava durumunu iki cümleyle anlat: İstanbul, 14 °C, yağmurlu; Ankara, 9 °C, karlı.",
      "Describe the weather in two sentences according to the data: Istanbul, 14 °C, rainy; Ankara, 9 °C, snowy.",
      "İstanbul'da hava 14 °C ve yağmurlu. Ankara'da ise hava 9 °C ve karlı.",
      "In Istanbul the weather is 14 °C and rainy. In Ankara it is 9 °C and snowy.",
      'two sentences; Istanbul 14 °C rainy; Ankara 9 °C snowy', ['İstanbul', '14', 'yağmur', 'Ankara', '9', 'kar'], ['Istanbul', '14', 'rain', 'Ankara', '9', 'snow'],
      'Exactly two sentences in the requested language; each city paired with the right temperature and condition (no swapping).',
      None),
    T('ol04-presentation-reminder', 'output_language_control',
      "Yarınki sunum için bir meslektaşına en fazla iki cümlelik kısa bir hatırlatma mesajı yaz. Bilgiler: sunum saat 10.00'da, salon B.",
      "Write a short reminder message of at most two sentences to a colleague about tomorrow's presentation. Details: the presentation is at 10:00, room B.",
      "Merhaba, yarınki sunum saat 10.00'da B salonunda yapılacak. Lütfen zamanında hazır ol.",
      "Hi, tomorrow's presentation will be at 10:00 in room B. Please be ready on time.",
      'reminder with 10:00 and room B', ['10.00', 'B'], ['10:00', 'B'],
      'At most two sentences in the requested language; keeps 10:00 and room B; does not invent other details (agenda, names).',
      None),
    T('ol05-quote-error', 'output_language_control',
      "Aşağıdaki hata mesajını aynen alıntıla ve ne anlama geldiğini tek cümleyle açıkla: \"Error 404: Page not found\"",
      "Quote the following error message exactly and explain what it means in one sentence: \"Error 404: Page not found\"",
      "\"Error 404: Page not found\" — İstenen sayfa bulunamadı.",
      "\"Error 404: Page not found\" — The requested page could not be found.",
      'quote kept verbatim; explanation in requested language', ['Error 404: Page not found', 'bulunamadı'], ['Error 404: Page not found', 'not be found'],
      'Quoted text kept verbatim (English even in Turkish answers); explanation sentence in the requested language only.',
      None),
]

SYMBOLIC = ['(54 + 38) * 3 - 17', '412 - 7 * 36', '(144 / 12) + 9 * 8', '(250 - 75) / 5 + 18',
            '9 * 8 - 6 * 7 + 5', '(19 + 23) * (8 - 3)', '1000 / (4 * 5) - 12', '(86 - 29) * 2 + 33']

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


def evaluate(expr):
    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return Fraction(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](walk(node.left), walk(node.right))
        raise ValueError(expr)
    return walk(ast.parse(expr, mode='eval'))


def build():
    prompts, refs = [], []
    for t in TASKS:
        if t['verify']:
            computed = t['verify']()
            computed = str(computed.numerator) if isinstance(computed, Fraction) and computed.denominator == 1 else str(computed)
            assert computed == t['final'], (t['task_id'], computed, t['final'])
        group = f"bpe01-{t['task_id']}"
        for direction in DIRECTIONS:
            src, dst = direction.split('-')
            user = with_instruction(t[src], src, dst)
            row_id = f'{group}-{direction}'
            prompts.append(dict(id=row_id, group_id=group, task_id=t['task_id'], category=t['category'],
                direction=direction, input_language=src, output_language=dst,
                messages=[dict(role='system', content=SYSTEM[src]), dict(role='user', content=user)],
                evaluation_only=True, training_allowed=False,
                provenance='Agent-authored 2026-11-17 before translation of any training row; not derived from training, '
                           'previous evaluation packets, or benchmark data'))
            refs.append(dict(id=row_id, group_id=group, direction=direction, output_language=dst,
                final_answer=t['final'], reference_answer=t['ref_' + dst],
                key_facts=t['facts_' + dst], rubric=t['rubric'],
                verification=('computed in script and asserted' if t['verify'] else 'manual logical derivation, reviewed twice'),
                note='Reference is illustrative; accept equivalent correct wording. Never exact-match prose.'))
    assert len(TASKS) == 35 and len(prompts) == 140 and len({p['id'] for p in prompts}) == 140
    cat_counts = {}
    for t in TASKS:
        cat_counts[t['category']] = cat_counts.get(t['category'], 0) + 1
    sym_prompts, sym_refs = [], []
    for i, expr in enumerate(SYMBOLIC, 1):
        value = evaluate(expr)
        assert value.denominator == 1
        sym_prompts.append(dict(id=f'bpe01-symbolic-{i:02d}', task='symbolic_arithmetic',
            messages=[dict(role='user', content=f'{expr} = ?\nOutput only the number. / Yalnızca sayıyı yaz.')],
            evaluation_only=True, training_allowed=False, reported_separately=True))
        sym_refs.append(dict(id=f'bpe01-symbolic-{i:02d}', final_answer=str(value.numerator),
                             verification='exact Fraction evaluation of the expression'))
    return prompts, refs, sym_prompts, sym_refs, cat_counts


def main():
    prompts, refs, sym_prompts, sym_refs, cats = build()
    OUT.mkdir(parents=True, exist_ok=True)
    files = {'eval-prompts.jsonl': jsonl_bytes(prompts), 'eval-references.jsonl': jsonl_bytes(refs),
             'symbolic-controls-prompts.jsonl': jsonl_bytes(sym_prompts),
             'symbolic-controls-references.jsonl': jsonl_bytes(sym_refs)}
    manifest_path = OUT / 'manifest.json'
    frozen_at = (json.loads(manifest_path.read_text(encoding='utf-8'))['frozen_at_utc']
                 if manifest_path.exists() else datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'))
    manifest = dict(
        status='frozen-before-training-translation',
        frozen_at_utc=frozen_at,
        underlying_task_groups=35, prompts=140, per_direction=35,
        directions=DIRECTIONS, categories=cats,
        symbolic_controls=len(sym_prompts),
        training_allowed=False, generation_demonstration_allowed=False,
        prompt_files_without_references=['eval-prompts.jsonl', 'symbolic-controls-prompts.jsonl'],
        reference_files=['eval-references.jsonl', 'symbolic-controls-references.jsonl'],
        reference_policy='Keep reference files out of annotation displays and model inputs. Illustrative wording only.',
        files={name: dict(sha256=sha256_bytes(data), bytes=len(data)) for name, data in files.items()},
        builder='scripts/datasets/prepare_lfm3_bilingual_pilot_eval.py',
        language_instruction='Appended to the user turn in the input language; identical wording to training rows (bilingual_pilot_common.INSTRUCTION)',
        system_prompt='Language-matched system prompt identical to the matching training rows (bilingual_pilot_common.SYSTEM)',
        regression_sets='Previous 20 (old20/dev20) and 15 (crosslingual) records remain development/regression checks, not a fresh final test.',
        limitations=['35 underlying tasks are a diagnostic, not a benchmark; four directions per task are correlated, not 140 independent trials.',
                     'Authored by one agent; Turkish naturalness not owner-reviewed.',
                     'Once used to choose checkpoints this becomes development data; a new final test is required for promotion.'])
    for name, data in files.items():
        freeze(OUT / name, data)
    freeze(manifest_path, json_bytes(manifest))
    print('eval frozen:', {k: v['sha256'][:12] for k, v in manifest['files'].items()}, cats)


if __name__ == '__main__':
    main()
