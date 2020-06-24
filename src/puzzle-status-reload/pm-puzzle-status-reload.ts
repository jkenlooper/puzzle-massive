import { html, render } from "lit-html";

import { streamService } from "../puzzle-pieces/stream.service";
import { Status } from "../site/puzzle-images.service";

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
      console.log("puzzleStatusAttribute", puzzleStatusAttribute);
      this.puzzleStatus = puzzleStatusAttribute
        ? <Status>(<unknown>parseInt(puzzleStatusAttribute.value))
        : Status.MAINTENANCE;
      this.status = this.puzzleStatus;
      console.log("puzzle status", this.puzzleStatus);

      streamService.connect(this.puzzleId);
      streamService.subscribe(
        "puzzle/status",
        this.onPuzzleStatus.bind(this),
        this.instanceId
      );
      this.render();
    }

    onPuzzleStatus(status: Status) {
      console.log("onPuzzleStatus", status);
      this.status = status;
      this.render();
    }

    template(data: TemplateData) {
      return html` ${data.status} `;
    }

    get data(): TemplateData {
      return {
        status: this.status,
        hasChanged: this.status !== this.puzzleStatus,
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    disconnectedCallback() {
      streamService.unsubscribe("puzzle/status", this.instanceId);
    }
  }
);
