"""Human-readable bilingual repairs; optional reasoning only replaces existing reasoning."""
REPAIRS = {}


def answer(group, tr, en, thinking_tr=None, thinking_en=None):
    REPAIRS.setdefault(group, {}).update(tr_output=tr, en_output=en)
    if thinking_tr is not None:
        REPAIRS[group].update(tr_thinking=thinking_tr, en_thinking=thinking_en)


answer('g018',
'''Bu sprintte de işler planlanan sürede tamamlanamamıştır. Ekip içinde karşılıklı suçlamalar yaşanmış, planlama ve koordinasyon süreçlerinde aksaklıklar ortaya çıkmıştır.''',
'''The work was again not completed within the planned sprint timeframe. Team members exchanged accusations, and planning and coordination processes were disrupted.''')
answer('g022',
'''Bu geniş kapsamlı sonuç öncüllerden zorunlu olarak çıkmaz. Dördüncü öncül kabul edilirse Tanzimat Fermanı'nın belirtilen sürecin sivil uzantısı olduğu söylenebilir. Bir öncülün sonucunu tekrar etmek çıkarımı biçimsel olarak geçersiz yapmaz; yalnızca bağımsız bir gerekçe sağlamaz.

Ancak tek bir ferman hakkındaki bu ifade, Osmanlı'daki bütün sivil modernleşme reformlarının bu yolla başladığını ya da gelişmenin doğal ve zorunlu olduğunu göstermez. İlk üç öncül de Tanzimat'ın ilanını içermez. Dolayısıyla sınırlı öncülü kabul etmek ile daha geniş tarihsel genellemeyi kanıtlamak birbirinden ayrılmalıdır.''',
'''The broader conclusion does not necessarily follow. If premise 4 is accepted, the Tanzimat Edict can be described as a civilian extension of the stated process. Repeating a premise as a conclusion does not make an inference formally invalid; it simply provides no independent justification.

However, a statement about one edict does not establish that all Ottoman civilian modernization reforms began this way or that the development was natural and necessary. Nor do premises 1–3 mention the proclamation of the Tanzimat. Accepting the limited premise must therefore be distinguished from proving the broader historical generalization.''',
'''Dördüncü öncül Tanzimat'a ilişkin sınırlı bir ilişkiyi açıkça kabul ediyor. Bunu yinelemek mantıksal geçersizlik değildir. Sorulan sonuç ise tüm sivil reformların başlangıcına ve ilişkinin doğal oluşuna genelleniyor; bu ek kapsam öncüllerde yok. İlk üç öncüle Tanzimat olayını eklememeliyim.''',
'''Premise 4 explicitly grants a limited relationship concerning the Tanzimat. Repeating it is not logical invalidity. The proposed conclusion generalizes to the beginning of all civilian reforms and calls the relationship natural; that additional scope is not supplied. I must not insert the Tanzimat into premises 1–3.''')
answer('g030',
'''“Biz sadece ihale yaptık” demek, belediyenin kendi denetim görevini yerine getirip getirmediği sorusunu cevaplamaz. Hizmetin yükleniciye gördürülmesi, idarenin görev alanındaki izleme ve kontrol sorumluluğunu kendiliğinden ortadan kaldırmaz.

Anayasa'nın 56. maddesi çevreyi koruma ve kirlenmeyi önleme ödevini devlete ve vatandaşlara yükler. Senaryoda firmanın çevre kurallarına uyumunun denetlenmediği açıkça belirtilmiştir; değerlendirilmesi gereken, somut denetim yükümlülüğünün kapsamı ve bu eksikliğin zarara etkisidir.

Denetim eksikliğinin kirliliğe katkısı ve gerekli diğer koşullar ortaya konulursa idarenin sorumluluğu gündeme gelebilir. Firmanın kendi kusuru bunu tek başına ortadan kaldırmaz. Bununla birlikte, verilen bilgilerden belirli yaptırım yetkilerinin hiç kullanılmadığı veya hukuki illiyet bağının kesin olarak kurulduğu sonucu çıkarılamaz.''',
'''Saying “we only conducted the tender” does not answer whether the municipality fulfilled its own oversight duty. Contracting out the service does not automatically eliminate monitoring and control responsibilities within the authority's remit.

Article 56 of the Constitution assigns environmental protection and pollution prevention duties to the state and citizens. The scenario explicitly states that the firm's compliance was not checked; the relevant questions are the scope of the specific oversight duty and the effect of that omission on the harm.

Administrative liability may arise if the omission's contribution to the pollution and the other required conditions are established. The contractor's own fault does not by itself remove that possibility. However, the supplied facts do not establish that particular enforcement powers were never exercised or that legal causation has conclusively been proved.''')
answer('g033',
'''D(x): devrik cümle, F(x): söz diziminde farklılık gösteren cümle, S(x): soru cümlesi; a: “Neden bu kadar geç kaldın?” olsun. Öncüllerin sonuçları, bunların mantıksal eşdeğerleri ve birleşimleriyle sınırsız biçimde yazılabilir. Başlıca kesin sonuçlar şunlardır:

* ¬D(a): Verilen cümle devrik değildir; üçüncü ve dördüncü öncülden çıkar.
* ∃x(S(x) ∧ ¬D(x)): Bazı soru cümleleri devrik değildir; a bunun tanığıdır.
* Hiçbir cümle hem soru hem devrik olamaz: ∀x ¬(S(x) ∧ D(x)). Bu, üçüncü öncülün eşdeğeridir; devrik bir cümle varsa soru değildir.
* Söz diziminde farklılık gösteren ve devrik olmayan en az bir cümle vardır; bu zaten ikinci öncülde verilmiştir.

F(a) çıkarılamaz: devrik olmayanların tümünün farklılık gösterdiği söylenmemiştir. Soru cümlelerinin bazılarının veya tümünün F olduğu da zorunlu değildir. Devrik cümlelerin varlığı verilmediği için “bazı devrik cümleler F'dir” sonucu da çıkarılamaz. Bu değerlendirme, öncülleri alıştırmanın kabulleri olarak ele alır.''',
'''Let D(x) mean an inverted sentence, F(x) a sentence with a syntactic difference, S(x) a question, and a the sentence “Neden bu kadar geç kaldın?”. Consequences can be expressed in indefinitely many equivalent forms and combinations. The principal certain conclusions are:

* ¬D(a): The given sentence is not inverted, by premises 3 and 4.
* ∃x(S(x) ∧ ¬D(x)): Some question is not inverted; a is a witness.
* No sentence is both a question and inverted: ∀x ¬(S(x) ∧ D(x)). This is equivalent to premise 3; any inverted sentence is not a question.
* At least one sentence has a syntactic difference and is not inverted; this is already given in premise 2.

F(a) does not follow: not all non-inverted sentences are said to have a syntactic difference. Neither some nor all questions must have property F. Since the existence of inverted sentences is not given, “some inverted sentences have property F” does not follow either. This analysis treats the premises as assumptions of the exercise.''',
'''3 ve 4 birlikte ¬D(a) verir. S(a) ile ¬D(a) aynı tanıkta birleştiğinden ∃x(S∧¬D) de çıkar. D→¬S, S→¬D'nin karşıt tersidir. D'nin varlığı verilmez; F(a) belirsizdir. Tüm sonuçları sonlu ve tüketici bir liste gibi sunmamalıyım.''',
'''Premises 3 and 4 yield ¬D(a). Together with S(a), the same witness establishes ∃x(S∧¬D). D→¬S is the contrapositive of S→¬D. Existence of D is not given, and F(a) is undetermined. I should not claim a finite exhaustive list of all consequences.''')
answer('g035',
'''Vardiya süreleri verilmediği için çalışan-saat sınırını uygulamak bir süre varsayımı gerektirir. Altı işçinin de tek vardiyaya atandığını ve vardiyaların eşit uzunlukta olduğunu varsayarsak 6t ≤ 24, yani t ≤ 4 saat olur. Dört saatlik vardiyalar seçilirse şu plan uygundur:

* Gündüz: Fatma, Ali
* Akşam: Veli, Ayşe
* Gece: Hüseyin, Zeynep

Her vardiyada iki işçi vardır; Ali ve Veli ayrıdır, Fatma gündüzdedir ve toplam 6 × 4 = 24 çalışan-saattir. Bu, belirtilen varsayım altında bir çözümdür. Eşit süre koşulu verilmediğinden her vardiyanın ayrı ayrı en çok dört saat olması zorunlu değildir; örneğin bu dağılımda 2, 4 ve 6 saat de toplam 24 çalışan-saat eder. Gerçek süreler farklıysa plan bunlarla yeniden kontrol edilmelidir.''',
'''The shift durations are missing, so applying the employee-hour limit requires an assumption. If all six workers are assigned once and all shifts have equal duration, 6t ≤ 24, so t ≤ 4 hours. Choosing four-hour shifts gives this feasible plan:

* Day: Fatma, Ali
* Evening: Veli, Ayşe
* Night: Hüseyin, Zeynep

Each shift has two workers; Ali and Veli are separated, Fatma works by day, and the total is 6 × 4 = 24 employee-hours. This is a solution under the stated assumption. Equal durations were not required, so each individual shift need not be at most four hours: with this allocation, durations of 2, 4 and 6 hours also total 24 employee-hours. The plan must be checked again if actual durations differ.''',
'''Süreler eksik. Altı kişi birer vardiya çalışır ve süreler eşitse 6t≤24 koşulu t≤4 verir. Dört saat bir mümkün seçimdir, tek çözüm değildir. İkişer kişilik dağılımda çalışan-saat 2(t1+t2+t3) olduğundan 2,4,6 da sınırı sağlar. Fatma gündüz ve Ali/Veli ayrı tutulmalı.''',
'''Durations are missing. If six people each work one shift and durations are equal, 6t≤24 gives t≤4. Four hours is one feasible choice, not the only solution. With two people per shift, employee-hours equal 2(t1+t2+t3), so 2,4,6 also satisfies the cap. Fatma must be on days and Ali/Veli separated.''')
answer('g039',
'''Evet; dikdörtgenin yatay ve dikey orta çizgileri simetri eksenleri olduğundan halı bu çizgilerin her biri üzerinden katlandığında iki yarısı, kenar oranından bağımsız olarak çakışır.''',
'''Yes; a rectangle's horizontal and vertical midlines are axes of symmetry, so folding the carpet along either midline makes its two halves coincide regardless of the side-length ratio.''')
answer('g063',
'''Atasözü, mecazi kullanımında bir söylenti veya belirtinin arkasında mutlaka gerçek bir olay bulunduğunu varsayabilir. Adli değerlendirmede ise bir belirti, tek başına belirli bir kişinin suçunu kanıtlamaz; güvenilirliği ve alternatif açıklamaları incelenmelidir.

Mantıksal ayrım önemlidir: “Ateş varsa duman vardır” kabulünden “Duman varsa ateş vardır” sonucuna koşulsuz geçmek sonucu doğrulama hatasıdır. Buna karşılık duman çıkarmayan bir ateş örneği, “Duman varsa ateş vardır” iddiasını çürütmez; ters yöndeki koşulu sorgular. Ayrıca duman gibi görünen sis veya buhar, gerçek dumanla aynı şey değildir.

Bu nedenle bir gözlem araştırma için başlangıç olabilir, fakat gözlemin ne olduğu, nasıl oluştuğu ve diğer bulgularla uyumu değerlendirilmeden hükme dönüşmemelidir. Söylentiyi doğrudan suçun kanıtı saymak yerine, iddiayı bağımsız ve sınanabilir bulgularla desteklemek gerekir.''',
'''In its figurative use, the proverb may suggest that a rumor or sign must have a real event behind it. In forensic assessment, however, a sign alone does not prove a particular person's guilt; its reliability and alternative explanations must be examined.

The logical distinction matters: moving unconditionally from “if there is fire, there is smoke” to “if there is smoke, there is fire” affirms the consequent. Conversely, a fire without smoke would not refute “if there is smoke, there is fire”; it challenges the conditional in the other direction. Fog or steam that looks like smoke is also not the same as actual smoke.

An observation can therefore initiate an inquiry, but it should not become a verdict before its nature, origin and consistency with other evidence have been assessed. A rumor should be supported with independent, testable evidence rather than treated directly as proof of guilt.''')
answer('g097',
'''* Sistem A: Hızlıdır; risk: maliyet.
* Sistem B: Güvenlidir; risk: yavaşlık.
* Özet: Hibrit model önerilir.''',
'''* System A: Fast; risk: cost.
* System B: Secure; risk: slowness.
* Summary: A hybrid model is recommended.''')
answer('g100',
'''Kısaca: Ürünü teslim aldığınız tarihten itibaren 14 gün içinde gerekçe göstermeden, kullanılmamış olarak, orijinal ambalajı ve faturasıyla iade edebilirsiniz. Ürün ayıplı değilse iade kargosunu siz ödersiniz; iade onaylandıktan sonra ödeme ilk ödeme yönteminize 5–10 iş günü içinde yapılır.''',
'''In short: You may return the unused product within 14 days of receipt without giving a reason, in its original packaging and with its invoice. You pay return shipping unless the product is defective; after the return is approved, the refund is made to your original payment method within 5–10 business days.''')
answer('g104',
'''Yıllık 7.200 TL, aylık 600 TL abonelik gideri demektir. Bu tutar harçlığın %40'ıysa aylık harçlık 600 ÷ 0,40 = 1.500 TL'dir; abonelikler sonrasında 900 TL kalır.

Tam iptal, abonelik giderini yılda 7.200 TL azaltır. Ancak bunun tamamının birikime dönüşmesi, paranın başka harcamalara gitmemesine bağlıdır. Eğlence ve arkadaşlarla bağlantı gibi faydaların kaybı da hesaba katılmalıdır; bu öznel faydalar doğrudan TL tutarından çıkarılabilecek ölçüler değildir.

Fırsat maliyeti, aynı paranın en iyi alternatif kullanımından vazgeçmektir. Bunu abonelik ücretine ayrı bir nakit gider gibi eklemek yerine, aboneliklerin sağladığı faydayla alternatiflerin faydasını karşılaştırmak gerekir.

Dengeli bir yaklaşım, her aboneliğin kullanımını ve kişisel değerini gözden geçirmek, az kullanılanları geçici olarak iptal etmek ve bir ay sonra sonucu değerlendirmektir. Böylece maliyet ile yaşam kalitesi arasındaki tercih görünür olur; her iptalin mutlaka iyileşme sağlayacağı varsayılmaz.''',
'''Annual spending of 7,200 TL means 600 TL per month on subscriptions. If that is 40% of the allowance, the monthly allowance is 600 ÷ 0.40 = 1,500 TL, leaving 900 TL after subscriptions.

Cancelling everything reduces subscription spending by 7,200 TL per year. Whether all of that becomes savings depends on not spending it elsewhere. The loss of entertainment and connection with friends also matters; these subjective benefits are not quantities that can simply be subtracted from a TL amount.

Opportunity cost is the value of the best alternative use forgone. Rather than adding it to the subscription fee as another cash expense, compare the benefits of subscriptions with those of the alternatives.

A balanced approach is to review each subscription's use and personal value, temporarily cancel little-used services, and reassess after a month. This makes the trade-off between cost and quality of life explicit without assuming every cancellation must be an improvement.''',
'''7.200/12=600; 600/0,40=1.500; kalan 900 TL. İptalin kesin etkisi abonelik giderindeki azalmadır, fiili birikim başka harcamalara bağlıdır. Para ile öznel faydayı ortak ölçü olmadan toplamayacağım. Fırsat maliyetini ikinci bir nakit gider saymayacağım. Küçük bir deneme kişisel fayda kaybını değerlendirmeye yardımcı olabilir.''',
'''7,200/12=600; 600/0.40=1,500; 900 TL remains. Cancellation reduces subscription spending, but actual savings depend on other spending. I will not combine money and subjective benefit without a common measure or treat opportunity cost as another cash expense. A small trial can help assess the personal loss of benefits.''')
answer('g105',
'''1. Hayır. Verilen olaylar ve tarihler, “başlangıç” için hangi ölçütün kullanılacağını belirtmez. Bu nedenle 19 Mayıs'ın başlangıç kabul edilmesi gerektiği, yalnızca bu öncüllerden tümdengelimle zorunlu olarak çıkmaz. Bu, tarihin yerleşik veya simgesel önemini reddetmek değildir.

2. Öncüller Erzurum ve Sivas kongrelerinden söz etmediği ve bir başlangıç ölçütü vermediği için kongrelerin başlangıç sayılabileceği görüşünü de zorunlu olarak çürütmez veya doğrulamaz. Böyle bir değerlendirme için ek tarihsel bilgi ve açık bir ölçüt gerekir.''',
'''1. No. The supplied events and dates do not specify a criterion for what counts as the beginning. Therefore, the claim that 19 May should be accepted as the beginning does not necessarily follow by deduction from these premises alone. This does not deny the date's established or symbolic importance.

2. Because the premises neither mention the Erzurum and Sivas congresses nor provide a criterion for the beginning, they do not deductively refute or establish the view that those congresses could count as the beginning. That assessment requires additional historical information and an explicit criterion.''',
'''Öncüller dört tarihsel olayı bildiriyor; yerel direniş ve kongrelerin özellikleri bunlara dahil değil. Başlangıcı belirleyen ölçüt olmadan tek bir tarih zorunlu çıkmaz. Kongreler lehine veya aleyhine sonuç için de ek bilgi gerekir; dış bilgiyi öncül gibi kullanmamalıyım.''',
'''The premises report four historical events; local resistance and the characteristics of the congresses are not among them. Without a criterion defining the beginning, no single date follows necessarily. A conclusion for or against the congresses also needs more information; I must not treat outside knowledge as a supplied premise.''')
answer('g115',
'''1. Tez çalışmamın literatür taramasını tamamladım. 2. Metodoloji bölümüm kurul onayından geçti. 3. Veri toplama sürecini başlattım.''',
'''1. I have completed the literature review for my thesis. 2. My methodology section has received board approval. 3. I have started the data collection process.''')
answer('g117',
'''Yalnızca son kalite kontrolünü geçen seramik parçalar paketlenip cuma gönderilecek; geçmeyenler yeniden yapılacak.''',
'''Only ceramic pieces that pass the final quality check will be packed and shipped on Friday; those that fail will be remade.''')
answer('g121',
'''* Maliyet optimizasyonu kapsamında akıllı aydınlatma kullanımının değerlendirilmesi önerilmektedir.
* İklimlendirme sistemlerinin izlenmesi ve kontrolü için HVAC sensörlerinin değerlendirilmesi önerilmektedir.
* Belirtilen %12 tasarruf potansiyelinin, uygulama öncesi ve sonrası ölçümlerle doğrulanması önerilmektedir; verilen bilgiler bu potansiyelin dönemini veya hesaplama kapsamını belirtmemektedir.''',
'''* Assessing smart lighting is recommended as part of cost optimization.
* Assessing HVAC sensors for monitoring and controlling climate systems is recommended.
* The stated 12% savings potential should be verified through measurements before and after implementation; the supplied information does not specify its timeframe or calculation scope.''')
answer('g142',
'''Elif'in cevabının zorunlu olarak kendi kendini çürüttüğü söylenemez. Birinin konuştuğunu fark etmek veya sesini duymak, söylediklerini dikkatle dinlemek ve anlamakla aynı şey değildir. Elif, annesinin konuştuğunu fark etmiş ama içeriğine dikkat etmemiş olabilir.

Cevabın bağlama uygun oluşu, dinlemiş olabileceğini düşündürebilir; fakat bunu kanıtlamaz. Dolayısıyla burada kesin bir mantıksal çelişki veya Yalancı Paradoksu yoktur. En fazla, bağlama göre açıklanabilecek bir edimsel gerilimden söz edilebilir. Sorudaki “kendi kendini çürütüyor” varsayımı ek bilgi olmadan kabul edilmemelidir.''',
'''Elif's reply does not necessarily refute itself. Noticing that someone is speaking or hearing their voice is not the same as listening attentively to and understanding their words. Elif may have noticed her mother speaking without attending to the content.

The reply's relevance may suggest that she listened, but it does not prove it. There is therefore no established logical contradiction or Liar Paradox. At most, the context may create a pragmatic tension that needs explanation. The question's assumption of self-refutation should not be accepted without further information.''',
'''Yanıt vermek yalnızca konuşmayı fark etmeyi gerektirebilir; içeriği dinlemeyi zorunlu kılmaz. Elif'in sözünü doğru yapan tutarlı bir durum mümkündür. Bu yüzden kesin çelişki çıkaramam; bağlamsal kuşku ile ispatı ayırmalıyım.''',
'''Replying may require only noticing speech, not attending to its content. A coherent situation exists in which Elif's statement is true. I cannot infer a necessary contradiction; contextual suspicion must be distinguished from proof.''')
answer('g144',
'''Şirket, gözlenen ilişkiyi doğrudan süre → satın alma biçiminde yorumluyor. Oysa satın alma niyeti → sayfada geçirilen süre yönünü de değerlendirmelidir: niyeti yüksek kişiler ürünü daha uzun inceleyebilir.

Niyet aynı zamanda satın alma olasılığını artırıyorsa ortak neden, yani karıştırıcıdır: niyet → süre ve niyet → satın alma. Bu yapı, satın alma → süre biçimindeki ters nedensellikle aynı değildir. Gözlenen ilişki, ortak nedenden, sürenin gerçek etkisinden veya bunların birlikte işlemesinden kaynaklanabilir.

Bu nedenle kullanıcıyı yapay olarak daha uzun tutmanın satışı artıracağı da artırmayacağı da yalnızca bu korelasyondan belirlenemez. Belirli bir müdahalenin etkisi iyi tasarlanmış rastgele bir deneyle incelenebilir; niyeti istatistiksel olarak kontrol etmek ise ancak ilgili ölçüm ve nedensel varsayımlar yeterliyse yardımcı olur.''',
'''The company interprets the association directly as time → purchase. It should also consider purchase intention → time spent on the page: people with stronger intention may examine the product longer.

If intention also increases purchase probability, it is a common cause, or confounder: intention → time and intention → purchase. This structure is not the same as reverse causation of purchase → time. The observed association could arise from the common cause, a real effect of time, or both.

Therefore, this correlation alone establishes neither that artificially extending time would increase sales nor that it would not. A well-designed randomized experiment can investigate a particular intervention; statistical adjustment for intention helps only when the relevant measurement and causal assumptions are adequate.''',
'''Niyetin hem süreyi hem satın almayı etkilemesi ortak neden yapısıdır, satın alma→süre biçiminde ters nedensellik değildir. Sürenin nedensel etkisi bu korelasyondan belirlenemez. Ne sıfır etkiyi ne de artışı kesin söylemeliyim; müdahale ile yalnızca süre kavramını da ayırmalıyım.''',
'''Intention influencing both time and purchase is a common-cause structure, not reverse causation of purchase→time. The correlation does not identify time's causal effect. I should assert neither zero effect nor an increase, and distinguish a particular intervention from the abstract duration variable.''')
answer('g145',
'''“Değerli müşterilerimiz, sistemimizde yaşanan bir sorun nedeniyle siparişleriniz 3 gün gecikecek. Gecikmenin yaratacağı güçlük için özür dileriz; anlayışınız için teşekkür ederiz.”

Savunmacı sorumluluk reddi çıkarıldı; bilinen gecikme açıkça belirtildi ve özür eklendi. Doğrulanmamış çözüm çalışmaları, e-posta bildirimleri veya kesintisiz destek taahhütleri eklenmedi.''',
'''“Dear customers, an issue with our system will delay your orders by 3 days. We apologize for the inconvenience this delay will cause and thank you for your understanding.”

The defensive denial of responsibility was removed, the known delay was stated clearly, and an apology was added. No unverified claims about resolution work, email updates or round-the-clock support were introduced.''')
answer('g148',
'''İki kaynak da 2023'te Akdeniz'deki orman yangınlarını ve etkilenen alanı ele alıyor. Kaynak A 50 bin hektar, Kaynak B 45 bin hektar bildiriyor; verilen alanlar arasında 5 bin hektar fark var. Kaynak A ana neden olarak insan hatasını gösterirken Kaynak B iklim değişikliğini %60 oranında sorumlu tutuyor. Ancak bu yüzdenin neyin payı olduğu ve raporların ölçüm kapsamlarının aynı olup olmadığı açıklanmıyor. Nedenlere ilişkin farklı vurguların birbirini dışladığı veya yüzde ifadesinin yangın sayısının payını gösterdiği yalnızca bu metinlerden çıkarılamaz.''',
'''Both sources discuss Mediterranean forest fires in 2023 and the affected area. Source A reports 50 thousand hectares and Source B 45 thousand, a difference of 5 thousand hectares. Source A identifies human error as the main cause, whereas Source B attributes 60% responsibility to climate change. However, the denominator of that percentage and whether the reports use the same measurement scope are not specified. The texts alone do not establish that their causal emphases are mutually exclusive or that the percentage refers to the share of individual fires.''')

