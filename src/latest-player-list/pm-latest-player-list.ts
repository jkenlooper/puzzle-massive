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
  showTimeSince: boolean;
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
    offset: number = 0;
    limit: number = 10;
    showTimeSince: boolean = false;
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

      const offset = this.attributes.getNamedItem("offset");
      if (offset && offset.value && !isNaN(parseInt(offset.value))) {
        this.offset = parseInt(offset.value);
      }

      const limit = this.attributes.getNamedItem("limit");
      if (limit && limit.value && !isNaN(parseInt(limit.value))) {
        this.limit = parseInt(limit.value);
      }

      const showTimeSince = this.attributes.getNamedItem("show-time-since");
      if (showTimeSince) {
        this.showTimeSince = true;
      }

      // TODO: fetch data
      this._setPlayers();

      this.render();
    }

    template(data: TemplateData) {
      if (!data.isReady) {
        return html`
          loading...
        `;
      }
      if (data.hasError) {
        return html`
          ${data.errorMessage}
        `;
      }

      const offset = this.offset;
      const limit = this.limit;

      if (data.showTimeSince) {
        return playerListWithTimeSince();
      } else {
        return playerListWithoutTimeSince();
      }

      function playerListWithTimeSince() {
        return html`
          <div class="pm-Preview-latest">
            ${data.players.length === 0
              ? html``
              : html`
                  <h2>
                    ${data.players.length > 1 ? data.players.length : ""}
                    Players
                    ${data.recentPlayersCount > 0
                      ? html`
                          <em class="pm-Preview-activeCount"
                            ><small
                              >${data.recentPlayersCount} Active</small
                            ></em
                          >
                        `
                      : ""}
                  </h2>
                  <div class="pm-Preview-latestList" role="list">
                    <div class="pm-Preview-latestItem">
                      <small class="pm-Preview-latestItemCell"></small>
                      <small
                        class="pm-Preview-latestItemCell pm-Preview-latestItemCell--pieces"
                      >
                        Pieces
                      </small>
                      <small class="pm-Preview-latestItemCell">
                        Time since
                      </small>
                    </div>
                    ${itemsWithTimeSince()}
                  </div>
                `}
          </div>
        `;
      }
      function itemsWithTimeSince() {
        const playerSlice = data.players.slice(offset, limit);
        return html`
          ${playerSlice.map((item) => {
            return html`
              <div
                class=${classMap({
                  "pm-Preview-latestItem": true,
                  isActive: item.isRecent,
                })}
                role="listitem"
              >
                <small class="pm-Preview-latestItemCell">
                  <pm-player-bit player=${item.id}></pm-player-bit>
                </small>
                <small
                  class="pm-Preview-latestItemCell pm-Preview-latestItemCell--pieces"
                >
                  ${item.score}
                </small>
                <small class="pm-Preview-latestItemCell">
                  ${item.timeSince}
                </small>
              </div>
            `;
          })}
        `;
      }

      function playerListWithoutTimeSince() {
        return html`
          <div class="pm-Preview-pieceJoins">
            ${data.players.length === 0
              ? html`
                  <p>
                    <small>No players have moved pieces on this puzzle.</small>
                  </p>
                `
              : html`
                  ${data.players.length > offset
                    ? html`
                        <h2 class="u-textRight">Players (continued)</h2>
                        <div class="pm-Preview-pieceJoinsList" role="list">
                          ${itemsWithoutTimeSince()}
                        </div>
                      `
                    : html``}
                `}
          </div>
        `;
      }
      function itemsWithoutTimeSince() {
        const playerSlice = data.players.slice(offset);
        return html`
          ${playerSlice.map((item) => {
            return html`
              <span
                class=${classMap({
                  "pm-Preview-pieceJoinsListItem": true,
                  isActive: item.isRecent,
                })}
                role="listitem"
              >
                <pm-player-bit player=${item.id}></pm-player-bit>
                ${item.score}
              </span>
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
        showTimeSince: this.showTimeSince,
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
