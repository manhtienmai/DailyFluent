import json

from django import forms
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import KanjiLesson, Kanji, KanjiVocab, UserKanjiProgress


# ─────────────────────────────────────────────────────────────────────────────
# Inlines
# ─────────────────────────────────────────────────────────────────────────────

class KanjiVocabInline(admin.TabularInline):
    model = KanjiVocab
    extra = 1
    fields = ['word', 'reading', 'meaning', 'priority']
    ordering = ['priority', 'id']
    verbose_name = "Từ vựng mẫu"
    verbose_name_plural = "Từ vựng mẫu (sắp xếp theo ưu tiên)"


class KanjiInline(admin.TabularInline):
    model = Kanji
    extra = 0
    fields = ['char', 'sino_vi', 'onyomi', 'kunyomi', 'meaning_vi', 'order']
    ordering = ['order']
    show_change_link = True
    verbose_name = "Hán tự"
    verbose_name_plural = "Danh sách Hán tự trong bài"


# ─────────────────────────────────────────────────────────────────────────────
# JSON Import form
# ─────────────────────────────────────────────────────────────────────────────

class KanjiJsonImportForm(forms.Form):
    json_data = forms.CharField(
        label='Dữ liệu JSON',
        widget=forms.Textarea(attrs={'rows': 15, 'style': 'width: 100%; min-width: 500px; font-family: monospace; font-size: 13px;'}),
        required=False,
        help_text='Dán nội dung dữ liệu JSON vào đây. Cấu trúc JSON: [{jlpt_level, lesson_id, topic, kanji_list:[...]}]'
    )
    json_file = forms.FileField(
        label='Hoặc upload file JSON',
        required=False,
        help_text='Nếu có file JSON lưu sẵn, bạn có thể upload.'
    )
    replace_existing = forms.BooleanField(
        required=False,
        initial=True,
        label='Xóa và thay thế dữ liệu bài học có cùng jlpt_level + lesson_id',
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('json_data') and not cleaned_data.get('json_file'):
            raise forms.ValidationError("Vui lòng paste dữ liệu JSON hoặc upload file.")
        return cleaned_data


# ─────────────────────────────────────────────────────────────────────────────
# KanjiLesson admin
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(KanjiLesson)
class KanjiLessonAdmin(admin.ModelAdmin):
    list_display = ['jlpt_level', 'lesson_number', 'topic', 'kanji_count', 'order']
    list_filter = ['jlpt_level']
    list_editable = ['order']
    search_fields = ['topic']
    ordering = ['jlpt_level', 'order', 'lesson_number']
    inlines = [KanjiInline]

    @admin.display(description="Số Hán tự")
    def kanji_count(self, obj):
        return obj.kanjis.count()

    # ── Custom URL for JSON import ──

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'import-json/',
                self.admin_site.admin_view(self.import_json_view),
                name='kanji_kanjilesson_import_json',
            ),
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_json_url'] = reverse('admin:kanji_kanjilesson_import_json')
        return super().changelist_view(request, extra_context=extra_context)

    def import_json_view(self, request):
        opts = self.model._meta
        if request.method == 'POST':
            form = KanjiJsonImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    if form.cleaned_data.get('json_file'):
                        raw = request.FILES['json_file'].read().decode('utf-8')
                    else:
                        raw = form.cleaned_data.get('json_data', '')
                    data = json.loads(raw)
                    replace = form.cleaned_data['replace_existing']
                    stats = _import_kanji_json(data, replace=replace)
                    messages.success(
                        request,
                        f"Import thanh cong: {stats['lessons']} bai hoc, "
                        f"{stats['kanji']} han tu, {stats['vocab']} tu vung."
                    )
                    return redirect(reverse('admin:kanji_kanjilesson_changelist'))
                except json.JSONDecodeError as e:
                    messages.error(request, f"JSON loi: {e}")
                except Exception as e:
                    messages.error(request, f"Loi: {e}")
        else:
            form = KanjiJsonImportForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'opts': opts,
            'title': 'Import Kanji tu file JSON',
        }
        return render(request, 'admin/kanji/import_json.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# Kanji admin
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Kanji)
class KanjiAdmin(admin.ModelAdmin):
    list_display = ['char_display', 'sino_vi', 'meaning_vi', 'onyomi', 'kunyomi', 'lesson_link', 'order']
    list_filter = ['lesson__jlpt_level', 'lesson']
    search_fields = ['char', 'sino_vi', 'keyword', 'onyomi', 'kunyomi', 'meaning_vi']
    inlines = [KanjiVocabInline]
    ordering = ['lesson', 'order']
    fieldsets = [
        (None, {
            'fields': ['char', 'lesson', 'order'],
        }),
        ('Thong tin doc', {
            'fields': ['sino_vi', 'meaning_vi', 'keyword', 'onyomi', 'kunyomi'],
        }),
        ('Chi tiet', {
            'fields': ['strokes', 'note'],
            'classes': ['collapse'],
        }),
    ]

    @admin.display(description="Han tu")
    def char_display(self, obj):
        return format_html(
            '<span style="font-size:1.8em;font-family:serif;font-weight:bold">{}</span>',
            obj.char,
        )

    @admin.display(description="Bai hoc")
    def lesson_link(self, obj):
        if obj.lesson:
            return format_html(
                '<a href="/admin/kanji/kanjilesson/{}/change/">{}</a>',
                obj.lesson.pk,
                str(obj.lesson),
            )
        return '-'


