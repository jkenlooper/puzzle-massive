import { html, render } from "lit-html";
import { interpret } from "@xstate/fsm";

import { streamService } from "../puzzle-pieces/stream.service";
import { puzzleService } from "../puzzle-pieces/puzzle.service";
import { Status } from "../site/puzzle-images.service";
import { puzzleAlertMachine } from "./puzzle-alert-machine";

import "./puzzle-alert.css";

enum AlertStatus {
  none = "none",
  connecting = "connecting",
  error = "error",
  connected = "connected",
  reconnecting = "reconnecting",
  disconnected = "disconnected",
  blocked = "blocked",
  completed = "completed",
  frozen = "frozen",
  deleted = "deleted",
  in_queue = "in_queue",
  invalid = "invalid",
}

interface TemplateData {
  status: AlertStatus;
  message: string | undefined;
  reason: string | undefined;
}

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
    private puzzleStatus: Status | undefined;
    private status: AlertStatus = AlertStatus.connecting;
    private message: string | undefined;
    private reason: string | undefined;
    private puzzleAlertService: any;
    private blockedTimer: number = 0;
    private blockedTimeout: number | undefined;
    private readonly timeoutForCompletedAlert = 5000;

    constructor() {
      super();
      this.instanceId = PmPuzzleAlerts._instanceId;

      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      this.puzzleId = puzzleId ? puzzleId.value : "";

      const puzzleStatus = this.attributes.getNamedItem("status");
      this.puzzleStatus = puzzleStatus
        ? <Status>(<unknown>parseInt(puzzleStatus.value))
        : undefined;
      if (!this.puzzleStatus || this.puzzleStatus !== Status.ACTIVE) {
        return;
      }

      puzzleService.subscribe(
        "piece/move/blocked",
        this.onMoveBlocked.bind(this),
        this.instanceId
      );
      streamService.subscribe(
        "socket/disconnected",
        this.onDisconnected.bind(this),
        this.instanceId
      );
      streamService.subscribe(
        "socket/reconnecting",
        this.onReconnecting.bind(this),
        this.instanceId
      );
      streamService.subscribe(
        "socket/connected",
        this.onConnected.bind(this),
        this.instanceId
      );
      streamService.subscribe(
        "puzzle/status",
        this.onPuzzleStatus.bind(this),
        this.instanceId
      );
      streamService.subscribe(
        "puzzle/ping/error",
        this.onPuzzlePingError.bind(this),
        this.instanceId
      );

      streamService.connect(this.puzzleId);

      this.puzzleAlertService = interpret(puzzleAlertMachine).start();
      this.puzzleAlertService.subscribe(this.handleStateChange.bind(this));

      this.render();
    }

    private handleStateChange(state) {
      //console.log(`puzzle-alert: ${state.value}`);
      switch (state.value) {
        case "connecting":
          state.actions.forEach((action) => {
            switch (action.type) {
              case "setStatusReconnecting":
                this.status = AlertStatus.reconnecting;
                break;
              case "setStatusError":
                this.status = AlertStatus.error;
                break;
              default:
                break;
            }
          });
          break;
        case "active":
          state.actions.forEach((action) => {
            switch (action.type) {
              case "setStatusConnected":
                this.status = AlertStatus.connected;
                break;
              case "showPieceMoveBlocked":
                this.status = AlertStatus.blocked;
                break;
              case "hidePieceMoveBlocked":
                // Reset back to connected state.
                this.status = AlertStatus.connected;
                break;
              default:
                break;
            }
          });
          break;
        case "inactive":
          state.actions.forEach((action) => {
            switch (action.type) {
              case "setStatusCompleted":
                this.status = AlertStatus.completed;
                break;
              case "hideCompletedAlert":
                this.status = AlertStatus.none;
                break;
              case "setStatusInQueue":
                this.status = AlertStatus.in_queue;
                break;
              case "setStatusFrozen":
                this.status = AlertStatus.frozen;
                break;
              case "setStatusDeleted":
                this.status = AlertStatus.deleted;
                break;
              case "setInvalid":
                this.status = AlertStatus.invalid;
                break;
            }
          });
          break;
        case "disconnected":
          state.actions.forEach((action) => {
            switch (action.type) {
              case "setStatusDisconnected":
                this.status = AlertStatus.disconnected;
                break;
            }
          });
          break;
      }
      this.render();
    }

    template(data: TemplateData) {
      return html`
        ${data.status && data.status !== AlertStatus.connected
          ? showAlert(data.status)
          : ""}
      `;
      function showAlert(status: AlertStatus) {
        if (status === AlertStatus.none) {
          return "";
        }
        return html`
          <section class="pm-PuzzleAlert-section">
            <h1><small>Alerts</small></h1>
            ${getAlert(status)}
          </section>
        `;
        function getAlert(status: AlertStatus) {
          switch (status) {
            case AlertStatus.connecting:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--connecting"
                >
                  <h2>Connecting&hellip;</h2>
                  <p>
                    Puzzle piece movement updates are disabled while connecting.
                  </p>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.error:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--error"
                >
                  <h2>Error</h2>
                  <p>
                    Please reload.
                  </p>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.reconnecting:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--reconnecting"
                >
                  <h2>Reconnecting&hellip;</h2>
                  <p>
                    Puzzle piece movement updates are disabled while
                    reconnecting.
                  </p>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.disconnected:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--disconnected"
                >
                  <h2>Disconnected</h2>
                  <p>
                    Puzzle piece movement updates are disabled. Try reloading
                    the page.
                  </p>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.blocked:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--blocked"
                >
                  <h2>Piece movement blocked</h2>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.completed:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--statusCompleted"
                >
                  <h2>Puzzle Completed</h2>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.frozen:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--statusFrozen"
                >
                  <h2>Puzzle Frozen</h2>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.deleted:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--statusDeleted"
                >
                  <h2>Puzzle Deleted</h2>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.in_queue:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--statusInQueue"
                >
                  <h2>Puzzle In Queue</h2>
                  ${getDetails()}
                </div>
              `;
              break;
            case AlertStatus.invalid:
              return html`
                <div
                  class="pm-PuzzleAlert-message pm-PuzzleAlert-message--invalid"
                >
                  <h2>Invalid</h2>
                  <p>
                    Connection to puzzle piece updates is invalid.
                  </p>
                  ${getDetails()}
                </div>
              `;
              break;
            default:
              return "";
          }
          function getDetails() {
            return html`
              ${data.message
                ? html`
                    <p>
                      ${data.message}
                    </p>
                  `
                : ""}
              ${data.reason
                ? html`
                    <p>
                      ${data.reason}
                    </p>
                  `
                : ""}
            `;
          }
        }
      }
    }
    get data(): TemplateData {
      return {
        status: this.status,
        message: this.message,
        reason: this.reason,
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    onMoveBlocked(data) {
      if (data.msg) {
        this.message = data.msg;
      } else {
        this.message =
          "Your puzzle piece movements on this puzzle have been blocked. Please wait.";
      }

      this.reason = data.reason;
      if (data.expires && typeof data.expires === "number") {
        const expireDate = new Date(data.expires * 1000);
        this.reason =
          this.reason + ` Expires: ${expireDate.toLocaleTimeString()}`;
      }

      if (data.timeout && typeof data.timeout === "number") {
        const now = new Date().getTime();
        const remainingTime = Math.max(0, this.blockedTimer - now);
        const timeout = data.timeout * 1000 + remainingTime;
        window.clearTimeout(this.blockedTimeout);
        this.blockedTimer = now + timeout;
        this.blockedTimeout = window.setTimeout(() => {
          this.puzzleAlertService.send("PIECE_MOVE_BLOCKED_TIMER");
        }, timeout);
      }

      this.puzzleAlertService.send("PIECE_MOVE_BLOCKED");
      this.render();
    }

    onDisconnected() {
      this.message = "";
      this.reason = "";
      this.puzzleAlertService.send("DISCONNECTED");
    }

    onReconnecting(data) {
      this.message = `Reconnect attempt: ${data}`;
      this.reason = "";
      this.puzzleAlertService.send("RECONNECTING");
    }

    onConnected() {
      this.message = "";
      this.reason = "";
      this.puzzleAlertService.send("SUCCESS");
    }

    onPuzzleStatus(status: Status) {
      this.message = "";
      this.reason = "";
      switch (status) {
        case Status.COMPLETED:
          this.puzzleAlertService.send("PUZZLE_COMPLETED");
          window.setTimeout(() => {
            this.puzzleAlertService.send("PUZZLE_COMPLETED_TIMER");
          }, this.timeoutForCompletedAlert);
          break;
        case Status.IN_QUEUE:
          this.puzzleAlertService.send("PUZZLE_IN_QUEUE");
          break;
        case Status.FROZEN:
          this.puzzleAlertService.send("PUZZLE_FROZEN");
          break;
        case Status.DELETED_REQUEST:
          this.puzzleAlertService.send("PUZZLE_DELETED");
          break;
        default:
          this.puzzleAlertService.send("PUZZLE_INVALID");
          break;
      }
    }
    onPuzzlePingError() {
      this.message = "Failed to get a response when pinging the puzzle API.";
      this.reason = "";
      this.puzzleAlertService.send("PING_ERROR");
    }

    disconnectedCallback() {
      const topics = [
        //"socket/max",
        "socket/disconnected",
        "socket/connected",
        "socket/reconnecting",
        "puzzle/status",
        "puzzle/ping/error",
      ];
      topics.forEach((topic) => {
        streamService.unsubscribe(topic, this.instanceId);
      });
      puzzleService.unsubscribe("piece/move/blocked", this.instanceId);
    }
  }
);
