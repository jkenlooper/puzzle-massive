import { html, render } from "lit-html";
import { playerStatsService, } from "../site/player-stats.service";
const tag = "pm-total-active-player-count";
let lastInstanceId = 0;
customElements.define(tag, class PmTotalActivePlayerCount extends HTMLElement {
    constructor() {
        super();
        this.hasError = false;
        this.isReady = false;
        this.count = 0;
        this.instanceId = PmTotalActivePlayerCount._instanceId;
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    template(data) {
        if (!data.playerStats.isReady) {
            return html ``;
        }
        if (data.playerStats.hasError) {
            return html ``;
        }
        if (!data.playerStats.totalActivePlayers) {
            return html ``;
        }
        return html `
        <strong>${data.playerStats.totalActivePlayers}</strong>
        <small>
          active
          ${data.playerStats.totalActivePlayers > 1
            ? html ` players `
            : html ` player `}
        </small>
      `;
    }
    get data() {
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
});
