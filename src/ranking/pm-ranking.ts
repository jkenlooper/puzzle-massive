/* global HTMLElement, customElements, MEDIA_PATH */
declare const MEDIA_PATH: string;

import FetchService from "../site/fetch.service";
import userDetailsService from "../site/user-details.service";

import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";

import "./ranking.css";

interface RankData {
  active: number;
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

interface TemplateData {
  isReady: boolean;
  hasError: boolean;
  errorMessage?: string;
  playerRank: number;
  playerId: number | undefined;
  totalActivePlayers: number;
  hasUp: boolean;
  hasDown: boolean;
  playerRanks: Array<PlayerRankDetail>;
  selectPlayerRanksUp: Function;
  selectPlayerRanksDown: Function;
}

function setPlayerRankDetails(item: RankData, index: number): PlayerRankDetail {
  const playerRank = <PlayerRankDetail>Object.assign(
    {
      topPlayer: index < 15,
      iconSrc: `${MEDIA_PATH}bit-icons/64-${item.icon || "unknown-bit"}.png`,
      iconAlt: item.icon || "unknown bit",
    },
    item
  );
  return playerRank;
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
    private allPlayerRanks: Array<PlayerRankDetail> = [];
    playerRanks: Array<PlayerRankDetail> = [];
    playerRank: number = 0;
    playerId: number | undefined;
    totalActivePlayers: number = 0;
    hasUp: boolean = false;
    hasDown: boolean = false;
    private instanceId: string;
    private offset: number = 0;

    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    constructor() {
      super();
      const self = this;
      this.instanceId = PmRanking._instanceId;

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
      if (playerId != undefined) {
        this.playerId = playerId;
        this._setPlayerRanks(playerId);
      } else {
        userDetailsService.subscribe(updateOnce, this.instanceId);
      }
      function updateOnce() {
        let playerId = userDetailsService.userDetails.id;
        if (playerId === undefined) {
          throw new Error("No user id available to set player ranking");
        }
        self.playerId = playerId;
        self._setPlayerRanks(playerId);
        userDetailsService.unsubscribe(self.instanceId);
      }

      this.render();
    }

    _setPlayerRanks(playerId: number) {
      const rankingService = new FetchService(this.player_ranks_url);
      rankingService
        .get<Array<RankData>>()
        .then((data) => {
          const list = data.filter((item) => {
            return (
              item.id === playerId || !(item.score === 0 || item.icon === "")
            );
          });
          this.playerRank = list.findIndex((item) => item.id === playerId) + 1;

          this.allPlayerRanks = list.map(setPlayerRankDetails);
          this.totalActivePlayers = this.allPlayerRanks.length;
          this.selectPlayerRanks(this.offset);
        })
        .finally(() => {
          this.isReady = true;
          this.render();
        });
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
          data.totalActivePlayers
        } players.
            </strong>
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
                  "pm-Ranking-listitem--current": item.id === data.playerId,
                  "pm-Ranking-listitem--topPlayer": item.topPlayer,
                })}
              >
                <img
                  class="pm-Ranking-img"
                  src=${item.iconSrc}
                  width="64"
                  height="64"
                  alt=${item.iconAlt}
                />

                <strong class="pm-Ranking-rank">${item.score}</strong>
                <span class="pm-Ranking-status">
                  ${item.active === 0
                    ? html`
                        <small title="bit icon has expired">Inactive</small>
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
        playerRank: this.playerRank,
        playerId: this.playerId,
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

    selectPlayerRanks(offset: number) {
      let start = Math.max(this.playerRank - 1 - offset - this.range / 2, 0);
      let end = Math.max(
        this.playerRank - 1 - offset + this.range / 2,
        this.range
      );
      this.playerRanks = this.allPlayerRanks.slice(start, end);
      this.hasUp = start > 1;
      this.hasDown = end < this.allPlayerRanks.length;
    }

    selectPlayerRanksUp() {
      this.offset = this.offset + this.range;
      this.selectPlayerRanks(this.offset);
      this.render();
    }

    selectPlayerRanksDown() {
      this.offset = this.offset - this.range;
      this.selectPlayerRanks(this.offset);
      this.render();
    }
  }
);
