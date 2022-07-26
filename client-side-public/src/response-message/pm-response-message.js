import { html, render } from "lit";
import "./response-message.css";
const tag = "pm-response-message";
customElements.define(
  tag,
  class PmResponseMessage extends HTMLElement {
    constructor() {
      super();
      this.link = "";
      this.message = "";
      this.name = "";
    }
    static get observedAttributes() {
      return ["link", "message", "name"];
    }
    template(data) {
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
    get data() {
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
