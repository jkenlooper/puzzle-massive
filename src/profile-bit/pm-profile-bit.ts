import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";

import userDetailsService from "../site/user-details.service";

import "./profile-bit.css";

interface TemplateData {
  isExpired: boolean;
  loginLink: string;
  iconSrc: string;
  icon: string;
  hasIcon: boolean;
  userId: number;
  showScore: boolean;
  score: number;
  showDots: boolean;
  dots: number;
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
          <a class="pm-profileBit-link" href=${data.loginLink}>
            ${data.hasIcon
              ? html`
                  <img
                    src=${data.iconSrc}
                    width="64"
                    height="64"
                    alt=${data.icon}
                  />
                `
              : html`
                  <span>${data.userId}</span>
                `}
          </a>
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
      `;
    }

    get data(): TemplateData {
      return {
        isExpired: !!userDetailsService.userDetails.bit_expired,
        loginLink: `${this.player_profile_url}${
          userDetailsService.userDetails.login
        }/`,
        icon: userDetailsService.userDetails.icon || "",
        hasIcon: !!userDetailsService.userDetails.icon,
        iconSrc: `${this.mediaPath}bit-icons/64-${
          userDetailsService.userDetails.icon
        }.png`,
        userId: userDetailsService.userDetails.id || 0,
        showScore: this.showScore,
        score: userDetailsService.userDetails.score,
        showDots: this.showDots,
        dots: userDetailsService.userDetails.dots,
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
    /*
    attributeChangedCallback(
      name: string,
      _oldValue: string | null,
      _newValue: string | null
    ) {
      // Need to only render initially if the player has enough dots.
      if (name === "dots") {
        if (_newValue) {
          this.render();
        }
      }
    }
       */
  }
);
