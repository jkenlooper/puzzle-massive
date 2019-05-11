import { html, render } from "lit-html";
import FetchService from "../site/fetch.service";
import "./latest-player-list.css";

interface PlayerStatsData {
  now: number;
  players: Array<PlayerData>;
}

interface PlayerData {
  bitactive: boolean;
  icon: string;
  id: number;
  rank: number;
  score: number;
  seconds_from_now: number;
}

interface PlayerDetail extends PlayerData {
  iconSrc: string;
  iconAlt: string;
  timeSince: string;
}

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isReady: boolean;
  players: Array<PlayerDetail>;
  showTimeSince: boolean;
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
    private mediaPath: string;
    constructor() {
      super();

      const mediaPath = this.attributes.getNamedItem("media-path");
      this.mediaPath = mediaPath ? mediaPath.value : "";

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

    // <pm-latest-player-list media-path="" puzzle-id="{{recent.puzzle_id}}" show-time-since limit="9"></pm-latest-player-list>
    // <pm-latest-player-list media-path="" puzzle-id="{{recent.puzzle_id}}" offset="9" limit="25"></pm-latest-player-list>
    template(data: TemplateData) {
      if (!data.isReady) {
        return html`
          ... loading ...
        `;
      }
      if (data.hasError) {
        return html`
          ${data.errorMessage}
        `;
      }

      if (data.showTimeSince) {
        return playerListWithTimeSince();
      } else {
        return playerListWithoutTimeSince();
      }

      function playerListWithTimeSince() {
        return html`
          <div class="pm-Preview-latest">
            <h2>Players</h2>
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
          </div>
        `;
      }
      function itemsWithTimeSince() {
        return html`
          ${data.players.map((item) => {
            return html`
              <div class="pm-Preview-latestItem" role="listitem">
                <small class="pm-Preview-latestItemCell">
                  <img
                    width="32"
                    height="32"
                    src=${item.iconSrc}
                    alt=${item.iconAlt}
                  />
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
                    <small
                      >No players<br />
                      have moved pieces<br />
                      on this puzzle.</small
                    >
                  </p>
                `
              : html`
                  <h2 class="u-textRight">Players (continued)</h2>
                  <div class="pm-Preview-pieceJoinsList" role="list">
                    ${itemsWithoutTimeSince()}
                  </div>
                `}
          </div>
        `;
      }
      function itemsWithoutTimeSince() {
        return html`
          ${data.players.map((item) => {
            return html`
              <span class="pm-Preview-pieceJoinsListItem" role="listitem">
                <img
                  width="32"
                  height="32"
                  src=${item.iconSrc}
                  alt=${item.iconAlt}
                />
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
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    getTimePassed(secondsFromNow: number): string {
      let timePassed = "";

      if (secondsFromNow < 60) {
        timePassed = "less than a minute";
      } else if (secondsFromNow < 2 * 60) {
        timePassed = "1 minute";
      } else if (secondsFromNow < 60 * 60) {
        timePassed = `${Math.floor(secondsFromNow / 60)} minutes`;
      } else if (secondsFromNow < 60 * 60 * 2) {
        timePassed = "1 hour";
      } else if (secondsFromNow < 60 * 60 * 24) {
        timePassed = `${Math.floor(secondsFromNow / 60 / 60)} hours`;
      } else if (secondsFromNow < 60 * 60 * 24 * 2) {
        timePassed = "1 day";
      } else if (secondsFromNow < 60 * 60 * 24 * 14) {
        timePassed = `${Math.floor(secondsFromNow / 60 / 60 / 24)} days`;
      } else {
        timePassed = "a long time";
      }
      timePassed = `${timePassed} ago`;
      return timePassed;
    }

    _setPlayers() {
      const puzzleStatsService = new FetchService(
        `/newapi/puzzle-stats/${this.puzzleId}/`
      );
      const self = this;
      const setPlayerDetails = _setPlayerDetails.bind(this);
      return puzzleStatsService
        .get<PlayerStatsData>()
        .then((playerStats) => {
          this.players = playerStats.players.map(setPlayerDetails);
        })
        .catch(() => {
          this.hasError = true;
          this.errorMessage = "Error getting the player stats for puzzle.";
        })
        .finally(() => {
          this.isReady = true;
          this.render();
        });

      function _setPlayerDetails(item: PlayerData): PlayerDetail {
        const playerDetail = <PlayerDetail>Object.assign(
          {
            iconSrc: `${self.mediaPath}bit-icons/64-${item.icon ||
              "unknown-bit"}.png`,
            iconAlt: item.icon || "unknown bit",
            timeSince: this.getTimePassed(item.seconds_from_now),
          },
          item
        );
        return playerDetail;
      }
    }
  }
);
