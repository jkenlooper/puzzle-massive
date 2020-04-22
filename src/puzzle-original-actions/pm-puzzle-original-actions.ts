import { html, render } from "lit-html";
//import { classMap } from "lit-html/directives/class-map.js";
import userDetailsService from "../site/user-details.service";
import "./puzzle-original-actions.css";

import {
  puzzleDetailsService,
  PuzzleOriginalDetails,
} from "../site/puzzle-details.service";

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isReady: boolean;
  hasPuzzleDetails: boolean;
  hasActions: boolean;
  canBump: boolean;
  highestBid: number;
  bumpDisabledMessage: string;
  isProcessing: boolean; // the status on the puzzle page is not the same as the status returned.
  actionHandler: any; // event listener object
}

const tag = "pm-puzzle-original-actions";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleOriginalActions extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    puzzleId: string = "";
    hasError: boolean = false;
    errorMessage: string = "";
    isReady: boolean = false;
    puzzleDetails: undefined | PuzzleOriginalDetails = undefined;
    status: number = -99;

    constructor() {
      super();
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

      userDetailsService.subscribe(
        this._setPuzzleData.bind(this),
        this.instanceId
      );
    }

    _setPuzzleData() {
      return puzzleDetailsService
        .getPuzzleOriginalDetails(this.puzzleId)
        .then((puzzleDetails: PuzzleOriginalDetails) => {
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

    template(data: TemplateData) {
      if (!data.isReady) {
        return html``;
      }
      if (data.hasError) {
        return html` ${data.errorMessage} `;
      }
      if (!data.hasPuzzleDetails || !data.hasActions) {
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
        ${data.canBump
          ? html`
              <button data-action="bump" @click=${data.actionHandler}>
                Bump
              </button>
            `
          : html` <button disabled>Bump</button> `}
        ${data.canBump
          ? html`
              <p>
                <em
                  >Bumping this puzzle forward in the queue will cost
                  ${data.highestBid} dots.</em
                >
              </p>
            `
          : html`
              <p>
                <em>${data.bumpDisabledMessage}</em>
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
