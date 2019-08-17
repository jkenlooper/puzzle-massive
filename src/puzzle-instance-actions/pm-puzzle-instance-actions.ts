import { html, render } from "lit-html";
//import { classMap } from "lit-html/directives/class-map.js";
import userDetailsService from "../site/user-details.service";
import "./puzzle-instance-actions.css";

import {
  puzzleStatsService,
  PuzzleDetails,
} from "../site/puzzle-stats.service";

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isReady: boolean;
  puzzleDetails: boolean | PuzzleDetails;
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
    puzzleDetails: boolean | PuzzleDetails = false;

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
      return puzzleStatsService
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

    template(data: TemplateData) {
      if (!data.isReady) {
        return html``;
      }
      if (data.hasError) {
        return html`
          ${data.errorMessage}
        `;
      }
      if (!data.puzzleDetails) {
        return html``;
      }
      return html`
        ...
      `;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        hasError: this.hasError,
        errorMessage: this.errorMessage,
        puzzleDetails: this.puzzleDetails,
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
