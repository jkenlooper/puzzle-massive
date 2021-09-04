import { html, render } from "lit-html";
import {
  playerStatsService,
  PlayerStatsData,
} from "../site/player-stats.service";

interface TemplateData {
  playerStats: PlayerStatsData;
}

const tag = "pm-total-active-player-count";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmTotalActivePlayerCount extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    hasError: boolean = false;
    isReady: boolean = false;
    count: number = 0;

    constructor() {
      super();
      this.instanceId = PmTotalActivePlayerCount._instanceId;
    }

    template(data: TemplateData) {
      if (!data.playerStats.isReady) {
        return html``;
      }
      if (data.playerStats.hasError) {
        return html``;
      }
      if (!data.playerStats.totalActivePlayers) {
        return html``;
      }
      return html`
        <strong>${data.playerStats.totalActivePlayers}</strong>
        <small>
          active
          ${data.playerStats.totalActivePlayers > 1
            ? html` players `
            : html` player `}
        </small>
      `;
    }

    get data(): TemplateData {
      return {
        playerStats: playerStatsService.data,
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    connectedCallback() {
      playerStatsService.subscribe(this.render.bind(this), this.instanceId);
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      playerStatsService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
  }
);
