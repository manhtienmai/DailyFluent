/**
 * Dictation Exercise Application
 * Refactored into modular classes for better maintainability
 */

// ==========================================
// Utility Functions
// ==========================================

function formatTime(s) {
  if (isNaN(s)) return "00:00";
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m < 10 ? '0' + m : m}:${sec < 10 ? '0' + sec : sec}`;
}

/**
 * Normalize a single word: lowercase, strip punctuation
 */
function normalizeWord(w) {
  return (w || '').toLowerCase().replace(/[.,?!;:'"…()[\]{}\-–—]/g, '').trim();
}

/**
 * Normalize full text for comparison: lowercase, strip punctuation, collapse whitespace
 */
function normalizeForCompare(s) {
  return (s || '').toLowerCase().replace(/[.,?!;:'"…()[\]{}\-–—]/g, '').replace(/\s+/g, ' ').trim();
}

/**
 * Levenshtein edit distance between two strings
 */
function levenshtein(a, b) {
  const m = a.length, n = b.length;
  if (m === 0) return n;
  if (n === 0) return m;
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1]);
    }
  }
  return dp[m][n];
}

/**
 * Check match quality between two words
 * Returns: 'exact' | 'near' | 'wrong'
 *   1-3 chars: exact only (short words must match perfectly)
 *   4-5 chars: edit distance <= 1
 *   6+ chars:  edit distance <= 2
 */
function wordMatchType(userWord, correctWord) {
  const u = normalizeWord(userWord);
  const c = normalizeWord(correctWord);
  if (!u || !c) return 'wrong';
  if (u === c) return 'exact';
  const threshold = c.length <= 3 ? 0 : c.length <= 5 ? 1 : 2;
  if (threshold === 0) return 'wrong';
  return levenshtein(u, c) <= threshold ? 'near' : 'wrong';
}

/**
 * LCS-based word alignment between user input and correct text.
 * Uses fuzzy matching so small typos still align properly.
 * Returns array of { type, userWord, correctWord }
 *   type: 'exact' | 'near' | 'missing' | 'extra'
 */
function lcsAlign(userWords, correctWords) {
  const m = userWords.length;
  const n = correctWords.length;

  // Precompute match types between all word pairs
  const mt = Array.from({ length: m }, () => Array(n).fill('wrong'));
  for (let i = 0; i < m; i++) {
    for (let j = 0; j < n; j++) {
      mt[i][j] = wordMatchType(userWords[i], correctWords[j]);
    }
  }

  // LCS DP table
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (mt[i - 1][j - 1] !== 'wrong') {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  // Backtrack to produce alignment
  const result = [];
  let i = m, j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && mt[i - 1][j - 1] !== 'wrong' && dp[i][j] === dp[i - 1][j - 1] + 1) {
      result.unshift({ type: mt[i - 1][j - 1], userWord: userWords[i - 1], correctWord: correctWords[j - 1] });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.unshift({ type: 'missing', userWord: null, correctWord: correctWords[j - 1] });
      j--;
    } else {
      result.unshift({ type: 'extra', userWord: userWords[i - 1], correctWord: null });
      i--;
    }
  }
  return result;
}

/**
 * Generate a hint for a missing/wrong word: first letter + underscores
 */
function hintWord(word) {
  const clean = word.replace(/[.,?!;:'"…()[\]{}\-–—]/g, '');
  if (clean.length <= 1) return '_';
  return clean[0] + '\u2009'.repeat(0) + '·'.repeat(clean.length - 1);
}

/**
 * Generate diff HTML using LCS alignment with fuzzy matching.
 * - Green: exact match
 * - Amber with wavy underline: near match (small typo, shows correct spelling)
 * - Red hint: missing word (first letter + dots)
 * - Gray strikethrough: extra word user added
 */
function diffString(userText, correctText) {
  const uWords = userText.trim().split(/\s+/).filter(w => w);
  const cWords = correctText.trim().split(/\s+/).filter(w => w);
  const alignment = lcsAlign(uWords, cWords);

  let html = '';
  for (const item of alignment) {
    switch (item.type) {
      case 'exact':
        html += `<span class="text-green-600 dark:text-green-400 font-medium">${item.correctWord}</span> `;
        break;
      case 'near':
        html += `<span class="text-amber-600 dark:text-amber-400 font-medium underline decoration-wavy decoration-amber-400" title="Bạn viết: ${item.userWord}">${item.correctWord}</span> `;
        break;
      case 'missing':
        html += `<span class="text-red-500 font-mono tracking-wide" title="Từ bị thiếu">${hintWord(item.correctWord)}</span> `;
        break;
      case 'extra':
        html += `<span class="text-gray-400 line-through" title="Từ thừa">${item.userWord}</span> `;
        break;
    }
  }
  return html.trim();
}

// CSRF helper
function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie ? document.cookie.split(';') : [];
  for (let i = 0; i < cookies.length; i++) {
    const c = cookies[i].trim();
    if (c.startsWith(name + '=')) {
      return decodeURIComponent(c.substring(name.length + 1));
    }
  }
  return '';
}

// ==========================================
// Audio Seeker Class
// ==========================================

class AudioSeeker {
  constructor(audio) {
    this.audio = audio;
  }

  checkAudioReady(targetTime) {
    const source = this.audio.querySelector('source');
    const src = source ? source.src : this.audio.src;

    if (!src || src === '') return false;
    if (!this.audio.src || this.audio.src === '' || this.audio.src === window.location.href) {
      this.audio.src = src;
      return false;
    }
    if (!this.audio.duration || isNaN(this.audio.duration) || this.audio.duration === 0) return false;
    if (targetTime < 0 || targetTime >= this.audio.duration) return false;
    if (this.audio.readyState < 2) return false;

    return true;
  }

  async seekAndPlay(targetTime, endTime, onPlay, onEnd, continuous = false) {
    const seekAndPlayInternal = () => {
      if (!this.checkAudioReady(targetTime)) {
        const onCanPlay = () => {
          this.audio.removeEventListener('canplay', onCanPlay);
          setTimeout(seekAndPlayInternal, 100);
        };
        this.audio.addEventListener('canplay', onCanPlay, { once: true });
        if (this.audio.networkState === 0 || this.audio.networkState === 3) {
          this.audio.load();
        }
        return;
      }

      this.audio.currentTime = targetTime;

      let seekCompleted = false;
      const onSeeked = () => {
        seekCompleted = true;
        this.audio.removeEventListener('seeked', onSeeked);
        const diff = Math.abs(this.audio.currentTime - targetTime);
        if (diff < 0.5) {
          this.startPlayback(endTime, onPlay, onEnd, continuous);
        } else {
          this.playThenSeek(targetTime, endTime, onPlay, onEnd, continuous);
        }
      };
      this.audio.addEventListener('seeked', onSeeked, { once: true });

      let attempts = 0;
      const poll = setInterval(() => {
        if (seekCompleted) {
          clearInterval(poll);
          return;
        }
        attempts++;
        if (Math.abs(this.audio.currentTime - targetTime) < 0.5 || attempts >= 30) {
          clearInterval(poll);
          this.audio.removeEventListener('seeked', onSeeked);
          if (!seekCompleted) {
            seekCompleted = true;
            this.startPlayback(endTime, onPlay, onEnd, continuous);
          }
        }
      }, 50);
    };

    seekAndPlayInternal();
  }

  async playThenSeek(targetTime, endTime, onPlay, onEnd, continuous) {
    try {
      await this.audio.play();
      this.audio.pause();
      setTimeout(() => {
        this.audio.currentTime = targetTime;
        setTimeout(() => {
          this.startPlayback(endTime, onPlay, onEnd, continuous);
        }, 100);
      }, 50);
    } catch (e) {
      this.startPlayback(endTime, onPlay, onEnd, continuous);
    }
  }

  startPlayback(endTime, onPlay, onEnd, continuous) {
    this.audio.play().then(() => {
      if (onPlay) onPlay();

      if (!continuous && endTime) {
        const checkInterval = setInterval(() => {
          if (!this.audio.paused && this.audio.currentTime >= endTime) {
            this.audio.pause();
            clearInterval(checkInterval);
            if (onEnd) onEnd();
          }
        }, 50);
      }
    }).catch(e => {
      console.error('[AudioSeeker] Play error:', e);
    });
  }
}

// ==========================================
// Settings manager
// ==========================================

class DictationSettings {
  constructor() {
    this.storageKey = 'df_dictation_settings';
    this.defaults = {
      replayKey: 'Ctrl',
      playKey: 'Backtick',
      autoReplay: 'No',
      replayGap: 1,
      wordSuggest: 'Disabled',
      showTips: 'Show',
    };
    this.state = { ...this.defaults };
    this.load();
  }

  load() {
    try {
      const raw = localStorage.getItem(this.storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        this.state = { ...this.defaults, ...parsed };
      }
    } catch (e) {
      console.warn('Cannot load dictation settings', e);
    }
  }

  save() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.state));
    } catch (e) {
      console.warn('Cannot save dictation settings', e);
    }
  }

  get(key) {
    return this.state[key];
  }

  bindUI() {
    const bindSelect = (id, key) => {
      const el = document.getElementById(id);
      if (!el) return;
      // set initial
      if (this.state[key] !== undefined) {
        el.value = String(this.state[key]);
      }
      el.addEventListener('change', () => {
        let val = el.value;
        if (key === 'replayGap') val = parseFloat(val) || this.defaults.replayGap;
        this.state[key] = val;
        this.save();
      });
    };

    bindSelect('dict-replay-key', 'replayKey');
    bindSelect('dict-play-key', 'playKey');
    bindSelect('dict-auto-replay', 'autoReplay');
    bindSelect('dict-replay-gap', 'replayGap');
    bindSelect('dict-word-suggest', 'wordSuggest');
    bindSelect('dict-show-tips', 'showTips');
  }
}

// ==========================================
// Dictation Mode Class
// ==========================================

class DictationMode {
  constructor(audio, segments, elements, settings, opts = {}) {
    this.audio = audio;
    this.segments = segments;
    this.elements = elements;
    this.seeker = new AudioSeeker(audio);
    this.settings = settings;
    this.currentIndex = Math.max(0, Math.min(opts.initialIndex || 0, Math.max(0, segments.length - 1)));

    this.playbackRate = 1.0;
    this.isChecked = false;
    this.correctCount = 0;
    this.checkInterval = null;
    this.onProgress = typeof opts.onProgress === 'function' ? opts.onProgress : null;
    
    // Constructive Feedback Loop state
    this.attempts = 0;
    this.MAX_ATTEMPTS = 3;

    this.setupEventListeners();
  }

  stop() {
    // Stop any audio or timeouts from dictation mode
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    this.audio.pause();
    this.updatePlayButton(false);
    this.updateVisualizer(false);
  }

  setupEventListeners() {
    this.elements.btnPlay.addEventListener('click', () => {
      if (!this.audio.paused) {
        this.audio.pause();
        this.updatePlayButton(false);
      } else {
        this.playCurrentSegment();
      }
    });

    if (this.elements.speedSelect) {
      this.elements.speedSelect.addEventListener('change', (e) => {
        const val = parseFloat(e.target.value);
        this.playbackRate = isNaN(val) ? 1.0 : val;
      });
    }

    if (this.elements.btnReplay) {
      this.elements.btnReplay.addEventListener('click', () => {
        this.playCurrentSegment();
      });
    }

    this.elements.btnCheck.addEventListener('click', () => this.checkAnswer());
    this.elements.btnNext.addEventListener('click', () => this.nextSegment());
    
    // Reveal button handler
    if (this.elements.btnReveal) {
      this.elements.btnReveal.addEventListener('click', () => this.revealAnswer());
    }

    this.elements.userInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        // If already correct, go next
        if (this.isChecked) {
          this.nextSegment();
        } else {
          // Otherwise check answer (retry)
          this.checkAnswer();
        }
      }
      // Reset feedback on typing if not correct yet
      if (!this.isChecked) {
        // Optional: Hide feedback when user starts correcting?
        // this.elements.feedback.classList.add('hidden');
      }
    });
  }

  render() {
    if (this.currentIndex >= this.segments.length) {
      this.showSummary();
      return;
    }

    const seg = this.segments[this.currentIndex];

    this.isChecked = false;
    this.attempts = 0; // Reset attempts
    
    this.elements.userInput.value = '';
    this.elements.userInput.disabled = false;
    this.elements.userInput.focus();
    
    this.elements.btnCheck.classList.remove('hidden');
    this.elements.btnCheck.textContent = 'Kiểm tra';
    
    this.elements.btnNext.classList.add('hidden');
    if (this.elements.btnReveal) this.elements.btnReveal.classList.add('hidden');
    
    this.elements.feedback.classList.add('hidden');

    // Reset Play button state
    this.updatePlayButton(false);

    if (seg.hint) {
      this.elements.hintText.textContent = '💡 ' + seg.hint;
      this.elements.hintText.classList.remove('hidden');
    } else {
      this.elements.hintText.classList.add('hidden');
    }

    this.elements.progressText.textContent = `${this.currentIndex + 1} / ${this.segments.length}`;
    this.elements.progressBar.style.width = `${(this.currentIndex / this.segments.length) * 100}%`;

    if (this.onProgress) {
      this.onProgress(this.currentIndex, this.segments.length);
    }
  }

  playCurrentSegment() {
    if (this.currentIndex >= this.segments.length) return;

    const seg = this.segments[this.currentIndex];
    const targetTime = parseFloat(seg.start_time);
    const endTime = parseFloat(seg.end_time);

    if (this.checkInterval) clearInterval(this.checkInterval);

    this.audio.pause();
    this.audio.playbackRate = this.playbackRate || 1.0;

    this.seeker.seekAndPlay(
      targetTime,
      endTime,
      () => {
        this.updateVisualizer(true);
        this.updatePlayButton(true);
      },
      () => {
        this.updateVisualizer(false);
        this.updatePlayButton(false);
        const autoReplay = (this.settings.get('autoReplay') === 'Yes');
        const gap = parseFloat(this.settings.get('replayGap')) || 1;
        if (autoReplay) {
          setTimeout(() => this.playCurrentSegment(), gap * 1000);
        }
      },
      false
    );
  }

  updatePlayButton(playing) {
    if (playing) {
      this.elements.btnPlay.innerHTML = `
        <svg style="width:18px;height:18px;" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>
        Tạm dừng
      `;
    } else {
      this.elements.btnPlay.innerHTML = `
        <svg style="width:18px;height:18px;" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        Phát
      `;
    }
  }

  updateVisualizer(playing) {
    if (playing) {
      this.elements.viz.classList.remove('paused');
    } else {
      this.elements.viz.classList.add('paused');
    }
  }

  checkAnswer() {
    if (this.isChecked) return;
    this.updatePlayButton(false);

    const seg = this.segments[this.currentIndex];
    const userText = this.elements.userInput.value.trim();

    // Empty input guard
    if (!userText) {
      this.elements.feedback.classList.remove('hidden');
      this.elements.feedbackContent.innerHTML = `
        <div class="diff-result diff-result--wrong">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
          Hãy nhập câu trả lời
        </div>
      `;
      return;
    }

    // Align words using LCS with fuzzy matching
    const uWords = userText.split(/\s+/).filter(w => w);
    const cWords = seg.correct_text.trim().split(/\s+/).filter(w => w);
    const alignment = lcsAlign(uWords, cWords);

    const exactCount = alignment.filter(a => a.type === 'exact').length;
    const nearCount = alignment.filter(a => a.type === 'near').length;
    const missingCount = alignment.filter(a => a.type === 'missing').length;
    const extraCount = alignment.filter(a => a.type === 'extra').length;

    const isExactCorrect = normalizeForCompare(userText) === normalizeForCompare(seg.correct_text);
    const isNearCorrect = missingCount === 0 && extraCount === 0 && nearCount > 0;

    this.elements.feedback.classList.remove('hidden');

    if (isExactCorrect || isNearCorrect) {
      // CORRECT — exact or all words matched with minor typos
      this.isChecked = true;
      this.correctCount++;

      if (isExactCorrect) {
        this.elements.feedbackContent.innerHTML = `
          <div class="diff-result diff-result--correct">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            Chính xác!
          </div>
          <div class="diff-answer">${seg.correct_text}</div>
        `;
      } else {
        // Near-correct: accepted but show typos for learning
        this.elements.feedbackContent.innerHTML = `
          <div class="diff-result diff-result--correct" style="background:#fefce8;border-color:#facc15;color:#a16207;">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            Đúng rồi! Có ${nearCount} lỗi chính tả nhỏ
          </div>
          <div class="diff-box">${diffString(userText, seg.correct_text)}</div>
        `;
      }

      this.elements.userInput.disabled = true;
      this.elements.btnCheck.classList.add('hidden');
      if (this.elements.btnReveal) this.elements.btnReveal.classList.add('hidden');
      this.elements.btnNext.classList.remove('hidden');
      this.elements.btnNext.focus();

    } else {
      // INCORRECT — show partial score and LCS diff
      this.attempts++;
      const matchedWords = exactCount + nearCount;
      const scoreText = `${matchedWords}/${cWords.length} từ đúng`;

      this.elements.feedbackContent.innerHTML = `
        <div class="diff-result diff-result--wrong">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
          Chưa đúng — ${scoreText}
        </div>
        <div class="diff-box">${diffString(userText, seg.correct_text)}</div>
      `;

      this.elements.userInput.disabled = false;
      this.elements.userInput.focus();

      if (this.attempts >= this.MAX_ATTEMPTS && this.elements.btnReveal) {
        this.elements.btnReveal.classList.remove('hidden');
      }
    }
  }
  
  revealAnswer() {
    const seg = this.segments[this.currentIndex];
    this.isChecked = true; // Mark done but NOT incrementing correct count
    
    this.elements.userInput.value = seg.correct_text;
    this.elements.userInput.disabled = true;
    
    this.elements.feedbackContent.innerHTML = `
      <div class="diff-result diff-result--wrong" style="background:#fef3c7;border-color:#f59e0b;color:#d97706;">
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        Đáp án đúng
      </div>
      <div class="diff-answer">${seg.correct_text}</div>
    `;
    
    this.elements.feedback.classList.remove('hidden');
    this.elements.btnCheck.classList.add('hidden');
    if (this.elements.btnReveal) this.elements.btnReveal.classList.add('hidden');
    this.elements.btnNext.classList.remove('hidden');
    this.elements.btnNext.focus();
  }

  nextSegment() {
    this.currentIndex++;
    this.render();
    this.playCurrentSegment();
  }

  showSummary() {
    this.elements.exerciseApp.classList.add('hidden');
    this.elements.summaryScreen.classList.remove('hidden');
    this.elements.progressBar.style.width = '100%';
    this.elements.finalScore.textContent = `${this.correctCount} / ${this.segments.length} câu đúng`;
  }
}

// ==========================================
// Transcript Mode Class
// ==========================================

class TranscriptMode {
  constructor(audio, segments, elements) {
    this.audio = audio;
    this.segments = segments;
    this.elements = elements;
    this.seeker = new AudioSeeker(audio);

    this.activeIndex = -1;
    this.isPlaying = false;
    this.continuousMode = true; // play liên tục các segment
    this.autoStarted = false;

    this.setupEventListeners();
    this.renderList();
  }

  setupEventListeners() {
    // Main play/pause button
    this.elements.btnPlay.addEventListener('click', () => {
      if (this.isPlaying) {
        this.pause();
      } else {
        this.play(true);
      }
    });

    // Replay current segment
    if (this.elements.btnReplay) {
      this.elements.btnReplay.addEventListener('click', () => {
        if (this.activeIndex >= 0) {
          this.playSegment(this.activeIndex, false);
        }
      });
    }

    // Previous segment
    this.elements.btnPrev.addEventListener('click', () => {
      let target = this.activeIndex - 1;
      if (target < 0) target = 0;
      this.playSegment(target, this.continuousMode);
    });

    // Next segment
    this.elements.btnNext.addEventListener('click', () => {
      let target = this.activeIndex + 1;
      if (target >= this.segments.length) target = 0;
      this.playSegment(target, this.continuousMode);
    });

    // Click on progress bar to seek
    this.elements.progressContainer.addEventListener('click', (e) => {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = x / rect.width;
      const targetTime = pct * this.audio.duration;
      this.audio.currentTime = targetTime;
      if (!this.isPlaying) {
        this.play(true);
      }
    });


    // Update progress bar and highlight on timeupdate
    this.audio.addEventListener('timeupdate', () => {
      // Only process updates if active in this mode
      if (document.getElementById('view-transcript').classList.contains('hidden')) return;

      const cur = this.audio.currentTime;
      const dur = this.audio.duration;

      if (dur > 0) {
        const pct = (cur / dur) * 100;
        this.elements.progressBar.style.width = `${pct}%`;
        this.elements.currentTime.textContent = formatTime(cur);
      }

      // Find and highlight current segment
      const idx = this.segments.findIndex(s => cur >= s.start_time && cur < s.end_time);
      if (idx !== -1 && idx !== this.activeIndex) {
        this.highlightItem(idx);
      }
    });


    // Handle audio pause/play events
    this.audio.addEventListener('pause', () => {
      this.isPlaying = false;
      this.updatePlayButton();
    });

    this.audio.addEventListener('play', () => {
      this.isPlaying = true;
      this.updatePlayButton();
    });

    this.audio.addEventListener('ended', () => {
      this.isPlaying = false;
      this.updatePlayButton();
    });

    // Set total time when metadata loads
    const onMeta = () => {
      this.elements.totalTime.textContent = formatTime(this.audio.duration);
      this.autoStartIfNeeded();
    };
    this.audio.addEventListener('loadedmetadata', onMeta);
    if (this.audio.readyState >= 1) onMeta();

    // Keyboard navigation (arrow left/right)
    document.addEventListener('keydown', (e) => {
      const tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea') return;
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        let target = this.activeIndex + 1;
        if (target >= this.segments.length) target = this.segments.length - 1;
        this.playSegment(target, this.continuousMode);
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        let target = this.activeIndex - 1;
        if (target < 0) target = 0;
        this.playSegment(target, this.continuousMode);
      }
    });
  }

  renderList() {
    this.elements.list.innerHTML = '';
    this.segments.forEach((seg, idx) => {
      const div = document.createElement('div');
      div.className = `transcript-item group`;
      div.dataset.index = idx;

      div.innerHTML = `
        <div class="transcript-item-inner">
          <button class="transcript-play-btn" title="Phát câu này" data-index="${idx}">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          </button>
          <span class="transcript-text">${seg.correct_text}</span>
        </div>
      `;

      div.querySelector('.transcript-play-btn').onclick = (e) => {
        e.stopPropagation();
        this.playSegment(idx, false); // Single segment, not continuous
      };
      div.onclick = () => {
        this.playSegment(idx, this.continuousMode);
      };

      this.elements.list.appendChild(div);
    });

    this.updateListButtons(false);
  }

  play() {
    if (this.activeIndex < 0) {
      this.playSegment(0, this.continuousMode);
    } else {
      this.playSegment(this.activeIndex, this.continuousMode);
    }
  }

  pause() {
    this.stop(); // Stop logic is same as pause + state clear
  }

  stop() {
    // Stop continuous playback
    this.continuousPlaying = false;
    this.isPlaying = false;
    
    // Clear any pending segment transition
    if (this.nextSegmentTimeout) {
      clearTimeout(this.nextSegmentTimeout);
      this.nextSegmentTimeout = null;
    }
    
    if (!this.audio.paused) {
      this.audio.pause();
    }
    this.updatePlayButton();
  }

  playSegment(idx, continuous = true) {
    if (idx < 0 || idx >= this.segments.length) return;

    const seg = this.segments[idx];
    const targetTime = parseFloat(seg.start_time);
    const endTime = parseFloat(seg.end_time);
    const GAP_AFTER_SEGMENT_MS = 1000; // 1s pause between segments

    this.highlightItem(idx);
    
    // Clear any pending segment timeout
    if (this.nextSegmentTimeout) {
      clearTimeout(this.nextSegmentTimeout);
      this.nextSegmentTimeout = null;
    }
    
    this.audio.pause();
    this.continuousPlaying = continuous;

    const handleEnd = () => {
      this.updatePlayButton();
      this.updateListButtons(false);
      // Only continue if still in continuous mode and not paused by user
      if (this.continuousPlaying && this.isPlaying) {
        const next = idx + 1;
        if (next < this.segments.length) {
          this.nextSegmentTimeout = setTimeout(() => {
            if (this.continuousPlaying) {
              this.playSegment(next, true);
            }
          }, GAP_AFTER_SEGMENT_MS);
        } else {
          this.isPlaying = false;
          this.updatePlayButton();
        }
      }
    };

    this.seeker.seekAndPlay(
      targetTime,
      endTime,
      () => {
        this.isPlaying = true;
        this.updatePlayButton();
        this.updateListButtons(true, idx);
      },
      handleEnd,
      false // always segment-bounded playback
    );
  }

  highlightItem(idx) {
    if (this.activeIndex === idx) return;
    this.activeIndex = idx;

    Array.from(this.elements.list.children).forEach((el, i) => {
      if (i === idx) {
        el.classList.add('active');
        if (this.elements.autoScroll.checked) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      } else {
        el.classList.remove('active');
      }
    });

    if (idx >= 0 && this.segments[idx]) {
      this.elements.activeText.textContent = this.segments[idx].correct_text;
    }
  }

  updatePlayButton() {
    if (this.isPlaying) {
      this.elements.btnPlay.innerHTML = `
        <svg class="w-7 h-7" fill="currentColor" viewBox="0 0 24 24">
          <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
        </svg>
      `;
      this.elements.btnPlay.classList.add('playing');
    } else {
      this.elements.btnPlay.innerHTML = `
        <svg class="w-7 h-7 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8 5v14l11-7z"/>
        </svg>
      `;
      this.elements.btnPlay.classList.remove('playing');
    }

    this.updateListButtons(this.isPlaying, this.activeIndex);
  }

  updateListButtons(playing, idx) {
    const items = Array.from(this.elements.list.querySelectorAll('.transcript-item'));
    items.forEach((item, i) => {
      const btn = item.querySelector('.transcript-play-btn');
      if (!btn) return;
      if (playing && i === idx) {
        btn.innerHTML = `<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/></svg>`;
      } else {
        btn.innerHTML = `<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>`;
      }
    });
  }

  autoStartIfNeeded() {
    if (this.autoStarted) return;
    if (!this.segments || this.segments.length === 0) return;
    const pane = document.getElementById('view-transcript');
    if (pane && pane.classList.contains('hidden')) return; // chỉ auto khi tab transcript đang mở
    this.autoStarted = true;
    this.playSegment(0, true);
  }
}

// ==========================================
// Main Dictation App Class
// ==========================================

class DictationApp {
  constructor(config) {
    this.segments = config.segments;
    this.audio = config.audio;

    this.settings = new DictationSettings();
    this.settings.bindUI();

    const initialIndex = config.initialIndex || 0;
    const onProgress = typeof config.onProgress === 'function' ? config.onProgress : null;

    this.dictationMode = new DictationMode(this.audio, this.segments, config.dictationElements, this.settings, {
      initialIndex,
      onProgress,
    });
    this.transcriptMode = new TranscriptMode(this.audio, this.segments, config.transcriptElements);

    // Set initial mode
    this.dictationMode.render();

    // Toggle settings panel
    const settingsBtn = document.getElementById('dict-settings-btn');
    const settingsPanel = document.getElementById('dict-settings-panel');
    if (settingsBtn && settingsPanel) {
      settingsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        settingsPanel.classList.toggle('hidden');
      });
      document.addEventListener('click', () => {
        settingsPanel.classList.add('hidden');
      });
      settingsPanel.addEventListener('click', (e) => e.stopPropagation());
    }

    // Auto-resize textarea (no manual drag)
    const textarea = document.getElementById('user-input');
    if (textarea) {
      const autoResize = () => {
        textarea.style.height = 'auto';
        textarea.style.height = `${textarea.scrollHeight}px`;
      };
      textarea.addEventListener('input', autoResize);
      // initial
      autoResize();
    }

    // Keymap handlers (dictation tab)
    document.addEventListener('keydown', (e) => {
      const tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || e.metaKey) return;
      const pane = document.getElementById('view-dictation');
      if (!pane || pane.classList.contains('hidden')) return;

      const playKey = this.settings.get('playKey');
      const replayKey = this.settings.get('replayKey');

      // Play/Pause
      if (
        (playKey === 'Backtick' && e.key === '`') ||
        (playKey === 'Space' && e.code === 'Space') ||
        (playKey === 'Enter' && e.key === 'Enter')
      ) {
        e.preventDefault();
        if (!this.audio.paused) {
          this.audio.pause();
        } else {
          this.dictationMode.playCurrentSegment();
        }
        return;
      }

      // Replay current segment
      if (
        (replayKey === 'Ctrl' && e.key === 'Control') ||
        (replayKey === 'Alt' && e.key === 'Alt') ||
        (replayKey === 'Shift' && e.key === 'Shift')
      ) {
        e.preventDefault();
        this.dictationMode.playCurrentSegment();
      }
    });

    // Expose switchTab globally for HTML onclick handlers
    window.switchTab = (tabName) => this.switchTab(tabName);
  }

  switchTab(tabName) {
    document.querySelectorAll('.tab-pane').forEach(el => {
      el.classList.add('hidden');
      el.classList.remove('animate-fade-in-up');
    });
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    const pane = document.getElementById('view-' + tabName);
    pane.classList.remove('hidden');
    void pane.offsetWidth;
    pane.classList.add('animate-fade-in-up');

    document.getElementById('tab-btn-' + tabName).classList.add('active');

    // Always stop both to ensure clean state
    this.transcriptMode.stop();
    this.dictationMode.stop();

    if (tabName === 'transcript') {
      this.transcriptMode.autoStartIfNeeded();
    }
  }
}

