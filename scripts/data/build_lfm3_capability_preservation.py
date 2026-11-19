"""Deterministic, CPU-only private-research packet; never imports eval as training.

Run from any directory. Existing outputs must match exactly (no overwrite).
All authored templates and targets live here; historical data is read only for
schema comparison and leakage screening, after new examples are constructed.
"""
import collections
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
OUT = BASE / 'capability-preservation-v01'
SCHEMA = BASE / 'bilingual-pilot-v01/revisions/v01-corrections-02/train.jsonl'
TRAIN, EVAL, REFS, CHECKS = [], [], [], []


def sha(b):
    return hashlib.sha256(b).hexdigest()


def encoded(x):
    return (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def norm(s):
    return ' '.join(unicodedata.normalize('NFKC', s).casefold().split())


def emit(split, lang, family, prompt, answer, solution=None, check=None):
    bucket = TRAIN if split == 'train' else EVAL
    ident = f'cp01-{split}-{len(bucket)+1:03d}'
    suffix = 'Yanıtını Türkçe ver.' if lang == 'tr' else 'Answer in English.'
    messages = [dict(role='system', content=('Doğru ve açık yanıt ver; eksik bilgiyi uydurma.' if lang == 'tr' else 'Answer accurately and clearly; do not invent missing information.')),
                dict(role='user', content=prompt + '\n\n' + suffix)]
    group = ident  # no translated copies or shared task groups across splits
    if split == 'eval':
        bucket.append(dict(id=ident, group_id=group, task_id=ident, category=family,
                           direction=f'{lang}-{lang}', input_language=lang, output_language=lang,
                           messages=messages, evaluation_only=True, training_allowed=False,
                           provenance='Fresh agent-authored synthetic case, 2026-11-19; no historical item used as a source'))
        REFS.append(dict(id=ident, group_id=group, direction=f'{lang}-{lang}', output_language=lang,
                         final_answer=answer, reference_answer=answer, key_facts=[answer],
                         rubric='Require correct meaning, every explicit constraint, requested language, and no invented facts. Accept equivalent prose; numeric tasks require the exact value with compatible units. Score correctness, format, language and stopping separately.',
                         verification='independent executable check' if check else 'agent semantic/constraint review; not owner-adjudicated',
                         worked_solution=solution, note='Evaluation only; never train on prompts, references, translations or derivatives.'))
    else:
        source = dict(source_repo=None, source_revision=None, source_filename=Path(__file__).name,
                      source_line_1based=None, source_row_id=ident, source_category=family,
                      source_split='train', original_record_sha256=None,
                      source_prompt_sha256=sha(prompt.encode()), source_answer_sha256=sha(answer.encode()))
        bucket.append(dict(id=ident, group_id=group, canonical_task_id=group, split='train',
            direction=f'{lang}-{lang}', input_language=lang, output_language=lang,
            messages=messages + [dict(role='assistant', content=answer)],
            worked_solution=solution, reasoning_language=lang if solution else None,
            has_reasoning=bool(solution), category=family,
            capability_label_basis='agent descriptive; not owner-adjudicated', source_key='fresh-synthetic-cp01',
            language_instruction=dict(text=suffix, position='user_suffix', language=lang, variant='standard'),
            output_language_effect='full', source_row_id=ident, original_source=source,
            original_row_sha256=None, source_user_sha256=sha(prompt.encode()),
            source_assistant_sha256=sha(answer.encode()), source_reasoning_sha256=sha(solution.encode()) if solution else None,
            transformation=dict(kind='fresh-authored', translated=dict(input=False, output=False, reasoning=False, system=False),
                translator=None, translated_on=None, translation_file=None, translation_file_sha256=None,
                system_prompt='fresh language-matched neutral instruction', language_instruction_added=True,
                trailing_whitespace='none', translation_flag_types=[], translation_flag_max_severity=None),
            generation_method='synthetic; Codex session authored templates; deterministic Python instantiation',
            use_restriction='Owner-authorized private research only; no publication or broader rights determination.',
            intended_use='training-candidate', quality_status='CPU verified arithmetic; agent reviewed prose; not independent human review'))
    if check:
        CHECKS.append(dict(id=ident, family=family, expected=answer, **check))


def math_train():
    # Five modest structures, four instances per language. No translated pairs.
    for lang in ['tr', 'en']:
        tr = lang == 'tr'
        for j in range(4):
            k = j + (0 if tr else 5)
            a, b, n = 31 + 2*k, 17 + k, 6 + k
            ans = (a-b)*n
            emit('train', lang, 'signed_change',
                 f'Bir soğuk odanın sıcaklığı her saat {a} derece yükselip {b} derece düşüyor. Bu döngü {n} kez tekrarlanırsa başlangıca göre net değişim kaç derecedir?' if tr else f'A test chamber warms by {a} degrees and cools by {b} degrees in each cycle. After {n} cycles, what is its net temperature change?',
                 str(ans), f'({a} - {b}) × {n} = {ans}.', dict(op='signed', args=[a,b,n]))
            start, step, idx = 43+3*k, 7+k, 9+k
            ans = start + step*(idx-1)
            emit('train', lang, 'indexed_progression',
                 f'Bir etiket dizisi {start} ile başlıyor; her yeni etiket öncekinin {step} fazlası. İlk etiket birinci sıradaysa {idx}. etiket nedir?' if tr else f'A label sequence begins at {start} and increases by {step} each time. Counting the first label as position one, what is label {idx}?',
                 str(ans), f'{start} + ({idx} - 1) × {step} = {ans}.', dict(op='progression', args=[start,step,idx]))
            x, y = 13+k, 19+2*k
            total, diff = x+y, y-x
            emit('train', lang, 'sum_difference',
                 f'İki arşiv rafında toplam {total} dosya var. İkinci rafta birinciden {diff} fazla dosya var. Birinci rafta kaç dosya bulunur?' if tr else f'Two archive shelves hold {total} files altogether. The second holds {diff} more than the first. How many files are on the first shelf?',
                 str(x), f'({total} - {diff}) / 2 = {x}.', dict(op='sumdiff', args=[total,diff]))
            count, divisor, add = 11+k, 8+k, 23+k
            initial = count*divisor-add
            emit('train', lang, 'reverse_operation',
                 f'Bir sayıya {add} ekleyip sonucu {divisor} ile bölünce {count} bulunuyor. Başlangıçtaki sayı nedir?' if tr else f'Adding {add} to a number and dividing the result by {divisor} gives {count}. Recover the original number.',
                 str(initial), f'{count} × {divisor} - {add} = {initial}.', dict(op='reverse', args=[count,divisor,add]))
            u, v, w = 71+k, 89+2*k, 103+3*k
            # Explicit transitive ordering, no world knowledge or hidden assumptions.
            emit('train', lang, 'transitive_order',
                 f'Üç sensörün ölçümleri: K={u}, L={v}, M={w}. En küçükten en büyüğe sensör kodlarını yaz.' if tr else f'Three sensor readings are K={u}, L={v}, M={w}. List the sensor codes from smallest to largest.',
                 'K, L, M', f'{u} < {v} < {w}; K < L < M.', dict(op='order', args=[u,v,w]))


# Individually authored general-language tasks, no source documents fetched.
GENERAL_TR = [
('grammar','“Bende yarın orada olacağım.” cümlesindeki bağlaç yazımını düzelt; yalnızca cümleyi yaz.','Ben de yarın orada olacağım.'),
('grammar','“Dosyayı sende mi bıraktım?” cümlesinde bulunma anlamındaki sözcük doğru mu? Kısaca açıkla.','Evet. “Sende”, dosyanın bulunduğu kişiyi belirttiği için bitişik yazılır.'),
('rewrite','“Raporu hemen yolla!” isteğini iş arkadaşına uygun, nazik bir soruya dönüştür.','Raporu uygun olduğunda gönderebilir misin?'),
('reading','Not: Prototipin gövdesi hazır; kapak henüz boyanmadı. Hangi parça için boyama işi bekliyor?','Kapak için boyama işi bekliyor.'),
('summary','Tek cümlede özetle: Tamir ekibi gevşeyen menteşeyi sıktı. Kapının sesi kesildi. Kilit değiştirilmedi.','Tamir ekibi kilidi değiştirmeden menteşeyi sıkarak kapının sesini giderdi.'),
('structured_extraction','“Cihaz: Lodos; durum: bakımda” bilgisini yalnızca cihaz ve durum anahtarları olan JSON nesnesine dönüştür.','{"cihaz":"Lodos","durum":"bakımda"}'),
('uncertainty','Notta yalnızca “Fidanlar gölgeli alana taşındı” yazıyor. Fidanların türü nedir?','Notta fidanların türü belirtilmiyor.'),
('explanation','Buharlaşma ile kaynama arasındaki farkı iki kısa cümlede açıkla.','Buharlaşma sıvının yüzeyinde farklı sıcaklıklarda gerçekleşebilir. Kaynama ise belirli basınçta kaynama sıcaklığına ulaşan sıvının içinde de kabarcıklar oluşmasıdır.'),
('classification','“Keşke anahtarımı yanıma alsaydım.” cümlesi geçmişe yönelik pişmanlık mı, gelecek planı mı anlatır?','Geçmişe yönelik pişmanlık anlatır.'),
('instruction','Yalnızca noktalı virgülle ayrılmış üç malzeme yaz: keçe, ip, düğme. Sıralamayı tersine çevir.','düğme;ip;keçe'),
('coreference','“Ekin çantayı sandalyeye koydu; ardından onu açtı.” cümlesinde açılan nesne için en doğal yorum nedir?','En doğal yorum, açılan nesnenin çanta olmasıdır.'),
('grounded_comparison','Notlar: Keten kılıf yıkanabilir ama fermuarsız. Yün kılıf fermuarlı ama yalnızca kuru temizlemeye uygun. Evde yıkanabilen hangisi?','Keten kılıf evde yıkanabilir.'),
('planning','Boya kurumadan çerçeve takılmamalı; boyadan önce yüzey zımparalanmalı. Üç işi sırayla yaz.','Yüzeyi zımparala; boya ve kurumasını bekle; çerçeveyi tak.'),
('grammar','“Çocuklar bahçede oynuyorlar.” cümlesini anlamını koruyarak tekil özneyle yeniden yaz.','Çocuk bahçede oynuyor.'),
('definition','Bir metindeki “örtük bilgi” ne demektir? Kısa bir tanım ver.','Doğrudan söylenmeyen, bağlamdan çıkarılabilen bilgidir.'),
('faithfulness','“Deneme başarılı olabilir.” ifadesini kesin başarı sözü vermeden başka türlü yaz.','Denemenin başarılı olma ihtimali var.'),
('reading','“Açık renkli numune kurutuldu; koyu renkli numune kapalı kapta saklandı.” Hangi numune kurutulmadı?','Koyu renkli numune kurutulmadı.'),
('punctuation','Hitaptan sonra virgül ekle: “Sevgili Derya mektubunu aldım.” Yalnızca düzeltilmiş cümleyi yaz.','Sevgili Derya, mektubunu aldım.'),
('word_sense','“Bu sözler içimi ısıttı.” cümlesindeki ısınma gerçek sıcaklık değişimi mi, mecaz mı?','Mecazdır; sözlerin kişiye iyi hissettirdiğini anlatır.'),
('clarification','Bir kullanıcı yalnızca “Onu daha kısa yap” diyor, ancak konuşmada metin yok. Uygun tek bir açıklayıcı soru yaz.','Hangi metni kısaltmamı istersin?'),
]
GENERAL_EN = [
('grammar','Correct only the verb agreement: “The bundle of cables are missing.”','The bundle of cables is missing.'),
('rewrite','Make “Give me the draft” a polite request without adding a deadline.','Could you please send me the draft?'),
('reading','Memo: The lens was cleaned, but its housing still needs polishing. What work remains?','The housing still needs polishing.'),
('summary','Summarize in one sentence: A storm damaged the footbridge. Inspectors closed it. The riverside path remains open.','The storm-damaged footbridge is closed for inspection, while the riverside path remains open.'),
('structured_extraction','Return only JSON with keys material and finish: “Material: brass; finish: matte”.','{"material":"brass","finish":"matte"}'),
('uncertainty','The log says “A replacement filter was fitted.” Does it identify the manufacturer?','No. The log does not identify the manufacturer.'),
('explanation','Explain why a metal spoon can feel colder than a wooden spoon at the same room temperature.','Metal transfers heat away from your hand faster than wood, so it can feel colder even when both are at the same temperature.'),
('classification','Does “If only I had saved the file” express regret or a confirmed future action?','It expresses regret.'),
('instruction','Return these words in reverse order, separated by a slash with no spaces: reed cork wax.','wax/cork/reed'),
('coreference','“Mira removed the vase from the crate and washed it.” What does “it” most naturally refer to?','The vase.'),
('grounded_comparison','A cedar box is light but unlined. A steel box is lined but heavy. Which is lined? Use only these facts.','The steel box is lined.'),
('planning','A seal must cure before pressure testing, and the joint must be cleaned before sealing. State the work order.','Clean the joint, apply the seal and let it cure, then pressure-test it.'),
('grammar','Change “The geese were resting” to singular while preserving tense.','The goose was resting.'),
('definition','What is a counterexample in an argument?','A case that contradicts a general claim.'),
('faithfulness','Paraphrase “The coating may reduce glare” without increasing certainty.','The coating might make glare less noticeable.'),
('reading','Only the amber switch activates the fan; the violet switch controls the lamp. Which switch should activate the fan?','The amber switch.'),
('punctuation','Add the missing possessive apostrophe for one artist: “The artists sketch is unfinished.”','The artist’s sketch is unfinished.'),
('word_sense','In “Her explanation shed light on the problem”, is light literal or figurative?','Figurative: the explanation made the problem clearer.'),
('clarification','A user says “Compare them” without naming any objects. Ask one useful clarifying question.','Which items would you like me to compare?'),
('logic_language','“Not every parcel is fragile.” Does this mean that no parcel is fragile?','No. It means at least one parcel is not fragile; others may be fragile.'),
]


def holdout():
    # Eight structures absent from new training. Different facts in each language.
    for lang in ['tr', 'en']:
        tr = lang == 'tr'
        a, b = (14, 21) if tr else (16, 28)
        import math
        n = math.lcm(a,b)
        emit('eval', lang, 'synchronization',
             f'İki uyarıcı birlikte çaldıktan sonra biri {a}, diğeri {b} dakikada bir çalıyor. İlk kez kaç dakika sonra yeniden birlikte çalarlar?' if tr else f'Two alarms sound together, then repeat every {a} and {b} minutes. After how many minutes will they first coincide again?',
             str(n), f'EKOK/LCM({a}, {b}) = {n}.', dict(op='lcm', args=[a,b]))
        side = 15 if tr else 18
        emit('eval', lang, 'border_area',
             f'Kenar uzunluğu {side} metre olan kare bir bahçenin içine, tüm kenarlar boyunca 2 metre genişliğinde yol yapılıyor. Yolun alanı kaç metrekaredir?' if tr else f'Inside a square garden of side {side} metres, a path two metres wide follows all four edges. What is the area of the path in square metres?',
             str(side**2-(side-4)**2), f'{side}² - ({side} - 4)² = {side**2-(side-4)**2}.', dict(op='border', args=[side,2]))
        reds, blues = (7, 9) if tr else (8, 11)
        from fractions import Fraction
        prob = str(Fraction(reds,reds+blues)*Fraction(reds-1,reds+blues-1))
        emit('eval', lang, 'without_replacement',
             f'Bir kesede {reds} kırmızı ve {blues} mavi taş var. Geri koymadan rastgele iki taş çekiliyor. İkisinin de kırmızı olma olasılığını sade kesirle yaz.' if tr else f'A bag contains {reds} red and {blues} blue stones. Draw two uniformly at random without replacement. Give the probability both are red as a reduced fraction.',
             prob, f'{reds}/{reds+blues} × {reds-1}/{reds+blues-1} = {prob}.', dict(op='probability', args=[reds,blues]))
        data = [6,13,18,24,37] if tr else [9,16,23,31,42]
        emit('eval',lang,'median',
             f'Ölçümler: {data}. Ortanca değer nedir?' if tr else f'The measurements are {data}. What is their median?',
             str(data[2]), f'{data}; '+('Sıralı dizinin üçüncü değeri.' if tr else 'The third value in the sorted list.'), dict(op='median',args=data))
        total, both, left, right = (91,12,38,29) if tr else (107,14,46,33)
        ans = total-left-right+both
        emit('eval',lang,'inclusion_exclusion',
             f'{total} kişiden {left} kişi seramik, {right} kişi gravür yapıyor; {both} kişi ikisini de yapıyor. Kaç kişi bu iki etkinliğin hiçbirini yapmıyor?' if tr else f'Among {total} people, {left} do ceramics and {right} do engraving; {both} do both. How many do neither?',
             str(ans),f'{total} - ({left} + {right} - {both}) = {ans}.',dict(op='neither',args=[total,left,right,both]))
        cap, target = (9,68) if tr else (11,94)
        n = (target+cap-1)//cap
        emit('eval',lang,'ceiling_capacity',
             f'Bir fırın her turda en fazla {cap} parça pişiriyor. {target} parçanın tamamı için en az kaç tur gerekir?' if tr else f'A kiln holds at most {cap} pieces per firing. What is the minimum number of firings needed for all {target} pieces?',
             str(n),f'{n-1} × {cap} < {target} ≤ {n} × {cap}.',dict(op='ceiling',args=[target,cap]))
        hours, minutes, duration = (23,47,38) if tr else (22,53,86)
        end = (hours*60+minutes+duration)%1440
        ans = f'{end//60:02d}:{end%60:02d}'
        emit('eval',lang,'midnight_rollover',
             f'Bir işlem {hours:02d}:{minutes:02d} saatinde başlıyor ve {duration} dakika sürüyor. Bitiş saatini 24 saat biçiminde yaz.' if tr else f'A process begins at {hours:02d}:{minutes:02d} and lasts {duration} minutes. Give the finishing time in 24-hour notation.',
             ans,f'({hours} × 60 + {minutes} + {duration}) mod 1440 = {end}; {ans}.',dict(op='clock',args=[hours,minutes,duration]))
        # Exhaustive truth-table verification of a constraint problem.
        emit('eval',lang,'exclusive_constraints',
             'P, R ve S anahtarlarından tam ikisi açık. P açıksa R kapalıdır. S kapalıysa P de kapalıdır. Hangi iki anahtarın açık olduğu kesin olarak söylenebilir mi?' if tr else 'Exactly two switches P, R and S are on. If P is on, R is off. If S is off, P is off. Can the two on-switches be uniquely identified?',
             'Hayır; P ve S ya da R ve S açık olabilir.' if tr else 'No; either P and S or R and S can be on.',
             'P,R,S: (1,0,1), (0,1,1).',dict(op='truth',args=[]))

    tr_cases = [
      ('ambiguity','“Fotoğrafçı ressamı dürbünle gördü.” cümlesinin iki farklı yorumunu yaz.','Fotoğrafçı dürbün kullanarak ressamı görmüş olabilir. Ressamın yanında dürbün bulunuyor da olabilir.'),
      ('conditional_reading','Kural: Etiketi yıpranmış kaplar yeniden etiketlenir; çatlak kaplar ise etiketine bakılmadan ayrılır. Etiketi sağlam ama çatlak kap ne yapılır?','Çatlak olduğu için ayrılır.'),
      ('negation_scope','“Sadece Selva raporu imzalamadı.” cümlesini, diğer kişilerin imzaladığını açıkça belirterek yeniden yaz.','Selva dışındaki herkes raporu imzaladı; Selva imzalamadı.'),
      ('title','Metin için en fazla dört sözcüklük başlık yaz: Tohumlar kâğıt zarflarda saklandı. Her zarfın üzerine bitkinin adı ve toplama yeri yazıldı.','Tohumların Etiketlenerek Saklanması'),
      ('register','“Başvurunuz işleme alınmıştır.” cümlesini samimi ama saygılı, ikinci tekil kişili bir ifadeye dönüştür.','Başvurunu işleme aldık.'),
      ('error_detection','Bir özet “Tüm perdeler değiştirildi” diyor. Kaynakta “Yalnızca yırtık perde değiştirildi” yazıyor. Özetteki anlam hatasını belirt.','Özet kapsamı genişletiyor; tüm perdeler değil, yalnızca yırtık perde değiştirildi.'),
      ('evidence','Bir araştırmada daha çok yürüyenlerin daha iyi uyuduğu görülmüş. Bu bulgu tek başına yürümenin iyi uykuya neden olduğunu kanıtlar mı?','Hayır. Birlikte görülmeleri tek başına nedenselliği kanıtlamaz; başka etkenler rol oynayabilir.'),
      ('lexical_constraint','“oysa” sözcüğünü içeren, beklenti ile sonucu karşılaştıran tek bir Türkçe cümle yaz.','Havanın açık kalacağını sanıyordum, oysa akşama doğru yağmur başladı.'),
    ]
    en_cases = [
      ('ambiguity','Give two readings of “The curator noticed the visitor with a telescope.”','The curator may have used a telescope to notice the visitor, or the visitor may have had a telescope.'),
      ('conditional_reading','Rule: Faded tags are replaced, but leaking jars are discarded regardless of their tags. What happens to a leaking jar with a new tag?','It is discarded because it leaks.'),
      ('negation_scope','Rewrite “Only Rowan did not submit the form” to state explicitly what everyone else did.','Everyone except Rowan submitted the form; Rowan did not.'),
      ('title','Write a title of at most four words: Clay samples were wrapped separately. Each wrapper recorded the excavation site and layer.','Labeling Excavated Clay Samples'),
      ('register','Rewrite “Your request has been received” in a friendly, direct style without promising a result.','We’ve received your request.'),
      ('error_detection','A summary says “Every window was sealed.” Its source says “The draughty attic window alone was sealed.” Explain the error.','The summary wrongly expands the scope: only the draughty attic window was sealed.'),
      ('evidence','A survey links more reading with higher vocabulary scores. Does the association alone establish that reading caused the difference?','No. Association alone does not establish causation; other factors may explain the difference.'),
      ('lexical_constraint','Write one sentence using “although” to contrast an expectation with an outcome.','Although the trail looked easy, the climb exhausted us.'),
    ]
    for lang, cases in [('tr',tr_cases),('en',en_cases)]:
        for cat,p,a in cases:
            emit('eval',lang,cat,p,a)


def verify_math(c):
    from fractions import Fraction
    from math import lcm
    a = c['args']; op=c['op']
    if op=='signed': value=sum([a[0],-a[1]]*a[2])
    elif op=='progression': value=list(range(a[0],a[0]+a[1]*a[2],a[1]))[-1]
    elif op=='sumdiff':
        value=next(x for x in range(a[0]+1) if x+(x+a[1])==a[0])
    elif op=='reverse':
        value=next(x for x in range(10000) if Fraction(x+a[2],a[1])==a[0])
    elif op=='order':
        value=', '.join(k for _,k in sorted(zip(a,['K','L','M'])))
    elif op=='lcm': value=next(x for x in range(1,a[0]*a[1]+1) if x%a[0]==x%a[1]==0)
    elif op=='border': value=sum(1 for x in range(a[0]) for y in range(a[0]) if x<a[1] or y<a[1] or x>=a[0]-a[1] or y>=a[0]-a[1])
    elif op=='probability':
        colors=[1]*a[0]+[0]*a[1]
        pairs=list(itertools.permutations(range(len(colors)),2))
        value=Fraction(sum(colors[i]*colors[j] for i,j in pairs),len(pairs))
    elif op=='median': value=sorted(a)[len(a)//2]
    elif op=='neither':
        # Explicit sets realizing the supplied counts/intersection.
        left=set(range(a[1])); right=set(range(a[1]-a[3],a[1]-a[3]+a[2]))
        value=len(set(range(a[0]))-(left|right))
    elif op=='ceiling': value=next(n for n in range(a[0]+1) if n*a[1]>=a[0])
    elif op=='clock':
        from datetime import datetime,timedelta
        value=(datetime(2000,1,1,a[0],a[1])+timedelta(minutes=a[2])).strftime('%H:%M')
    elif op=='truth':
        states=[s for s in itertools.product([0,1],repeat=3) if sum(s)==2 and (not s[0] or not s[1]) and (s[2] or not s[0])]
        assert states==[(0,1,1),(1,0,1)]
        assert ('Hayır' in c['expected'] or c['expected'].startswith('No;'))
        return
    else: raise ValueError(op)
    assert str(value)==c['expected'],c


def write(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        assert path.read_bytes()==data, f'Frozen file differs: {path}'
    else: path.write_bytes(data)


def main():
    math_train()
    for lang,cases in [('tr',GENERAL_TR),('en',GENERAL_EN)]:
        for cat,p,a in cases: emit('train',lang,cat,p,a)
    holdout()
    assert len(TRAIN)==80 and len(EVAL)==len(REFS)==32
    sample=json.loads(SCHEMA.read_text(encoding='utf-8').splitlines()[0])
    for row in TRAIN:
        assert set(row)==set(sample), (set(row)^set(sample))
        assert isinstance(row['worked_solution'],str) if row['has_reasoning'] else row['worked_solution'] is None
        assert [m['role'] for m in row['messages']]==['system','user','assistant']
    for row in EVAL: assert [m['role'] for m in row['messages']]==['system','user']
    assert {r['id'] for r in EVAL}=={r['id'] for r in REFS}
    assert len({r['id'] for r in TRAIN+EVAL})==112
    assert collections.Counter(r['input_language'] for r in TRAIN)=={'tr':40,'en':40}
    assert collections.Counter(r['input_language'] for r in EVAL)=={'tr':16,'en':16}
    assert len({norm(r['messages'][1]['content']) for r in TRAIN+EVAL})==112
    for c in CHECKS: verify_math(c)
    # Scan historical JSON/JSONL under the model experiment tree, excluding
    # our own packet. Extract only known prompt-bearing fields, never targets
    # as source material. Pin every inspected file, including zero-prompt files.
    historical=[]; inventory=[]; parse_errors=[]
    def extract(x, origin):
        if isinstance(x,dict):
            msgs=x.get('messages')
            if isinstance(msgs,list):
                for m in msgs:
                    if isinstance(m,dict) and m.get('role')=='user' and isinstance(m.get('content'),str): historical.append((origin,m['content']))
            for k,v in x.items():
                if k in ('prompt','question','user_prompt','user') and isinstance(v,str): historical.append((origin,v))
                elif k!='messages' and isinstance(v,(dict,list)): extract(v,origin)
        elif isinstance(x,list):
            for v in x: extract(v,origin)
    for path in sorted(BASE.rglob('*')):
        if OUT in path.parents or not path.is_file() or path.suffix not in ('.json','.jsonl'): continue
        raw=path.read_bytes(); rel=path.relative_to(ROOT).as_posix(); before=len(historical)
        if len(raw)>15_000_000:
            inventory.append(dict(path=rel,sha256=sha(raw),prompts=0,scan_status='hash only; oversized source/result artifact, not parsed'))
            continue
        try:
            if path.suffix=='.jsonl':
                for line in raw.decode('utf-8-sig').splitlines():
                    if line.strip(): extract(json.loads(line),rel)
            else: extract(json.loads(raw.decode('utf-8-sig')),rel)
        except (ValueError,UnicodeError) as e: parse_errors.append(dict(path=rel,error=str(e)))
        inventory.append(dict(path=rel,sha256=sha(raw),prompts=len(historical)-before))
    assert not parse_errors,parse_errors
    # Lexical screens complement, but cannot prove, semantic independence.
    def words(s): return set(re.findall(r'\w+',norm(s)))
    def grams(s):
        toks=re.findall(r'\w+',norm(s)); return set(zip(*(toks[i:] for i in range(5))))
    unique={norm(s):(origin,s) for origin,s in historical}
    old=[(o,s,words(s),None) for o,s in unique.values()]
    comparisons=[]
    for row in TRAIN+EVAL:
        prompt=row['messages'][1]['content']; w=words(prompt); g=grams(prompt)
        assert norm(prompt) not in unique, f'Historical exact overlap {row["id"]}'
        candidates=[]
        for origin,s,sw,sg in old:
            score=len(w&sw)/max(1,len(w|sw))
            shared=0
            candidates.append((score,shared,origin,s))
        score,shared,origin,s=max(candidates,default=(0,0,'',''))
        shared=len(g&grams(s))
        comparisons.append(dict(id=row['id'],max_word_jaccard=round(score,4),shared_5grams_at_nearest=shared,
                                nearest_path=origin,nearest_prompt=s))
        assert score<0.65, f'Near duplicate needs review: {row["id"]} {score}'
    cross=[]
    for t in TRAIN:
        for e in EVAL:
            tw,ew=words(t['messages'][1]['content']),words(e['messages'][1]['content'])
            cross.append((len(tw&ew)/len(tw|ew),t['id'],e['id']))
    assert max(cross)[0]<0.65
    def jsonl(rows): return ''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode('utf-8')
    payload={'train.jsonl':jsonl(TRAIN),'eval-prompts.jsonl':jsonl(EVAL),'eval-references.jsonl':jsonl(REFS),
             'verification-cases.json':encoded(CHECKS),'protected-inputs.json':encoded(inventory),
             'overlap-review.json':encoded(comparisons)}
    report=dict(status='PASS',train_rows=80,eval_rows=32,train_languages={'tr':40,'en':40},eval_languages={'tr':16,'en':16},
                independently_checked_reasoning_cases=len(CHECKS),train_reasoning_rows=sum(r['has_reasoning'] for r in TRAIN),
                schema_keys_match=True,unique_prompts=112,exact_historical_overlap=0,parse_errors=parse_errors,
                historical_files=len(inventory),historical_prompt_occurrences=len(historical),historical_unique_prompts=len(old),
                max_historical_word_jaccard=max(r['max_word_jaccard'] for r in comparisons),
                max_train_eval_word_jaccard=max(cross)[0],train_eval_nearest_pair=max(cross)[1:],
                train_categories=dict(collections.Counter(r['category'] for r in TRAIN)),
                eval_categories=dict(collections.Counter(r['category'] for r in EVAL)),
                length_characters={split:dict(min=min(len(json.dumps(r,ensure_ascii=False)) for r in rows),max=max(len(json.dumps(r,ensure_ascii=False)) for r in rows)) for split,rows in [('train',TRAIN),('eval',EVAL)]},
                tokenization='Not performed; no model/tokenizer downloaded. Native-template length, label and truncation audit remains required before GPU training.',
                limitations='Lexical checks are not semantic/cross-lingual proof. Training repeats five reasoning templates; paired eval families across languages are not independent family-level evidence. No external benchmark corpus scanned; broad task categories overlap deliberately.')
    payload['validation.json']=encoded(report)
    readme='''# Capability preservation v01

Prepared 2026-11-19 for the owner-authorized next GPU experiments. Data only;
no training, inference, GPU access, publication, or existing-file changes.
Hypothesis: a small verified bilingual supplement may reduce arithmetic and
English retention regressions while preserving useful Turkish behavior.

- `train.jsonl`: 80 fresh rows, 40 Turkish and 40 English; 40 worked-solution
  reasoning rows (five structures, four instances per language), 40 individually
  authored general-language rows. No translated copies of historical items.
- `eval-prompts.jsonl`: 32 fresh evaluation-only prompts, 16 per language;
  no assistant answers. Eight numeric/logic and eight general tasks per language.
- `eval-references.jsonl`: separate references/rubrics; never send to model or
  include in training. Freeze this holdout for one final comparison; using it to
  choose checkpoints or recipes consumes it as development data.
- `verification-cases.json`: 56 executable arithmetic/logic checks, including
  exhaustive search, cell counting, exact fractions, sets and truth tables.
- `validation.json`, `overlap-review.json`, `protected-inputs.json`, `manifest.json`:
  validation, nearest historical prompts, read-only input hashes and output hashes.

Schema matches all top-level active corrections-02 train keys. Native reasoning
is a separate `worked_solution` string, never invented reasoning tags. Assistant
targets are concise final answers. The future runner must apply the native chat
template and explicitly decide reasoning supervision; attaching this metadata
does not itself enable reasoning loss. Do not silently change the existing loss
policy. General rows keep null worked_solution/reasoning_language.

The builder contains all authored source text and deterministic templates. No API,
external corpus or prior evaluation is used to produce targets. Historical local
JSON/JSONL is scanned afterward only for leakage; its content is not a generator
input. Provenance: OpenAI Codex assistant session, exact backend revision and
sampling settings unavailable; Python instantiation deterministic, no RNG.
Owner authorization covers private research data creation/use for all three
experiments (NEXT-GPU-AUTHORIZATION.md); this packet does not authorize publishing
or resolve broader provider licensing terms. No third-party source is claimed.

Training reasoning families: signed repeated change, indexed progression,
sum/difference equations, reversed operations, transitive numeric ordering.
Holdout reasoning families: synchronization/LCM, inner border area, draws without
replacement, median, inclusion-exclusion, ceiling capacity, midnight rollover,
exclusive constraints with multiple satisfying assignments. These are absent
from this supplement's training templates, but not necessarily from historical
training or model pretraining. New train/eval arithmetic facts differ by language.
General holdout tasks emphasize ambiguity, scope, evidence versus causation,
titles, register and error detection rather than repeating new training prompts.

This is limited synthetic template generalization: 80 rows are not 80 independent
reasoning structures. Eight holdout reasoning structures each appear in both
languages; report 32 item outcomes plus family/language breakdowns, not 32 fully
independent families. Agent-authored prose has no independent owner adjudication.
Automated overlap screens do not prove semantic or cross-lingual independence.
Common small constants and generic instructions can recur; no claim of globally
disjoint individual numbers is made. Protected-input inventory scopes the local
scan; external benchmark contents and unstructured text files are not exhaustive.

Reproduce/verify (CPU, standard library only):
`python scripts/data/build_lfm3_capability_preservation.py`
Existing files must match byte-for-byte; the builder refuses to overwrite.
Freeze artifacts before baseline. If the repository's protected inputs change,
preserve this packet and produce a separately versioned audit rather than editing
its frozen inventory. Character lengths are reported; model token lengths are
not inferred. Before actual training, audit native-template labels, lengths,
EOT and truncation on the exact combined dataset and pin its order/token budget.
This supplement is not a replacement for the active 640-row dataset, and no
mixing ratio, run config, step count or checkpoint-selection rule is changed here.

For future inference use separate conversations, no reference/few-shot leakage,
and identical pinned model/template/backend/generation conditions per comparison.
Keep thinking-on/off separate cohorts. Score correctness, constraint/format and
language compliance, naturalness, and stopping separately; accept equivalent
prose rather than exact-string matching. Compare against untouched LFM3 and the
existing candidate controls. Preserve raw outputs, IDs, finish reasons and configs.
Predeclare acceptable regression budgets before observing these holdout results.
'''
    payload['README.md']=readme.encode('utf-8')
    manifest=dict(version='capability-preservation-v01',created_on='2026-11-19',status='prepared-data-only',
        builder='scripts/data/build_lfm3_capability_preservation.py',builder_sha256=sha(Path(__file__).read_bytes()),
        schema_reference=SCHEMA.relative_to(ROOT).as_posix(),schema_reference_sha256=sha(SCHEMA.read_bytes()),
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        generation='Fixed authored templates; deterministic Python; no RNG, model API, GPU or network',
        files={k:dict(sha256=sha(v),bytes=len(v)) for k,v in payload.items()})
    payload['manifest.json']=encoded(manifest)
    for name,data in payload.items(): write(OUT/name,data)
    print(json.dumps(report,ensure_ascii=True,indent=2))
    print('SHA256 '+sha(payload['manifest.json'])+' manifest.json')
    for name in ['train.jsonl','eval-prompts.jsonl','eval-references.jsonl']:
        print('SHA256 '+sha(payload[name])+' '+name)


if __name__=='__main__': main()
