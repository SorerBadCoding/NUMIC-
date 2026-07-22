(function () {
  "use strict";

  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.addEventListener("DOMContentLoaded", function () {
    initNavScroll();
    initRipples();
    if (!reducedMotion) {
      initEntranceAndReveal();
      initCounters();
    }
  });

  /* ---------------------------------------------------------------- */
  /* Navbar: intensify glass effect on scroll                          */
  /* ---------------------------------------------------------------- */

  function initNavScroll() {
    var nav = document.querySelector(".num-nav");
    if (!nav) return;
    var onScroll = function () {
      nav.classList.toggle("scrolled", window.scrollY > 8);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  /* ---------------------------------------------------------------- */
  /* Ripple effect on click, for buttons / nav links / icon buttons    */
  /* ---------------------------------------------------------------- */

  function initRipples() {
    if (reducedMotion) return;
    var selector = ".btn-num-primary, .btn-num-soft, .num-nav-link, .num-icon-btn";
    document.addEventListener("click", function (e) {
      var target = e.target.closest ? e.target.closest(selector) : null;
      if (!target) return;
      var rect = target.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height) * 1.5;
      var ripple = document.createElement("span");
      ripple.className = "num-ripple";
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = (e.clientX - rect.left - size / 2) + "px";
      ripple.style.top = (e.clientY - rect.top - size / 2) + "px";
      target.appendChild(ripple);
      ripple.addEventListener("animationend", function () {
        ripple.remove();
      });
    });
  }

  /* ---------------------------------------------------------------- */
  /* Entrance cascade (above-the-fold, GSAP) + scroll reveal (below)   */
  /* ---------------------------------------------------------------- */

  function initEntranceAndReveal() {
    // [data-no-reveal] opts a card out of the fade/stagger system entirely —
    // for dense, task-focused lists (e.g. the gradebook) where every row
    // needs to be immediately visible and interactive, not gated on scroll.
    var cards = Array.prototype.slice.call(
      document.querySelectorAll(".num-shell .num-card:not([data-no-reveal]), .num-shell > .num-page-head")
    );
    var hero = document.querySelector(".num-hero");
    var viewportH = window.innerHeight;

    var aboveFold = [];
    var belowFold = [];
    cards.forEach(function (el) {
      if (hero && el === hero) return;
      var rect = el.getBoundingClientRect();
      (rect.top < viewportH - 40 ? aboveFold : belowFold).push(el);
    });

    // Below-the-fold: fade up as they scroll into view (pure CSS + IO)
    if ("IntersectionObserver" in window && belowFold.length) {
      belowFold.forEach(function (el) { el.classList.add("reveal-pending"); });
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              entry.target.classList.add("revealed");
              io.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.12, rootMargin: "0px 0px -30px 0px" }
      );
      belowFold.forEach(function (el) { io.observe(el); });
    }

    // Above-the-fold: coordinated GSAP cascade on load
    if (window.gsap) {
      var tl = gsap.timeline({ defaults: { ease: "power3.out" } });
      if (hero) {
        tl.from(hero, { opacity: 0, y: 26, duration: .7 });
      }
      if (aboveFold.length) {
        tl.from(
          aboveFold,
          { opacity: 0, y: 20, duration: .55, stagger: .07 },
          hero ? "-=0.35" : 0
        );
      }
    }
  }

  /* ---------------------------------------------------------------- */
  /* Animated statistic counters — reads the already-rendered value    */
  /* from the DOM, so no template/backend change is needed.            */
  /* ---------------------------------------------------------------- */

  function initCounters() {
    var els = document.querySelectorAll(".num-stat-value, .num-hero-stat .value");
    if (!els.length) return;

    if (!("IntersectionObserver" in window)) {
      els.forEach(runCount);
      return;
    }
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          io.unobserve(entry.target);
          runCount(entry.target);
        });
      },
      { threshold: 0.4 }
    );
    els.forEach(function (el) { io.observe(el); });
  }

  function runCount(el) {
    var raw = el.textContent.trim();
    var match = raw.match(/^(-?[\d,]+(?:\.\d+)?)(.*)$/);
    if (!match) return; // e.g. "—" placeholder, nothing to animate
    var target = parseFloat(match[1].replace(/,/g, ""));
    if (isNaN(target)) return;
    var suffix = match[2] || "";
    var decimals = (match[1].split(".")[1] || "").length;
    var duration = 1000;
    var start = null;

    function tick(ts) {
      if (start === null) start = ts;
      var p = Math.min(1, (ts - start) / duration);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals) + suffix;
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = match[1] + suffix;
    }
    requestAnimationFrame(tick);
  }

  /* ---------------------------------------------------------------- */
  /* Small helper other templates can call for async-loaded regions    */
  /* ---------------------------------------------------------------- */

  window.NumAnim = {
    reducedMotion: reducedMotion,
    hideSkeleton: function (el) {
      if (el) el.classList.add("is-hidden");
    },
    showSkeleton: function (el) {
      if (el) el.classList.remove("is-hidden");
    },
  };
})();
