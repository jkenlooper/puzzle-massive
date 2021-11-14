import { html, render } from "lit-html";

import FetchService from "../site/fetch.service";

const baseUrl = `${window.location.protocol}//${window.location.host}`;

interface TemplateData {
  token: string;
  submitHandler: any; // event listener object
  showResponseLink: boolean;
  anonymousLoginLink: string;
  responseMessage: string;
  responseName: string;
}
interface SubmitFormResponse {
  link: string;
  message: string;
  name: string;
}

const tag = "pm-reset-login-by-token";

customElements.define(
  tag,
  class PmResetLoginByToken extends HTMLElement {
    private token: string;
    private responseLink: string = "";
    private responseMessage: string = "";
    private responseName: string = "";

    constructor() {
      super();
      const tokenAttr = this.attributes.getNamedItem("token");
      this.token = tokenAttr ? tokenAttr.value : "";
    }

    submit(form: HTMLFormElement) {
      const fetchService = new FetchService(form.action);
      const data = new FormData(form);
      this.responseLink = "";
      if (!form.reportValidity()) {
        this.responseMessage = "Form is not valid.";
        this.responseName = "invalid";
        this.render();
      } else {
        fetchService
          .postForm<SubmitFormResponse>(data)
          .then((response) => {
            this.responseLink = response.link;
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
          class="pm-ResetLoginByToken"
          id="reset-login-by-token-form"
          method="POST"
          action="/newapi/generate-anonymous-login-by-token/"
        >
          ${!data.showResponseLink
            ? html`
                <p>
                  Click the button below to reset your login link.
                  <span class="u-block">
                    <input type="hidden" name="token" value=${data.token} />
                    <button
                      class="Button"
                      form="reset-login-by-token-form"
                      @click=${data.submitHandler}
                    >
                      Reset Login
                    </button>
                  </span>
                </p>
              `
            : ""}
          ${data.responseMessage
            ? html`
                <pm-response-message
                  name=${data.responseName}
                  link=${data.showResponseLink ? data.anonymousLoginLink : ""}
                  message=${data.responseMessage}
                ></pm-response-message>
              `
            : ""}
        </form>
      `;
    }

    get data(): TemplateData {
      return {
        token: this.token,
        submitHandler: {
          handleEvent: (e) => {
            // Prevent the form from submitting
            e.preventDefault();
            const formEl = <HTMLFormElement>e.currentTarget.form;
            this.submit(formEl);
          },
          capture: true,
        },
        showResponseLink: !!this.responseLink,
        anonymousLoginLink: `${baseUrl}${this.responseLink}/`,
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
