/**
 * FlashcardApp - Reusable Flashcard Core
 * Supports both Japanese and English vocabulary
 */

class FlashcardApp {
  constructor(config) {
    // Configuration
    this.config = {
      language: config.language || 'japanese', // 'japanese' | 'english'
      containerId: config.containerId || 'flashcard-container',
      cardsDataId: config.cardsDataId || 'flashcards-data',
      csrfFormId: config.csrfFormId || 'csrf-form',
      gradeUrl: config.gradeUrl || '/vocab/flashcards/grade/',
      streakStatusUrl: config.streakStatusUrl || '/streak/status-api/',
      logTimeUrl: config.logTimeUrl || '/streak/log-flashcard-minutes/',
      goalMinutes: config.goalMinutes || 10,
      ...config
    };

    // State
    this.queue = [];
    this.current = null;
    this.completed = 0;
    this.locked = false;

    // Time tracking
    this.goalMs = this.config.goalMinutes * 60 * 1000;
    this.baseMs = 0;
    this.pendingMs = 0;
    this.lastInteractionAt = Date.now();
    this.lastSentAt = Date.now();
    this.IDLE_MS = 30 * 1000;
    this.SEND_EVERY_MS = 15 * 1000;

    // DOM Elements
    this.elements = {};
    
    this.init();
  }

  init() {
    // Get container
    const container = document.getElementById(this.config.containerId);
    if (!container) return;

    // Load cards data
    const cardsScript = document.getElementById(this.config.cardsDataId);
    const initialCards = cardsScript ? JSON.parse(cardsScript.textContent || '[]') : [];
    this.queue = [...initialCards];

    // Cache DOM elements
    this.cacheElements();

    // Get CSRF token
    const csrfInput = document.querySelector(`#${this.config.csrfFormId} [name=csrfmiddlewaretoken]`);
    this.csrfToken = csrfInput ? csrfInput.value : '';

    // Initialize goal tracking
    this.initGoalRing();
    this.initGoalFromStatus();

    // Bind events
    this.bindEvents();

    // Start time tracking
    this.startTimeTracking();

    // Show first card
    this.updateProgress();
    this.nextCard();
  }

  cacheElements() {
    const $ = (id) => document.getElementById(id);
    
    this.elements = {
      // Card elements
      cardWrapper: $('fc-card-wrapper'),
      cardFront: $('fc-front'),
      cardBack: $('fc-back'),
      flipBtn: $('fc-flip-btn'),
      
      // Front side
      mainWord: $('fc-main-word'),
      phonetic: $('fc-phonetic'),
      
      // Back side
      backWord: $('fc-back-word'),
      backReading: $('fc-back-reading'),
      meaning: $('fc-meaning'),
      sinoBlock: $('fc-sino-block'),
      sinoVi: $('fc-sino-vi'),
      definitionBlock: $('fc-definition'),
      definitionText: document.querySelector('#fc-definition .df-fc-definition'),
      exampleBox: $('fc-example'),
      exampleText: $('fc-example-text'),
      exampleTrans: $('fc-example-trans'),
      
      // Grade buttons container
      grades: $('fc-grades'),
      
      // Progress
      progressBar: $('fc-progress-bar'),
      remaining: $('fc-remaining'),
      
      // Goal
      goalRing: $('fc-goal-ring'),
      goalLabel: $('fc-goal-label'),
      goalMinutes: $('fc-goal-minutes'),
      
      // States
      noMore: $('fc-complete'),
      error: $('fc-error')
    };
  }

  // ========== Goal Tracking ==========
  
  initGoalRing() {
    if (!this.elements.goalRing) return;
    const circumference = 2 * Math.PI * 18;
    this.ringCircumference = circumference;
    this.elements.goalRing.setAttribute('stroke-dasharray', circumference.toFixed(2));
    this.elements.goalRing.setAttribute('stroke-dashoffset', circumference.toFixed(2));
  }

