import FetchService from "../site/fetch.service";
import userDetailsService from "../site/user-details.service";

import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";

import "./ranking.css";

interface RankData {
  active: boolean;
  bitactive: boolean;
  icon: string;
  id: number;
  rank: number;
  score: number;
}

interface PlayerRankDetail extends RankData {
  topPlayer: boolean;
  iconSrc: string;
  iconAlt: string;
}

interface PlayerStatsData {
  total_players: number;
  total_active_players: number;
  player_rank: number;
  rank_slice: Array<RankData>;
}

interface TemplateData {
  isReady: boolean;
  hasError: boolean;
  errorMessage?: string;
  playerRank: number;
  playerId: number | undefined;
  totalPlayers: number;
  totalActivePlayers: number;
  hasUp: boolean;
  hasDown: boolean;
  playerRanks: Array<PlayerRankDetail>;
  selectPlayerRanksUp: Function;
  selectPlayerRanksDown: Function;
}

const tag = "pm-ranking";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmRanking extends HTMLElement {
    player_ranks_url: string = "";
    isReady: boolean = false;
    hasError: boolean = false;
    errorMessage: string = "";
    range: number = 15;
    playerRanks: Array<PlayerRankDetail> = [];
    playerRank: number = 0;
    playerId: number | undefined;
    totalPlayers: number = 0;
    totalActivePlayers: number = 0;
    hasUp: boolean = false;
    hasDown: boolean = false;
    private instanceId: string;
    private offset: number = 0;
    private mediaPath: string;

    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    constructor() {
      super();
      const self = this;
      this.instanceId = PmRanking._instanceId;

      const mediaPath = this.attributes.getNamedItem("media-path");
      this.mediaPath = mediaPath ? mediaPath.value : "";

      // Set the attribute values
      const player_ranks_url = this.attributes.getNamedItem("player-ranks-url");
      if (!player_ranks_url || !player_ranks_url.value) {
        this.hasError = true;
        this.errorMessage = "No player-ranks-url has been set.";
      } else {
        this.player_ranks_url = player_ranks_url.value;
      }

      const range = this.attributes.getNamedItem("range");
      if (range && range.value && !isNaN(parseInt(range.value))) {
        this.range = parseInt(range.value);
      }

      let playerId = userDetailsService.userDetails.id;
      const setPlayerRanks = this._setPlayerRanks.bind(this);
      if (playerId != undefined) {
        this.playerId = playerId;
        setPlayerRanks();
      } else {
        userDetailsService.subscribe(updateOnce, this.instanceId);
      }
      function updateOnce() {
        let playerId = userDetailsService.userDetails.id;
        if (playerId === undefined) {
          throw new Error("No user id available to set player ranking");
        }
        self.playerId = playerId;
        setPlayerRanks();
        userDetailsService.unsubscribe(self.instanceId);
      }

      this.render();
    }

    _setPlayerRanks(start?: number) {
      const rankingService = new FetchService(
        `${this.player_ranks_url}?${
          start === undefined ? "" : `start=${start}&`
        }count=${this.range}`
      );
      const self = this;
      return rankingService
        .get<PlayerStatsData>()
        .then((playerStats) => {
          this.playerRank = playerStats.player_rank;
          const first = playerStats.rank_slice[0];
          if (first) {
            this.offset = first.rank;
          } else {
            this.offset = 0;
          }

          this.playerRanks = playerStats.rank_slice.map(setPlayerRankDetails);
          this.totalPlayers = playerStats.total_players;
          this.totalActivePlayers = playerStats.total_active_players;
          this.hasUp = this.offset > 1;
          const end = this.offset + this.range;
          this.hasDown = end < this.totalPlayers;
        })
        .catch(() => {
          this.hasError = true;
          this.errorMessage = "Error getting the player ranks data.";
        })
        .finally(() => {
          this.isReady = true;
          this.render();
        });
      function setPlayerRankDetails(item: RankData): PlayerRankDetail {
        const playerRank = <PlayerRankDetail>Object.assign(
          {
            topPlayer: item.rank < 15,
            iconSrc: `${self.mediaPath}bit-icons/64-${item.icon ||
              "unknown-bit"}.png`,
            iconAlt: item.icon || "unknown bit",
          },
          item
        );
        return playerRank;
      }
    }

    template(data: TemplateData) {
      return html`
        <section class="pm-Ranking">
          <h2 class="u-textCenter">Player Rankings</h2>
          ${contents()}
        </section>
      `;

      function contents() {
        if (!data.isReady) {
          return html`
            loading...
          `;
        }
        if (data.hasError) {
          return html`
            error: ${data.errorMessage}
          `;
        }
        return html`
          <p>
            <strong>
              Your Rank is ${data.playerRank} out of ${
          data.totalPlayers
        } players.
            </strong>
          </p>
          <p>
          ${data.totalActivePlayers} active players in the last two weeks.
          </p>
          <p class="u-textRight">
          ${
            data.hasUp
              ? html`
                  <button
                    class="pm-Ranking-pager pm-Ranking-pager--up"
                    @click=${data.selectPlayerRanksUp}
                  >
                    &uarr;
                  </button>
                `
              : html``
          }
          </p>
          <div class="pm-Ranking-list" role="list">
          ${items()}

          </div>
          <p class="u-textRight">
          ${
            data.hasDown
              ? html`
                  <button
                    class="pm-Ranking-pager pm-Ranking-pager--down"
                    @click=${data.selectPlayerRanksDown}
                  >
                    &darr;
                  </button>
                `
              : html``
          }
          </p>
        <p>
          <em>Players shown without bit icons have lost them due to inactivity.</em>
        </p>
        </section>
      `;
      }
      function items() {
        return html`
          ${data.playerRanks.map((item) => {
            return html`
              <div
                role="listitem"
                class=${classMap({
                  "pm-Ranking-listitem": true,
                  isExpired: !item.bitactive,
                  "pm-Ranking-listitem--current": item.id === data.playerId,
                  "pm-Ranking-listitem--topPlayer": item.topPlayer,
                })}
              >
                ${item.icon
                  ? html`
                      <img
                        class="pm-Ranking-img"
                        src=${item.iconSrc}
                        width="64"
                        height="64"
                        alt=${item.iconAlt}
                      />
                    `
                  : html`
                      <div class="pm-Ranking-img"></div>
                    `}

                <strong class="pm-Ranking-rank">${item.score}</strong>
                <span class="pm-Ranking-status">
                  ${item.active
                    ? html`
                        <small>Active</small>
                      `
                    : html``}
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
        playerRank: this.playerRank,
        playerId: this.playerId,
        totalPlayers: this.totalPlayers,
        totalActivePlayers: this.totalActivePlayers,
        hasUp: this.hasUp,
        hasDown: this.hasDown,
        playerRanks: this.playerRanks,
        selectPlayerRanksUp: this.selectPlayerRanksUp.bind(this),
        selectPlayerRanksDown: this.selectPlayerRanksDown.bind(this),
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    selectPlayerRanksUp() {
      const start = Math.max(0, this.offset - this.range);
      this._setPlayerRanks(start).finally(() => {
        this.render();
      });
    }

    selectPlayerRanksDown() {
      const start = this.offset + this.range;
      this._setPlayerRanks(start).finally(() => {
        this.render();
      });
    }
  }
);