answer('g154',
'''Nâzım Hikmet'te toplumcu gerçekçilik, toplumsal yaşamı ve sıradan insanların deneyimini şiirin merkezine taşır. İki örnek:

* Kuvâyi Milliye: Kurtuluş Savaşı'nı kolektif bir mücadele olarak ele alır. Tarih yalnızca yöneticilerin değil, mücadeleye katılan insanların deneyimleriyle de anlatılır.
* Kız Çocuğu: Hiroşima'da ölen bir çocuğun sesiyle savaşın siviller üzerindeki yıkımını ve barış isteğini görünür kılar.

İlk örnekte kolektif özne, ikincisinde savaş mağdurunun sesi öne çıkar. Eser adlarını doğrulamak için Yapı Kredi Yayınları'nın Kuvâyi Milliye yayınına ve MEB EBA'nın Nâzım Hikmet–Kız Çocuğu içeriğine başvurulabilir; burada baskı ve sayfa numarası iddiası sunulmuyor.''',
'''In Nâzım Hikmet's poetry, socialist realism brings social life and ordinary people's experiences to the foreground. Two examples:

* Kuvâyi Milliye: It presents the War of Independence as a collective struggle. History is conveyed through the experiences of people taking part, not only through leaders.
* Kız Çocuğu: Through the voice of a child killed in Hiroshima, it makes the devastation of war on civilians and the desire for peace visible.

The first foregrounds a collective subject; the second gives a voice to a victim of war. The titles can be checked against Yapı Kredi Publications' edition of Kuvâyi Milliye and the Turkish Ministry of Education's EBA content Nâzım Hikmet–Kız Çocuğu; no edition-specific page references are claimed here.''')

