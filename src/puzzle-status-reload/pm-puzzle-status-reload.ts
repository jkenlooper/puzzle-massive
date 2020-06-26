import { html, render } from "lit-html";

import { streamService } from "../puzzle-pieces/stream.service";
import { Status } from "../site/puzzle-images.service";

import "./puzzle-status-reload.css";

interface TemplateData {
  status: Status;
  hasChanged: boolean;
}

const tag = "pm-puzzle-status-reload";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleStatusReload extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    private puzzleId: string;
    private status: Status;
    private readonly puzzleStatus: Status;

    constructor() {
      super();
      this.instanceId = PmPuzzleStatusReload._instanceId;

      const puzzleIdAttribute = this.attributes.getNamedItem("puzzle-id");
      this.puzzleId = puzzleIdAttribute ? puzzleIdAttribute.value : "";

      const puzzleStatusAttribute = this.attributes.getNamedItem("status");
      this.puzzleStatus = puzzleStatusAttribute
        ? <Status>(<unknown>parseInt(puzzleStatusAttribute.value))
        : Status.MAINTENANCE;
      this.status = this.puzzleStatus;

      this.attachShadow({ mode: "open" });

      streamService.connect(this.puzzleId);
      streamService.subscribe(
        "puzzle/status",
        this.onPuzzleStatus.bind(this),
        this.instanceId
      );
    }

    onPuzzleStatus(status: Status) {
      if (status !== undefined) {
        // The status may be undefined if the puzzle is invalid.
        this.status = status;
        this.render();
      }
    }

    template(data: TemplateData) {
      if (data.hasChanged) {
        return html`<div class="pm-PuzzleStatusReload">
          <slot class="pm-PuzzleStatusReload-slotReload" name="reload"></slot>
        </div>`;
      } else {
        return html`<div class="pm-PuzzleStatusReload">
          <slot class="pm-PuzzleStatusReload-slot"></slot>
        </div>`;
      }
    }

    get data(): TemplateData {
      return {
        status: this.status,
        hasChanged: this.status !== this.puzzleStatus,
      };
    }

    render() {
      render(this.template(this.data), <DocumentFragment>this.shadowRoot);
    }
    connectedCallback() {
      this.render();
    }

    disconnectedCallback() {
      streamService.unsubscribe("puzzle/status", this.instanceId);
    }
  }
);
