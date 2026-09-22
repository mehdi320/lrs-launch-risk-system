document.addEventListener('click', function (e) {
  var btn = e.target.closest('[data-lrs-action="form-next"]');
  if (!btn) return;
  var current = btn.closest('.lrs-form-screen');
  var next = current.nextElementSibling;
  if (next) { current.hidden = true; next.hidden = false; }
});
