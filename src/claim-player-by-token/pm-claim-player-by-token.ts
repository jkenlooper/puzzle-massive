import { html, render } from "lit-html";

import FetchService from "../site/fetch.service";

interface TemplateData {
  token: string;
  submitHandler: any; // event listener object
  responseMessage: string;
  responseName: string;
}
interface SubmitFormResponse {
  message: string;
  name: string;
}

const tag = "pm-claim-player-by-token";

customElements.define(
  tag,
  class PmClaimPlayerByToken extends HTMLElement {
    private token: string;
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
          class="pm-ClaimPlayerByToken"
          id="claim-player-by-token-form"
          method="POST"
          action="/newapi/claim-user-by-token/"
        >
          <input type="hidden" name="token" value=${data.token} />
          <button
            class="Button"
            form="claim-player-by-token-form"
            @click=${data.submitHandler}
          >
            Verify Player
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
