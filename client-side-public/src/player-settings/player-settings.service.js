import defaultSettings from "./player-settings-defaults";

type Callback = () => any;

class PlayerSettingsService {
  static LocalStorageName = "player-settings";
  listeners: Map<string, Callback> = new Map();
  private _playPuzzlePieceSound = defaultSettings["playPuzzlePieceSound"];
  constructor() {
    if (!window.localStorage) {
      // User may have blocked the site from storing cookies and using
      // localStorage.
      return;
    }

    this._init();
  }

  _init() {
    const storedSetting = window.localStorage.getItem(
      `${PlayerSettingsService.LocalStorageName}:playPuzzlePieceSound`
    );
    if (storedSetting !== null) {
      this._playPuzzlePieceSound = storedSetting === "1";
    }
    this._broadcast();
  }

  get playPuzzlePieceSound() {
    return this._playPuzzlePieceSound;
  }
  set playPuzzlePieceSound(value: boolean) {
    window.localStorage.setItem(
      `${PlayerSettingsService.LocalStorageName}:playPuzzlePieceSound`,
      value ? "1" : "0"
    );
    this._playPuzzlePieceSound = value;
    this._broadcast();
  }
  togglePlayPuzzlePieceSound() {
    this.playPuzzlePieceSound = !this.playPuzzlePieceSound;
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

const playerSettingsService = new PlayerSettingsService();

export default playerSettingsService;
