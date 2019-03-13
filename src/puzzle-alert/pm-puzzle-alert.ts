import { divulgerService } from "../puzzle-pieces/divulger.service";

import "./puzzle-alert.css";

interface Alerts {
  container: HTMLElement;
  max: HTMLElement;
  reconnecting: HTMLElement;
  disconnected: HTMLElement;
  blocked: HTMLElement;
}
const BLOCKED_MSG_NOT_SPECIFIED =
  "It would seem that recent piece moves from you were flagged as unhelpful on this puzzle.";

const tag = "pm-puzzle-alert";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleAlerts extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    private puzzleId: string;
    private blocked: boolean = false;
    private alerts: Alerts;

    constructor() {
      super();
      this.instanceId = PmPuzzleAlerts._instanceId;

      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      this.puzzleId = puzzleId ? puzzleId.value : "";

      // For this component the template can be rendered server-side.
      const template = this.querySelector("template");
      if (!template) {
        throw new Error(`No template found for ${tag}`);
      }

      const alertEl = template.content.cloneNode(true);
      this.appendChild(alertEl);

      const alert_selectors = {
        container: "#puzzle-pieces-alert",
        max: "#puzzle-pieces-alert-max",
        reconnecting: "#puzzle-pieces-alert-reconnecting",
        disconnected: "#puzzle-pieces-alert-disconnected",
        blocked: "#puzzle-pieces-alert-blocked",
      };

      const alerts = {
        container: document.createElement("div"),
        max: document.createElement("div"),
        reconnecting: document.createElement("div"),
        disconnected: document.createElement("div"),
        blocked: document.createElement("div"),
      };
      Object.entries(alert_selectors).forEach(([name, selector]) => {
        const el = this.querySelector(selector);
        if (!el) {
          throw new Error(
            `Missing child element '${selector}' needed for ${tag}`
          );
        }
        alerts[name] = el;
      });

      this.alerts = alerts;

      // @ts-ignore: minpubsub
      window.subscribe("karma/updated", this.onKarmaUpdate.bind(this)); // PuzzleService
      // @ts-ignore: minpubsub
      window.subscribe("piece/move/blocked", this.onMoveBlocked.bind(this)); // PuzzleService
      divulgerService.subscribe(
        "socket/max",
        this.onMax.bind(this),
        this.instanceId
      );
      divulgerService.subscribe(
        "socket/disconnected",
        this.onDisconnected.bind(this),
        this.instanceId
      );
      divulgerService.subscribe(
        "socket/reconnecting",
        this.onReconnecting.bind(this),
        this.instanceId
      );
      divulgerService.subscribe(
        "socket/connected",
        this.onConnected.bind(this),
        this.instanceId
      );
      divulgerService.ping(this.puzzleId);
    }

    onKarmaUpdate(data) {
      // Remove blocked alert if present when going from 0 to 2
      if (data.karma > 0 && this.blocked) {
        this.alerts.container.classList.remove("is-active");
        this.alerts.blocked.classList.remove("is-active");
        this.blocked = false;
      }
    }

    onMoveBlocked(data) {
      this.alerts.container.classList.add("is-active");
      this.alerts.blocked.classList.add("is-active");
      const msgEl = this.alerts.blocked.querySelector(
        "#puzzle-pieces-alert-blocked-msg"
      );
      const reasonEl = this.alerts.blocked.querySelector(
        "#puzzle-pieces-alert-blocked-reason"
      );
      if (!msgEl) {
        throw new Error(
          `Missing child element '#puzzle-pieces-alert-blocked-msg' needed for ${tag}`
        );
      }
      if (!reasonEl) {
        throw new Error(
          `Missing child element '#puzzle-pieces-alert-blocked-reason' needed for ${tag}`
        );
      }

      if (data.msg) {
        msgEl.innerHTML = data.msg;
      } else {
        msgEl.innerHTML = BLOCKED_MSG_NOT_SPECIFIED;
      }
      if (data.reason) {
        reasonEl.innerHTML = data.reason;
      } else {
        reasonEl.innerHTML = "";
      }
      if (data.expires && typeof data.expires === "number") {
        const expireDate = new Date(data.expires * 1000);
        reasonEl.innerHTML =
          reasonEl.innerHTML + ` Expires: ${expireDate.toLocaleTimeString()}`;
      }
      if (data.timeout && typeof data.timeout === "number") {
        window.setTimeout(() => {
          this.alerts.container.classList.remove("is-active");
          this.alerts.blocked.classList.remove("is-active");
          this.blocked = false; // TODO: Only for karma updates?
        }, data.timeout * 1000);
      }
      this.blocked = true;
    }

    onMax() {
      this.alerts.container.classList.add("is-active");
      this.alerts.max.classList.add("is-active");
    }

    onDisconnected() {
      this.alerts.container.classList.add("is-active");
      this.alerts.disconnected.classList.add("is-active");
      this.alerts.reconnecting.classList.remove("is-active");
    }

    onReconnecting() {
      this.alerts.container.classList.add("is-active");
      this.alerts.reconnecting.classList.add("is-active");
      this.alerts.disconnected.classList.remove("is-active");
    }

    onConnected() {
      this.alerts.container.classList.remove("is-active");
      this.alerts.max.classList.remove("is-active");
      this.alerts.reconnecting.classList.remove("is-active");
      this.alerts.disconnected.classList.remove("is-active");
    }

    disconnectedCallback() {
      const topics = [
        "socket/max",
        "socket/disconnected",
        "socket/connected",
        "socket/reconnecting",
      ];
      topics.forEach((topic) => {
        divulgerService.unsubscribe(topic, this.instanceId);
      });
    }
  }
);
