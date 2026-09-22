(function () {
  var popup = document.getElementById('lrs-exit-popup');
  if (!popup) return;
  document.addEventListener('mouseout', function (e) {
    if (e.clientY > 0 || sessionStorage.getItem('lrsExitPopupShown')) return;
    popup.hidden = false;
    sessionStorage.setItem('lrsExitPopupShown', '1');
  });
  popup.addEventListener('click', function (e) {
    if (e.target.closest('[data-lrs-action="close-popup"]')) popup.hidden = true;
  });
})();
