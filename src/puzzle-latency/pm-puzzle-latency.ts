import { html, render } from "lit-html";

import { streamService } from "../puzzle-pieces/stream.service";

import "./puzzle-latency.css";

interface TemplateData {
  latency: number | string;
}

const tag = "pm-puzzle-latency";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleLatency extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    private puzzleId: string;
    private latency: number | string = "--";

    constructor() {
      super();
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

    template(data: TemplateData) {
      return html`
        <div class="pm-PuzzleLatency">
          <small class="pm-PuzzleLatency-label">latency:</small>
          <span class="pm-PuzzleLatency-value">${data.latency}</span>
        </div>
      `;
    }

    get data(): TemplateData {
      return {
        latency: this.latency,
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    onPuzzlePing(latency: number) {
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
