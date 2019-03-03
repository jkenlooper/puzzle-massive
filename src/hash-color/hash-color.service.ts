type Callback = () => any;

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
  static HashBackgroundPrefix = "#background=";
  static LocalStorageName = "hash-background-color";
  listeners: Map<string, Callback> = new Map();
  backgroundColor: string | undefined;
  constructor() {
    // init
    this._onhashchange();

    // listen
    window.addEventListener("hashchange", this._onhashchange.bind(this), false);
    window.addEventListener("pm-hash-color-change", (ev: any) => {
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

  subscribe(fn: Callback, id: string) {
    //console.log("subscribe", fn, id);
    // Add the fn to listeners
    this.listeners.set(id, fn);
  }

  unsubscribe(id: string) {
    //console.log("unsubscribe", id);
    // remove fn from listeners
    this.listeners.delete(id);
  }
}

const hashColorService = new HashColorService();

export default hashColorService;
