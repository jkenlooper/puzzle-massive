import { html, render } from "lit-html";

import FetchService from "../site/fetch.service";
import userDetailsService from "../site/user-details.service";
import "./player-name-register.css";

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

// TODO: Validate name to be unique before it is submitted

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
      return html`
        <form
          class="pm-PlayerNameRegister"
          id="player-name-register-form"
          method="POST"
          action="/newapi/player-name-register/"
        >
          <label for="player-name-input">
            Player Name
          </label>
          <input
            id="player-name-input"
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
                <pm-response-message
                  name=${data.responseName}
                  message=${data.responseMessage}
                ></pm-response-message>
              `
            : ""}
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
