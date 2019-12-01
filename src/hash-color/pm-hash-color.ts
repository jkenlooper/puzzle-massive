import * as Modernizr from "modernizr";
import { html, render } from "lit-html";

import hashColorService from "./hash-color.service";
import "./hash-color.css";

interface TemplateData {
  hasInputtypesColor: boolean;
  backgroundColor: string;
  handleChange: Function;
}

const tag = "pm-hash-color";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmHashColor extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    private defaultBackgroundColor: string;

    constructor() {
      super();
      this.instanceId = PmHashColor._instanceId;

      const backgroundColor = this.attributes.getNamedItem("background-color");
      this.defaultBackgroundColor = backgroundColor
        ? backgroundColor.value
        : "#404";

      hashColorService.subscribe(this.render.bind(this), this.instanceId);
    }

    template(data: TemplateData) {
      return html`
        <span class="pm-HashColor">
          <label for="hash-color-background-color">
            <pm-icon size="sm" class="pm-Puzzlepage-icon"
              >paint-can-sprite</pm-icon
            >
          </label>
          <span class="pm-HashColor-field">
            ${data.hasInputtypesColor
              ? html`
                  <input
                    type="color"
                    class="pm-HashColor-inputColor"
                    id="hash-color-background-color"
                    @input=${data.handleChange}
                    value=${data.backgroundColor}
                  />
                `
              : html`
                  <input
                    type="text"
                    class="pm-HashColor-inputText jscolor {hash:true}"
                    id="hash-color-background-color"
                    @change=${data.handleChange}
                    value=${data.backgroundColor}
                  />
                `}
          </span>
        </span>
      `;
    }

    handleChange(ev: any) {
      this.dispatchEvent(
        new CustomEvent("pm-hash-color-change", {
          bubbles: true,
          detail: ev.target.value.substr(1),
        })
      );
    }

    get data(): TemplateData {
      return {
        hasInputtypesColor: Modernizr.inputtypes.color,
        backgroundColor:
          hashColorService.backgroundColor || this.defaultBackgroundColor,
        handleChange: this.handleChange.bind(this),
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    connectedCallback() {
      this.render();
    }
  }
);
