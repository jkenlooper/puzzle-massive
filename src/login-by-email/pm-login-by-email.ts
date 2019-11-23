import { html, render } from "lit-html";

import FetchService from "../site/fetch.service";

interface TemplateData {
  submitHandler: any; // event listener object
  responseMessage: string;
  responseName: string;
}
interface SubmitFormResponse {
  message: string;
  name: string;
}

const tag = "pm-login-by-email";

customElements.define(
  tag,
  class PmLoginByEmail extends HTMLElement {
    private responseMessage: string = "";
    private responseName: string = "";

    constructor() {
      super();
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
            this.render();
          });
      }
    }

    template(data: TemplateData) {
      return html`
        <form
          class="pm-LoginByEmail"
          id="login-by-email-form"
          method="POST"
          action="/newapi/player-email-login-reset/"
        >
          <label for="login-by-email-input">
            E-mail
          </label>
          <input
            id="login-by-email-input"
            type="email"
            maxlength="254"
            name="email"
            value=""
          />

          <button form="login-by-email-form" @click=${data.submitHandler}>
            Login by E-mail
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
        submitHandler: {
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
      this.render();
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
  }
);
