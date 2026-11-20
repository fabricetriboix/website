(function () {
  var KEY = "ft-consent";

  var granted = {
    ad_storage: "granted",
    ad_user_data: "granted",
    ad_personalization: "granted",
    analytics_storage: "granted",
    functionality_storage: "denied",
    personalization_storage: "denied",
  };

  var denied = {
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    analytics_storage: "denied",
    functionality_storage: "denied",
    personalization_storage: "denied",
  };

  function readChoice() {
    try {
      var value = localStorage.getItem(KEY);
      if (value === "granted" || value === "denied") return value;
    } catch (err) {}
    return null;
  }

  function writeChoice(value) {
    try {
      localStorage.setItem(KEY, value);
    } catch (err) {}
  }

  function apply(value) {
    var payload = value === "granted" ? granted : denied;
    window.dataLayer = window.dataLayer || [];
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", payload);
    } else {
      window.dataLayer.push(["consent", "update", payload]);
    }
  }

  var banner = document.createElement("div");
  banner.id = "consent-banner";
  banner.className = "consent-banner";
  banner.setAttribute("role", "dialog");
  banner.setAttribute("aria-labelledby", "consent-text");
  banner.tabIndex = -1;
  banner.hidden = true;
  banner.innerHTML =
    '<div class="wrap consent-inner">' +
    '<div class="consent-copy">' +
    '<p id="consent-text" class="consent-text">May I use your data for analytics?</p>' +
    "</div>" +
    '<div class="consent-actions">' +
    '<button type="button" class="consent-reject">Reject</button>' +
    '<button type="button" class="consent-accept">Accept</button>' +
    "</div>" +
    "</div>";
  document.body.appendChild(banner);

  var reject = banner.querySelector(".consent-reject");
  var accept = banner.querySelector(".consent-accept");
  var manage = document.querySelector(".consent-manage");
  var lastFocused = null;

  function setExpanded(open) {
    if (manage) manage.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function openBanner(fromControl) {
    lastFocused = fromControl ? document.activeElement : null;
    banner.hidden = false;
    banner.setAttribute("aria-modal", readChoice() ? "false" : "true");
    document.body.classList.add("has-consent-banner");
    setExpanded(true);
    banner.focus();
  }

  function closeBanner() {
    banner.hidden = true;
    document.body.classList.remove("has-consent-banner");
    setExpanded(false);
    if (lastFocused && typeof lastFocused.focus === "function") {
      lastFocused.focus();
    }
  }

  function choose(value) {
    writeChoice(value);
    apply(value);
    closeBanner();
  }

  function activateOnKey(event) {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    event.currentTarget.click();
  }

  reject.addEventListener("keydown", activateOnKey);
  accept.addEventListener("keydown", activateOnKey);
  if (manage) manage.addEventListener("keydown", activateOnKey);

  reject.addEventListener("click", function () {
    choose("denied");
  });
  accept.addEventListener("click", function () {
    choose("granted");
  });

  banner.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && readChoice()) {
      event.preventDefault();
      closeBanner();
      return;
    }
    if (event.key !== "Tab" || readChoice()) return;
    if (event.shiftKey) {
      if (document.activeElement === reject || document.activeElement === banner) {
        event.preventDefault();
        accept.focus();
      }
    } else if (document.activeElement === accept || document.activeElement === banner) {
      event.preventDefault();
      reject.focus();
    }
  });

  if (manage) {
    manage.setAttribute("aria-controls", "consent-banner");
    manage.setAttribute("aria-expanded", "false");
    manage.addEventListener("click", function () {
      if (banner.hidden) openBanner(true);
      else closeBanner();
    });
  }

  if (!readChoice()) openBanner(false);
})();
