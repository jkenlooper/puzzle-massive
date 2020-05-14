import { html, render } from "lit-html";
//import { classMap } from "lit-html/directives/class-map.js";
import userDetailsService from "../site/user-details.service";
import "./puzzle-instance-actions.css";

import {
  puzzleDetailsService,
  PuzzleInstanceDetails,
} from "../site/puzzle-details.service";

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isReady: boolean;
  hasPuzzleDetails: boolean;
  hasActions: boolean;
  isFrozen: boolean;
  canDelete: boolean;
  deletePenalty: number;
  deleteDisabledMessage: string;
  isProcessing: boolean; // the status on the puzzle page is not the same as the status returned.
  actionHandler: any; // event listener object
  view: string;
}

const tag = "pm-puzzle-instance-actions";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleInstanceActions extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    puzzleId: string = "";
    owner: number = 0;
    hasError: boolean = false;
    errorMessage: string = "";
    isReady: boolean = false;
    puzzleDetails: undefined | PuzzleInstanceDetails = undefined;
    status: number = -99;
    view: string = ""; // buttons, message

    constructor() {
      super();
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

    _setPuzzleData() {
      if (userDetailsService.userDetails.id != this.owner) {
        this.isReady = true;
        this.render();
        return;
      }
      return puzzleDetailsService
        .getPuzzleInstanceDetails(this.puzzleId)
        .then((puzzleDetails: PuzzleInstanceDetails) => {
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

    template(data: TemplateData) {
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
              <p>
                Processing last action that has updated the puzzle status.
              </p>
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
          `;
          break;
        case "message":
          renderedView = html`
            ${data.canDelete
              ? html`
                  <p>
                    ${data.deletePenalty > 0
                      ? html` Deleting this puzzle will cost
                        ${data.deletePenalty} dots because it is not complete.`
                      : html``}
                  </p>
                `
              : html`
                  <p>
                    ${data.deleteDisabledMessage}
                  </p>
                `}
          `;
      }
      return renderedView;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        hasError: this.hasError,
        errorMessage: this.errorMessage,
        hasPuzzleDetails: !!this.puzzleDetails,
        hasActions: this.puzzleDetails ? this.puzzleDetails.hasActions : false,
        isFrozen: !!this.puzzleDetails ? this.puzzleDetails.isFrozen : false,
        canDelete: !!this.puzzleDetails ? this.puzzleDetails.canDelete : false,
        deletePenalty: !!this.puzzleDetails
          ? this.puzzleDetails.deletePenalty
          : -1,
        deleteDisabledMessage: !!this.puzzleDetails
          ? this.puzzleDetails.deleteDisabledMessage
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

    disconnectedCallback() {
      userDetailsService.unsubscribe(this.instanceId);
    }
  }
);
