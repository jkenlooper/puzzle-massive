import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import { streamService } from "../puzzle-pieces/stream.service";
import "./puzzle-karma-alert.css";
const tag = "pm-puzzle-karma-alert";
let lastInstanceId = 0;
customElements.define(tag, class PmPuzzleKarmaAlert extends HTMLElement {
    constructor() {
        super();
        this.isActive = false;
        this.karma = 1;
        this.karmaLevel = 2;
        this.instanceId = PmPuzzleKarmaAlert._instanceId;
        streamService.subscribe("karma/updated", this.updateKarmaValue.bind(this), this.instanceId);
        this.render();
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    template(data) {
        return html `
        <div
          data-karma-level=${data.karmaLevel}
          class=${classMap({
            "pm-PuzzleKarmaAlert-status": true,
            "is-active": data.isActive,
        })}
        >
          ${data.karma}
        </div>
      `;
    }
    get data() {
        return {
            isActive: this.isActive,
            karma: this.karma,
            karmaLevel: this.karmaLevel,
        };
    }
    render() {
        render(this.template(this.data), this);
    }
    updateKarmaValue(data) {
        const karma = data.karma;
        if (karma && typeof karma === "number") {
            this.karma = karma;
            window.clearTimeout(this.karmaStatusIsActiveTimeout);
            const karmaLevel = Math.floor(karma / 6);
            this.karmaLevel = karmaLevel;
            this.isActive = true;
            // Hide the karma status after a timeout when it is normal
            if (karmaLevel > 2) {
                this.karmaStatusIsActiveTimeout = window.setTimeout(() => {
                    this.isActive = false;
                    this.render();
                }, 5000);
            }
            this.render();
        }
    }
    disconnectedCallback() {
        streamService.unsubscribe("karma/updated", this.instanceId);
    }
});
