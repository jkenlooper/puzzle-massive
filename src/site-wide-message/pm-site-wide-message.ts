import { html, render } from "lit-html";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";

import FetchService from "../site/fetch.service";

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
    private message = "";
    constructor() {
      super();
      const messageService = new FetchService("/newapi/message/");
      messageService
        .getText()
        .then((message) => {
          this.message = message;
        })
        .finally(() => {
          this.render();
        });
    }

    template(data: TemplateData) {
      if (!data.hasMessage) {
        return "";
      }
      return html`
        <p class="pm-SiteWideMessage">
          ${unsafeHTML(data.message)}
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
