import { html, render } from "lit";
import { puzzleStatsService, } from "../site/puzzle-stats.service";
import "./active-player-count.css";
const tag = "pm-active-player-count";
customElements.define(tag, class PmActivePlayerCount extends HTMLElement {
    constructor() {
        super();
        this.hasError = false;
        this.isReady = false;
        this.puzzleId = "";
        this.activePlayerCount = 0;
    }
    _setPlayerCount() {
        return puzzleStatsService
            .getActivePlayerCountOnPuzzle(this.puzzleId)
            .then((playerCount) => {
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
    template(data) {
        if (!data.isReady) {
            return html ``;
        }
        if (data.hasError) {
            return html ``;
        }
        if (!data.activePlayerCount) {
            return html ``;
        }
        return html `
        <span class="pm-ActivePlayerCount">
          <strong class="pm-ActivePlayerCount-amount"
            >${data.activePlayerCount}</strong
          >
          <small class="pm-ActivePlayerCount-label">
            Active
            ${data.activePlayerCount > 1 ? html ` Players ` : html ` Player `}
          </small>
        </span>
      `;
    }
    get data() {
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
        }
        else {
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
});