// Export for global use
window.DictationApp = DictationApp;



// Auto-init using data attributes to avoid inline JSON errors
document.addEventListener('DOMContentLoaded', () => {
  const dataEl = document.getElementById('dictation-data');
  if (!dataEl || typeof DictationApp === 'undefined') return;

  const parseJSONSafe = (str, fallback) => {
    try {
      return JSON.parse(str);
    } catch (e) {
      return fallback;
    }
  };

  // Prefer JSON from script tag to avoid dataset encoding issues
  let rawSegments = [];
  const scriptEl = document.getElementById('dict-segments-json');
  if (scriptEl) {
    rawSegments = parseJSONSafe(scriptEl.textContent || '[]', []);
  } else {
    rawSegments = parseJSONSafe(dataEl.dataset.segments || '[]', []);
  }
  const initialIndex = parseInt(dataEl.dataset.initial || '0', 10) || 0;
  const progressApi = dataEl.dataset.progressApi || null;
  const exerciseId = parseInt(dataEl.dataset.exerciseId || '0', 10) || null;
  const userAuthenticated = (dataEl.dataset.userAuth || 'false') === 'true';

  // Normalize segments: include all if no type, else only content
  const segments = (rawSegments || [])
    .filter(function (s) {
      const t = (s.type || "").toLowerCase();
      if (!t) return true;
      return t === "content";
    })
    .map(function (s, idx) {
      return {
        start_time: parseFloat(s.start_time != null ? s.start_time : s.start) || 0,
        end_time: parseFloat(s.end_time != null ? s.end_time : s.end) || 0,
        correct_text: (s.correct_text != null ? s.correct_text : (s.text || "")),
        hint: s.hint || "",
        words: s.words || [],
        order: idx + 1
      };
    });

  const audio = document.getElementById('main-audio');
  if (!audio || !segments.length) {
    const card = document.querySelector('.dictation-card');
    if (card) card.innerHTML = '<div class="p-10 text-center text-slate-500">Chưa có dữ liệu bài tập. Hãy quay lại sau.</div>';
    return;
  }

  const onProgress = (currentIndex, total) => {
    if (!progressApi || !exerciseId || !userAuthenticated) return;
    clearTimeout(window._dictProgressTimer);
    window._dictProgressTimer = setTimeout(() => {
      fetch(progressApi, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
          exercise_id: exerciseId,
          current_segment: currentIndex,
          total_segments: total,
        }),
      })
      .then(r => r.json())
      .then(data => {
          if (data && data.new_badges && window.BadgeManager) {
              window.BadgeManager.show(data.new_badges);
          }
      })
      .catch(() => {});
    }, 300);
  };

  const app = new DictationApp({
    segments: segments,
    audio: audio,
    dictationElements: {
      viz: document.getElementById('dictation-viz'),
      btnPlay: document.getElementById('dict-btn-play'),
      btnReplay: document.getElementById('dict-btn-replay'),
      speedSelect: document.getElementById('dict-speed-select'),
      btnCheck: document.getElementById('btn-check'),
      btnNext: document.getElementById('btn-next'),
      userInput: document.getElementById('user-input'),
      hintText: document.getElementById('hint-text'),
      feedback: document.getElementById('feedback'),
      feedbackContent: document.getElementById('feedback-content'),
      progressBar: document.getElementById('progress-bar'),
      progressText: document.getElementById('progress-text'),
      exerciseApp: document.getElementById('exercise-app'),
      summaryScreen: document.getElementById('summary-screen'),
      finalScore: document.getElementById('final-score')
    },
    transcriptElements: {
      activeText: document.getElementById('trans-active-text'),
      list: document.getElementById('transcript-list'),
      btnPlay: document.getElementById('trans-btn-play'),
      btnReplay: document.getElementById('trans-btn-replay'),
      btnPrev: document.getElementById('trans-btn-prev'),
      btnNext: document.getElementById('trans-btn-next'),
      progressBar: document.getElementById('trans-progress-bar'),
      progressContainer: document.getElementById('trans-progress-container'),
      currentTime: document.getElementById('trans-current-time'),
      totalTime: document.getElementById('trans-total-time'),
      autoScroll: document.getElementById('chk-autoscroll')
    },
    initialIndex,
    onProgress,
  });

  window.switchTab = (tabName) => app.switchTab(tabName);
});