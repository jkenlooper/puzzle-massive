import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import playerSettingsService from "./player-settings.service";
import "./toggle-puzzle-piece-sound.css";
var State;
(function (State) {
    State["On"] = "ON";
    State["Off"] = "OFF";
})(State || (State = {}));
const tag = "pm-toggle-puzzle-piece-sound";
let lastInstanceId = 0;
customElements.define(tag, class PmTogglePuzzlePieceSound extends HTMLElement {
    constructor() {
        super();
        this.instanceId = PmTogglePuzzlePieceSound._instanceId;
        this.status = playerSettingsService["playPuzzlePieceSound"]
            ? State.On
            : State.Off;
        playerSettingsService.subscribe(this._onPlayerSettingsChange.bind(this), this.instanceId);
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    _onPlayerSettingsChange() {
        this.status = playerSettingsService["playPuzzlePieceSound"]
            ? State.On
            : State.Off;
        this.render();
    }
    clickedButton(e) {
        e.preventDefault();
        playerSettingsService.togglePlayPuzzlePieceSound();
    }
    template(data) {
        return html `
        <label
          class=${classMap({
            "pm-TogglePuzzlePieceSound": true,
            isActive: data.status === State.On,
        })}
          @click=${data.clickedButtonHandler}
        >
          ${data.status === State.On
            ? html `<input type="checkbox" checked />`
            : html `<input type="checkbox" />`}
          Play click sound when joining puzzle pieces
        </label>
      `;
    }
    get data() {
        return {
            status: this.status,
            clickedButtonHandler: {
                handleEvent: this.clickedButton.bind(this),
                capture: true,
            },
        };
    }
    render() {
        render(this.template(this.data), this);
    }
    connectedCallback() {
        this.render();
    }
});
