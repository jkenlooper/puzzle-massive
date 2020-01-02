import { html, render } from "lit-html";

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

    clickedButton() {
      puzzleService.toggleMovable();
    }

    template(data: TemplateData) {
      console.log(data.status);
      return html`
        <button
          class="pm-ToggleMovablePieces"
          @click=${data.clickedButtonHandler}
        >
          <pm-icon size="sm">solution</pm-icon>
        </div>
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