answer('g012',
'''Yazım düzeltmesiyle: “İş ortaklığı mektubundaki maddeler onaylandı ki bunlar çok kritik. Proje yöneticisi, ki bu kişi çok tecrübeli, süreci yönetiyor ki ekip başarılı olsun.”

“mektubun daki” sözcüğü “mektubundaki” biçiminde bitişik yazılmalıdır. Buradaki “-ki” ektir; diğer üç “ki” ise bağlaçtır ve bu örneklerde ayrı yazılır. Proje yöneticisini açıklayan ara sözün sınırları virgüllerle gösterilmiştir. Virgül kullanımını yalnızca “ki” sözcüğünün varlığına bağlayan genel bir kural çıkarılmamalıdır.

Daha akıcı bir alternatif: “İş ortaklığı mektubundaki çok kritik maddeler onaylandı. Çok tecrübeli olan proje yöneticisi, ekibin başarılı olması için süreci yönetiyor.”''',
'''With the spelling corrected: “İş ortaklığı mektubundaki maddeler onaylandı ki bunlar çok kritik. Proje yöneticisi, ki bu kişi çok tecrübeli, süreci yönetiyor ki ekip başarılı olsun.”

“mektubun daki” must be written together as “mektubundaki”. Here “-ki” is a suffix; the other three instances of “ki” are conjunctions and are written separately in these examples. Commas mark the boundaries of the parenthetical description of the project manager. No general comma rule should be inferred merely from the presence of “ki”.

A more fluent alternative: “İş ortaklığı mektubundaki çok kritik maddeler onaylandı. Çok tecrübeli olan proje yöneticisi, ekibin başarılı olması için süreci yönetiyor.”''')

