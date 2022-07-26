import { html, render } from "lit";
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
    template(data) {
      if (data.latency <= 300) {
        return html`
          <div class="pm-PuzzleLatency">
            <small class="pm-PuzzleLatency-label">latency:</small>
            <span class="pm-PuzzleLatency-value-green">${data.latency}</span>
          </div>
        `;
      } else if (data.latency >= 301 && data.latency <= 999) {
        return html`
          <div class="pm-PuzzleLatency">
            <small class="pm-PuzzleLatency-label">latency:</small>
            <span class="pm-PuzzleLatency-value-yellow">${data.latency}</span>
          </div>
        `;
      } else if (data.latency >= 1000) {
        return html`
          <div class="pm-PuzzleLatency">
            <small class="pm-PuzzleLatency-label">latency:</small>
            <span class="pm-PuzzleLatency-value-red">${data.latency}</span>
          </div>
        `;
      } else {
        return html`
          <div class="pm-PuzzleLatency">
            <small class="pm-PuzzleLatency-label">latency:</small>
            <span class="pm-PuzzleLatency-value">${data.latency}</span>
          </div>
        `;
      }
    }
    get data() {
      return {
        latency: this.latency,
      };
    }
    render() {
      render(this.template(this.data), this);
    }
    onPuzzlePing(latency) {
      this.latency = latency;
      this.render();
    }
    onPuzzlePingError() {
      this.latency = "--";
    }
    disconnectedCallback() {
      const topics = ["puzzle/ping", "puzzle/ping/error"];
      topics.forEach((topic) => {
        streamService.unsubscribe(topic, this.instanceId);
      });
    }
  }
);
