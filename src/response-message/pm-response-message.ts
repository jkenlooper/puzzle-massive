import { html, render } from "lit-html";

import "./response-message.css";

interface TemplateData {
  showLink: boolean;
  link: string;
  message: string;
  name: string;
}

const tag = "pm-response-message";

customElements.define(
  tag,
  class PmResponseMessage extends HTMLElement {
    static get observedAttributes() {
      return ["link", "message", "name"];
    }
    private link = "";
    private message = "";
    private name = "";
    constructor() {
      super();
    }

    template(data: TemplateData) {
      return html`
        <p class="pm-ResponseMessage">
          ${data.showLink
            ? html`
                <strong class="u-block">
                  <a href=${data.link}>${data.link}</a>
                </strong>
              `
            : ""}
          ${data.message}<code class="u-block u-textRight">${data.name}</code>
        </p>
      `;
    }

    get data(): TemplateData {
      return {
        showLink: !!this.link,
        link: this.link,
        message: this.message,
        name: this.name,
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    connectedCallback() {
      this.render();
    }
    disconnectedCallback() {}
    adoptedCallback() {}
    attributeChangedCallback(name, oldValue, newValue) {
      if (oldValue !== newValue) {
        this[name] = newValue;
        this.render();
      }
    }
  }
);
