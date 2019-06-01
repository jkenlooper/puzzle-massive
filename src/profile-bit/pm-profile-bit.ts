import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import { styleMap } from "lit-html/directives/style-map.js";

import userDetailsService from "../site/user-details.service";
import { colorForPlayer } from "../player-bit/player-bit-img.service";

import "./profile-bit.css";

interface TemplateData {
  isExpired: boolean;
  canClaimUser: boolean;
  isProcessingClaimUser: boolean;
  claimUserHandler: any;
  profileLink: string;
  iconSrc: string;
  iconAlt: string;
  bitBackground: string;
  hasIcon: boolean;
  userId: number;
  showScore: boolean;
  score: number;
  showDots: boolean;
  dots: number;
  anonymousLoginLink: string | boolean;
}

const tag = "pm-profile-bit";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmProfileBit extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private player_profile_url: string;
    private instanceId: string;
    private showScore: boolean;
    private showDots: boolean;
    private mediaPath: string;
    private isProcessingClaimUser: boolean = false;

    constructor() {
      super();
      this.instanceId = PmProfileBit._instanceId;

      const mediaPath = this.attributes.getNamedItem("media-path");
      this.mediaPath = mediaPath ? mediaPath.value : "";

      // Set the attribute values
      const player_profile_url = this.attributes.getNamedItem(
        "player-profile-url"
      );
      this.player_profile_url = player_profile_url
        ? player_profile_url.value
        : "";

      this.showScore = this.hasAttribute("score");
      this.showDots = this.hasAttribute("dots");

      userDetailsService.subscribe(this.render.bind(this), this.instanceId);
    }

    template(data: TemplateData) {
      return html`
        <div
          class=${classMap({
            "pm-profileBit": true,
            isExpired: data.isExpired,
          })}
        >
          ${data.anonymousLoginLink
            ? html`
                <a href=${data.anonymousLoginLink}>Login again</a>
                <br />
                <pm-logout-link></pm-logout-link>
              `
            : html`
                <a class="pm-profileBit-link" href=${data.profileLink}>
                  ${data.hasIcon
                    ? html`
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
                    : html`
                        <span
                          class="hasNoBit pm-PlayerBit"
                          style=${`--pm-PlayerBit-color:${colorForPlayer(
                            data.userId
                          )}`}
                          >${data.userId.toString(36)}</span
                        >
                      `}
                </a>
              `}
          <strong class="u-textCenter u-block">
            ${data.iconAlt.substr(0, 26)}<!-- TODO: use player assigned name -->
          </strong>
        </div>
        ${data.showScore
          ? html`
              <div>Score <b>${data.score}</b></div>
            `
          : html``}
        ${data.showDots
          ? html`
              <div>Dots <b>${data.dots}</b></div>
            `
          : html``}
        ${data.canClaimUser
          ? html`
              ${data.isProcessingClaimUser
                ? html`
                    ...
                  `
                : html`
                    <button @click=${data.claimUserHandler}>claim</button>
                  `}
            `
          : html``}
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

    get data(): TemplateData {
      return {
        isExpired: !!userDetailsService.userDetails.bit_expired,
        canClaimUser: !!userDetailsService.userDetails.can_claim_user,
        isProcessingClaimUser: this.isProcessingClaimUser,
        claimUserHandler: {
          handleEvent: this.handleClickClaimUser.bind(this),
          capture: true,
        },
        profileLink: `${this.player_profile_url}${
          userDetailsService.userDetails.login
        }/`,
        iconAlt: "bit icon " + userDetailsService.userDetails.icon || "",
        hasIcon: !!userDetailsService.userDetails.icon,
        iconSrc: `${this.mediaPath}bit-icons/64-${
          userDetailsService.userDetails.icon
        }.png`,
        bitBackground: userDetailsService.userDetails.bitBackground,
        userId: userDetailsService.userDetails.id || 0,
        showScore: this.showScore,
        score: userDetailsService.userDetails.score,
        showDots: this.showDots,
        dots: userDetailsService.userDetails.dots,
        anonymousLoginLink: userDetailsService.userDetails.loginAgain
          ? userDetailsService.anonymousLoginLink
          : false,
      };
    }

    render() {
      //console.log("render", this.instanceId, this.data);
      render(this.template(this.data), this);
    }

    connectedCallback() {
      //console.log("connectedCallback");
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      userDetailsService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
  }
);
