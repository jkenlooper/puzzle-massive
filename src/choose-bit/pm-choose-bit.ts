/* global HTMLElement, customElements, MEDIA_PATH */
declare const MEDIA_PATH: string;

import { html, render } from "lit-html";

import { chooseBitService } from "./choose-bit.service";

interface TemplateData {
  message: string;
  limit: string;
  bits: string[];
}

customElements.define(
  "pm-choose-bit",
  class PmChooseBit extends HTMLElement {
    static get observedAttributes() {
      // TODO: Should the player dots be an attribute?  If the dots value changes
      // then it may need to render if it hasn't already.
      // Or it could listen to a websocket that has the dot value for the
      // player.
      return ["message", "limit"];
    }

    private bits: string[] = [];

    constructor() {
      super();
      this.init().then(() => {
        this.render();
      });
    }

    init() {
      // TODO: Need to only render if the player has enough dots:
      // <div ng-if="SiteController.detailsReady && SiteController.hasBit && SiteController.userDetails.dots >= 1400">

      return chooseBitService
        .getBits(10)
        .then((bits) => {
          this.bits = bits;
        })
        .catch((err) => {
          console.log("error", err);
        });
    }

    template(data: TemplateData) {
      if (!this.bits.length) {
        return html`
          <!-- no bits -->
          no bits
        `;
      } else {
        return html`
          <section class="pm-ChooseBit">
            <h1 class="pm-ChooseBit-message">
              ${data.message}
            </h1>
            <div class="pm-ChooseBit-items">
              ${data.bits.map(
                (item) => html`
                  <button
                    role="list-item"
                    ng-click="ChooseBitController.claimBit(item)"
                  >
                    <img
                      src="${MEDIA_PATH}bit-icons/64-${item}.png"
                      width="64"
                      height="64"
                      alt="${item}"
                    />
                  </button>
                `
              )}
            </div>
            <button ng-click="ChooseBitController.getBits()">More</button>
          </section>
        `;
      }
    }

    get data(): TemplateData {
      return PmChooseBit.observedAttributes.reduce(
        (data: any, item: string) => {
          const attr = this.attributes.getNamedItem(item);
          data[item] = attr ? attr.value : null;
          return data;
        },
        {
          bits: this.bits,
        }
      );
    }

    render() {
      console.log(this.data);
      render(this.template(this.data), this);
    }

    connectedCallback() {
      console.log("connectedCallback");
    }
    disconnectedCallback() {
      console.log("disconnectedCallback");
    }
    adoptedCallback() {
      console.log("adoptedCallback");
    }
    attributeChangedCallback(name: String, oldValue: String, newValue: String) {
      console.log("attributeChangedCallback", name, oldValue, newValue);
      this.render();
    }
  }
);
