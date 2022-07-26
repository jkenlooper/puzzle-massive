import defaultSettings from "./player-settings-defaults";
class PlayerSettingsService {
  constructor() {
    this.listeners = new Map();
    this._playPuzzlePieceSound = defaultSettings["playPuzzlePieceSound"];
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
  set playPuzzlePieceSound(value) {
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
PlayerSettingsService.LocalStorageName = "player-settings";
const playerSettingsService = new PlayerSettingsService();
export default playerSettingsService;
