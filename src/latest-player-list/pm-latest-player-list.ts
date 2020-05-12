import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import {
  puzzleStatsService,
  PlayerStatsData,
  PlayerDetail,
} from "../site/puzzle-stats.service";
import "./latest-player-list.css";

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isReady: boolean;
  players: Array<PlayerDetail>;
  recentPlayersCount: number;
}

const tag = "pm-latest-player-list";

customElements.define(
  tag,
  class PmLatestPlayerList extends HTMLElement {
    puzzleId: string = "";
    hasError: boolean = false;
    errorMessage: string = "";
    isReady: boolean = false;
    limit: number = 100;
    players: Array<PlayerDetail> = [];
    constructor() {
      super();

      // Set the attribute values
      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      if (!puzzleId || !puzzleId.value) {
        this.hasError = true;
        this.errorMessage = "No puzzle-id has been set.";
      } else {
        this.puzzleId = puzzleId.value;
      }

      const limit = this.attributes.getNamedItem("limit");
      if (limit && limit.value && !isNaN(parseInt(limit.value))) {
        this.limit = parseInt(limit.value);
      }

      // TODO: fetch data
      this._setPlayers();

      this.render();
    }

    template(data: TemplateData) {
      if (!data.isReady) {
        return html` loading... `;
      }
      if (data.hasError) {
        return html` ${data.errorMessage} `;
      }

      const limit = this.limit;

      if (data.players.length === 0) {
        return html`
          <p>
            <small>No players have joined pieces on this puzzle.</small>
          </p>
        `;
      } else {
        return playerListWithTimeSince();
      }

      function playerListWithTimeSince() {
        return html`
          <div class="pm-LatestPlayerList">
            <h2>
              ${data.players.length > 1 ? data.players.length : ""} Players
              ${data.recentPlayersCount > 0
                ? html`
                    <em><small>${data.recentPlayersCount} Active</small></em>
                  `
                : ""}
            </h2>
            <div class="pm-LatestPlayerList-list" role="list">
              ${itemsWithTimeSince()}
            </div>
          </div>
        `;
      }
      function itemsWithTimeSince() {
        const playerSlice = data.players.slice(0, limit);
        return html`
          ${playerSlice.map((item) => {
            return html`
              <div
                class=${classMap({
                  "pm-LatestPlayerList-item": true,
                  "is-active": item.isRecent,
                })}
                role="listitem"
              >
                <span class="pm-LatestPlayerList-timeSince">
                  ${item.timeSince}
                </span>
                <span class="pm-LatestPlayerList-score">
                  ${item.score}
                </span>
                <span class="pm-LatestPlayerList-playerBit">
                  <pm-player-bit player=${item.id}></pm-player-bit>
                </span>
              </div>
            `;
          })}
        `;
      }
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        hasError: this.hasError,
        errorMessage: this.errorMessage,
        players: this.players,
        recentPlayersCount: this.players.reduce((acc, player) => {
          if (player.isRecent) {
            acc += 1;
          }
          return acc;
        }, 0),
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    _setPlayers() {
      return puzzleStatsService
        .getPlayerStatsOnPuzzle(this.puzzleId)
        .then((playerStats: PlayerStatsData) => {
          this.players = playerStats.players;
        })
        .catch(() => {
          this.hasError = true;
          this.errorMessage = "Error getting the player stats for puzzle.";
        })
        .finally(() => {
          this.isReady = true;
          this.render();
        });
    }
  }
);
