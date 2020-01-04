import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";
import { classMap } from "lit-html/directives/class-map.js";
import { styleMap } from "lit-html/directives/style-map.js";

import { puzzleBitsService, PlayerBit } from "./puzzle-bits.service";
import "./puzzle-bits.css";

interface TemplateData {
  collection: Array<PlayerBit>;
}

const tag = "pm-puzzle-bits";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleBits extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    constructor() {
      super();
      this.instanceId = PmPuzzleBits._instanceId;

      puzzleBitsService.subscribe(this.render.bind(this), this.instanceId);
      this.render();
    }

    template(data: TemplateData) {
      return html`
        <div class="pm-PuzzleBits" role="list">
          ${bits()}
        </div>
      `;

      function bits() {
        return html`
          ${repeat(
            data.collection,
            (bit) => bit.id, // Key fn
            (bit) => {
              return html`
                <div
                  class=${classMap({
                    "pm-PuzzleBits-bit": true,
                    "is-active": bit.active,
                    "pm-PuzzleBits-bit--ownBit": bit.ownBit,
                  })}
                  role="listitem"
                  style=${styleMap({
                    transform: `translate(${bit.x}px, ${bit.y}px)`,
                  })}
                >
                  <pm-player-bit player=${bit.id}></pm-player-bit>
                </div>
              `;
            }
          )}
        `;
      }
    }

    get data(): TemplateData {
      return {
        collection: puzzleBitsService.collection,
      };
    }

    render() {
      render(this.template(this.data), this);
    }
  }
);
