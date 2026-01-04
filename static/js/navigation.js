/**
 * Navigation JavaScript
 * Handles mobile menu toggle and account menu dropdown
 */

(function() {
  'use strict';

  // Breakpoint for md: (matches Tailwind md: breakpoint)
  const MD_BREAKPOINT = 768;

  document.addEventListener('DOMContentLoaded', function () {
    // Account menu (desktop)
    initAccountMenu();
    
    // Mobile menu toggle
    initMobileMenu();
    
    // Handle window resize
    initResizeHandler();
  });

  /**
   * Initialize account menu dropdown (desktop)
   */
  function initAccountMenu() {
    const btn = document.getElementById('accountMenuButton');
    const menu = document.getElementById('accountMenu');

    if (!btn || !menu) return;

    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      const isHidden = menu.classList.toggle('hidden');
      btn.setAttribute('aria-expanded', !isHidden);
    });

    // Close menu when clicking outside
    document.addEventListener('click', function () {
      menu.classList.add('hidden');
      btn.setAttribute('aria-expanded', 'false');
    });

    // Prevent menu from closing when clicking inside
    menu.addEventListener('click', function (e) {
      e.stopPropagation();
    });
  }

  /**
   * Initialize mobile menu toggle
   */
  function initMobileMenu() {
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const mobileMenu = document.getElementById('mobileMenu');

    if (!mobileMenuButton || !mobileMenu) return;

    mobileMenuButton.addEventListener('click', function () {
      const isHidden = mobileMenu.classList.toggle('hidden');
      mobileMenuButton.setAttribute('aria-expanded', !isHidden);
      toggleMenuIcon(mobileMenuButton, isHidden);
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', function (e) {
      if (!mobileMenu.contains(e.target) && !mobileMenuButton.contains(e.target)) {
        closeMobileMenu(mobileMenuButton, mobileMenu);
      }
    });

    // Close mobile menu on ESC key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !mobileMenu.classList.contains('hidden')) {
        closeMobileMenu(mobileMenuButton, mobileMenu);
        mobileMenuButton.focus();
      }
    });

    // Close mobile menu when clicking a link
    mobileMenu.querySelectorAll('a').forEach(function(link) {
      link.addEventListener('click', function() {
        closeMobileMenu(mobileMenuButton, mobileMenu);
      });
    });
  }

  /**
   * Close mobile menu helper
   */
  function closeMobileMenu(button, menu) {
    menu.classList.add('hidden');
    button.setAttribute('aria-expanded', 'false');
    toggleMenuIcon(button, true);
  }

  /**
   * Handle window resize - close mobile menu when resizing to desktop
   */
  function initResizeHandler() {
    let resizeTimeout;
    
    window.addEventListener('resize', function() {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(function() {
        const mobileMenuButton = document.getElementById('mobileMenuButton');
        const mobileMenu = document.getElementById('mobileMenu');
        
        if (window.innerWidth >= MD_BREAKPOINT && mobileMenu && !mobileMenu.classList.contains('hidden')) {
          closeMobileMenu(mobileMenuButton, mobileMenu);
        }
      }, 100);
    });
  }

  /**
   * Toggle menu icon between hamburger and X
   * @param {HTMLElement} button - The menu button element
   * @param {boolean} isClosed - Whether the menu is closed
   */
  function toggleMenuIcon(button, isClosed) {
    const icon = button.querySelector('svg');
    if (!icon) return;

    if (isClosed) {
      // Show hamburger icon
      icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>';
    } else {
      // Show X icon
      icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>';
    }
  }
})();

