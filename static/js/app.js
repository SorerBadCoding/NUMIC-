/* ------------------------------------------------------------------ */
/* Dark mode toggle. The pre-paint <script> in base.html <head> already */
/* set data-theme before first paint; this just handles clicks + persists. */
/* ------------------------------------------------------------------ */

function numSetTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.setAttribute("data-bs-theme", theme);
  try { localStorage.setItem("num-theme", theme); } catch (e) {}
  document.cookie = "num_theme=" + theme + ";path=/;max-age=31536000;SameSite=Lax";
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const current = document.documentElement.dataset.theme || "light";
  document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
    btn.setAttribute("aria-pressed", current === "dark" ? "true" : "false");
    btn.addEventListener("click", () => {
      const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      numSetTheme(next);
    });
  });
});

document.addEventListener("DOMContentLoaded", () => {
  const isDesktopNav = () => window.matchMedia("(min-width: 768px)").matches;

  document.querySelectorAll("[data-dropdown-toggle]").forEach((btn) => {
    const target = document.querySelector(btn.dataset.dropdownToggle);
    if (!target) return;
    btn.addEventListener("click", (e) => {
      // Below 768px the trigger is a plain link to the full notifications
      // page (a cramped floating dropdown doesn't fit on a phone) — let the
      // browser navigate normally instead of intercepting it as a toggle.
      if (!isDesktopNav()) return;
      e.preventDefault();
      e.stopPropagation();
      document.querySelectorAll(".num-dropdown.show").forEach((el) => {
        if (el !== target) el.classList.remove("show");
      });
      const willShow = !target.classList.contains("show");
      target.classList.toggle("show", willShow);
      btn.setAttribute("aria-expanded", willShow ? "true" : "false");
    });
  });

  document.addEventListener("click", (e) => {
    document.querySelectorAll(".num-dropdown.show").forEach((el) => {
      if (!el.contains(e.target)) {
        el.classList.remove("show");
        const trigger = document.querySelector(`[data-dropdown-toggle="#${el.id}"]`);
        if (trigger) trigger.setAttribute("aria-expanded", "false");
      }
    });
  });
});

function numCsrfToken() {
  const el = document.querySelector('[name=csrfmiddlewaretoken]');
  return el ? el.value : "";
}
