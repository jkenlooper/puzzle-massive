import { html, render } from "lit";
//import { classMap } from "lit/directives/class-map.js";
import userDetailsService from "../site/user-details.service";
import "./puzzle-instance-actions.css";
import { Status } from "../site/puzzle-images.service";
import { puzzleDetailsService } from "../site/puzzle-details.service";
const tag = "pm-puzzle-instance-actions";
let lastInstanceId = 0;
customElements.define(
  tag,
  class PmPuzzleInstanceActions extends HTMLElement {
    constructor() {
      super();
      this.puzzleId = "";
      this.owner = 0;
      this.hasError = false;
      this.errorMessage = "";
      this.isReady = false;
      this.puzzleDetails = undefined;
      this.status = -99;
      this.view = ""; // buttons, message
      this.instanceId = PmPuzzleInstanceActions._instanceId;
      // Set the attribute values
      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      if (!puzzleId || !puzzleId.value) {
        this.hasError = true;
        this.errorMessage = "No puzzle-id has been set.";
      } else {
        this.puzzleId = puzzleId.value;
      }
      const owner = this.attributes.getNamedItem("owner");
      if (!owner || !owner.value) {
        this.hasError = true;
        this.errorMessage = "No owner has been set.";
      } else {
        this.owner = parseInt(owner.value);
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
      userDetailsService.subscribe(
        this._setPuzzleData.bind(this),
        this.instanceId
      );
    }
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }
    _setPuzzleData() {
      if (userDetailsService.userDetails.id != this.owner) {
        // The instance actions are only for the owner of the puzzle.
        this.isReady = true;
        this.render();
        return;
      }
      return puzzleDetailsService
        .getPuzzleInstanceDetails(this.puzzleId)
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
        .patchPuzzleInstanceDetails(this.puzzleId, action)
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
        }
        return renderedView;
      }
      switch (data.view) {
        case "buttons":
          renderedView = html`
            ${data.canDelete
              ? html`
                  <button
                    class="Button"
                    data-action="delete"
                    @click=${data.actionHandler}
                  >
                    Delete
                  </button>
                `
              : html` <button class="Button" disabled>Delete</button> `}
            ${data.canFreeze
              ? html`
                  ${data.isFrozen
                    ? html`
                        <button
                          class="Button"
                          data-action="unfreeze"
                          @click=${data.actionHandler}
                        >
                          Unfreeze
                        </button>
                      `
                    : html`
                        <button
                          class="Button"
                          data-action="freeze"
                          @click=${data.actionHandler}
                        >
                          Freeze
                        </button>
                      `}
                `
              : ""}
            ${data.canReset
              ? html`
                  <button
                    class="Button"
                    data-action="reset"
                    @click=${data.actionHandler}
                  >
                    Reset
                  </button>
                `
              : ""}
          `;
          break;
        case "message":
          renderedView = html`
            ${data.canDelete
              ? html`
                  <p>
                    ${data.deletePenalty === -1
                      ? html`The last modified date for this puzzle is old.
                          Deleting the puzzle will <b>not</b> cost any dots.`
                      : ""}
                    ${data.deletePenalty > 0
                      ? html` Deleting this puzzle will cost
                        ${data.deletePenalty} dots because it is not complete.`
                      : ""}
                  </p>
                `
              : html` <p>${data.deleteDisabledMessage}</p> `}
          `;
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
        isFrozen: !!this.puzzleDetails ? this.puzzleDetails.isFrozen : false,
        canFreeze: !!this.puzzleDetails ? this.puzzleDetails.canFreeze : false,
        canDelete: !!this.puzzleDetails ? this.puzzleDetails.canDelete : false,
        canReset: !!this.puzzleDetails ? this.puzzleDetails.canReset : false,
        deletePenalty: !!this.puzzleDetails
          ? this.puzzleDetails.deletePenalty
          : -1,
        deleteDisabledMessage: !!this.puzzleDetails
          ? this.puzzleDetails.deleteDisabledMessage
          : "",
        isProcessing:
          (!!this.puzzleDetails && this.status !== this.puzzleDetails.status) ||
          this.status === Status.MAINTENANCE,
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
    disconnectedCallback() {
      userDetailsService.unsubscribe(this.instanceId);
    }
  }
);
