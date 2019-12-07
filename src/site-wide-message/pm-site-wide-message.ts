import { html, render } from "lit-html";

import "./site-wide-message.css";

interface TemplateData {
  hasMessage: boolean;
  message: string;
}

const tag = "pm-site-wide-message";

customElements.define(
  tag,
  class PmSiteWideMessage extends HTMLElement {
    // TODO: get message from /newapi/message/
    private message = "This is a test.";
    constructor() {
      super();
    }

    template(data: TemplateData) {
      if (!data.hasMessage) {
        return "";
      }
      return html`
        <p class="pm-SiteWideMessage">
          ${data.message}
        </p>
      `;
    }

    get data(): TemplateData {
      return {
        hasMessage: !!this.message,
        message: this.message,
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
  }
);
