import { html, render } from "lit-html";
import userDetailsService from "../site/user-details.service";
import { areCookiesEnabled, hasUserCookie } from "../site/cookies";

const baseUrl = `${window.location.protocol}//${window.location.host}`;

interface TemplateData {
  anonymousLoginLink: string;
  isGeneratingLoginLink: boolean;
  hasBitLink: boolean;
  generateBitLink: Function;
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

    constructor() {
      super();
      this.instanceId = PmAccount._instanceId;
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
      if (!(areCookiesEnabled() && hasUserCookie())) {
        return html``;
      }
      return html`
        <div>
          <h2>Account Management</h2>
          <div class="pm-Profilepage-account">
            <div class="pm-Profilepage-accountMessage">
              <p>
                You are currently logged in anonymously for this browser. There
                is no login or password needed in order to play as your bit
                icon. This is based on a stored cookie on this browser and will
                eventually expire. In order to login again when your cookie
                expires you'll need to generate an
                <em>Anonymous Login Link</em> which you should save as a
                bookmark. Following that link will log you back in.
              </p>
              <p>
                Click the <em>Anonymous Login Link</em> button to generate a new
                login link. Save this link as a bookmark and use it log back in.
              </p>
              <p>
                Note that all new players get a randomly assigned bit icon based
                on their IP address. After a new player has joined enough pieces
                they may change their bit icon and thus save a cookie. Then the
                below anonymous login link will apply.
              </p>
            </div>
            <div class="pm-Profilepage-accountActions">
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
                      @click=${data.generateBitLink}
                      ?disabled=${data.isGeneratingLoginLink}
                    >
                      Anonymous Login Link
                    </button>
                  `}
              <p>
                <em
                  >Only logout if you have saved your anonymous login link.</em
                >
              </p>
              <a href="/newapi/user-logout/">Logout</a>
            </div>
          </div>
        </div>
      `;
    }

    get data(): TemplateData {
      return {
        anonymousLoginLink: `${baseUrl}${this.bitLink}/`,
        hasBitLink: !!this.bitLink,
        generateBitLink: this.generateBitLink.bind(this),
        isGeneratingLoginLink: this.isGeneratingLoginLink,
      };
    }

    render() {
      render(this.template(this.data), this);
    }
  }
);
