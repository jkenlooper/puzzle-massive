import { html, render } from "lit-html";
//import { classMap } from "lit-html/directives/class-map.js";
import userDetailsService from "../site/user-details.service";

interface TemplateData {
  isReady: boolean;
  createPuzzleInstanceHref: string;
  hasUserPuzzleSlots: boolean;
  hasAvailableUserPuzzleSlot: boolean;
  linkText: string;
  view: string;
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
    view: string = ""; // buttons, message

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

      const viewAttr = this.attributes.getNamedItem("view");
      if (!viewAttr || !viewAttr.value) {
        this.view = "";
      } else {
        this.view = viewAttr.value;
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
      if (!data.isReady) {
        return html``;
      }
      let renderedView = html``;
      switch (data.view) {
        case "buttons":
          if (data.hasUserPuzzleSlots) {
            renderedView = html`
              ${!data.hasAvailableUserPuzzleSlot
                ? html`
                    <span class="Button is-disabled">${data.linkText}</span>
                  `
                : html`
                    <a class="Button" href=${data.createPuzzleInstanceHref}
                      >${data.linkText}</a
                    >
                  `}
            `;
          } else {
            renderedView = html``;
          }
          break;
        case "message":
          if (data.hasUserPuzzleSlots) {
            renderedView = html`
              ${!data.hasAvailableUserPuzzleSlot
                ? html`<p>
                    All your Puzzle Instance Slots have been filled.
                    <a href="/d/buy-stuff/">Buy another Puzzle Instance Slot</a>
                    or delete one of your Puzzle Instances to free up a slot.
                  </p>`
                : html``}
            `;
          } else {
            renderedView = html`<p>
              Create your own puzzle from this image. Buy a
              <a href="/d/buy-stuff/">Puzzle Instance Slot</a>.
            </p>`;
          }
          break;
        default:
          renderedView = html``;
      }
      return renderedView;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        hasUserPuzzleSlots: this.hasUserPuzzleSlots,
        hasAvailableUserPuzzleSlot: this.hasAvailableUserPuzzleSlot,
        createPuzzleInstanceHref: this.createPuzzleInstanceHref,
        linkText: "New Puzzle Instance",
        view: this.view,
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
