import { html, render } from "lit-html";
//import { classMap } from "lit-html/directives/class-map.js";
import userDetailsService from "../site/user-details.service";

interface TemplateData {
  isReady: boolean;
  createPuzzleInstanceHref: string;
  hasUserPuzzleSlots: boolean;
  hasAvailableUserPuzzleSlot: boolean;
  linkText: string;
}

const tag = "pm-player-create-puzzle-instance-link";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPlayerCreatePuzzleInstanceLink extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    createPuzzleInstanceHref: string = "";
    isReady: boolean = false;
    hasUserPuzzleSlots: boolean = false;
    hasAvailableUserPuzzleSlot: boolean = false;

    constructor() {
      super();
      this.instanceId = PmPlayerCreatePuzzleInstanceLink._instanceId;

      // Set the attribute values
      const createPuzzleInstanceHref = this.attributes.getNamedItem(
        "create-puzzle-instance-href"
      );
      if (!createPuzzleInstanceHref || !createPuzzleInstanceHref.value) {
        throw new Error(
          "no create-puzzle-instance-href attribute has been set"
        );
      } else {
        this.createPuzzleInstanceHref = createPuzzleInstanceHref.value;
      }

      userDetailsService.subscribe(this._setData.bind(this), this.instanceId);
    }

    _setData() {
      this.hasUserPuzzleSlots =
        userDetailsService.userDetails.hasUserPuzzleSlots;
      this.hasAvailableUserPuzzleSlot =
        userDetailsService.userDetails.hasAvailableUserPuzzleSlot;

      this.isReady = true;
      this.render();
    }

    template(data: TemplateData) {
      if (!data.isReady || !data.hasUserPuzzleSlots) {
        return html``;
      }
      if (!data.hasAvailableUserPuzzleSlot) {
        return html`
          <span>${data.linkText}</span>
        `;
      }
      return html`
        <div class="u-block u-textRight">
          ${!data.hasAvailableUserPuzzleSlot
            ? html`
                <span>Create New Puzzle Instance</span>
              `
            : html`
                <a
                  class="u-block u-textRight"
                  href=${data.createPuzzleInstanceHref}
                  >${data.linkText}</a
                >
              `}
        </div>
      `;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        hasUserPuzzleSlots: this.hasUserPuzzleSlots,
        hasAvailableUserPuzzleSlot: this.hasAvailableUserPuzzleSlot,
        createPuzzleInstanceHref: this.createPuzzleInstanceHref,
        linkText: "Create New Puzzle Instance",
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    disconnectedCallback() {
      userDetailsService.unsubscribe(this.instanceId);
    }
  }
);
