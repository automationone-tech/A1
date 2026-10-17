/* Automation One — GA4 conversion helpers (phone + quote/contact forms)
   Uses beacon + short delay so tel:/mailto: navigation doesn't cancel the hit. */
(function () {
  function track(name, params, done) {
    if (typeof gtag !== "function") {
      if (done) done();
      return;
    }
    var payload = Object.assign(
      {
        transport_type: "beacon",
        event_timeout: 2000,
      },
      params || {}
    );
    var finished = false;
    function finish() {
      if (finished) return;
      finished = true;
      if (done) done();
    }
    payload.event_callback = finish;
    gtag("event", name, payload);
    setTimeout(finish, 500);
  }

  // Phone number clicks (mobile tap-to-call / desktop FaceTime prompt)
  document.addEventListener(
    "click",
    function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href^="tel:"]') : null;
      if (!a) return;
      var href = a.getAttribute("href") || "";
      if (!href) return;

      e.preventDefault();
      track(
        "phone_click",
        {
          event_category: "contact",
          phone_number: href.replace(/^tel:/i, ""),
          link_url: href,
          link_text: (a.textContent || "").trim().slice(0, 80),
        },
        function () {
          window.location.href = href;
        }
      );
    },
    true
  );

  // Quote drawer + contact forms (mailto flow)
  document.addEventListener(
    "submit",
    function (e) {
      var form = e.target;
      if (!form || form.tagName !== "FORM") return;
      var id = form.id || "";
      var isQuote =
        id === "quote-drawer-form" ||
        form.classList.contains("quote-drawer-form") ||
        form.classList.contains("contact-form") ||
        id === "form-vancouver" ||
        id === "form-burnaby";
      if (!isQuote) return;

      var office = form.getAttribute("data-office") || "";
      // Fire immediately (capture). Form scripts still open mailto after.
      track("generate_lead", {
        event_category: "lead",
        method: "quote_form",
        form_id: id || "quote_form",
        office: office || undefined,
      });
    },
    true
  );
})();
