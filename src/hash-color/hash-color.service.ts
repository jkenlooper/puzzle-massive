type Callback = () => any;

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
      // TODO: store multiple colors instead of just a single color
      const storedBackgroundColor = window.localStorage.getItem(
        HashColorService.LocalStorageName
      );
      if (storedBackgroundColor !== null) {
        this.backgroundColor = storedBackgroundColor;
        /*
        window.location.hash = `${HashColorService.HashBackgroundPrefix.substr(
          1
        )}${storedBackgroundColor.substr(1)}`;
         */
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
          HashColorService.LocalStorageName,
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
