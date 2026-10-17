(function () {
  function pickSource(video) {
    var sources = video.querySelectorAll('source[src]');
    if (!sources.length) return null;
    for (var i = 0; i < sources.length; i++) {
      var s = sources[i];
      var media = s.getAttribute('media');
      if (!media) return s.getAttribute('src');
      try {
        if (window.matchMedia(media).matches) return s.getAttribute('src');
      } catch (e) {}
    }
    return sources[sources.length - 1].getAttribute('src');
  }

  function ensureVideoSrc(video) {
    if (!video) return false;
    if (video.getAttribute('src')) return true;
    var src = pickSource(video);
    if (!src) return false;
    video.setAttribute('src', src);
    try { video.load(); } catch (e) {}
    return true;
  }

  function wireVideo(v, opts) {
    if (!v) return;
    v.muted = true;
    v.defaultMuted = true;
    v.setAttribute('muted', '');
    v.setAttribute('playsinline', '');
    v.setAttribute('webkit-playsinline', '');
    if (opts && opts.loop) v.loop = true;
    var tryPlay = function () {
      var p = v.play();
      if (p && typeof p.catch === 'function') p.catch(function () {});
    };
    if (opts && opts.ensureSrc) ensureVideoSrc(v);
    if (v.readyState >= 2) tryPlay();
    v.addEventListener('loadeddata', tryPlay, { once: true });
    v.addEventListener('canplay', tryPlay, { once: true });
    tryPlay();
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) tryPlay();
    });
    if (opts && opts.ioRoot && 'IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            if (opts.ensureSrc) ensureVideoSrc(v);
            tryPlay();
          } else if (opts.pauseOffscreen) {
            v.pause();
          }
        });
      }, { threshold: 0.12, rootMargin: opts.rootMargin || '8% 0px' }).observe(opts.ioRoot);
    }
  }

  function initHomepageVideos() {
    // Hero: poster-first path owns fetch/play via inline script. Do not eager-play here.
    var hero = document.querySelector('.hero-video');
    if (hero) {
      hero.muted = true;
      hero.defaultMuted = true;
      hero.setAttribute('muted', '');
      hero.setAttribute('playsinline', '');
    }

    var brandsVideo = document.querySelector('.brands-scene-photo-video');
    var brandsPin = document.querySelector('.brands-scene-pin') || document.querySelector('.brands-scene');
    if (brandsVideo) {
      brandsVideo.preload = 'none';
      brandsVideo.setAttribute('preload', 'none');
      brandsVideo.loop = true;
      // Only attach src when near viewport (preload=none alone is not enough once src is set)
      if ('IntersectionObserver' in window && brandsPin) {
        var armed = false;
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting || armed) return;
            armed = true;
            ensureVideoSrc(brandsVideo);
            wireVideo(brandsVideo, { loop: true, pauseOffscreen: false });
            io.disconnect();
          });
        }, { threshold: 0.01, rootMargin: '40% 0px' });
        io.observe(brandsPin);
      } else {
        ensureVideoSrc(brandsVideo);
        wireVideo(brandsVideo, { loop: true });
      }
    }
  }

  window.automationOneWireVideo = wireVideo;
  window.automationOneInitHomepageVideos = initHomepageVideos;
  window.automationOneEnsureVideoSrc = ensureVideoSrc;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHomepageVideos);
  } else {
    initHomepageVideos();
  }

  document.addEventListener('touchstart', function once() {
    document.querySelectorAll('video.is-ready, .brands-scene-photo-video').forEach(function (v) {
      if (v.classList.contains('hero-video') && !v.classList.contains('is-ready')) return;
      if (v.paused) {
        var p = v.play();
        if (p && typeof p.catch === 'function') p.catch(function () {});
      }
    });
  }, { once: true, passive: true });
})();
