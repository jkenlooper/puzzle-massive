import { html, render } from "lit-html";

import FetchService from "../site/fetch.service";
import userDetailsService from "../site/user-details.service";
import "./player-email-register.css";

interface TemplateData {
  email: string;
  emailVerifed: boolean;
  submitEmailHandler: any; // event listener object
  responseMessage: string;
  responseName: string;
}
interface SubmitFormResponse {
  message: string;
  name: string;
}

const tag = "pm-player-email-register";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPlayerEmailRegister extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    private responseMessage: string = "";
    private responseName: string = "";

    constructor() {
      super();
      this.instanceId = PmPlayerEmailRegister._instanceId;
      userDetailsService.subscribe(this.render.bind(this), this.instanceId);
    }

    submit(form: HTMLFormElement) {
      const fetchService = new FetchService(form.action);
      const data = new FormData(form);
      if (!form.reportValidity()) {
        this.responseMessage = "Form is not valid.";
        this.responseName = "invalid";
        this.render();
      } else {
        fetchService
          .postForm<SubmitFormResponse>(data)
          .then((response) => {
            this.responseMessage = response.message;
            this.responseName = response.name;
          })
          .catch((err: any) => {
            if (err.message && err.name) {
              this.responseMessage = err.message;
              this.responseName = err.name;
            }
          })
          .finally(() => {
            const userDetailsChangeEvent = new Event("userDetailsChange", {
              bubbles: true,
            });
            this.dispatchEvent(userDetailsChangeEvent);
          });
      }
    }

    template(data: TemplateData) {
      return html`
        <form
          class="pm-PlayerEmailRegister"
          id="email-register-form"
          method="POST"
          action="/newapi/player-email-register/"
        >
          ${data.email
            ? html`
                <p>
                  The e-mail address (${data.email}) has
                  ${data.emailVerifed
                    ? html`
                        been verified.
                      `
                    : html`
                        <strong>not</strong> been verified. Please check your
                        e-mail for a verification link.
                      `}
                </p>
              `
            : ""}
          <label for="player-email-input">
            E-mail
          </label>
          <input
            id="player-email-input"
            type="email"
            maxlength="254"
            name="email"
            value=${data.email}
          />
          <button form="email-register-form" @click=${data.submitEmailHandler}>
            Register E-mail
          </button>

          ${data.responseMessage
            ? html`
                <p class="pm-PlayerEmailRegister-message">
                  ${data.responseMessage}<code class="u-block u-textRight"
                    >${data.responseName}</code
                  >
                </p>
              `
            : ""}
        </form>
      `;
    }

    get data(): TemplateData {
      return {
        email: userDetailsService.userDetails.email,
        emailVerifed: userDetailsService.userDetails.emailVerified,
        submitEmailHandler: {
          handleEvent: (e) => {
            // Prevent the form from submitting
            e.preventDefault();
            const formEl = <HTMLFormElement>e.currentTarget.form;
            this.submit(formEl);
          },
          capture: true,
        },
        responseMessage: this.responseMessage,
        responseName: this.responseName,
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
