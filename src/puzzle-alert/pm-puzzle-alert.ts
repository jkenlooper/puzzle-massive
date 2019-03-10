import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";
import { classMap } from "lit-html/directives/class-map.js";

import "./puzzle-alert.css";

interface TemplateData {}

const tag = "pm-puzzle-alerts";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleAlerts extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;

    constructor() {
      super();
      this.instanceId = PmPuzzleAlerts._instanceId;
      this.render();
    }

    template(data: TemplateData) {
      return html``;
    }

    get data(): TemplateData {
      return {};
    }

    render() {
      render(this.template(this.data), this);
    }
  }
);
