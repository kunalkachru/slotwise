// Classic / New look. A normal (not module) script at the top of <head>, so the chosen look
// is set on <html data-theme> before the first paint and the page never flashes the wrong
// one. "classic" is the default; css/calm.css styles only :root[data-theme="calm"].
(function () {
  var KEY = "slotwise:theme";
  function read() {
    try {
      return localStorage.getItem(KEY) === "calm" ? "calm" : "classic";
    } catch (e) {
      return "classic"; // private mode
    }
  }
  function apply(theme) {
    document.documentElement.dataset.theme = theme;
  }
  apply(read());
  window.slotwiseTheme = {
    current: function () {
      return document.documentElement.dataset.theme === "calm" ? "calm" : "classic";
    },
    set: function (theme) {
      try {
        localStorage.setItem(KEY, theme);
      } catch (e) { /* private mode: still switch for this page */ }
      apply(theme);
    },
  };
})();
