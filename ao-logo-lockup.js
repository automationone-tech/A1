(function () {
  var LOCKUPS = [
    { root: '.logo-text', name: '.name', sub: '.sub' },
    { root: '.brands-scene-logo-text', name: '.brands-scene-logo-name', sub: '.brands-scene-logo-sub' },
    { root: '.pt-text', name: '.pt-name', sub: '.pt-sub' },
  ];

  function getTextNode(el) {
    if (!el) return null;
    if (el.firstChild && el.firstChild.nodeType === Node.TEXT_NODE) return el.firstChild;
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
    return walker.nextNode();
  }

  function charLeft(el, index) {
    var tn = getTextNode(el);
    if (!tn) return el.getBoundingClientRect().left;
    var range = document.createRange();
    var i = Math.max(0, Math.min(index, tn.length));
    range.setStart(tn, 0);
    range.setEnd(tn, i);
    return range.getBoundingClientRect().left;
  }

  function charRight(el, index) {
    var tn = getTextNode(el);
    if (!tn) return el.getBoundingClientRect().right;
    var range = document.createRange();
    var i = Math.max(0, Math.min(index, tn.length));
    range.setStart(tn, 0);
    range.setEnd(tn, i);
    return range.getBoundingClientRect().right;
  }

  function mIndexInAutomation(text) {
    var t = (text || '').replace(/\u00a0/g, ' ');
    var auto = (t.split(/\s+/)[0] || t);
    for (var i = 0; i < auto.length; i++) {
      if (auto[i] === 'm' || auto[i] === 'M') return t.indexOf(auto[i]);
    }
    return t.indexOf('m');
  }

  function fitSubUnderM(root, nameEl, subEl, nameSize) {
    var mi = mIndexInAutomation(nameEl.textContent);
    if (mi < 0) return;

    subEl.style.width = '100%';
    subEl.style.textAlign = 'right';
    subEl.style.display = 'block';
    subEl.style.boxSizing = 'border-box';
    subEl.style.marginLeft = '0';
    subEl.style.marginRight = '0';
    subEl.style.paddingLeft = '0';
    subEl.style.paddingRight = '0';

    var nameTn = getTextNode(nameEl);
    var subTn = getTextNode(subEl);
    var nameEnd = nameTn ? nameTn.length : 0;
    var subEnd = subTn ? subTn.length : 0;

    function scoreAt(fontPx) {
      subEl.style.fontSize = fontPx + 'px';
      var lockLeft = root.getBoundingClientRect().left;
      var bGap = charLeft(subEl, 0) - lockLeft - (charLeft(nameEl, mi) - lockLeft);
      var rightGap = charRight(nameEl, nameEnd) - charRight(subEl, subEnd);
      return Math.abs(bGap) + 2.5 * Math.abs(rightGap);
    }

    var bestPx = nameSize * 0.535;
    var bestScore = scoreAt(bestPx);
    var px = nameSize * 0.48;
    var end = nameSize * 0.58;
    while (px <= end + 0.01) {
      var s = scoreAt(px);
      if (s < bestScore) {
        bestScore = s;
        bestPx = px;
      }
      px += 0.2;
    }

    subEl.style.fontSize = bestPx + 'px';
  }

  function syncPtMarkWidth(root, nameEl) {
    var ptLogo = root.closest('.pt-logo');
    if (!ptLogo) return;
    var wrap = ptLogo.querySelector('.pt-mark-wrap');
    var mark = wrap && wrap.querySelector('.pt-mark');
    if (!wrap || !mark) return;

    var w = Math.ceil(nameEl.getBoundingClientRect().width);
    if (w < 1) return;
    wrap.style.width = w + 'px';
    mark.style.width = '100%';
    mark.style.height = 'auto';
  }

  function syncLockup(root, nameEl, subEl) {
    root.classList.add('ao-logo-lockup');
    nameEl.classList.add('ao-lockup-name');
    subEl.classList.add('ao-lockup-sub');

    nameEl.style.width = '';
    nameEl.style.fontSize = '';
    subEl.style.fontSize = '';
    root.style.width = 'max-content';

    var nameSize = parseFloat(getComputedStyle(nameEl).fontSize) || 16;
    var nameWidth = Math.ceil(nameEl.getBoundingClientRect().width);
    if (nameWidth > 0) {
      root.style.width = nameWidth + 'px';
      nameEl.style.width = '100%';
      subEl.style.width = '100%';
    }

    fitSubUnderM(root, nameEl, subEl, nameSize);

    nameWidth = Math.ceil(nameEl.getBoundingClientRect().width);
    if (nameWidth > 0) {
      root.style.width = nameWidth + 'px';
      nameEl.style.width = '100%';
      subEl.style.width = '100%';
    }
    syncPtMarkWidth(root, nameEl);
  }

  function syncAll() {
    LOCKUPS.forEach(function (cfg) {
      document.querySelectorAll(cfg.root).forEach(function (root) {
        var nameEl = root.querySelector(cfg.name);
        var subEl = root.querySelector(cfg.sub);
        if (nameEl && subEl) syncLockup(root, nameEl, subEl);
      });
    });
  }

  window.syncAoLogoLockups = syncAll;

  function schedule() {
    requestAnimationFrame(function () {
      requestAnimationFrame(syncAll);
    });
  }

  function boot() {
    schedule();
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(schedule).catch(schedule);
    }
    window.addEventListener('load', schedule, { once: true });
    window.addEventListener('resize', schedule, { passive: true });

    var overlay = document.getElementById('page-transition');
    if (overlay && !overlay.dataset.aoPtHook) {
      overlay.dataset.aoPtHook = '1';
      new MutationObserver(function () {
        if (
          overlay.classList.contains('is-covered') ||
          overlay.classList.contains('is-cover-in') ||
          overlay.classList.contains('is-cover-out')
        ) {
          schedule();
        }
      }).observe(overlay, { attributes: true, attributeFilter: ['class'] });
    }

    document.querySelectorAll('.pt-logo .pt-mark').forEach(function (img) {
      img.addEventListener('load', schedule, { passive: true });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