# ─────────────────────────────────────────────────────────────────────────────
# KanjiVocab admin
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(KanjiVocab)
class KanjiVocabAdmin(admin.ModelAdmin):
    list_display = ['kanji_char', 'word', 'reading', 'meaning', 'priority']
    list_filter = ['kanji__lesson__jlpt_level', 'kanji__lesson']
    search_fields = ['word', 'kanji__char', 'meaning', 'reading']
    list_editable = ['priority']
    ordering = ['kanji__lesson', 'kanji__order', 'priority']

    @admin.display(description="Han tu")
    def kanji_char(self, obj):
        return format_html(
            '<span style="font-size:1.4em;font-family:serif">{}</span>',
            obj.kanji.char,
        )


# ─────────────────────────────────────────────────────────────────────────────
# UserKanjiProgress admin
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(UserKanjiProgress)
class UserKanjiProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'kanji', 'status', 'correct_streak', 'last_practiced']
    list_filter = ['status']
    search_fields = ['user__username', 'kanji__char']
    readonly_fields = ['last_practiced']


# ─────────────────────────────────────────────────────────────────────────────
# JSON import logic (shared by admin view and management command)
# ─────────────────────────────────────────────────────────────────────────────

def _import_kanji_json(data: list, replace: bool = True) -> dict:
    """
    Parse the JSON structure and create/update KanjiLesson, Kanji, KanjiVocab records.
    Also auto-creates Vocabulary -> WordEntry -> WordDefinition for each vocab word.
    """
    from vocab.models import Vocabulary, WordEntry, WordDefinition

    lesson_count = 0
    kanji_count = 0
    vocab_count = 0
    vocab_linked = 0

    for lesson_data in data:
        jlpt_level = lesson_data.get('jlpt_level', 'N5').upper()
        lesson_number = int(lesson_data.get('lesson_id', 0))
        topic = lesson_data.get('topic', '')
        kanji_list = lesson_data.get('kanji_list', [])

        if replace:
            KanjiLesson.objects.filter(
                jlpt_level=jlpt_level, lesson_number=lesson_number
            ).delete()

        lesson, _ = KanjiLesson.objects.get_or_create(
            jlpt_level=jlpt_level,
            lesson_number=lesson_number,
            defaults={'topic': topic, 'order': lesson_number - 1},
        )
        # Update topic if lesson already existed
        if lesson.topic != topic:
            lesson.topic = topic
            lesson.save(update_fields=['topic'])
        lesson_count += 1

        for order, kdata in enumerate(kanji_list):
            char = kdata.get('character', '')
            if not char:
                continue

            onyomi_str = '・'.join(kdata.get('onyomi', []))
            kunyomi_str = '・'.join(kdata.get('kunyomi', []))

            kanji, _ = Kanji.objects.update_or_create(
                char=char,
                defaults={
                    'lesson': lesson,
                    'order': order,
                    'sino_vi': kdata.get('han_viet', ''),
                    'onyomi': onyomi_str,
                    'kunyomi': kunyomi_str,
                    'meaning_vi': kdata.get('meaning_vi', ''),
                    'formation': kdata.get('formation', ''),
                },
            )
            kanji_count += 1

            for priority, ex in enumerate(kdata.get('examples', [])):
                word = ex.get('word', '')
                if not word:
                    continue
                kv, created = KanjiVocab.objects.update_or_create(
                    kanji=kanji,
                    word=word,
                    defaults={
                        'reading': ex.get('hiragana', ''),
                        'meaning': ex.get('meaning', ''),
                        'priority': priority,
                    },
                )
                if created:
                    vocab_count += 1

                # Auto-create Vocabulary chain (skip if already linked)
                if not kv.vocabulary_id:
                    meaning = ex.get('meaning', '') or kv.meaning
                    reading = ex.get('hiragana', '') or kv.reading
                    vocab_obj, _ = Vocabulary.objects.get_or_create(
                        word=word,
                        defaults={
                            'language': 'jp',
                            'extra_data': {'reading': reading},
                        },
                    )
                    entry, _ = WordEntry.objects.get_or_create(
                        vocab=vocab_obj,
                        part_of_speech='',
                        defaults={'ipa': reading},
                    )
                    WordDefinition.objects.get_or_create(
                        entry=entry,
                        meaning=meaning,
                    )
                    kv.vocabulary = vocab_obj
                    kv.save(update_fields=['vocabulary'])
                    vocab_linked += 1

    return {
        'lessons': lesson_count,
        'kanji': kanji_count,
        'vocab': vocab_count,
        'vocab_linked': vocab_linked,
    }

