/* global HTMLElement, customElements, MEDIA_PATH */
declare const MEDIA_PATH: string;

import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";

import "./choose-bit.css";
import { chooseBitService } from "./choose-bit.service";

interface TemplateData {
  isLoading: boolean;
  isReloading: boolean;
  hasError: boolean;
  message: string;
  limit: number;
  bits: string[];
  dots: string;
}

const minimumDotsRequired = 1400;
const limitBits = 10;

const tag = "pm-choose-bit";

customElements.define(
  tag,
  class PmChooseBit extends HTMLElement {
    static get observedAttributes() {
      // If the dots value changes then it may need to render if it hasn't
      // already.
      return ["dots"];
    }

    static getBits(
      self: PmChooseBit,
      limit: number = limitBits
    ): Promise<void> {
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
          self.isReloading = false;
          self.render();
        });
    }

    private bits: string[] = Array(limitBits);
    private message: string = "";
    private limit: number;
    private isLoading: boolean = true;
    private isReloading: boolean = false;
    private hasError: boolean = false;

    constructor() {
      super();

      // Set the message from the message attribute
      const message = this.attributes.getNamedItem("message");
      this.message = message ? message.value : "";

      // Set the limit from the limit attribute
      const limit = this.attributes.getNamedItem("limit");
      this.limit = limit ? parseInt(limit.value) : limitBits;
    }

    handleClickMore() {
      this.isReloading = true;
      this.render();
      PmChooseBit.getBits(this, this.limit);
    }

    template(data: TemplateData) {
      const self = this;
      if (!(parseInt(data.dots) > minimumDotsRequired)) {
        return html`
          Insufficient dots to pick a different bit.
        `;
      }

      return html`
        <section class="pm-ChooseBit">
          <h1 class="pm-ChooseBit-message">
            ${data.message}
          </h1>
          <div class="pm-ChooseBit-items">
            ${items()}
          </div>
          <button
            ?disabled=${self.isReloading}
            @click=${self.handleClickMore.bind(self)}
          >
            More
          </button>
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
                      <button @click=${claimBit.bind(self)}>
                        <img
                          src="${MEDIA_PATH}bit-icons/64-${item}.png"
                          width="64"
                          height="64"
                          alt="${item}"
                        />
                      </button>
                    </span>
                  `;

                  function claimBit() {
                    chooseBitService.claimBit(item).then(() => {
                      const userDetailsChangeEvent = new Event(
                        "userDetailsChange",
                        {
                          bubbles: true,
                        }
                      );
                      self.dispatchEvent(userDetailsChangeEvent);
                    });
                  }
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
          isReloading: this.isReloading,
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
      //console.log("connectedCallback");
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback");
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
    attributeChangedCallback(
      name: string,
      _oldValue: string | null,
      _newValue: string | null
    ) {
      // Need to only render initially if the player has enough dots.
      if (name === "dots") {
        if (_newValue && parseInt(_newValue) > minimumDotsRequired) {
          PmChooseBit.getBits(this, this.limit);
        } else if (!this.isLoading) {
          // Render the message for not enough dots since the list of bits were
          // available previously.
          this.render();
        }
      }
    }
  }
);
