import { html, render } from "lit-html";
import userDetailsService from "../site/user-details.service";

interface TemplateData {
  handleClick: (ev: Event) => void;
}

const tag = "pm-logout-link";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmLogoutLink extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;

    constructor() {
      super();
      this.instanceId = PmLogoutLink._instanceId;
      userDetailsService.subscribe(this.render.bind(this), this.instanceId);
    }

    template(data: TemplateData) {
      return html`
        <a @click=${data.handleClick} href="/newapi/user-logout/">
          <pm-icon>exit</pm-icon>
          Logout</a
        >
      `;
    }

    get data(): TemplateData {
      return {
        handleClick: this.handleClick.bind(this),
      };
    }

    handleClick() {
      userDetailsService.forgetAnonymousLogin();
    }

    render() {
      //console.log("render", this.instanceId, this.data);
      render(this.template(this.data), this);
    }

    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      userDetailsService.unsubscribe(this.instanceId);
    }
  }
);
