import { html, render } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { streamService } from "../puzzle-pieces/stream.service";
import "./puzzle-latency.css";
const tag = "pm-puzzle-latency";
let lastInstanceId = 0;
customElements.define(
  tag,
  class PmPuzzleLatency extends HTMLElement {
    constructor() {
      super();
      this.latency = "--";
      this.status = "";
      this.instanceId = PmPuzzleLatency._instanceId;
      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      this.puzzleId = puzzleId ? puzzleId.value : "";
      streamService.subscribe(
        "puzzle/ping",
        this.onPuzzlePing.bind(this),
        this.instanceId
      );
      streamService.subscribe(
        "puzzle/ping/error",
        this.onPuzzlePingError.bind(this),
        this.instanceId
      );
      streamService.connect(this.puzzleId);
      this.render();
    }
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }

    getStatus(latency) {
      if (latency <= 300) {
        return "good";
      } else if (latency >= 301 && latency <= 999) {
        return "okay";
      } else if (latency >= 1000) {
        return "bad";
      } else {
        return "";
      }
    }

    template(data) {
      return html`
        <div class="pm-PuzzleLatency">
          <small class="pm-PuzzleLatency-label">latency:</small>
          <span
            class=${classMap({
              "pm-PuzzleLatency-value": true,
              "is-good": data.status == "good",
              "is-okay": data.status == "okay",
              "is-bad": data.status == "bad",
            })}
            >${data.latency}</span
          >
        </div>
      `;
    }
    get data() {
      return {
        latency: this.latency,
        status: this.status,
      };
    }
    render() {
      render(this.template(this.data), this);
    }
    onPuzzlePing(latency) {
      this.latency = latency;
      this.status = this.getStatus(latency);
      this.render();
    }
    onPuzzlePingError() {
      this.latency = "--";
      this.status = "";
    }
    disconnectedCallback() {
      const topics = ["puzzle/ping", "puzzle/ping/error"];
      topics.forEach((topic) => {
        streamService.unsubscribe(topic, this.instanceId);
      });
    }
  }
);
