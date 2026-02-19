/**
 * Grammar Exercise — Alpine.js Component
 * Supports MCQ and SENTENCE_ORDER (★) question types.
 */
function grammarExercise(questionsData, submitUrl, exerciseSetId) {
  return {
    questions: questionsData,
    currentIndex: 0,
    answered: false,
    showResults: false,
    score: 0,
    answerHistory: [],

    // MCQ state
    selectedChoice: null,

    // SENTENCE_ORDER state
    boxContents: [null, null, null, null],   // token index placed in each box
    selectedChip: null,                       // chip index selected for click mode
    dragChipIdx: null,                        // chip index being dragged

    // ── Computed ────────────────────────────────────────────────
    get current() { return this.questions[this.currentIndex]; },
    get totalQuestions() { return this.questions.length; },
    get progressPct() { return ((this.currentIndex) / this.totalQuestions) * 100; },
    get progressPctFinal() { return (this.totalQuestions ? (this.score / this.totalQuestions) * 100 : 0); },
    get allBoxesFilled() { return this.boxContents.every(b => b !== null); },

    // ── Reset per question ───────────────────────────────────────
    resetQuestion() {
      this.answered = false;
      this.selectedChoice = null;
      this.boxContents = [null, null, null, null];
      this.selectedChip = null;
      this.dragChipIdx = null;
    },

    // ── MCQ ─────────────────────────────────────────────────────
    selectChoice(key) {
      if (this.answered) return;
      this.selectedChoice = key;
    },

    checkMCQ() {
      if (!this.selectedChoice || this.answered) return;
      this.answered = true;
      const isCorrect = this.selectedChoice === this.current.correct_answer;
      if (isCorrect) this.score++;
      this.answerHistory.push({
        question_id: this.current.id,
        user_answer: this.selectedChoice,
        is_correct: isCorrect,
        question_text: this.current.question_text,
        type: 'MCQ',
      });
    },

    choiceClass(key) {
      if (!this.answered) {
        return this.selectedChoice === key ? 'selected' : '';
      }
      if (key === this.current.correct_answer) return 'correct';
      if (key === this.selectedChoice && key !== this.current.correct_answer) return 'incorrect';
      return '';
    },

    // ── SENTENCE_ORDER (★) ──────────────────────────────────────
    isChipUsed(chipIdx) {
      return this.boxContents.includes(chipIdx);
    },

    // Click mode: select chip
    selectChip(chipIdx) {
      if (this.answered) return;
      if (this.isChipUsed(chipIdx)) return;
      this.selectedChip = this.selectedChip === chipIdx ? null : chipIdx;
    },

    // Click mode: place selected chip into box
    placeInBox(boxIdx) {
      if (this.answered) return;
      if (this.selectedChip === null) {
        // If box has content, remove it
        if (this.boxContents[boxIdx] !== null) {
          this.boxContents[boxIdx] = null;
        }
        return;
      }
      // Place chip
      this.boxContents[boxIdx] = this.selectedChip;
      this.selectedChip = null;
    },

    removeFromBox(boxIdx) {
      if (this.answered) return;
      this.boxContents[boxIdx] = null;
    },

    checkOrder() {
      if (!this.allBoxesFilled || this.answered) return;
      this.answered = true;

      const userOrder = this.boxContents.slice(); // [tokenIdx, tokenIdx, tokenIdx, tokenIdx]
      const isCorrect = JSON.stringify(userOrder) === JSON.stringify(this.current.correct_order);
      if (isCorrect) this.score++;

      // Get star answer (the correct token for the star box)
      const starBox = (this.current.star_position || 1) - 1;
      const correctStarToken = this.current.tokens[this.current.correct_order[starBox]];

      this.answerHistory.push({
        question_id: this.current.id,
        user_answer: userOrder,
        is_correct: isCorrect,
        question_text: this.current.sentence_prefix + '…' + this.current.sentence_suffix,
        type: 'SENTENCE_ORDER',
      });
    },

    boxClass(boxIdx) {
      const isStar = this.current.star_position === boxIdx + 1;
      let cls = isStar ? 'star-box' : '';
      if (this.boxContents[boxIdx] !== null) cls += ' filled';
      if (this.answered) {
        const userIdx = this.boxContents[boxIdx];
        const correctIdx = this.current.correct_order ? this.current.correct_order[boxIdx] : -1;
        if (userIdx === correctIdx) cls += ' correct-box';
        else cls += ' incorrect-box';
      }
      return cls;
    },

    boxLabel(boxIdx) {
      const chipIdx = this.boxContents[boxIdx];
      if (chipIdx !== null && this.current.tokens) {
        return this.current.tokens[chipIdx];
      }
      return String(boxIdx + 1);
    },

    // ── Drag & Drop ─────────────────────────────────────────────
    onDragStart(chipIdx, event) {
      if (this.answered) { event.preventDefault(); return; }
      this.dragChipIdx = chipIdx;
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', String(chipIdx));
    },

    onDragOver(boxIdx, event) {
      event.preventDefault();
      event.dataTransfer.dropEffect = 'move';
      event.currentTarget.classList.add('drag-over');
    },

    onDragLeave(event) {
      event.currentTarget.classList.remove('drag-over');
    },

    onDrop(boxIdx, event) {
      event.preventDefault();
      event.currentTarget.classList.remove('drag-over');
      if (this.answered) return;
      const chipIdx = parseInt(event.dataTransfer.getData('text/plain'), 10);
      if (isNaN(chipIdx)) return;
      // If this chip is already in another box, remove it
      this.boxContents = this.boxContents.map(c => c === chipIdx ? null : c);
      this.boxContents[boxIdx] = chipIdx;
      this.dragChipIdx = null;
    },

    // ── Navigation ───────────────────────────────────────────────
    nextQuestion() {
      if (this.currentIndex < this.totalQuestions - 1) {
        this.currentIndex++;
        this.resetQuestion();
      } else {
        this.submitResults();
      }
    },

    // ── Submit ───────────────────────────────────────────────────
    async submitResults() {
      this.showResults = true;

      try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
          || this.getCookie('csrftoken');

        await fetch(submitUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
            exercise_set_id: exerciseSetId,
            answers: this.answerHistory,
          }),
        });
      } catch (e) {
        console.warn('Submit failed:', e);
      }
    },

    getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop().split(';').shift();
      return '';
    },

    // ── Score ring SVG ───────────────────────────────────────────
    get scoreRingDashoffset() {
      const r = 54;
      const circumference = 2 * Math.PI * r;
      const pct = this.progressPctFinal / 100;
      return circumference * (1 - pct);
    },

    restart() {
      this.currentIndex = 0;
      this.answered = false;
      this.showResults = false;
      this.score = 0;
      this.answerHistory = [];
      this.resetQuestion();
    },
  };
}
