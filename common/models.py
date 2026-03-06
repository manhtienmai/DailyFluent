from django.conf import settings
from django.db import models


class QuizResult(models.Model):
    """
    Kết quả 1 lần làm bài từ bất kỳ công cụ học tập nào.
    Generic: dùng cho grammar EN, bunpou JP, usage quiz, phrasal verbs, v.v.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_results",
    )

    # Flexible key: "grammar", "bunpou", "usage", "phrasal-verbs"
    quiz_type = models.CharField(max_length=50, db_index=True)
    # Topic/slug: "nouns", "present-simple", "N3:day01", etc.
    quiz_id = models.CharField(max_length=100, db_index=True)

    total_questions = models.PositiveIntegerField()
    correct_count = models.PositiveIntegerField()
    score = models.FloatField(help_text="0.0 - 10.0")

    # [{q: 0, selected: 2, correct: 1, is_correct: false}, ...]
    answers_detail = models.JSONField(default=list, blank=True)

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]
        indexes = [
            models.Index(fields=["user", "quiz_type", "quiz_id"]),
        ]
        verbose_name = "Quiz Result"
        verbose_name_plural = "Quiz Results"

    def __str__(self):
        return f"{self.user} — {self.quiz_type}/{self.quiz_id} — {self.correct_count}/{self.total_questions}"
