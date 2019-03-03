import * as Modernizr from "modernizr";
import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import { styleMap } from "lit-html/directives/style-map.js";

import hashColorService from "./hash-color.service";
import "./hash-color.css";

interface TemplateData {
  hasInputtypesColor: boolean;
  backgroundColor: string;
  vertical: boolean;
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
    private vertical: boolean = false;
    private defaultBackgroundColor: string;

    constructor() {
      super();
      this.instanceId = PmHashColor._instanceId;

      this.vertical = !!this.attributes.getNamedItem("vertical");

      const backgroundColor = this.attributes.getNamedItem("background-color");
      this.defaultBackgroundColor = backgroundColor
        ? backgroundColor.value
        : "#404";

      hashColorService.subscribe(this.render.bind(this), this.instanceId);
      this.render();
    }

    template(data: TemplateData) {
      return html`
        <span
          class=${classMap({
            "pm-HashColor": true,
            "pm-HashColor--vertical": data.vertical,
          })}
          style=${styleMap({ "background-color": data.backgroundColor })}
        >
          <label for="hash-color-background-color">
            <svg class="pm-Puzzlepage-icon">
              <use xlink:href="#paint-can-sprite" />
            </svg>
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
        vertical: this.vertical,
        handleChange: this.handleChange.bind(this),
      };
    }

    render() {
      render(this.template(this.data), this);
    }
  }
);
