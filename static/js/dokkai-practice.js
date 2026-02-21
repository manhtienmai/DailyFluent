/* =============================================
   Dokkai Practice — Alpine.js Component
   ============================================= */

function renderRuby(text) {
  if (!text) return '';
  // {漢字}(ふりがな) → <ruby>漢字<rt>ふりがな</rt></ruby>
  return text.replace(/\{([^}]+)\}\(([^)]+)\)/g, '<ruby>$1<rt>$2</rt></ruby>');
}

function dokkaiPractice(config) {
  return {
    // state
    selectedAnswers: Object.assign({}, config.initialAnswers || {}),
    submitted: false,
    submitting: false,
    results: {},   // { qId: { is_correct, explanation_json } }
    showVocab: false,
    showExplanations: {},  // { qId: bool }
    score: null,
    correctCount: 0,
    totalCount: config.totalCount || 0,

    // config
    submitUrl: config.submitUrl || '',
    csrfToken: config.csrfToken || '',
    loginUrl: config.loginUrl || '',
    isAuthenticated: config.isAuthenticated || false,

    // computed
    answeredCount() {
      return Object.keys(this.selectedAnswers).length;
    },

    allAnswered() {
      return this.answeredCount() >= this.totalCount && this.totalCount > 0;
    },

    scorePercent() {
      if (!this.totalCount) return 0;
      return Math.round((this.correctCount / this.totalCount) * 100);
    },

    ratingLabel() {
      const pct = this.scorePercent();
      if (pct >= 80) return 'Xuất sắc!';
      if (pct >= 60) return 'Trung bình';
      return 'Cần cố gắng';
    },

    // actions
    selectAnswer(qId, choiceKey) {
      if (this.submitted) return;
      this.selectedAnswers[qId] = choiceKey;
    },

    isSelected(qId, choiceKey) {
      return this.selectedAnswers[qId] === choiceKey;
    },

    isCorrect(qId, choiceKey, correctKey) {
      return this.submitted && choiceKey === correctKey;
    },

    isWrong(qId, choiceKey) {
      return this.submitted && this.selectedAnswers[qId] === choiceKey && this.results[qId] && !this.results[qId].is_correct;
    },

    resultForQuestion(qId) {
      return this.results[qId] || null;
    },

    toggleExplanation(qId) {
      this.showExplanations[qId] = !this.showExplanations[qId];
    },

    async submit() {
      if (this.submitting || this.submitted) return;
      if (this.answeredCount() === 0) {
        alert('Vui lòng chọn ít nhất một đáp án trước khi nộp bài.');
        return;
      }

      this.submitting = true;
      try {
        const res = await fetch(this.submitUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken,
          },
          body: JSON.stringify({ answers: this.selectedAnswers }),
        });

        if (res.status === 403 && !this.isAuthenticated) {
          window.location.href = this.loginUrl + '?next=' + encodeURIComponent(window.location.pathname);
          return;
        }

        const data = await res.json();
        if (data.success) {
          this.submitted = true;
          this.score = data.score;
          this.correctCount = data.correct_count;
          this.totalCount = data.total;

          // Build results map
          for (const ans of (data.answers || [])) {
            this.results[ans.q_id] = {
              is_correct: ans.is_correct,
              explanation_json: ans.explanation_json || {},
            };
          }

          // Scroll to score panel
          this.$nextTick(() => {
            const el = document.getElementById('dk-score-panel');
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
          });
        } else {
          alert(data.error || 'Nộp bài thất bại. Vui lòng thử lại.');
        }
      } catch (e) {
        alert('Lỗi kết nối. Vui lòng thử lại.');
      }
      this.submitting = false;
    },

    // Helpers for explanation rendering
    getExplanationSummary(qId) {
      const r = this.results[qId];
      if (!r || !r.explanation_json) return '';
      const ej = r.explanation_json;
      return ej.overall_analysis?.summary || ej.summary || '';
    },

    getExplanationOptions(qId) {
      const r = this.results[qId];
      if (!r || !r.explanation_json) return {};
      return r.explanation_json.options_breakdown || {};
    },

    getCorrectOptionLabel(qId) {
      const r = this.results[qId];
      if (!r || !r.explanation_json) return '';
      return r.explanation_json.correct_option || '';
    },
  };
}
