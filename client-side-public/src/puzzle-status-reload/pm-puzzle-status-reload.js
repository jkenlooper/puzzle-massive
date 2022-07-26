import { html, render } from "lit";
import { streamService } from "../puzzle-pieces/stream.service";
import { Status } from "../site/puzzle-images.service";
import "./puzzle-status-reload.css";
const tag = "pm-puzzle-status-reload";
let lastInstanceId = 0;
customElements.define(
  tag,
  class PmPuzzleStatusReload extends HTMLElement {
    constructor() {
      super();
      this.instanceId = PmPuzzleStatusReload._instanceId;
      const puzzleIdAttribute = this.attributes.getNamedItem("puzzle-id");
      this.puzzleId = puzzleIdAttribute ? puzzleIdAttribute.value : "";
      const puzzleStatusAttribute = this.attributes.getNamedItem("status");
      this.puzzleStatus = puzzleStatusAttribute
        ? parseInt(puzzleStatusAttribute.value)
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
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }
    onPuzzleStatus(status) {
      if (status !== undefined) {
        // The status may be undefined if the puzzle is invalid.
        this.status = status;
        this.render();
      }
    }
    template(data) {
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
    get data() {
      return {
        status: this.status,
        hasChanged: this.status !== this.puzzleStatus,
      };
    }
    render() {
      render(this.template(this.data), this.shadowRoot);
    }
    connectedCallback() {
      this.render();
    }
    disconnectedCallback() {
      streamService.unsubscribe("puzzle/status", this.instanceId);
    }
  }
);
