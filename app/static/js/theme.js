// Classic look / Figma design. A normal (not module) script at the top of <head>, so the
// chosen look is set on <html data-theme> before the first paint and the page never flashes
// the wrong one. The Figma design ("calm", css/calm.css, which styles only
// :root[data-theme="calm"]) is the default; "classic" only when the visitor chose it.
(function () {
  var KEY = "slotwise:theme";
  function read() {
    try {
      return localStorage.getItem(KEY) === "classic" ? "classic" : "calm";
    } catch (e) {
      return "calm"; // private mode: the default
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
