import { html, render } from "lit-html";
import userDetailsService from "../site/user-details.service";
import { hasUserCookie } from "../site/cookies";

const baseUrl = `${window.location.protocol}//${window.location.host}`;

interface TemplateData {
  anonymousLoginLink: string;
  isGeneratingLoginLink: boolean;
  hasBitLink: boolean;
  generateBitLink: Function;
  hasEmailConfigured: boolean;
}

const tag = "pm-account";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmAccount extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    private bitLink: string = "";
    private isGeneratingLoginLink: boolean = false;
    private hasEmailConfigured: boolean = false;

    constructor() {
      super();
      this.instanceId = PmAccount._instanceId;
      this.hasEmailConfigured = !!this.attributes.getNamedItem(
        "email-configured"
      );
      userDetailsService.subscribe(this.render.bind(this), this.instanceId);
      this.render();
    }

    generateBitLink() {
      this.isGeneratingLoginLink = true;
      this.render();
      userDetailsService
        .generateAnonymousLogin()
        .then((data) => {
          this.bitLink = data.bit;
          userDetailsService.storeAnonymousLogin(data.bit);
        })
        .catch(() => {
          // ignore errors
        })
        .finally(() => {
          this.isGeneratingLoginLink = false;
          this.render();
        });
    }

    template(data: TemplateData) {
      return html`
        <div class="pm-account">
          ${hasUserCookie()
            ? html`
                ${data.hasBitLink
                  ? html`
                      <p>
                        <strong class="u-textNoWrap">
                          Anonymous Login Link:
                        </strong>
                        <br />
                        <span>${data.anonymousLoginLink}</span>
                        <br />
                        <small>Copy the link or bookmark it.</small>
                      </p>
                    `
                  : html`
                      <button
                        class="Button"
                        @click=${data.generateBitLink}
                        ?disabled=${data.isGeneratingLoginLink}
                      >
                        Anonymous Login Link
                      </button>
                    `}
                <p>
                  <em
                    >Only logout if you have saved your anonymous login
                    link.</em
                  >
                </p>
                <pm-logout-link></pm-logout-link>
              `
            : data.hasEmailConfigured
            ? html`
                <p>
                  Existing players can reset their login link by e-mail:
                  <pm-login-by-email></pm-login-by-email>
                  <em
                    >Requires the player to register their e-mail with the site
                    first.</em
                  >
                </p>
              `
            : ""}
        </div>
      `;
    }

    get data(): TemplateData {
      return {
        anonymousLoginLink: `${baseUrl}${this.bitLink}/`,
        hasBitLink: !!this.bitLink,
        generateBitLink: this.generateBitLink.bind(this),
        isGeneratingLoginLink: this.isGeneratingLoginLink,
        hasEmailConfigured: this.hasEmailConfigured,
      };
    }

    render() {
      render(this.template(this.data), this);
    }
  }
);
