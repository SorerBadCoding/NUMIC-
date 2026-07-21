document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-dropdown-toggle]").forEach((btn) => {
    const target = document.querySelector(btn.dataset.dropdownToggle);
    if (!target) return;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      document.querySelectorAll(".num-dropdown.show").forEach((el) => {
        if (el !== target) el.classList.remove("show");
      });
      target.classList.toggle("show");
    });
  });

  document.addEventListener("click", (e) => {
    document.querySelectorAll(".num-dropdown.show").forEach((el) => {
      if (!el.contains(e.target)) el.classList.remove("show");
    });
  });
});

function numCsrfToken() {
  const el = document.querySelector('[name=csrfmiddlewaretoken]');
  return el ? el.value : "";
}
