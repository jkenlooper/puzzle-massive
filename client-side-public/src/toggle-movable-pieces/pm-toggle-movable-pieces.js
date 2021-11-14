import { html, render } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { puzzleService } from "../puzzle-pieces/puzzle.service";
import "./toggle-movable-pieces.css";
var State;
(function (State) {
    State["On"] = "ON";
    State["Off"] = "OFF";
})(State || (State = {}));
const tag = "pm-toggle-movable-pieces";
let lastInstanceId = 0;
customElements.define(tag, class PmToggleMovablePieces extends HTMLElement {
    constructor() {
        super();
        this.instanceId = PmToggleMovablePieces._instanceId;
        puzzleService.subscribe("pieces/info/toggle-movable", this._onToggleMovablePieces.bind(this), this.instanceId);
        this.status = puzzleService.showMovable ? State.On : State.Off;
        this.render();
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    _onToggleMovablePieces(showMovable) {
        this.status = showMovable ? State.On : State.Off;
        this.render();
    }
    clickedButton(e) {
        e.preventDefault();
        puzzleService.toggleMovable();
    }
    template(data) {
        return html `
        <label
          class=${classMap({
            "pm-ToggleMovablePieces": true,
            isActive: data.status === State.On,
        })}
          @click=${data.clickedButtonHandler}
        >
          <input
            type="checkbox"
            class="u-hidden"
            ?checked=${data.status === State.On}
          />
          <pm-icon class="pm-ToggleMovablePieces-icon" size="sm"
            >solution</pm-icon
          >
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
});
