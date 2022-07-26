import { html, render } from "lit";
//import { classMap } from "lit/directives/class-map.js";
import userDetailsService from "../site/user-details.service";
import "./puzzle-original-actions.css";
import { puzzleDetailsService } from "../site/puzzle-details.service";
const tag = "pm-puzzle-original-actions";
let lastInstanceId = 0;
customElements.define(
  tag,
  class PmPuzzleOriginalActions extends HTMLElement {
    constructor() {
      super();
      this.puzzleId = "";
      this.hasError = false;
      this.errorMessage = "";
      this.isReady = false;
      this.puzzleDetails = undefined;
      this.status = -99;
      this.view = ""; // buttons, message
      this.instanceId = PmPuzzleOriginalActions._instanceId;
      // Set the attribute values
      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      if (!puzzleId || !puzzleId.value) {
        this.hasError = true;
        this.errorMessage = "No puzzle-id has been set.";
      } else {
        this.puzzleId = puzzleId.value;
      }
      const status = this.attributes.getNamedItem("status");
      if (!status || !status.value) {
        this.hasError = true;
        this.errorMessage = "No status has been set.";
      } else {
        this.status = parseInt(status.value);
      }
      const viewAttr = this.attributes.getNamedItem("view");
      if (!viewAttr || !viewAttr.value) {
        this.view = "";
      } else {
        this.view = viewAttr.value;
      }
    }
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }
    _setPuzzleData() {
      return puzzleDetailsService
        .getPuzzleOriginalDetails(this.puzzleId)
        .then((puzzleDetails) => {
          this.puzzleDetails = puzzleDetails;
        })
        .catch(() => {
          this.hasError = true;
          this.errorMessage = "Error getting the puzzle details.";
        })
        .finally(() => {
          this.isReady = true;
          this.render();
        });
    }
    handleAction(e) {
      const action = e.target.dataset["action"];
      this.isReady = false;
      puzzleDetailsService
        .patchPuzzleOriginalDetails(this.puzzleId, action)
        .then((data) => {
          if (this.puzzleDetails) {
            this.puzzleDetails.status = data.status;
          }
        })
        .catch(() => {
          this.hasError = true;
          this.errorMessage = `Oops. That puzzle action (${action}) had an error.`;
        })
        .finally(() => {
          this.isReady = true;
          this.render();
        });
    }
    template(data) {
      if (!data.isReady) {
        return html``;
      }
      let renderedView = html``;
      if (data.hasError) {
        switch (data.view) {
          case "buttons":
            break;
          case "message":
            renderedView = html` ${data.errorMessage} `;
            break;
        }
        return renderedView;
      }
      if (!data.hasPuzzleDetails || !data.hasActions) {
        return html``;
      }
      if (data.isProcessing) {
        // When action buttons are pressed the server will respond with
        // a processing request code (202 or something?).  This is because the
        // front page is cached for a minute and removing that cache isn't within
        // scope of this.
        switch (data.view) {
          case "buttons":
            renderedView = html`<a class="Button" href="">Reload</a>`;
            break;
          case "message":
            renderedView = html`
              <p>Processing last action that has updated the puzzle status.</p>
            `;
            break;
        }
        return renderedView;
      }
      switch (data.view) {
        case "buttons":
          renderedView = html`
            ${data.canBump
              ? html`
                  <button
                    class="Button"
                    data-action="bump"
                    @click=${data.actionHandler}
                  >
                    Bump
                  </button>
                `
              : html` <button class="Button" disabled>Bump</button> `}
          `;
          break;
        case "message":
          renderedView = html`
            ${data.canBump
              ? html`
                  <p>
                    Bumping this puzzle forward in the queue will cost
                    ${data.highestBid} dots.
                  </p>
                `
              : html` <p>${data.bumpDisabledMessage}</p> `}
          `;
          break;
      }
      return renderedView;
    }
    get data() {
      return {
        isReady: this.isReady,
        hasError: this.hasError,
        errorMessage: this.errorMessage,
        hasPuzzleDetails: !!this.puzzleDetails,
        hasActions: this.puzzleDetails ? this.puzzleDetails.hasActions : false,
        canBump: !!this.puzzleDetails ? this.puzzleDetails.canBump : false,
        highestBid: !!this.puzzleDetails ? this.puzzleDetails.highestBid : 0,
        bumpDisabledMessage: !!this.puzzleDetails
          ? this.puzzleDetails.bumpDisabledMessage
          : "",
        isProcessing:
          !!this.puzzleDetails && this.status != this.puzzleDetails.status,
        actionHandler: {
          handleEvent: this.handleAction.bind(this),
          capture: true,
        },
        view: this.view,
      };
    }
    render() {
      render(this.template(this.data), this);
    }
    connectedCallback() {
      userDetailsService.subscribe(
        this._setPuzzleData.bind(this),
        this.instanceId
      );
    }
    disconnectedCallback() {
      userDetailsService.unsubscribe(this.instanceId);
    }
  }
);
