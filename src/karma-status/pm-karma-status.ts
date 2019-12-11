import { html, render } from "lit-html";

import { puzzleService, KarmaData } from "../puzzle-pieces/puzzle.service";

import "./karma-status.css";

interface TemplateData {
  amount: number;
}

const tag = "pm-karma-status";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmKarmaStatus extends HTMLElement {
    private instanceId: string;
    static max: number = 25;
    private amount: number = -1;
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    constructor() {
      super();
      this.instanceId = PmKarmaStatus._instanceId;
      puzzleService.subscribe(
        "karma/updated",
        this._onKarmaUpdate.bind(this),
        this.instanceId
      );
      puzzleService.subscribe(
        "piece/move/blocked",
        this._onMoveBlocked.bind(this),
        this.instanceId
      );
      this.render();
    }

    _onKarmaUpdate(data: KarmaData) {
      this.amount = Math.min(data.karma, PmKarmaStatus.max);
      this.render();
    }

    _onMoveBlocked() {
      this.amount = 0;
      this.render();
    }

    template(data: TemplateData) {
      return html`
        <div
          class="pm-KarmaStatus"
          title="Your puzzle karma.  Changes based on your recent piece movements on this puzzle.  Your piece movements will be blocked temporarily if this reaches 0."
        >
          <pm-icon size="sm">solution</pm-icon>
          <span class="pm-KarmaStatus-amount">
            ${data.amount === -1 ? "--" : data.amount}
          </span>
        </div>
      `;
    }

    get data(): TemplateData {
      return {
        amount: this.amount,
      };
    }

    render() {
      render(this.template(this.data), this);
    }
  }
);
