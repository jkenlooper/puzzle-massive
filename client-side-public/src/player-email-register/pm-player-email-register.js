import { html, render } from "lit";
import FetchService from "../site/fetch.service";
import userDetailsService from "../site/user-details.service";
import "./player-email-register.css";
const tag = "pm-player-email-register";
let lastInstanceId = 0;
customElements.define(
  tag,
  class PmPlayerEmailRegister extends HTMLElement {
    constructor() {
      super();
      this.responseMessage = "";
      this.responseName = "";
      this.instanceId = PmPlayerEmailRegister._instanceId;
      userDetailsService.subscribe(this.render.bind(this), this.instanceId);
    }
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }
    submit(form) {
      const fetchService = new FetchService(form.action);
      const data = new FormData(form);
      if (!form.reportValidity()) {
        this.responseMessage = "Form is not valid.";
        this.responseName = "invalid";
        this.render();
      } else {
        fetchService
          .postForm(data)
          .then((response) => {
            this.responseMessage = response.message;
            this.responseName = response.name;
          })
          .catch((err) => {
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
    template(data) {
      return html`
        <form
          class="pm-PlayerEmailRegister"
          id="email-register-form"
          method="POST"
          action="/newapi/player-email-register/"
        >
          ${data.isShareduser
            ? html`
                <p>
                  This player account is currently a shared user account with
                  other users on the same network. The email address for the
                  shared user account is not shown.
                </p>
              `
            : ""}
          ${data.email
            ? html`
                <p>
                  The e-mail address (${data.email}) has
                  ${data.emailVerifed
                    ? html` been verified. `
                    : html`
                        <strong>not</strong> been verified. Please check your
                        e-mail for a verification link.
                      `}
                </p>
              `
            : ""}
          <label for="player-email-input"> E-mail </label>
          <input
            id="player-email-input"
            type="email"
            maxlength="254"
            name="email"
            value=${data.email}
          />
          <button
            class="Button"
            form="email-register-form"
            @click=${data.submitEmailHandler}
          >
            Register E-mail
          </button>

          ${data.responseMessage
            ? html`
                <pm-response-message
                  name=${data.responseName}
                  message=${data.responseMessage}
                ></pm-response-message>
              `
            : ""}
        </form>
      `;
    }
    get data() {
      return {
        email: userDetailsService.userDetails.email,
        emailVerifed: userDetailsService.userDetails.emailVerified,
        isShareduser: userDetailsService.userDetails.isShareduser,
        submitEmailHandler: {
          handleEvent: (e) => {
            // Prevent the form from submitting
            e.preventDefault();
            const formEl = e.currentTarget.form;
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
