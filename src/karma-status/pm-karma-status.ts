import { html, render } from "lit-html";
import { styleMap } from "lit-html/directives/style-map.js";

import "./karma-status.css";

interface TemplateData {
  amount: number;
}

const tag = "pm-karma-status";

customElements.define(
  tag,
  class PmKarmaStatus extends HTMLElement {
    static max: number = 25;
    private amount: number = 0;

    constructor() {
      super();
      // @ts-ignore: TODO: minpubsub
      window.subscribe("karma/updated", this._onKarmaUpdate.bind(this));
      // @ts-ignore: TODO: minpubsub
      window.subscribe("piece/move/blocked", this._onMoveBlocked.bind(this));
      this.render();
    }

    _onKarmaUpdate(data: any) {
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
