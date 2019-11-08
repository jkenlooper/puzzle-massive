import { html, render } from "lit-html";

import FetchService from "../site/fetch.service";
import userDetailsService from "../site/user-details.service";
//import { playerNameRegisterService } from "./player-name-register.service";

interface TemplateData {
  username: string;
  usernameApproved: boolean;
  usernameRejected: boolean;
  submitNameHandler: any; // event listener object
  responseMessage: string;
  responseName: string;
}
interface SubmitFormResponse {
  message: string;
  name: string;
}

const tag = "pm-player-name-register";
let lastInstanceId = 0;

// TODO:
// Validate name to be unique
// Should show message when it is waiting to be approved
// Show errors if name is rejected

customElements.define(
  tag,
  class PmPlayerNameRegister extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    private responseMessage: string = "";
    private responseName: string = "";

    constructor() {
      super();
      this.instanceId = PmPlayerNameRegister._instanceId;
      userDetailsService.subscribe(this.render.bind(this), this.instanceId);
    }

    submit(form: HTMLFormElement) {
      const fetchService = new FetchService(form.action);
      const data = new FormData(form);
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

    template(data: TemplateData) {
      // forminput.setCustomValidity(...)
      // TODO: submit button is disabled if name not valid
      //<input type="submit" value="Submit Name" />
      return html`
        <form
          id="player-name-register-form"
          method="POST"
          action="/newapi/player-name-register/"
        >
          <p>
            The player name is <b>not</b> used when logging into your account
            and can be anything that you would like. Names are limited to 26
            characters and must be unique from other player names.
          </p>
          <label for="name">
            Player Name
          </label>
          <input
            id="player-name-input"
            required
            type="text"
            maxlength="26"
            name="name"
            value=${data.username}
            placeholder="Hedgewig von Bitty"
          />
          <button
            form="player-name-register-form"
            @click=${data.submitNameHandler}
          >
            Submit Name
          </button>

          ${data.responseMessage
            ? html`
                <p>
                  ${data.responseMessage}<br /><code class="u-block u-textRight"
                    >${data.responseName}</code
                  >
                </p>
              `
            : ""}

          <p>
            The name will be reviewed within a couple of days after submitting.
            Names that are rejected will be shown as crossed out. Accepted names
            will be shown next to your bit icon in various places on the site.
            Thank you for your patience.
          </p>
        </form>
      `;
    }

    get data(): TemplateData {
      return {
        username: userDetailsService.userDetails.name,
        usernameApproved: userDetailsService.userDetails.nameApproved,
        usernameRejected: userDetailsService.userDetails.nameRejected,
        submitNameHandler: {
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
