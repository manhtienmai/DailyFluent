"""
Re-link N1 kanji entries to their restored lessons.
"""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from kanji.models import KanjiLesson, Kanji

# Build mapping: char -> lesson_number from the original data
CHAR_TO_LESSON = {}

L1 = ["維持","意図","寄附","拒否","処置","阻止","破棄","保護","保守","加味","寄与","指揮","支持","自首","所持","補助","麻痺","餓死","帰化","危惧","起訴","忌避","挙手","駆使","駆除","固辞","誇示","示唆"]
L2 = ["自負","除去","図示","打破","治癒","卑下","補佐","拉致","濾過","意義","異議","意地","過疎","規模","義務","個々","誤差","磁気","時期","自己","視野","砂利","趣旨","種々","措置","墓地","余地","危機","義理","下痢","語彙"]
L3 = ["語句","孤児","詐欺","歯科","自我","磁器","時差","自主","守備","助詞","庶務","世辞","著書","徒歩","秘書","不意","部下","捕虜","未知","余暇","利子","意気","囲碁","遺書","歌詞","過度","可否","飢餓","機器","季語","機種"]
L4 = ["旗手","既知","虚偽","虚無","呼気","誤字","語尾","差異","時価","時下","時機","次期","私語","死語","事後","私費","自費","首位","主旨","種子","手話","書記","齟齬","地価","致死","覇者","馬車","避暑","比喩","部署","不和"]
L5 = ["簿記","母語","無期","路地","和語","移行","委託","違反","依頼","汚染","加減","企画","棄権","記載","規制","偽造","誤解","故障","誇張","雇用","孤立","作用","飼育","自覚","志向","思考","施行"]

for char in L1: CHAR_TO_LESSON[char] = 1
for char in L2: CHAR_TO_LESSON[char] = 2
for char in L3: CHAR_TO_LESSON[char] = 3
for char in L4: CHAR_TO_LESSON[char] = 4
for char in L5: CHAR_TO_LESSON[char] = 5

# Get lesson objects
lessons = {l.lesson_number: l for l in KanjiLesson.objects.filter(jlpt_level="N1")}

# Re-link kanji
updated = 0
for char, lesson_num in CHAR_TO_LESSON.items():
    lesson = lessons.get(lesson_num)
    if not lesson:
        continue
    count = Kanji.objects.filter(char=char, lesson__isnull=True).update(lesson=lesson)
    updated += count

print(f"Re-linked {updated} kanji entries to their N1 lessons.")
print(f"Remaining orphaned kanji: {Kanji.objects.filter(lesson__isnull=True).count()}")
