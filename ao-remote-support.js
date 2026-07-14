/* Remote Support drawer ? self-contained.
   Injects a slide-in drawer with Windows / Mac tabs and wires up every
   "Remote Support" link on the page to open it. */
(function () {
  'use strict';

  var AO_REMOTE_DOWNLOAD_URL_WINDOWS = 'https://my.anydesk.com/v2/api/v2/custom-clients/downloads/public/JJTSCFPPBUIW/A1-AnyDeskClient.exe';
  var AO_REMOTE_DOWNLOAD_URL_MAC = 'https://my.anydesk.com/v2/api/v2/custom-clients/downloads/public/A8J2Z1OHNWFF/A1AnyDeskClient.exe';

  function build() {
    if (document.getElementById('remote-drawer')) return;

    var overlay = document.createElement('div');
    overlay.className = 'remote-drawer-overlay';
    overlay.id = 'remote-drawer-overlay';
    overlay.setAttribute('aria-hidden', 'true');

    var drawer = document.createElement('aside');
    drawer.className = 'remote-drawer';
    drawer.id = 'remote-drawer';
    drawer.setAttribute('aria-hidden', 'true');
    drawer.setAttribute('aria-labelledby', 'remote-drawer-title');
    drawer.setAttribute('role', 'dialog');
    drawer.innerHTML = [
      '<img class="remote-drawer-watermark" src="ao-nav-logo.png" width="416" height="288" alt="" aria-hidden="true" loading="lazy" decoding="async" />',
      '<div class="remote-drawer-header">',
      '  <h2 id="remote-drawer-title">Remote Support</h2>',
      '  <button type="button" class="remote-drawer-close" id="remote-drawer-close" aria-label="Close remote support">&times;</button>',
      '</div>',
      '<div class="remote-drawer-body">',
      '  <p class="remote-drawer-intro">Let our team connect to your computer to help. Choose your system, download the support app, then share the code with your technician on the phone.</p>',
      '  <div class="remote-tabs" role="tablist" aria-label="Choose your operating system">',
      '    <button type="button" class="remote-tab is-active" role="tab" id="remote-tab-windows" aria-selected="true" aria-controls="remote-panel-windows" data-remote-tab="windows">',
      '      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3 5.1 10.3 4v7.3H3V5.1zM10.3 12.7V20L3 18.9v-6.2h7.3zM11.4 3.85 21 2.5v8.8h-9.6V3.85zM21 12.7v8.8l-9.6-1.35V12.7H21z"/></svg>',
      '      Windows / PC',
      '    </button>',
      '    <button type="button" class="remote-tab" role="tab" id="remote-tab-mac" aria-selected="false" aria-controls="remote-panel-mac" data-remote-tab="mac" tabindex="-1">',
      '      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M16.36 12.65c-.02-2.05 1.68-3.03 1.75-3.08-.95-1.39-2.44-1.58-2.97-1.6-1.27-.13-2.47.74-3.11.74-.64 0-1.63-.72-2.68-.7-1.38.02-2.65.8-3.36 2.03-1.43 2.49-.37 6.17 1.03 8.19.68.99 1.5 2.1 2.57 2.06 1.03-.04 1.42-.66 2.66-.66 1.24 0 1.59.66 2.68.64 1.11-.02 1.81-1 2.49-2 .78-1.15 1.11-2.26 1.13-2.32-.02-.01-2.17-.83-2.19-3.29zM14.3 6.34c.56-.68.94-1.63.84-2.57-.81.03-1.79.54-2.37 1.22-.52.6-.98 1.56-.86 2.48.9.07 1.83-.46 2.39-1.13z"/></svg>',
      '      Mac',
      '    </button>',
      '  </div>',
      '  <div class="remote-panel is-active" id="remote-panel-windows" role="tabpanel" aria-labelledby="remote-tab-windows">',
      '    <h3>Windows / PC</h3>',
      '    <ol>',
      '      <li>Click the button below to download the support app.</li>',
      '      <li>Open the downloaded file and allow it to run.</li>',
      '      <li>Give the ID and code shown to Automation One.</li>',
      '    </ol>',
      '    <a href="' + AO_REMOTE_DOWNLOAD_URL_WINDOWS + '" class="remote-download" data-remote-download="windows" download rel="noopener">',
      '      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
      '      Download for Windows',
      '    </a>',
      '  </div>',
      '  <div class="remote-panel" id="remote-panel-mac" role="tabpanel" aria-labelledby="remote-tab-mac" hidden>',
      '    <h3>Mac</h3>',
      '    <ol>',
      '      <li>Click the button below to download the support app.</li>',
      '      <li>Open the downloaded file and follow the prompts.</li>',
      '      <li>Give the ID and code shown to Automation One.</li>',
      '    </ol>',
      '    <a href="' + AO_REMOTE_DOWNLOAD_URL_MAC + '" class="remote-download" data-remote-download="mac" download rel="noopener">',
      '      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
      '      Download for Mac',
      '    </a>',
      '  </div>',
      '  <p class="remote-drawer-hint">Need help getting connected? Call us at <a href="tel:+16042556622">604-255-6622</a> or toll-free <a href="tel:+18886305880">1-888-630-5880</a>.</p>',
      '</div>'
    ].join('');

    document.body.appendChild(overlay);
    document.body.appendChild(drawer);
    return drawer;
  }

  function init() {
    var drawer = build();
    var overlay = document.getElementById('remote-drawer-overlay');
    var closeBtn = document.getElementById('remote-drawer-close');
    if (!drawer || !overlay) return;

    var lastFocus = null;

    function setOpen(open) {
      drawer.classList.toggle('is-open', open);
      overlay.classList.toggle('is-open', open);
      drawer.setAttribute('aria-hidden', open ? 'false' : 'true');
      overlay.setAttribute('aria-hidden', open ? 'false' : 'true');
      document.body.classList.toggle('remote-drawer-open', open);
      if (open) {
        lastFocus = document.activeElement;
        var active = drawer.querySelector('.remote-tab.is-active');
        if (active) active.focus();
      } else if (lastFocus && lastFocus.focus) {
        lastFocus.focus();
      }
    }

    function openDrawer(e) {
      if (e) e.preventDefault();
      activate('windows');
      setOpen(true);
    }
    function closeDrawer() { setOpen(false); }

    // Wire up every "Remote Support" link on the page.
    var links = document.querySelectorAll('a');
    for (var i = 0; i < links.length; i++) {
      var txt = (links[i].textContent || '').replace(/\s+/g, ' ').trim().toLowerCase();
      if (txt === 'remote support') {
        links[i].addEventListener('click', openDrawer);
      }
    }

    if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
    overlay.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && drawer.classList.contains('is-open')) closeDrawer();
    });

    // Tab switching.
    var tabs = drawer.querySelectorAll('.remote-tab');
    function activate(name) {
      for (var t = 0; t < tabs.length; t++) {
        var isActive = tabs[t].getAttribute('data-remote-tab') === name;
        tabs[t].classList.toggle('is-active', isActive);
        tabs[t].setAttribute('aria-selected', isActive ? 'true' : 'false');
        tabs[t].tabIndex = isActive ? 0 : -1;
      }
      var panels = drawer.querySelectorAll('.remote-panel');
      for (var p = 0; p < panels.length; p++) {
        var show = panels[p].id === 'remote-panel-' + name;
        panels[p].classList.toggle('is-active', show);
        if (show) { panels[p].removeAttribute('hidden'); }
        else { panels[p].setAttribute('hidden', ''); }
      }
    }
    for (var k = 0; k < tabs.length; k++) {
      tabs[k].addEventListener('click', function () {
        activate(this.getAttribute('data-remote-tab'));
        this.focus();
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
