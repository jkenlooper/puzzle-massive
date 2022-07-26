import { html, render } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { puzzleStatsService } from "../site/puzzle-stats.service";
import "./latest-player-list.css";
const tag = "pm-latest-player-list";
customElements.define(
  tag,
  class PmLatestPlayerList extends HTMLElement {
    constructor() {
      super();
      this.puzzleId = "";
      this.hasError = false;
      this.errorMessage = "";
      this.isReady = false;
      this.limit = 100;
      this.playerCount = 0;
      this.players = [];
      // Set the attribute values
      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      if (!puzzleId || !puzzleId.value) {
        this.hasError = true;
        this.errorMessage = "No puzzle-id has been set.";
      } else {
        this.puzzleId = puzzleId.value;
      }
      const limitAttr = this.attributes.getNamedItem("limit");
      if (limitAttr && limitAttr.value && !isNaN(parseInt(limitAttr.value))) {
        this.limit = parseInt(limitAttr.value);
      }
      this._setPlayers();
      this.render();
    }
    template(data) {
      if (!data.isReady) {
        return html` loading... `;
      }
      if (data.hasError) {
        return html` ${data.errorMessage} `;
      }
      if (data.playerCount === 0) {
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
            <h2>${data.playerCount > 1 ? data.playerCount : ""} Players</h2>
            ${data.players.recent.length > 0
              ? html`
                  <div
                    class="pm-LatestPlayerList-group pm-LatestPlayerList-group--recent"
                  >
                    <details open>
                      <summary>
                        ${data.players.recent.length > 1
                          ? data.players.recent.length
                          : ""}
                        players in the last 5 minutes
                      </summary>
                      <div class="pm-LatestPlayerList-list" role="list">
                        ${itemsWithTimeSince(
                          data.players.recent,
                          data.players.recent.length > 10 ? "condensed" : "row"
                        )}
                      </div>
                    </details>
                  </div>
                `
              : ""}
            ${data.players.lastHour.length > 0
              ? html`
                  <div
                    class="pm-LatestPlayerList-group pm-LatestPlayerList-group--lastHour"
                  >
                    <details ?open=${data.players.lastHour.length === 1}>
                      <summary>
                        ${data.players.lastHour.length > 1
                          ? data.players.lastHour.length
                          : ""}
                        players in the last hour
                      </summary>
                      <div class="pm-LatestPlayerList-list" role="list">
                        ${itemsWithTimeSince(
                          data.players.lastHour,
                          data.players.recent.length > 15 ? "condensed" : "row"
                        )}
                      </div>
                    </details>
                  </div>
                `
              : ""}
            ${data.players.lastSevenHours.length > 0
              ? html`
                  <div
                    class="pm-LatestPlayerList-group pm-LatestPlayerList-group--lastSevenHours"
                  >
                    <details ?open=${data.players.lastSevenHours.length === 1}>
                      <summary>
                        ${data.players.lastSevenHours.length > 1
                          ? data.players.lastSevenHours.length
                          : ""}
                        players in the last 7 hours
                      </summary>
                      <div class="pm-LatestPlayerList-list" role="list">
                        ${itemsWithTimeSince(
                          data.players.lastSevenHours,
                          data.players.recent.length > 15 ? "condensed" : "row"
                        )}
                      </div>
                    </details>
                  </div>
                `
              : ""}
            ${data.players.rest.length > 0
              ? html`
                  <div
                    class="pm-LatestPlayerList-group pm-LatestPlayerList-group--rest"
                  >
                    <details ?open=${data.players.rest.length === 1}>
                      <summary>
                        ${data.players.rest.length === 1
                          ? html`players ${data.players.rest[0].timeSince} ago`
                          : html`${data.players.rest.length > 1
                                ? data.players.rest.length
                                : ""}
                              players
                              <span class="u-textNoWrap"
                                >from ${data.players.rest[0].timeSince}
                                ${data.players.rest[0].timeSince ===
                                data.players.rest[data.players.rest.length - 1]
                                  .timeSince
                                  ? ""
                                  : html`
                                      to
                                      ${data.players.rest[
                                        data.players.rest.length - 1
                                      ].timeSince}
                                    `}
                                ago</span
                              >`}
                      </summary>
                      <div class="pm-LatestPlayerList-list" role="list">
                        ${itemsWithTimeSince(
                          data.players.rest,
                          data.players.rest.length > 10 ? "condensed" : "row"
                        )}
                      </div>
                    </details>
                  </div>
                `
              : ""}
            ${data.notShownCount > 0
              ? html`
                  <div>
                    ...plus ${data.notShownCount} more
                    player${data.notShownCount > 1 ? "s" : ""} not listed here.
                  </div>
                `
              : ""}
          </div>
        `;
      }
      function itemsWithTimeSince(players, variant) {
        return html`
          ${players.map((item) => {
            return html`
              <div
                class=${classMap({
                  "pm-LatestPlayerList-item": true,
                  "pm-LatestPlayerList-item--row": variant === "row",
                  "pm-LatestPlayerList-item--condensed":
                    variant === "condensed",
                  "is-active": item.isRecent,
                  "u-textNoWrap": true,
                })}
                role="listitem"
              >
                ${item.score || variant !== "condensed"
                  ? html` <span class="pm-LatestPlayerList-badge">
                      ${item.score
                        ? html`<span class="pm-LatestPlayerList-score"
                            >${item.score}<span
                              class="pm-LatestPlayerList-badgeLabel"
                            >
                              Piece${item.score > 1 ? "s" : ""}</span
                            ></span
                          >`
                        : ""}
                      <br /><span class="pm-LatestPlayerList-timeSince"
                        >${item.timeSince}</span
                      >
                    </span>`
                  : ""}
                <span class="pm-LatestPlayerList-playerBit">
                  <pm-player-bit player=${item.id}></pm-player-bit>
                </span>
              </div>
            `;
          })}
        `;
      }
    }
    get data() {
      return {
        isReady: this.isReady,
        hasError: this.hasError,
        errorMessage: this.errorMessage,
        playerCount: this.playerCount,
        players: this.players.reduce(
          (acc, player) => {
            if (player.isRecent) {
              acc.recent.push(player);
            } else if (player.seconds_from_now <= 60 * 60) {
              acc.lastHour.push(player);
            } else if (player.seconds_from_now <= 7 * (60 * 60)) {
              acc.lastSevenHours.push(player);
            } else {
              acc.rest.push(player);
            }
            return acc;
          },
          {
            recent: [],
            lastHour: [],
            lastSevenHours: [],
            rest: [],
          }
        ),
        notShownCount: this.playerCount - this.players.length,
      };
    }
    render() {
      render(this.template(this.data), this);
    }
    _setPlayers() {
      return puzzleStatsService
        .getPlayerStatsOnPuzzle(this.puzzleId)
        .then((playerStats) => {
          this.playerCount = playerStats.players.length;
          this.players = playerStats.players.slice(0, this.limit);
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
