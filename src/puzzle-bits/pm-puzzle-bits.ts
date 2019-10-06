import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";
import { classMap } from "lit-html/directives/class-map.js";
import { styleMap } from "lit-html/directives/style-map.js";

import { colorForPlayer } from "../player-bit/player-bit-img.service";
import { puzzleBitsService, PlayerBit } from "./puzzle-bits.service";
import "./puzzle-bits.css";

interface TemplateData {
  collection: Array<PlayerBit>;
  mediaPath: string;
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
    private mediaPath: string;
    constructor() {
      super();
      this.instanceId = PmPuzzleBits._instanceId;

      const mediaPath = this.attributes.getNamedItem("media-path");
      this.mediaPath = mediaPath ? mediaPath.value : "";

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
                  ${bit.icon
                    ? html`
                        <img
                          src=${`${data.mediaPath}bit-icons/64-${bit.icon}.png`}
                          class="pm-PlayerBit"
                          width="64"
                          height="64"
                          alt=${bit.icon}
                        />
                      `
                    : html`
                        <span
                          class="hasNoBit pm-PlayerBit"
                          style=${`--pm-PlayerBit-color:${colorForPlayer(
                            bit.id
                          )}`}
                          >${bit.id.toString(36)}</span
                        >
                      `}
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
        mediaPath: this.mediaPath,
      };
    }

    render() {
      render(this.template(this.data), this);
    }
  }
);