answer('g113',
'''* Belirli bir konu ve hedef kitle seçin; profiliniz hesabın amacını açıkça anlatsın.
* Düzenli ve paylaşılmaya değer içerik üretin. Reels dahil farklı biçimleri deneyip hangisinin kitlenizde işe yaradığını ölçün; tek bir biçimin her zaman en hızlı büyümeyi sağlayacağını varsaymayın.
* Yorumlara ve mesajlara yanıt verin; benzer hesaplarla ilgili ve samimi etkileşim kurun.
* Uygun hesaplarla ortak içerik veya iş birliği deneyin.
* İçeriğe uygun birkaç etiket kullanın; alakasız etiketlerle doldurmaktan kaçının.
* Insights üzerinden erişim ve etkileşimi izleyerek yaklaşımınızı güncelleyin.

Takipçi satın almak veya bot kullanmak, gerçek ilgi yerine yanıltıcı sayılar yaratabilir. Dağıtım kuralları değişebileceğinden belirli bir algoritmik sonucu garanti etmek yerine kendi hesabınızdaki veriye bakın.''',
'''* Choose a topic and target audience; make the account's purpose clear in your profile.
* Publish consistently and make content worth sharing. Test formats including Reels and measure what works for your audience; do not assume one format always produces the fastest growth.
* Respond to comments and messages, and engage relevantly and sincerely with similar accounts.
* Try suitable collaborations or joint content.
* Use a few relevant tags rather than filling posts with unrelated ones.
* Update your approach using reach and engagement data from Insights.

Buying followers or using bots can create misleading numbers rather than genuine interest. Since distribution rules can change, examine your account's data instead of assuming a guaranteed algorithmic outcome.''')


