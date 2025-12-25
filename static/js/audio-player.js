(function () {
  function formatTime(sec) {
    if (!sec && sec !== 0) return "00:00";
    const total = Math.floor(sec);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  function initAudioPlayers() {
    const players = document.querySelectorAll("[data-audio-player]");
    if (!players.length) return;

    const audios = [];

    function closeAllPopovers(exceptRoot) {
      players.forEach((root) => {
        if (exceptRoot && root === exceptRoot) return;
        root.querySelectorAll("[data-audio-popover]").forEach((pop) => {
          pop.classList.remove("df-open");
        });
      });
    }

    document.addEventListener("click", (e) => {
      const root = e.target.closest("[data-audio-player]");
      if (!root) {
        closeAllPopovers(null);
      } else {
        closeAllPopovers(root);
      }
    });

    players.forEach((root) => {
      const audio = root.querySelector("audio");
      if (!audio) return;
      audios.push(audio);

      const playBtn = root.querySelector("[data-audio-play]");
      const range = root.querySelector("[data-audio-range]");
      const currentEl = root.querySelector("[data-audio-current]");
      const durationEl = root.querySelector("[data-audio-duration]");
      const skipBtns = root.querySelectorAll("[data-audio-skip]");
      const volumeBtn = root.querySelector("[data-audio-volume-btn]");
      const volumePopover = root.querySelector(
        '[data-audio-popover="volume"]'
      );
      const volumeSlider = root.querySelector("[data-audio-volume]");
      const settingsBtn = root.querySelector("[data-audio-settings-btn]");
      const settingsPopover = root.querySelector(
        '[data-audio-popover="speed"]'
      );
      const speedButtons = settingsPopover
        ? settingsPopover.querySelectorAll("[data-audio-speed]")
        : [];
      const iconPlay = root.querySelector(".df-icon-play");
      const iconPause = root.querySelector(".df-icon-pause");

      audio.volume = 1;
      if (volumeSlider) volumeSlider.value = 1;

      audio.addEventListener("loadedmetadata", () => {
        if (durationEl) durationEl.textContent = formatTime(audio.duration);
      });

      audio.addEventListener("timeupdate", () => {
        if (currentEl) currentEl.textContent = formatTime(audio.currentTime);
        if (range && audio.duration) {
          range.value = (audio.currentTime / audio.duration) * 100;
        }
      });

      audio.addEventListener("play", () => {
        audios.forEach((a) => {
          if (a !== audio) a.pause();
        });
        if (iconPlay && iconPause) {
          iconPlay.classList.add("hidden");
          iconPause.classList.remove("hidden");
        }
      });

      audio.addEventListener("pause", () => {
        if (iconPlay && iconPause) {
          iconPlay.classList.remove("hidden");
          iconPause.classList.add("hidden");
        }
      });

      if (playBtn) {
        playBtn.addEventListener("click", () => {
          if (audio.paused) audio.play();
          else audio.pause();
        });
      }

      if (range) {
        range.addEventListener("input", () => {
          if (!audio.duration) return;
          const v = parseFloat(range.value || "0");
          audio.currentTime = (v / 100) * audio.duration;
        });
      }

      skipBtns.forEach((btn) => {
        const delta = parseFloat(btn.dataset.audioSkip || "0");
        btn.addEventListener("click", () => {
          if (!audio.duration) return;
          const next = Math.min(
            audio.duration,
            Math.max(0, audio.currentTime + delta)
          );
          audio.currentTime = next;
        });
      });

      if (volumeBtn && volumePopover) {
        volumeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const isOpen = volumePopover.classList.contains("df-open");
            // đóng các popover khác của player này
            closeAllPopovers(root);
            if (!isOpen) {
            volumePopover.classList.add("df-open");
            }
        });

        volumePopover.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }



      if (volumeSlider) {
        volumeSlider.addEventListener("input", () => {
          const v = parseFloat(volumeSlider.value || "0");
          audio.volume = Math.min(1, Math.max(0, v));
        });
      }

      if (settingsBtn && settingsPopover) {
        settingsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = settingsPopover.classList.contains('df-open');
            closeAllPopovers(root);
            if (!isOpen) {
            settingsPopover.classList.add('df-open');
            }
        });

        settingsPopover.addEventListener('click', (e) => {
            e.stopPropagation();
        });
        }

        speedButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            const rate = parseFloat(btn.dataset.audioSpeed || "1");
            audio.playbackRate = rate || 1;

            speedButtons.forEach((b) => b.classList.remove("df-speed-active"));
            btn.classList.add("df-speed-active");

            if (settingsPopover) {
            settingsPopover.classList.remove("df-open");   // đóng dropdown
            }
        });
        });

    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAudioPlayers);
  } else {
    initAudioPlayers();
  }
})();
