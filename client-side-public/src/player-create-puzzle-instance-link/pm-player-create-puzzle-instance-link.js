import { html, render } from "lit-html";
//import { classMap } from "lit-html/directives/class-map.js";
import userDetailsService from "../site/user-details.service";
const tag = "pm-player-create-puzzle-instance-link";
let lastInstanceId = 0;
customElements.define(tag, class PmPlayerCreatePuzzleInstanceLink extends HTMLElement {
    constructor() {
        super();
        this.createPuzzleInstanceHref = "";
        this.isReady = false;
        this.hasUserPuzzleSlots = false;
        this.hasAvailableUserPuzzleSlot = false;
        this.view = ""; // buttons, message
        this.instanceId = PmPlayerCreatePuzzleInstanceLink._instanceId;
        // Set the attribute values
        const createPuzzleInstanceHref = this.attributes.getNamedItem("create-puzzle-instance-href");
        if (!createPuzzleInstanceHref || !createPuzzleInstanceHref.value) {
            throw new Error("no create-puzzle-instance-href attribute has been set");
        }
        else {
            this.createPuzzleInstanceHref = createPuzzleInstanceHref.value;
        }
        const viewAttr = this.attributes.getNamedItem("view");
        if (!viewAttr || !viewAttr.value) {
            this.view = "";
        }
        else {
            this.view = viewAttr.value;
        }
        userDetailsService.subscribe(this._setData.bind(this), this.instanceId);
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    _setData() {
        this.hasUserPuzzleSlots =
            userDetailsService.userDetails.hasUserPuzzleSlots;
        this.hasAvailableUserPuzzleSlot =
            userDetailsService.userDetails.hasAvailableUserPuzzleSlot;
        this.isReady = true;
        this.render();
    }
    template(data) {
        if (!data.isReady) {
            return html ``;
        }
        let renderedView = html ``;
        switch (data.view) {
            case "buttons":
                if (data.hasUserPuzzleSlots) {
                    renderedView = html `
              ${!data.hasAvailableUserPuzzleSlot
                        ? html `
                    <span class="Button is-disabled">${data.linkText}</span>
                  `
                        : html `
                    <a class="Button" href=${data.createPuzzleInstanceHref}
                      >${data.linkText}</a
                    >
                  `}
            `;
                }
                else {
                    renderedView = html ``;
                }
                break;
            case "message":
                if (data.hasUserPuzzleSlots) {
                    renderedView = html `
              ${!data.hasAvailableUserPuzzleSlot
                        ? html `<p>
                    All your Puzzle Instance Slots have been filled. Delete one
                    of your Puzzle Instances to free up a slot.
                  </p>`
                        : html ``}
            `;
                }
                else {
                    /* Nothing. Could advertise to the player to buy stuff like a puzzle
                     * instance slot, but that was a bit pushy.
                     */
                }
                break;
            default:
                renderedView = html ``;
        }
        return renderedView;
    }
    get data() {
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
});