  async initGoalFromStatus() {
    try {
      const resp = await fetch(this.config.streakStatusUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!resp.ok) return;
      const data = await resp.json();
      this.baseMs = Math.max(0, (data.seconds_today || 0) * 1000);
      this.updateGoalUI();
    } catch (err) {
      // Silent fail
    }
  }

  updateGoalUI() {
    if (!this.elements.goalRing) return;
    
    const totalMs = this.baseMs + this.pendingMs;
    const pct = Math.min(1, totalMs / this.goalMs);
    const offset = this.ringCircumference * (1 - pct);
    
    this.elements.goalRing.style.strokeDashoffset = offset.toFixed(2);
    
    if (this.elements.goalLabel) {
      this.elements.goalLabel.textContent = `${Math.round(pct * 100)}%`;
    }
    
    if (this.elements.goalMinutes) {
      const mins = Math.floor(totalMs / 60000);
      this.elements.goalMinutes.textContent = `${Math.min(this.config.goalMinutes, mins)}/${this.config.goalMinutes} phút`;
    }
  }

  // ========== Time Tracking ==========

  startTimeTracking() {
    // Track user interaction
    ['click', 'keydown', 'touchstart', 'scroll', 'mousemove'].forEach(evt => {
      window.addEventListener(evt, () => { this.lastInteractionAt = Date.now(); }, { passive: true });
    });
    
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) this.lastInteractionAt = Date.now();
    });

    // Flush when leaving page
    window.addEventListener('beforeunload', () => {
      const seconds = Math.floor(this.pendingMs / 1000);
      if (seconds <= 0) return;
      try {
        const data = new URLSearchParams({ seconds: String(seconds) });
        navigator.sendBeacon(this.config.logTimeUrl, data);
      } catch (e) {}
    });

    // Timer loop
    let lastTs = performance.now();
    const tick = (now) => {
      const delta = now - lastTs;
      lastTs = now;
      this.tickTimer(delta);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  isActiveNow() {
    if (document.hidden) return false;
    return (Date.now() - this.lastInteractionAt) <= this.IDLE_MS;
  }

  tickTimer(deltaMs) {
    if (!this.isActiveNow()) return;
    this.pendingMs += deltaMs;
    this.updateGoalUI();
    this.flushTime(false);
  }

  async flushTime(force = false) {
    const now = Date.now();
    if (!force && (now - this.lastSentAt) < this.SEND_EVERY_MS) return;

    const seconds = Math.floor(this.pendingMs / 1000);
    if (seconds <= 0) return;

    this.pendingMs -= seconds * 1000;
    this.lastSentAt = now;
    this.updateGoalUI();

    try {
      const resp = await fetch(this.config.logTimeUrl, {
        method: "POST",
        headers: {
          "X-CSRFToken": this.csrfToken,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ seconds: String(seconds) }),
      });
      
      if (resp.ok) {
        const data = await resp.json();
        this.baseMs = Math.max(0, (data.seconds_today || 0) * 1000);
        this.updateGoalUI();
      }
    } catch (e) {
      this.pendingMs += seconds * 1000;
    }
  }

  // ========== Card Rendering ==========

  remainingCount() {
    return this.queue.length + (this.current ? 1 : 0);
  }

  updateProgress() {
    const remaining = this.remainingCount();
    const denom = this.completed + remaining;
    const progress = denom ? (this.completed / denom) * 100 : 100;
    
    if (this.elements.progressBar) {
      this.elements.progressBar.style.width = progress.toFixed(2) + '%';
    }
    
    if (this.elements.remaining) {
      this.elements.remaining.textContent = String(remaining);
    }
  }

  setIntervals(card) {
    if (!this.elements.grades) return;
    
    const spans = this.elements.grades.querySelectorAll('[data-interval]');
    spans.forEach(el => {
      const key = el.getAttribute('data-interval');
      const val = (card && card.intervals && key && card.intervals[key]) ? card.intervals[key] : '';
      el.textContent = val ? `(${val})` : '';
    });
  }

  showEmpty() {
    if (this.elements.cardWrapper) {
      this.elements.cardWrapper.classList.add('hidden');
    }
    if (this.elements.noMore) {
      this.elements.noMore.classList.remove('hidden');
    }
    if (this.elements.remaining) {
      this.elements.remaining.textContent = "0";
    }
    if (this.elements.progressBar) {
      this.elements.progressBar.style.width = '100%';
    }
  }

  renderCard(card) {
    if (!card) {
      this.showEmpty();
      return;
    }

    if (this.config.language === 'japanese') {
      this.renderJapaneseCard(card);
    } else {
      this.renderEnglishCard(card);
    }

    // Reset to front
    if (this.elements.cardFront) this.elements.cardFront.classList.remove('hidden');
    if (this.elements.cardBack) this.elements.cardBack.classList.add('hidden');

    this.setIntervals(card);
    this.updateProgress();
  }

  renderJapaneseCard(card) {
    const mainWord = card.jp_kanji || card.jp_kana;
    
    // Front
    if (this.elements.mainWord) {
      this.elements.mainWord.textContent = mainWord || '';
      this.elements.mainWord.classList.add('df-fc-main-word--jp');
    }
    if (this.elements.phonetic) {
      this.elements.phonetic.classList.add('hidden');
    }
    
    // Back
    if (this.elements.backWord) {
      this.elements.backWord.textContent = mainWord || '';
      this.elements.backWord.classList.add('df-fc-back-word--jp');
    }
    if (this.elements.backReading) {
      this.elements.backReading.textContent = card.jp_kanji ? card.jp_kana : '';
      this.elements.backReading.classList.toggle('hidden', !card.jp_kanji);
    }
    if (this.elements.meaning) {
      this.elements.meaning.textContent = card.vi_meaning;
    }
    
    // Sino Vietnamese
    if (this.elements.sinoBlock) {
      if (card.sino_vi) {
        this.elements.sinoVi.textContent = card.sino_vi;
        this.elements.sinoBlock.classList.remove('hidden');
      } else {
        this.elements.sinoBlock.classList.add('hidden');
      }
    }
    
    // Hide English definition
    if (this.elements.definitionBlock) {
      this.elements.definitionBlock.classList.add('hidden');
    }
    
    // Example
    if (this.elements.exampleBox) {
      if (card.example_jp || card.example_vi) {
        this.elements.exampleText.textContent = card.example_jp || '';
        this.elements.exampleTrans.textContent = card.example_vi || '';
        this.elements.exampleBox.classList.remove('hidden');
      } else {
        this.elements.exampleBox.classList.add('hidden');
      }
    }
  }

  renderEnglishCard(card) {
    // Front
    if (this.elements.mainWord) {
      this.elements.mainWord.textContent = card.en_word || '';
      this.elements.mainWord.classList.remove('df-fc-main-word--jp');
      this.elements.mainWord.classList.add('df-fc-main-word--en');
    }
    if (this.elements.phonetic) {
      if (card.phonetic) {
        this.elements.phonetic.textContent = card.phonetic;
        this.elements.phonetic.classList.remove('hidden');
      } else {
        this.elements.phonetic.classList.add('hidden');
      }
    }
    
    // Back
    if (this.elements.backWord) {
      this.elements.backWord.textContent = card.en_word || '';
      this.elements.backWord.classList.remove('df-fc-back-word--jp');
      this.elements.backWord.classList.add('df-fc-back-word--en');
    }
    if (this.elements.backReading) {
      this.elements.backReading.textContent = card.phonetic || '';
      this.elements.backReading.classList.toggle('hidden', !card.phonetic);
    }
    if (this.elements.meaning) {
      this.elements.meaning.textContent = card.vi_meaning;
    }
    
    // Hide Sino Vietnamese for English
    if (this.elements.sinoBlock) {
      this.elements.sinoBlock.classList.add('hidden');
    }
    
    // English definition
    if (this.elements.definitionBlock) {
      if (card.en_definition && this.elements.definitionText) {
        this.elements.definitionText.textContent = card.en_definition;
        this.elements.definitionBlock.classList.remove('hidden');
      } else {
        this.elements.definitionBlock.classList.add('hidden');
      }
    }
    
    // Example
    if (this.elements.exampleBox) {
      if (card.example_en || card.example_vi) {
        this.elements.exampleText.textContent = card.example_en || '';
        this.elements.exampleTrans.textContent = card.example_vi || '';
        this.elements.exampleBox.classList.remove('hidden');
      } else {
        this.elements.exampleBox.classList.add('hidden');
      }
    }
  }

  nextCard() {
    if (this.locked) return;
    
    if (this.queue.length === 0) {
      this.current = null;
      this.renderCard(null);
      return;
    }
    
    this.current = this.queue.shift();
    this.renderCard(this.current);
  }

  // ========== Event Handling ==========

  bindEvents() {
    // Flip button
    if (this.elements.flipBtn) {
      this.elements.flipBtn.addEventListener('click', () => this.flipCard());
    }

    // Grade buttons
    if (this.elements.grades) {
      this.elements.grades.addEventListener('click', (e) => {
        const btn = e.target.closest('button[data-rating]');
        if (!btn) return;
        if (this.elements.cardBack && this.elements.cardBack.classList.contains('hidden')) return;
        
        const rating = btn.dataset.rating;
        if (!rating) return;
        
        btn.classList.add('opacity-50');
        this.gradeCard(rating).finally(() => {
          btn.classList.remove('opacity-50');
        });
      });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => this.handleKeyboard(e));
  }

  flipCard() {
    if (this.locked) return;
    
    const isFront = this.elements.cardFront && !this.elements.cardFront.classList.contains('hidden');
    
    if (this.elements.cardFront) {
      this.elements.cardFront.classList.toggle('hidden', isFront);
    }
    if (this.elements.cardBack) {
      this.elements.cardBack.classList.toggle('hidden', !isFront);
    }
  }

  handleKeyboard(e) {
    if (!this.current) return;

    // Space/Enter to flip when on front
    if (this.elements.cardFront && !this.elements.cardFront.classList.contains('hidden')) {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        this.flipCard();
      }
      return;
    }

    // Only process number keys on back
    if (this.elements.cardBack && this.elements.cardBack.classList.contains('hidden')) return;

    const keyMap = { '1': 'again', '2': 'hard', '3': 'good', '4': 'easy' };
    const rating = keyMap[e.key];
    
    if (rating) {
      e.preventDefault();
      const btn = this.elements.grades?.querySelector(`button[data-rating="${rating}"]`);
      if (btn) btn.click();
    }
  }

  // ========== Grading ==========

  async gradeCard(ratingKey) {
    if (!this.current || this.locked) return;
    
    this.locked = true;
    if (this.elements.error) this.elements.error.classList.add('hidden');

    try {
      const resp = await fetch(this.config.gradeUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": this.csrfToken,
        },
        body: new URLSearchParams({
          state_id: String(this.current.state_id),
          rating: String(ratingKey),
          is_new: (this.current.card_state === 0) ? "true" : "false",
        }),
      });

      if (!resp.ok) {
        throw new Error("Không thể chấm điểm. Vui lòng thử lại.");
      }

      const data = await resp.json();

      // Update client-side card data
      if (data && data.new_intervals) this.current.intervals = data.new_intervals;
      if (data && typeof data.card_state === "number") this.current.card_state = data.card_state;

      // Requeue if needed (Anki-like behavior)
      if (data && data.requeue) {
        const snapshot = { ...this.current };
        const delay = Math.max(0, Number(data.requeue_delay_ms || 0));
        setTimeout(() => {
          this.queue.push(snapshot);
          this.updateProgress();
        }, delay);
      }

      this.completed += 1;
      this.locked = false;
      setTimeout(() => this.nextCard(), 150);
      
    } catch (err) {
      this.locked = false;
      if (this.elements.error) {
        this.elements.error.textContent = err.message || "Có lỗi xảy ra. Vui lòng thử lại.";
        this.elements.error.classList.remove('hidden');
      }
    }
  }
}

// Export for module usage or global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FlashcardApp;
} else {
  window.FlashcardApp = FlashcardApp;
}
