(function () {
  function fmt(diffMs) {
    if (diffMs <= 0) return "Expiré";
    var s = Math.floor(diffMs / 1000);
    var d = Math.floor(s / 86400); s -= d * 86400;
    var h = Math.floor(s / 3600); s -= h * 3600;
    var m = Math.floor(s / 60); s -= m * 60;
    return d + "j " + h + "h " + m + "m " + s + "s";
  }
  document.querySelectorAll('[data-countdown-target]').forEach(function (el) {
    var target = new Date(el.dataset.countdownTarget).getTime();
    var span = el.querySelector('.lrs-countdown-static');
    if (!span || isNaN(target)) return;
    var idx = span.textContent.lastIndexOf(":");
    var prefix = idx >= 0 ? span.textContent.slice(0, idx) : span.textContent;
    function tick() {
      span.textContent = prefix + ": " + fmt(target - Date.now());
    }
    tick();
    setInterval(tick, 1000);
  });
})();
