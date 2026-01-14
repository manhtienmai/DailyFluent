/**
 * Sidebar Layout JavaScript
 * Handles sidebar toggle, user modal, theme switching, and countdown timer
 */

(function() {
  'use strict';

  // Elements
  const body = document.body;
  const sidebar = document.getElementById('df-sidebar');
  const sidebarOverlay = document.getElementById('df-sidebar-overlay');
  const collapseBtn = document.getElementById('df-sidebar-collapse');
  const mobileMenuBtn = document.getElementById('df-mobile-menu-btn');
  const userBtn = document.getElementById('df-sidebar-user-btn');
  const userModal = document.getElementById('df-user-modal');
  const userModalOverlay = document.getElementById('df-user-modal-overlay');
  const userModalClose = document.getElementById('df-user-modal-close');
  const themeToggle = document.getElementById('df-theme-toggle');

  // ========================================
  // Sidebar Toggle (Desktop collapse)
  // ========================================
  if (collapseBtn) {
    collapseBtn.addEventListener('click', function() {
      body.classList.toggle('sidebar-collapsed');
      localStorage.setItem('sidebar-collapsed', body.classList.contains('sidebar-collapsed'));
    });

    // Restore state
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
      body.classList.add('sidebar-collapsed');
    }
  }

  // ========================================
  // Mobile Menu Toggle
  // ========================================
  if (mobileMenuBtn && sidebar && sidebarOverlay) {
    mobileMenuBtn.addEventListener('click', function() {
      sidebar.classList.toggle('mobile-open');
      sidebarOverlay.classList.toggle('active');
    });

    sidebarOverlay.addEventListener('click', function() {
      sidebar.classList.remove('mobile-open');
      sidebarOverlay.classList.remove('active');
    });
  }

  // ========================================
  // User Modal
  // ========================================
  function openUserModal() {
    if (userModal && userModalOverlay) {
      userModal.classList.add('active');
      userModalOverlay.classList.add('active');
    }
  }

  function closeUserModal() {
    if (userModal && userModalOverlay) {
      userModal.classList.remove('active');
      userModalOverlay.classList.remove('active');
    }
  }

  if (userBtn) {
    userBtn.addEventListener('click', openUserModal);
  }

  if (userModalClose) {
    userModalClose.addEventListener('click', closeUserModal);
  }

  if (userModalOverlay) {
    userModalOverlay.addEventListener('click', closeUserModal);
  }

  // Close modal on Escape
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeUserModal();
    }
  });

  // ========================================
  // Theme Toggle
  // ========================================
  function setTheme(isDark) {
    if (isDark) {
      body.classList.add('dark');
      body.setAttribute('data-theme', 'dark');
    } else {
      body.classList.remove('dark');
      body.removeAttribute('data-theme');
    }
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      const isDark = !body.classList.contains('dark');
      setTheme(isDark);
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // Restore theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      setTheme(true);
    } else if (savedTheme === 'light') {
      setTheme(false);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme(true);
    }
  }

  // ========================================
  // Countdown Timer
  // ========================================
  const countdownEl = document.getElementById('df-countdown-timer');
  const targetDateStr = window.EXAM_TARGET_DATE;

  if (countdownEl && targetDateStr) {
    const targetDate = new Date(targetDateStr + 'T00:00:00');

    function updateCountdown() {
      const now = new Date();
      const diff = targetDate - now;

      if (diff <= 0) {
        document.getElementById('cd-days').textContent = '00';
        document.getElementById('cd-hours').textContent = '00';
        document.getElementById('cd-mins').textContent = '00';
        document.getElementById('cd-secs').textContent = '00';
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const secs = Math.floor((diff % (1000 * 60)) / 1000);

      document.getElementById('cd-days').textContent = String(days).padStart(2, '0');
      document.getElementById('cd-hours').textContent = String(hours).padStart(2, '0');
      document.getElementById('cd-mins').textContent = String(mins).padStart(2, '0');
      document.getElementById('cd-secs').textContent = String(secs).padStart(2, '0');
    }

    updateCountdown();
    setInterval(updateCountdown, 1000);
  }

  // ========================================
  // Exam Goal Date Update
  // ========================================
  const examGoalInput = document.getElementById('df-exam-goal-date');
  if (examGoalInput) {
    examGoalInput.addEventListener('change', function() {
      const newDate = this.value;
      if (!newDate) return;

      // Get CSRF token
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                        getCookie('csrftoken');

      fetch('/api/exam-goal/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({ exam_date: newDate }),
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Update the countdown
          window.EXAM_TARGET_DATE = newDate;
          location.reload(); // Simple reload to update countdown
        }
      })
      .catch(err => console.error('Failed to update exam goal:', err));
    });
  }

  // Helper: get cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

})();

