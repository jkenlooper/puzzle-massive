import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import { styleMap } from "lit-html/directives/style-map.js";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";
import userDetailsService from "../site/user-details.service";
import { colorForPlayer } from "../player-bit/player-bit-img.service";
import "./profile-bit.css";
const tag = "pm-profile-bit";
let lastInstanceId = 0;
customElements.define(tag, class PmProfileBit extends HTMLElement {
    constructor() {
        super();
        this.isProcessingClaimUser = false;
        this.iconAttribution = "";
        this.instanceId = PmProfileBit._instanceId;
        const mediaPath = this.attributes.getNamedItem("media-path");
        this.mediaPath = mediaPath ? mediaPath.value : "";
        // Set the attribute values
        const player_profile_url = this.attributes.getNamedItem("player-profile-url");
        this.player_profile_url = player_profile_url
            ? player_profile_url.value
            : "";
        this.showClaimButton = this.hasAttribute("claim");
        this.showScore = this.hasAttribute("score");
        this.showDots = this.hasAttribute("dots");
        this.showName = this.hasAttribute("name");
        this.showAttribution = this.hasAttribute("attribution");
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    template(data) {
        return html `
        <div
          class=${classMap({
            "pm-profileBit": true,
            isExpired: data.isExpired,
        })}
        >
          ${data.anonymousLoginLink
            ? html `
                <a href=${data.anonymousLoginLink}>Login again</a>
                <br />
                <pm-logout-link></pm-logout-link>
              `
            : html `
                <a class="pm-profileBit-link" href=${data.profileLink}>
                  ${data.hasIcon
                ? html `
                        <span
                          style=${styleMap({
                    "--pm-profileBit-color": data.bitBackground,
                })}
                          class="pm-profileBit-background"
                        >
                          <img
                            class="pm-profileBit-img"
                            src=${data.iconSrc}
                            width="64"
                            height="64"
                            alt=${data.iconAlt}
                          />
                        </span>
                      `
                : html `
                        <span
                          class="hasNoBit pm-PlayerBit"
                          style=${`--pm-PlayerBit-color:${colorForPlayer(data.userId)}`}
                          ><span class="pm-PlayerBit-id"
                            >${data.userId.toString(36)}</span
                          ></span
                        >
                      `}
                </a>
              `}
          ${data.username && data.showName
            ? data.usernameRejected
                ? html ` <s class="u-textCenter u-block"> ${data.username} </s> `
                : data.usernameApproved
                    ? html `
                  <strong class="u-textCenter u-block">
                    ${data.username}
                  </strong>
                `
                    : html `
                  <span class="u-textCenter u-block"> ${data.username} </span>
                `
            : ""}
          ${data.showScore
            ? html ` <div>Score <b>${data.score}</b></div> `
            : html ``}
          ${data.showDots
            ? html ` <div>Dots <b>${data.dots}</b></div> `
            : html ``}
          ${data.canClaimUser && data.showClaimButton
            ? html `
                ${data.isProcessingClaimUser
                ? html ` ... `
                : html `
                      <div class="u-marginTopSm">
                        <button
                          class="Button Button--accent"
                          @click=${data.claimUserHandler}
                        >
                          Claim
                        </button>
                      </div>
                    `}
              `
            : html ``}
          ${data.showAttribution
            ? html `<div class="u-textRight pm-profileBit-attribution">
                ${unsafeHTML(data.iconAttribution)}
              </div>`
            : ""}
        </div>
      `;
    }
    handleClickClaimUser() {
        this.isProcessingClaimUser = true;
        this.render();
        fetch("/newapi/claim-user/", {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
            },
        }).finally(() => {
            this.isProcessingClaimUser = false;
            const userDetailsChangeEvent = new Event("userDetailsChange", {
                bubbles: true,
            });
            this.dispatchEvent(userDetailsChangeEvent);
        });
    }
    get data() {
        return {
            isExpired: !!userDetailsService.userDetails.bit_expired,
            canClaimUser: !!userDetailsService.userDetails.can_claim_user,
            showClaimButton: this.showClaimButton,
            isProcessingClaimUser: this.isProcessingClaimUser,
            claimUserHandler: {
                handleEvent: this.handleClickClaimUser.bind(this),
                capture: true,
            },
            profileLink: this.player_profile_url,
            iconAlt: "bit icon " + userDetailsService.userDetails.icon || "",
            hasIcon: !!userDetailsService.userDetails.icon,
            iconSrc: `${this.mediaPath}bit-icons/64-${userDetailsService.userDetails.icon}.png`,
            bitBackground: userDetailsService.userDetails.bitBackground,
            iconAttribution: this.iconAttribution,
            showAttribution: this.showAttribution,
            userId: userDetailsService.userDetails.id || 0,
            username: userDetailsService.userDetails.name,
            usernameApproved: userDetailsService.userDetails.nameApproved,
            usernameRejected: userDetailsService.userDetails.nameRejected,
            showName: this.showName,
            showScore: this.showScore,
            score: userDetailsService.userDetails.score,
            showDots: this.showDots,
            dots: userDetailsService.userDetails.dots,
            anonymousLoginLink: userDetailsService.userDetails.loginAgain
                ? userDetailsService.anonymousLoginLink
                : false,
        };
    }
    getAttribution() {
        if (this.deferGetAttribution) {
            return Promise.resolve(this.deferGetAttribution);
        }
        else {
            this.deferGetAttribution = fetch(`/chill/site/bit-icons-attribution/${userDetailsService.userDetails.icon}/`, {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "text/html",
                },
            })
                .then((response) => {
                if (response.ok) {
                    return response.text();
                }
                else {
                    return "";
                }
            })
                .catch(() => {
                return "";
            })
                .finally(() => {
                this.deferGetAttribution = undefined;
            });
            return this.deferGetAttribution;
        }
    }
    render() {
        //console.log("render", this.instanceId, this.data);
        this.iconAttribution = "";
        render(this.template(this.data), this);
        if (userDetailsService.userDetails.icon && this.showAttribution) {
            this.getAttribution().then((text) => {
                this.iconAttribution = text;
                render(this.template(this.data), this);
            });
        }
    }
    connectedCallback() {
        //console.log("connectedCallback");
        userDetailsService.subscribe(this.render.bind(this), this.instanceId);
    }
    disconnectedCallback() {
        //console.log("disconnectedCallback", this.instanceId);
        userDetailsService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
        //console.log("adoptedCallback");
    }
});
