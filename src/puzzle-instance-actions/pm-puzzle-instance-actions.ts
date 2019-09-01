import { html, render } from "lit-html";
//import { classMap } from "lit-html/directives/class-map.js";
import userDetailsService from "../site/user-details.service";
import "./puzzle-instance-actions.css";

import {
  puzzleDetailsService,
  PuzzleDetails,
} from "../site/puzzle-details.service";

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isReady: boolean;
  hasPuzzleDetails: boolean;
  isFrozen: boolean;
  canDelete: boolean;
  deletePenalty: number;
  deleteDisabledMessage: string;
  isProcessing: boolean; // the status on the puzzle page is not the same as the status returned.
  actionHandler: any; // event listener object
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
    puzzleDetails: undefined | PuzzleDetails = undefined;
    status: number = -99;

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
        .getPuzzleDetails(this.puzzleId)
        .then((puzzleDetails: PuzzleDetails) => {
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
        .patchPuzzleDetails(this.puzzleId, action)
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
      if (data.hasError) {
        return html`
          ${data.errorMessage}
        `;
      }
      if (!data.hasPuzzleDetails) {
        return html``;
      }
      if (data.isProcessing) {
        // When action buttons are pressed the server will respond with
        // a processing request code (202 or something?).  This is because the
        // front page is cached for a minute and removing that cache isn't within
        // scope of this.
        return html`
          <em>Processing last action that has updated the puzzle status.</em>
        `;
      }
      return html`
        ${data.canDelete
          ? html`
              <button data-action="delete" @click=${data.actionHandler}>
                delete
              </button>
            `
          : html`
              <button disabled>delete</button>
            `}
        ${data.isFrozen
          ? html`
              <button data-action="unfreeze" @click=${data.actionHandler}>
                unfreeze
              </button>
            `
          : html`
              <button data-action="freeze" @click=${data.actionHandler}>
                freeze
              </button>
            `}
        ${data.canDelete
          ? html`
              <p>
                ${data.deletePenalty > 0
                  ? html`
                    <em
                      >Deleting this puzzle will cost ${data.deletePenalty} dots
                      because it is not complete.</em
                    >
                  </p>`
                  : html``}
              </p>
            `
          : html`
              <p>
                <em>${data.deleteDisabledMessage}</em>
              </p>
            `}
      `;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        hasError: this.hasError,
        errorMessage: this.errorMessage,
        hasPuzzleDetails: !!this.puzzleDetails,
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
