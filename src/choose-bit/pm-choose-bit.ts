/* global HTMLElement, customElements, MEDIA_PATH */
declare const MEDIA_PATH: string;

import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";

import { chooseBitService } from "./choose-bit.service";

interface TemplateData {
  isLoading: boolean;
  hasError: boolean;
  message: string;
  limit: number;
  bits: string[];
}

const tag = "pm-choose-bit";

customElements.define(
  tag,
  class PmChooseBit extends HTMLElement {
    static get observedAttributes() {
      // TODO: Should the player dots be an attribute?  If the dots value changes
      // then it may need to render if it hasn't already.
      // Or it could listen to a websocket that has the dot value for the
      // player.
      return [
        /*"dots"*/
      ];
    }

    static getBits(self: PmChooseBit, limit: number = 10): Promise<void> {
      return chooseBitService
        .getBits(limit)
        .then((bits) => {
          self.bits = bits;
        })
        .catch(() => {
          self.hasError = true;
        })
        .finally(() => {
          self.isLoading = false;
          self.render();
        });
    }

    private bits: string[] = [];
    private message: string = "";
    private limit: number;
    private isLoading: boolean = true;
    private hasError: boolean = false;

    constructor() {
      super();

      // Set the message from the message attribute
      const message = this.attributes.getNamedItem("message");
      this.message = message ? message.value : "";

      // Set the limit from the limit attribute
      const limit = this.attributes.getNamedItem("limit");
      this.limit = limit ? parseInt(limit.value) : 10;

      this.init();
    }

    handleClickMore() {
      this.isLoading = true;
      this.render();
      PmChooseBit.getBits(this, this.limit);
    }

    init() {
      // TODO: Need to only render if the player has enough dots:
      // <div ng-if="SiteController.detailsReady && SiteController.hasBit && SiteController.userDetails.dots >= 1400">
      return PmChooseBit.getBits(this, this.limit);
    }

    template(data: TemplateData) {
      const self = this;

      return html`
        <section class="pm-ChooseBit">
          <h1 class="pm-ChooseBit-message">
            ${data.message}
          </h1>
          <div class="pm-ChooseBit-items">
            ${items()}
          </div>
          <button @click=${self.handleClickMore.bind(self)}>More</button>
        </section>
      `;

      // During and after successfully loading the count of items should be
      // static.  Only show no items if there is an error or no bits are
      // available.
      function items() {
        if (data.isLoading) {
          return html`
            ${repeat(
              data.bits,
              (item) => item, // Key fn
              () => {
                return html`
                  <span class="pm-ChooseBit-item" role="list-item"></span>
                `;
              }
            )}
          `;
        }
        if (data.hasError) {
          return html`
            An error occured.
          `;
        } else {
          if (!data.bits.length) {
            return html`
              No bits are available at this time.
            `;
          } else {
            return html`
              ${repeat(
                data.bits,
                (item) => item, // Key fn
                (item) => {
                  return html`
                    <span class="pm-ChooseBit-item" role="list-item">
                      <button ng-click="ChooseBitController.claimBit(item)">
                        <img
                          src="${MEDIA_PATH}bit-icons/64-${item}.png"
                          width="64"
                          height="64"
                          alt="${item}"
                        />
                      </button>
                    </span>
                  `;
                }
              )}
            `;
          }
        }
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
          isLoading: this.isLoading,
          hasError: this.hasError,
          message: this.message,
          limit: this.limit,
          bits: this.bits,
        }
      );
    }

    render() {
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
