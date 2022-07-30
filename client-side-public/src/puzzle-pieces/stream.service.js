var _a, _b, _c, _d, _e, _f, _g, _h;
import { interpret } from "@xstate/fsm";
import FetchService from "../site/fetch.service";
import { puzzleBitsService } from "../puzzle-bits/puzzle-bits.service";
import {
  puzzleStreamMachine,
  RECONNECT_INTERVAL,
} from "./puzzle-stream-machine";
import userDetailsService from "../site/user-details.service";
import { Status } from "../site/puzzle-images.service";
// Ping interval should be at least one less minute than 5 to keep the
// connection.
const PING_INTERVAL = 0.5 * 60 * 1000;
// event types that the stream service will send
var EventType;
(function (EventType) {
  EventType["invalid"] = "invalid";
  EventType["ping"] = "ping";
  EventType["move"] = "move";
  EventType["karma"] = "karma";
  // The 'message' is the default if no event type was set
  EventType["message"] = "message";
  // Connection is open
  EventType["open"] = "open";
  // Error with connecting
  EventType["error"] = "error";
})(EventType || (EventType = {}));
const socketDisconnected = Symbol("socket/disconnected");
const socketConnected = Symbol("socket/connected");
const socketReconnecting = Symbol("socket/reconnecting");
const pieceUpdate = Symbol("piece/update");
const karmaUpdated = Symbol("karma/updated");
const puzzlePingTopic = Symbol("puzzle/ping");
const puzzlePingErrorTopic = Symbol("puzzle/ping/error");
const puzzleStatusTopic = Symbol("puzzle/status");
const topics = {
  "socket/disconnected": socketDisconnected,
  "socket/connected": socketConnected,
  "socket/reconnecting": socketReconnecting,
  "piece/update": pieceUpdate,
  "karma/updated": karmaUpdated,
  "puzzle/ping": puzzlePingTopic,
  "puzzle/ping/error": puzzlePingErrorTopic,
  "puzzle/status": puzzleStatusTopic,
};
class PuzzleStream {
  constructor(puzzleId, broadcast) {
    this.pingToken = "";
    this.puzzleId = puzzleId;
    this.broadcast = broadcast;
    this.eventSource = this.getEventSource(this.puzzleId);
    this.puzzleStreamService = interpret(puzzleStreamMachine).start();
    this.puzzleStreamService.subscribe(this.handleStateChange.bind(this));
  }
  get playerId() {
    return userDetailsService.userDetails.id;
  }
  getEventSource(puzzleId) {
    const eventSource = new EventSource(`/stream/puzzle/${puzzleId}/`, {
      withCredentials: false,
    });
    window.addEventListener("beforeunload", this.handleUnload.bind(this));
    eventSource.addEventListener(
      EventType.invalid,
      this.handleInvalidEvent.bind(this),
      false
    );
    eventSource.addEventListener(
      EventType.ping,
      this.handlePingEvent.bind(this),
      false
    );
    eventSource.addEventListener(
      EventType.move,
      this.handleMoveEvent.bind(this),
      false
    );
    eventSource.addEventListener(
      EventType.karma,
      this.handleKarmaEvent.bind(this),
      false
    );
    eventSource.addEventListener(
      EventType.message,
      this.handleMessageEvent.bind(this),
      false
    );
    eventSource.addEventListener(
      EventType.open,
      this.handleOpenEvent.bind(this),
      false
    );
    eventSource.addEventListener(
      EventType.error,
      this.handleErrorEvent.bind(this),
      false
    );
    return eventSource;
  }
  get readyState() {
    return this.eventSource.readyState;
  }
  disconnect() {
    this.puzzleStreamService.send("CLOSE");
    this.puzzleStreamService.stop();
  }
  destroyEventSource() {
    window.clearTimeout(this.pingIntervalId);
    this.eventSource.removeEventListener(
      EventType.invalid,
      this.handleInvalidEvent,
      false
    );
    this.eventSource.removeEventListener(
      EventType.ping,
      this.handlePingEvent,
      false
    );
    this.eventSource.removeEventListener(
      EventType.move,
      this.handleMoveEvent,
      false
    );
    this.eventSource.removeEventListener(
      EventType.move,
      this.handleKarmaEvent,
      false
    );
    this.eventSource.removeEventListener(
      EventType.message,
      this.handleMessageEvent,
      false
    );
    this.eventSource.removeEventListener(
      EventType.open,
      this.handleOpenEvent,
      false
    );
    this.eventSource.removeEventListener(
      EventType.error,
      this.handleErrorEvent,
      false
    );
    this.eventSource.close();
  }
  handleUnload() {
    // Close the connection when the visitor leaves the page.
    this.eventSource.close();
  }
  handleStateChange(state) {
    switch (state.value) {
      case "connecting":
        // Send a ping to the server every second while connecting.
        state.actions.forEach((action) => {
          switch (action.type) {
            case "sendPing":
              this.sendPing(1000);
              break;
            case "setEventSource":
              this.eventSource = this.getEventSource(this.puzzleId);
              break;
            case "broadcastPingError":
              this.broadcastPingError();
              break;
          }
        });
        break;
      case "connected":
        state.actions.forEach((action) => {
          switch (action.type) {
            case "destroyEventSource":
              this.destroyEventSource();
              break;
            case "sendPing":
              // Start sending a ping to server with the default PING_INTERVAL.
              this.sendPing(PING_INTERVAL);
              break;
            case "broadcastPlayerLatency":
              this.broadcastPlayerLatency();
              break;
            case "broadcastConnected":
              this.broadcast(socketConnected);
              break;
            case "broadcastPuzzleStatus":
              this.broadcastPuzzleStatus();
              break;
          }
        });
        break;
      case "disconnected":
        state.actions.forEach((action) => {
          switch (action.type) {
            case "destroyEventSource":
              this.destroyEventSource();
              break;
            case "startReconnectTimeout":
              this.reconnectTimeout();
              break;
            case "broadcastReconnecting":
              this.broadcast(socketReconnecting, state.context.reconnectCount);
              break;
            case "broadcastDisconnected":
              this.broadcast(socketDisconnected);
              break;
          }
        });
        break;
      case "inactive":
        state.actions.forEach((action) => {
          switch (action.type) {
            case "destroyEventSource":
              this.destroyEventSource();
              break;
            case "broadcastPuzzleStatus":
              this.broadcastPuzzleStatus();
              break;
          }
        });
        break;
      case "invalid":
        state.actions.forEach((action) => {
          switch (action.type) {
            case "destroyEventSource":
              this.destroyEventSource();
              break;
            case "broadcastPuzzleStatus":
              this.broadcastPuzzleStatus();
              break;
          }
        });
        break;
      default:
        break;
    }
  }
  handleInvalidEvent() {
    // any = MessageEvent
    this.puzzleStreamService.send("INVALID");
  }
  handlePingEvent(messageEvent) {
    // any = MessageEvent
    if (!this.playerId) {
      // Skip sending a pong when no playerId has been set yet from userDetailsService.
      return;
    }
    const playerIdPart = `${this.playerId}:`;
    if (messageEvent && messageEvent.data.startsWith(playerIdPart)) {
      this.pingToken = messageEvent.data.substr(playerIdPart.length);
      this.puzzleStreamService.send("PONG");
    }
  }
  broadcastPingError() {
    this.broadcast(puzzlePingErrorTopic);
  }
  broadcastPlayerLatency() {
    const pong = new FetchService(`/newapi/ping/puzzle/${this.puzzleId}/`);
    pong
      .patch({ token: this.pingToken })
      .then((response) => {
        if (response) {
          switch (response.name) {
            case "success":
              this.broadcast(
                puzzlePingTopic,
                response.data && response.data.latency
              );
              break;
            case "ignored":
              // do nothing
              break;
            case "invalid":
              this.puzzleStreamService.send("INVALID");
              break;
            case "error":
              this.puzzleStreamService.send("ERROR");
              break;
            default:
              break;
          }
        } else {
          this.puzzleStreamService.send("ERROR");
        }
      })
      .catch((err) => {
        console.error("error sending pong", err);
        // TODO: handle invalid
        this.puzzleStreamService.send("ERROR");
        // TODO: ignore error with sending ping?
      });
  }
  broadcastPuzzleStatus() {
    if (this.puzzleStatus !== undefined) {
      this.broadcast(puzzleStatusTopic, this.puzzleStatus);
    } else {
      // TODO: An undefined puzzleStatus will show the invalid alert.
      this.broadcast(puzzleStatusTopic, this.puzzleStatus);
    }
  }
  injectMoves(message) {
    this.handleMoveEvent({
      data: message,
    });
  }
  handleMoveEvent(messageEvent) {
    // any = MessageEvent
    const textline = messageEvent.data;
    const lines = textline.split("\n");
    const pieceMoves = [];
    lines.forEach((line) => {
      const items = line.split(",");
      items.forEach((item) => {
        let values = item.split(":");
        if (values.length === 7) {
          // puzzle_id, piece_id, x, y, r, parent, status
          const pieceData = {
            id: Number(values[1]),
          };
          if (values[5] !== "") {
            pieceData.parent = Number(values[5]);
          }
          if (values[6] !== "") {
            // s for status which could be:
            //   2 for stacked
            //   1 for immovable
            //   0 for reset
            pieceData.s = Number(values[6]);
          }
          if (values[2] !== "") {
            pieceData.x = Number(values[2]);
          }
          if (values[3] !== "") {
            pieceData.y = Number(values[3]);
          }
          // TODO: Add pieceData.r from values[4] when rotate of pieces is enabled
          //this.broadcast(pieceUpdate, pieceData);
          pieceMoves.push(pieceData);
        } else if (values.length === 4) {
          const bitData = {
            id: parseInt(values[1]),
            x: parseInt(values[2]),
            y: parseInt(values[3]),
          };
          puzzleBitsService.bitUpdate(bitData);
        }
      });
    });
    if (pieceMoves.length) {
      this.broadcast(pieceUpdate, pieceMoves);
    }
  }
  handleKarmaEvent(message) {
    if (message.data && typeof message.data === "string") {
      const [_player, _piece, _karma, _karma_change] = message.data
        .split(":")
        .map((item) => {
          return Number(item);
        });
      if (_player === this.playerId && _karma_change) {
        const karmaData = {
          id: _piece,
          karma: _karma,
          karmaChange: _karma_change,
        };
        this.broadcast(karmaUpdated, karmaData);
      }
    }
  }
  handleMessageEvent(message) {
    //console.log("message from event source", message);
    if (message.data && message.data.startsWith("status:")) {
      this.puzzleStatus = parseInt(message.data.substr("status:".length));
      switch (this.puzzleStatus) {
        case Status.COMPLETED:
          this.puzzleStreamService.send("PUZZLE_COMPLETED");
          break;
        case Status.FROZEN:
          this.puzzleStreamService.send("PUZZLE_FROZEN");
          break;
        case Status.ACTIVE:
          this.puzzleStreamService.send("PUZZLE_ACTIVE");
          break;
        case Status.MAINTENANCE:
          this.puzzleStreamService.send("PUZZLE_NOT_ACTIVE");
          break;
        case Status.DELETED_REQUEST:
          this.puzzleStreamService.send("PUZZLE_DELETED");
          break;
        default:
          break;
      }
    } else {
      console.log("generic message from event source", message);
    }
  }
  handleOpenEvent() {
    // connection to the event source has opened
    this.puzzleStreamService.send("SUCCESS");
  }
  handleErrorEvent(error) {
    switch (this.readyState) {
      case EventSource.CONNECTING:
        console.error("Failed to connect to puzzle stream.", error);
        this.puzzleStreamService.send("ERROR");
        break;
      case EventSource.OPEN:
        console.error("puzzle stream error.", error);
        this.puzzleStreamService.send("ERROR");
        break;
      case EventSource.CLOSED:
        console.error("puzzle stream closed.", error, this.puzzleStatus);
        if (this.puzzleStatus === undefined) {
          // The connection could have been closed because of a failure to
          // connect.
          this.puzzleStreamService.send("ERROR");
        } else if (this.puzzleStatus === Status.ACTIVE) {
          // The last set puzzleStatus was active.  The connection may have been
          // closed because of a connection error.
          this.puzzleStreamService.send("ERROR");
        } else {
          // Don't need to send this since the puzzleStatus was probably already
          // sent.
          //this.puzzleStreamService.send("PUZZLE_NOT_ACTIVE");
        }
        break;
      default:
        this.puzzleStreamService.send("ERROR");
        break;
    }
  }
  reconnectTimeout() {
    window.clearTimeout(this.reconnectIntervalId);
    this.puzzleStreamService.send("WAITING_TO_RECONNECT");
    this.reconnectIntervalId = window.setTimeout(() => {
      // RECONNECT is sent first since it is behind a cond in the machine.
      this.puzzleStreamService.send("RECONNECT");
      // RECONNECT_TIMEOUT is sent next in case no actions happen for the
      // RECONNECT.  This way the alert message for disconnected is not shown
      // between each attempt at reconnecting.
      this.puzzleStreamService.send("RECONNECT_TIMEOUT");
    }, RECONNECT_INTERVAL);
  }
  sendPing(interval = PING_INTERVAL) {
    window.clearTimeout(this.pingIntervalId);
    const ping = new FetchService(`/newapi/ping/puzzle/${this.puzzleId}/`);
    ping
      .postForm({})
      .then(() => {
        this.pingIntervalId = window.setTimeout(() => {
          this.puzzleStreamService.send("PING");
        }, interval);
      })
      .catch((err) => {
        if (err) {
          switch (err.name) {
            case "invalid":
              this.puzzleStreamService.send("INVALID");
              break;
            case "error":
              console.error("error sending ping", err);
              this.puzzleStreamService.send("ERROR");
              break;
            default:
              console.error("error sending ping", err);
              this.puzzleStreamService.send("ERROR");
              break;
          }
        } else {
          console.error("error sending ping", err);
          this.puzzleStreamService.send("PING_ERROR");
          this.pingIntervalId = window.setTimeout(() => {
            this.puzzleStreamService.send("PING");
          }, interval);
        }
      });
  }
}
let lastInstanceId = 0;
class StreamService {
  constructor() {
    this.puzzleStreams = {};
    // topics
    this[_a] = new Map();
    this[_b] = new Map();
    this[_c] = new Map();
    this[_d] = new Map();
    this[_e] = new Map();
    this[_f] = new Map();
    this[_g] = new Map();
    this[_h] = new Map();
    this.instanceId = StreamService._instanceId;
  }
  static get _instanceId() {
    return `stream-service ${lastInstanceId++}`;
  }
  connect(puzzleId) {
    const existingPuzzleStream = this.puzzleStreams[puzzleId];
    if (existingPuzzleStream) {
      switch (existingPuzzleStream.readyState) {
        case EventSource.CONNECTING:
        case EventSource.OPEN:
          // already called connect
          return;
          break;
        case EventSource.CLOSED:
          existingPuzzleStream.disconnect();
          //console.log("Existing puzzle stream is closed. Reconnecting");
          break;
        default:
          console.error("wat?", existingPuzzleStream);
          return;
          break;
      }
    }
    // The puzzleStream uses the playerId when pinging the server.
    userDetailsService.subscribe(() => {
      // The puzzleStream doesn't need to act on any updates to the user/player.
      userDetailsService.unsubscribe(this.instanceId);
    }, this.instanceId);
    const puzzleStream = new PuzzleStream(puzzleId, this._broadcast.bind(this));
    this.puzzleStreams[puzzleId] = puzzleStream;
  }
  _broadcast(topic, data) {
    this[topic].forEach((fn /*, id*/) => {
      fn(data);
    });
  }
  subscribe(topicString, fn, id) {
    const topic = topics[topicString];
    if (topic === undefined) {
      throw new Error(`Cannot subscribe to the '${topicString}'`);
    }
    // Add the fn to listeners
    this[topic].set(id, fn);
  }
  unsubscribe(topicString, id) {
    const topic = topics[topicString];
    if (topic === undefined) {
      throw new Error(`Cannot unsubscribe from the '${topicString}'`);
    }
    // remove fn from listeners
    this[topic].delete(id);
  }
  injectMoves(puzzleId, message) {
    this.puzzleStreams[puzzleId].injectMoves(message);
  }
}
(_a = socketDisconnected),
  (_b = socketConnected),
  (_c = socketReconnecting),
  (_d = pieceUpdate),
  (_e = karmaUpdated),
  (_f = puzzlePingTopic),
  (_g = puzzlePingErrorTopic),
  (_h = puzzleStatusTopic);
export const streamService = new StreamService();
