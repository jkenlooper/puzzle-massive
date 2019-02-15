/* global HTMLElement, customElements */
import { html, render } from "lit-html";

interface TemplateData {
  name: string;
  count: string;
}

customElements.define(
  "pm-test-no-shadow",
  class PmTestNoShadow extends HTMLElement {
    static get observedAttributes() {
      return ["name", "count"];
    }
    constructor() {
      super();
      this.render();
    }

    template(data: TemplateData) {
      return html`
        <div>
          <div>no shadow</div>
          <div>${data.name} can count to ${data.count}</div>
        </div>
      `;
    }

    get data(): TemplateData {
      return PmTestNoShadow.observedAttributes.reduce(
        (data: any, item: string) => {
          const attr = this.attributes.getNamedItem(item);
          data[item] = attr ? attr.value : null;
          return data;
        },
        {}
      );
    }

    render() {
      //render(this.template(this.data), this);
      console.log(this.data);
      render(this.template(this.data), this);
    }

    connectedCallback() {
      console.log("connectedCallback");
    }
    disconnectedCallback() {
      console.log("disconnectedCallback");
    }
    adoptedCallback() {
      console.log("adoptedCallback");
    }
    attributeChangedCallback(name: String, oldValue: String, newValue: String) {
      console.log("attributeChangedCallback", name, oldValue, newValue);
      this.render();
    }
  }
);