def replace_once(text, old, new):
    assert text.count(old) == 1, repr(old)
    return text.replace(old, new)


def prepare_repairs(groups):
    """Finish targeted edits from immutable input; return six-field replacements."""
    for gid, tr_old, tr_new, en_old, en_new in [
        ('g028', 'toplam yakıt maliyetinin 1100 TL’yi aşmaması', 'yol boyunca satın alınan ek yakıtın toplam maliyetinin 1100 TL’yi aşmaması (başlangıçtaki dolu deponun bedeli bu sınıra dahil değildir)',
         'the total fuel cost not exceeding 1100 TL', 'the total cost of additional fuel purchased en route not exceeding 1100 TL (the cost of the initially full tank is excluded)'),
        ('g039', 'orta çizgisine paralel', 'orta çizgisi üzerinden', 'parallel to its', 'along its'),
        ('g076', None, None,
         'would you realize what you could change in your current life with that money?', 'what would you realize you could change in your current life with that money?'),
        ('g140', 'Kaç müşteri destek hizmetinden memnun kalmıştır?', 'Kaç müşteri destek hizmetinden çok memnun kalmıştır?',
         'How many customers were satisfied with the support service?', 'How many customers were very satisfied with the support service?'),
        ('g154', 'doğru künyeli şiir örnekleriyle', 'doğru adlandırılmış şiir örnekleriyle', 'with correctly cited examples of poems', 'with correctly named examples of poems'),
    ]:
        group = groups['bp01-' + gid]
        repair = REPAIRS.setdefault(gid, {})
        for lang, old, new in [('tr', tr_old, tr_new), ('en', en_old, en_new)]:
            if old is None:
                continue
            inp = group[f'{lang}-{lang}']['messages'][1]['content']
            # Both horizontal and vertical occurrences change in the folding prompt.
            assert old in inp
            repair[lang + '_input'] = inp.replace(old, new)
    for lang in ('tr', 'en'):
        group = groups['bp01-g065'][lang + '-' + lang]
        text = group['messages'][-1]['content']
        edits = [
            ('Bu üç adım tamamlanmadan veri akışı başlamaz.', 'Bu, bağlantı kuruluşunun basitleştirilmiş anlatımıdır; bazı durumlarda SYN segmentleri de uygulama verisi taşıyabilir.'),
            ('Yeni bir işlem eklendiğinde bunu tüm köylüler onaylar ve kaydeder.', 'Yeni kayıtların kabulü ortak uzlaşma kurallarına bağlıdır; her katılımcının her işleme tek tek onay vermesi gerekmez.'),
            ('Data flow does not begin until these three steps are completed.', 'This is a simplified account of connection establishment; in some cases SYN segments can also carry application data.'),
            ('When a new transaction is added, all the villagers confirm and record it.', 'Acceptance of new records follows shared consensus rules; every participant need not individually approve every transaction.'),
        ]
        for old, new in edits:
            if old in text:
                text = replace_once(text, old, new)
        REPAIRS.setdefault('g065', {})[lang + '_output'] = text
        text = groups['bp01-g068'][lang + '-' + lang]['messages'][-1]['content']
        if lang == 'tr':
            text = text.replace('Buradaki taka,', 'Buradaki takas,').replace('Takayı görünür', 'Takası görünür')
            text = replace_once(text, 'Dolayısıyla topluluk düzeyinde habitat uygunluğu, sediman birikimine göre tek tepeli, yani bir optimumu olan bir eğri çizer;', 'Topluluk düzeyindeki eğri, türlerin tepkilerine ve kullanılan ağırlıklara bağlıdır; tek tepeli olması bir varsayım olarak sınanmalıdır, birden çok tepe de görülebilir;')
        else:
            text = replace_once(text, 'Therefore, at the community level, habitat suitability traces a unimodal curve against sediment accumulation, that is, a curve with an optimum;', 'The community-level curve depends on species responses and the chosen weights; unimodality should be tested as an assumption, and multiple peaks are also possible;')
        REPAIRS.setdefault('g068', {})[lang + '_output'] = text
        text = groups['bp01-g071'][lang + '-' + lang]['messages'][-1]['content']
        REPAIRS.setdefault('g071', {})[lang + '_output'] = replace_once(text, 'Karagöz Hacivat Neden Öldürüldü?', 'Hacivat Karagöz Neden Öldürüldü?')
        text = groups['bp01-g106'][lang + '-' + lang]['messages'][-1]['content']
        old, new = ('Net maaşın, brütün yaklaşık %30-40 altında olacağını da hesaba katın.', 'Net ve brüt tutarları karşılaştırırken vergi, kesinti ve yan hakları aynı koşullarda değerlendirin; sabit bir net/brüt oranı varsaymayın.') if lang == 'tr' else (
            'Also take into account that net salary will be roughly 30-40% below gross.', 'Compare net and gross amounts under the same tax, deduction and benefit assumptions; do not assume a fixed net-to-gross ratio.')
        REPAIRS.setdefault('g106', {})[lang + '_output'] = replace_once(text, old, new)
        text = groups['bp01-g126'][lang + '-' + lang]['messages'][-1]['content']
        REPAIRS.setdefault('g126', {})[lang + '_output'] = replace_once(text, '(155)', '(112)')
    # Mark the grammar rule as stipulated rather than universal English classification.
    answer('g034',
        'Verilen sınıflandırmaya göre bu, bağlı cümledir. Alıştırma “çünkü” ile birleştirilen iki yargıyı bu grupta sayıyor. Örneğin “Okula gidemedi çünkü hastalanmıştı” ifadesinde “Okula gidemedi” ve “Hastalanmıştı” yargıları bağlanır. Bu cevap, soruda verilen Türkçe dil bilgisi sınıflandırmasını uygular.',
        'Under the classification stipulated in the exercise, this is a “bağlı cümle” (a linked sentence). The exercise places two judgments joined by “çünkü” in that category. For example, “Okula gidemedi çünkü hastalanmıştı” links “Okula gidemedi” and “Hastalanmıştı”. This applies the supplied Turkish classification; it does not classify English “because” as a coordinating conjunction.',
        'Sorunun verdiği sınıflandırmayı uygulamalıyım. Bu kurala göre çünkü ile bağlanan yargılar bağlı cümle sayılır; bunu evrensel veya İngilizceye aynen aktarılan bir sınıflandırma diye sunmamalıyım.',
        'I should apply the classification supplied by the question. Under that rule, judgments linked by çünkü count as a linked sentence; I should not present this as universal or transfer it unchanged to English grammar.')
    return REPAIRS
