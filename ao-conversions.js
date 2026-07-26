/* Automation One — GA4 conversion helpers (phone + quote/contact forms) */
(function () {
  function track() {
    if (typeof gtag !== "function") return;
    gtag.apply(null, arguments);
  }

  // Phone number clicks (mobile tap-to-call)
  document.addEventListener(
    "click",
    function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a[href^="tel:"]') : null;
      if (!a) return;
      var href = a.getAttribute("href") || "";
      track("event", "phone_click", {
        event_category: "contact",
        phone_number: href.replace(/^tel:/i, ""),
        link_url: href,
        link_text: (a.textContent || "").trim().slice(0, 80),
      });
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
      track("event", "generate_lead", {
        event_category: "lead",
        method: "quote_form",
        form_id: id || "quote_form",
        office: office || undefined,
      });
    },
    true
  );
})();
