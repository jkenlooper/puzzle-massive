import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";

import { puzzleService } from "../puzzle-pieces/puzzle.service";

import "./toggle-movable-pieces.css";

enum State {
  On = "ON",
  Off = "OFF",
}

interface TemplateData {
  status: State;
  clickedButtonHandler: any; // event listener object
}

const tag = "pm-toggle-movable-pieces";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmToggleMovablePieces extends HTMLElement {
    private instanceId: string;
    private status: State;
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    constructor() {
      super();
      this.instanceId = PmToggleMovablePieces._instanceId;
      puzzleService.subscribe(
        "pieces/info/toggle-movable",
        this._onToggleMovablePieces.bind(this),
        this.instanceId
      );
      this.status = puzzleService.showMovable ? State.On : State.Off;
      this.render();
    }

    _onToggleMovablePieces(showMovable) {
      this.status = showMovable ? State.On : State.Off;
      this.render();
    }

    clickedButton(e) {
      e.preventDefault();
      puzzleService.toggleMovable();
    }

    template(data: TemplateData) {
      return html`
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

    get data(): TemplateData {
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
  }
);
