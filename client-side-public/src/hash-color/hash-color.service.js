function puzzleNameFromLocation() {
  const re = /\/puzzle\/(.+)\/$/;
  const match = window.location.pathname.match(re);
  let puzzleName = "";
  if (match != null) {
    puzzleName = match[1] || puzzleName;
  }
  return puzzleName;
}
class HashColorService {
  constructor() {
    this.listeners = new Map();
    if (!window.localStorage) {
      // User may have blocked the site from storing cookies and using
      // localStorage.
      return;
    }
    // init
    this._onhashchange();
    // listen
    window.addEventListener("hashchange", this._onhashchange.bind(this), false);
    window.addEventListener("pm-hash-color-change", (ev) => {
      const color = ev.detail;
      window.location.hash = `${HashColorService.HashBackgroundPrefix.substr(
        1
      )}${color}`;
    });
    // Set hash if defined in localstorage and no hash is already set.
    if (this.backgroundColor === undefined) {
      const storedBackgroundColor = window.localStorage.getItem(
        HashColorService.LocalStorageName + ":" + puzzleNameFromLocation()
      );
      if (storedBackgroundColor !== null) {
        this.backgroundColor = storedBackgroundColor;
        this._broadcast();
      }
    }
  }
  _onhashchange() {
    if (
      window.location.hash.startsWith(HashColorService.HashBackgroundPrefix)
    ) {
      const hashBackgroundColor =
        "#" +
        window.location.hash.substr(
          HashColorService.HashBackgroundPrefix.length
        );
      if (this.backgroundColor !== hashBackgroundColor) {
        window.localStorage.setItem(
          HashColorService.LocalStorageName + ":" + puzzleNameFromLocation(),
          hashBackgroundColor
        );
        this.backgroundColor = hashBackgroundColor;
        this._broadcast();
      }
    }
  }
  _broadcast() {
    this.listeners.forEach((fn /*, id*/) => {
      fn();
    });
  }
  subscribe(fn, id) {
    //console.log("subscribe", fn, id);
    // Add the fn to listeners
    this.listeners.set(id, fn);
  }
  unsubscribe(id) {
    //console.log("unsubscribe", id);
    // remove fn from listeners
    this.listeners.delete(id);
  }
}
HashColorService.HashBackgroundPrefix = "#background=";
HashColorService.LocalStorageName = "hash-background-color";
const hashColorService = new HashColorService();
export default hashColorService;
