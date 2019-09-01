import { html, render } from "lit-html";
import {
  puzzleStatsService,
  PlayerCountData,
} from "../site/puzzle-stats.service";

interface TemplateData {
  hasError: boolean;
  isReady: boolean;
  activePlayerCount: number;
}

const tag = "pm-active-player-count";

customElements.define(
  tag,
  class PmActivePlayerCount extends HTMLElement {
    hasError: boolean = false;
    isReady: boolean = false;
    puzzleId: string = "";
    activePlayerCount: number = 0;

    constructor() {
      super();
    }

    _setPlayerCount() {
      return puzzleStatsService
        .getActivePlayerCountOnPuzzle(this.puzzleId)
        .then((playerCount: PlayerCountData) => {
          this.activePlayerCount = playerCount.count;
        })
        .catch(() => {
          this.hasError = true;
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
        return html``;
      }
      if (!data.activePlayerCount) {
        return html``;
      }
      return html`
        <strong>${data.activePlayerCount}</strong>
        <small>
          Active
          ${data.activePlayerCount > 1
            ? html`
                Players
              `
            : html`
                Player
              `}
        </small>
      `;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        hasError: this.hasError,
        activePlayerCount: this.activePlayerCount,
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    connectedCallback() {
      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      if (!puzzleId || !puzzleId.value) {
        this.hasError = true;
      } else {
        this.puzzleId = puzzleId.value;
      }
      this._setPlayerCount();
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      //userDetailsService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
  }
);
