(function () {
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
          if (entry.isIntersecting) tryPlay();
          else if (opts.pauseOffscreen) v.pause();
        });
      }, { threshold: 0.12, rootMargin: '8% 0px' }).observe(opts.ioRoot);
    }
  }

  function initHomepageVideos() {
    wireVideo(document.querySelector('.hero-video'), { loop: true });
    var brandsVideo = document.querySelector('.brands-scene-photo-video');
    var brandsPin = document.querySelector('.brands-scene-pin');
    if (brandsVideo) {
      if (!brandsVideo.getAttribute('src')) {
        var srcEl = brandsVideo.querySelector('source[type="video/mp4"]');
        if (srcEl && srcEl.getAttribute('src')) {
          brandsVideo.setAttribute('src', srcEl.getAttribute('src'));
        }
      }
      brandsVideo.loop = true;
      wireVideo(brandsVideo, brandsPin ? { ioRoot: brandsPin, pauseOffscreen: false } : { loop: true });
    }
  }

  window.automationOneWireVideo = wireVideo;
  window.automationOneInitHomepageVideos = initHomepageVideos;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHomepageVideos);
  } else {
    initHomepageVideos();
  }

  document.addEventListener('touchstart', function once() {
    document.querySelectorAll('video').forEach(function (v) {
      if (v.paused) {
        var p = v.play();
        if (p && typeof p.catch === 'function') p.catch(function () {});
      }
    });
  }, { once: true, passive: true });
})();
