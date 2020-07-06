import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";

import { puzzleService, KarmaData } from "../puzzle-pieces/puzzle.service";
import { streamService } from "../puzzle-pieces/stream.service";

import "./puzzle-karma-alert.css";

interface TemplateData {
  isActive: boolean;
  karma: number;
  karmaLevel: number;
}

const tag = "pm-puzzle-karma-alert";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleKarmaAlert extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    private karmaStatusIsActiveTimeout: number | undefined;
    private isActive: boolean = false;
    private karma: number = 1;
    private karmaLevel: number = 2;

    constructor() {
      super();
      this.instanceId = PmPuzzleKarmaAlert._instanceId;

      puzzleService.subscribe(
        "karma/updated",
        this.updateKarmaValue.bind(this),
        this.instanceId
      );
      streamService.subscribe(
        "karma/updated",
        this.updateKarmaValue.bind(this),
        this.instanceId
      );
      puzzleService.subscribe(
        "piece/move/rejected",
        this.updateKarmaValue.bind(this),
        this.instanceId
      );

      this.render();
    }

    template(data: TemplateData) {
      return html`
        <div
          data-karma-level=${data.karmaLevel}
          class=${classMap({
            "pm-PuzzleKarmaAlert-status": true,
            "is-active": data.isActive,
          })}
        >
          ${data.karma}
        </div>
      `;
    }

    get data(): TemplateData {
      return {
        isActive: this.isActive,
        karma: this.karma,
        karmaLevel: this.karmaLevel,
      };
    }

    render() {
      render(this.template(this.data), this);
    }
    updateKarmaValue(data: KarmaData) {
      const karma = data.karma;
      if (karma && typeof karma === "number") {
        this.karma = karma;
        window.clearTimeout(this.karmaStatusIsActiveTimeout);
        const karmaLevel = Math.floor(karma / 6);
        this.karmaLevel = karmaLevel;
        this.isActive = true;

        // Hide the karma status after a timeout when it is normal
        if (karmaLevel > 2) {
          this.karmaStatusIsActiveTimeout = window.setTimeout(() => {
            this.isActive = false;
            this.render();
          }, 5000);
        }
        this.render();
      }
    }

    disconnectedCallback() {
      puzzleService.unsubscribe("karma/updated", this.instanceId);
      streamService.unsubscribe("karma/updated", this.instanceId);
      puzzleService.unsubscribe("piece/move/rejected", this.instanceId);
    }
  }
);
