import FetchService from "../site/fetch.service";
import userDetailsService from "../site/user-details.service";
import { html, render } from "lit";
import { classMap } from "lit/directives/class-map.js";
import "./ranking.css";
const tag = "pm-ranking";
let lastInstanceId = 0;
customElements.define(
  tag,
  class PmRanking extends HTMLElement {
    constructor() {
      super();
      this.player_ranks_url = "";
      this.isReady = false;
      this.hasError = false;
      this.errorMessage = "";
      this.range = 15;
      this.playerRanks = [];
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
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }
    _setPlayerRanks() {
      const rankingService = new FetchService(
        `${this.player_ranks_url}?count=${this.range}`
      );
      return rankingService
        .get()
        .then((playerStats) => {
          this.playerRanks = playerStats.rank_slice.map(setPlayerRankDetails);
        })
        .catch(() => {
          this.hasError = true;
          this.errorMessage = "Error getting the player ranks data.";
        })
        .finally(() => {
          this.isReady = true;
          this.render();
        });
      function setPlayerRankDetails(item) {
        const playerRank = Object.assign(item);
        return playerRank;
      }
    }
    template(data) {
      return html`
        <section class="pm-Ranking">
          <h2 class="u-textCenter">Your Direct Competition</h2>
          <p>Other active players within your range.</p>
          ${contents()}
        </section>
      `;
      function contents() {
        if (!data.isReady) {
          return html` loading... `;
        }
        if (data.hasError) {
          return html` error: ${data.errorMessage} `;
        }
        return html`
          <div class="pm-Ranking-list" role="list">
          ${items()}
          </div>
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
                })}
              >
                <strong class="pm-Ranking-rank">${item.score}</strong>
                <div class="pm-Ranking-img">
                  <pm-player-bit player=${item.id}></pm-player-bit>
                </div>
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
        playerId: this.playerId,
        playerRanks: this.playerRanks,
      };
    }
    render() {
      render(this.template(this.data), this);
    }
  }
);
