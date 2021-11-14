import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";
import userDetailsService from "../site/user-details.service";
import "./choose-bit.css";
import { chooseBitService } from "./choose-bit.service";
import { areCookiesEnabled } from "../site/cookies";
const limitBits = 10;
const tag = "pm-choose-bit";
let lastInstanceId = 0;
customElements.define(tag, class PmChooseBit extends HTMLElement {
    constructor() {
        super();
        this.bits = Array(limitBits);
        this.message = "";
        this.isLoading = true;
        this.isReloading = false;
        this.hasError = false;
        this.responseMessage = "";
        this.responseName = "";
        this.instanceId = PmChooseBit._instanceId;
        const mediaPath = this.attributes.getNamedItem("media-path");
        this.mediaPath = mediaPath ? mediaPath.value : "";
        // Set the message from the message attribute
        const message = this.attributes.getNamedItem("message");
        this.message = message ? message.value : "";
        // Set the limit from the limit attribute
        const limit = this.attributes.getNamedItem("limit");
        this.limit = limit ? parseInt(limit.value) : limitBits;
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    static getBits(self, limit = limitBits) {
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
    handleClickMore() {
        this.isReloading = true;
        this.render();
        PmChooseBit.getBits(this, this.limit);
    }
    template(data) {
        const self = this;
        if (!areCookiesEnabled()) {
            return html `
          <p class="pm-Message">
            <strong
              >Please enable cookies in your browser for this website.</strong
            >
            Choosing a bit icon and logging in require browser cookies.
          </p>
        `;
        }
        return html `
        <div class="pm-ChooseBit">
          <p class="pm-ChooseBit-message">
            <strong>${data.message}</strong>
          </p>
          ${data.hasDotRequirement
            ? ""
            : html `
                <p class="pm-ChooseBit-message">
                  Not enough dots to choose a bit icon.
                </p>
              `}
          <div class="pm-ChooseBit-items">${items()}</div>
          <div class="u-paddingTopSm u-paddingBottomSm u-textCenter">
            <button
              class="Button Button--primary"
              ?disabled=${self.isReloading}
              @click=${self.handleClickMore.bind(self)}
            >
              More
            </button>
            ${data.hasResponseMessage
            ? html `
                  <pm-response-message
                    message=${data.responseMessage}
                    name=${data.responseName}
                  ></pm-response-message>
                `
            : ""}
          </div>
        </div>
      `;
        // During and after successfully loading the count of items should be
        // static.  Only show no items if there is an error or no bits are
        // available.
        function items() {
            if (data.isLoading) {
                return html `
            ${repeat(data.bits, (item) => item, // Key fn
                () => {
                    return html `
                  <span class="pm-ChooseBit-item" role="list-item"></span>
                `;
                })}
          `;
            }
            if (data.hasError) {
                return html ` An error occured. `;
            }
            else {
                if (!data.bits.length) {
                    return html ` No bits are available at this time. `;
                }
                else {
                    return html `
              ${repeat(data.bits, (item) => item, // Key fn
                    (item) => {
                        return html `
                    <span class="pm-ChooseBit-item" role="list-item">
                      <button
                        class="Button"
                        ?disabled=${!data.hasDotRequirement}
                        @click=${claimBit.bind(self)}
                      >
                        <img
                          src="${self.mediaPath}bit-icons/64-${item}.png"
                          width="64"
                          height="64"
                          alt="${item}"
                        />
                      </button>
                    </span>
                  `;
                        function claimBit() {
                            chooseBitService
                                .claimBit(item)
                                .then((data) => {
                                const userDetailsChangeEvent = new Event("userDetailsChange", {
                                    bubbles: true,
                                });
                                self.responseMessage = data.message || "";
                                self.responseName = data.name || "";
                                self.dispatchEvent(userDetailsChangeEvent);
                            })
                                .catch((err) => {
                                self.responseMessage = err.message || "";
                                self.responseName = err.name || "";
                            })
                                .finally(() => {
                                self.render();
                            });
                        }
                    })}
            `;
                }
            }
        }
    }
    get data() {
        return {
            hasDotRequirement: userDetailsService.userDetails.dots > 100,
            isLoading: this.isLoading,
            isReloading: this.isReloading,
            hasError: this.hasError,
            message: this.message,
            limit: this.limit,
            bits: this.bits,
            hasResponseMessage: !!this.responseMessage,
            responseMessage: this.responseMessage,
            responseName: this.responseName,
        };
    }
    render() {
        render(this.template(this.data), this);
    }
    connectedCallback() {
        // need to get bits on the subscribe callback
        userDetailsService.subscribe(() => {
            PmChooseBit.getBits(this, this.limit);
            userDetailsService.unsubscribe(this.instanceId);
        }, this.instanceId);
        this.render();
    }
});
