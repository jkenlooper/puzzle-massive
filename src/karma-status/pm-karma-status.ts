import { html, render } from "lit-html";
import { styleMap } from "lit-html/directives/style-map.js";

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
    private amount: number = 0;
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    constructor() {
      super();
      this.instanceId = PmKarmaStatus._instanceId;
      // @ts-ignore: TODO: minpubsub
      //window.subscribe("karma/updated", this._onKarmaUpdate.bind(this));
      puzzleService.subscribe(
        "karma/updated",
        this._onKarmaUpdate.bind(this),
        this.instanceId
      );
      // @ts-ignore: TODO: minpubsub
      window.subscribe("piece/move/blocked", this._onMoveBlocked.bind(this));
      this.render();
    }

    _onKarmaUpdate(data: KarmaData) {
      this.amount =
        (Math.min(data.karma, PmKarmaStatus.max) / PmKarmaStatus.max) * 100;
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
          <span
            class="pm-KarmaStatus-bar"
            style=${styleMap({ height: data.amount + "%" })}
          >
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
