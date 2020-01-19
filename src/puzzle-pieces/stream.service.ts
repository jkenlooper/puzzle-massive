import { interpret } from "@xstate/fsm";

import FetchService from "../site/fetch.service";
import { puzzleBitsService } from "../puzzle-bits/puzzle-bits.service";
import { puzzleStreamMachine } from "./puzzle-stream-machine";
import userDetailsService from "../site/user-details.service";

// Set ping interval to be one less minute than 5.
const PING_INTERVAL = 4 * 60 * 1000;

// Set the reconnect interval to be 5 seconds.
const RECONNECT_INTERVAL = 5 * 1000;

export interface PieceMovementData {
  id: number;
  parent?: number;
  s?: number;
  x?: number;
  y?: number;
  r?: number;
  karma?: number; // from PuzzleService piece/move/rejected
}

export interface BitMovementData {
  id: number;
  x: number;
  y: number;
}

// event types that the stream service will send
enum EventType {
  ping = "ping",
  move = "move",
  // The 'message' is the default if no event type was set
  message = "message",
  // Connection is open
  open = "open",
  // Error with connecting
  error = "error",
}

interface PongResponse {
  message: string;
  data?: {
    latency: number;
  };
  name: string;
}

type Broadcaster = (topic: symbol, data?: any) => void;

type PuzzleId = string;
type PlayerId = number;
interface PuzzleStreamMap {
  [index: string]: PuzzleStream;
}

type SocketStatusCallback = () => any;
type PieceUpdateCallback = (data: PieceMovementData) => any;
type PingCallback = (data: string) => any;
const socketDisconnected = Symbol("socket/disconnected");
const socketConnected = Symbol("socket/connected");
const socketReconnecting = Symbol("socket/reconnecting");
const pieceUpdate = Symbol("piece/update");
const pingTopic = Symbol("ping");
const topics = {
  "socket/disconnected": socketDisconnected,
  "socket/connected": socketConnected,
  "socket/reconnecting": socketReconnecting,
  "piece/update": pieceUpdate,
  ping: pingTopic,
};

class PuzzleStream {
  private eventSource: EventSource;
  private readonly puzzleId: PuzzleId;
  private pingToken: string = "";
  private broadcast: Broadcaster;
  private pingIntervalId: number | undefined;
  private reconnectIntervalId: number | undefined;
  private puzzleStreamService: any;

  constructor(puzzleId: PuzzleId, broadcast: Broadcaster) {
    this.puzzleId = puzzleId;
    this.broadcast = broadcast;

    this.eventSource = this.getEventSource(this.puzzleId);

    this.puzzleStreamService = interpret(puzzleStreamMachine).start();
    this.puzzleStreamService.subscribe(this.handleStateChange.bind(this));
  }
  get playerId(): PlayerId | undefined {
    return userDetailsService.userDetails.id;
  }

  private getEventSource(puzzleId: PuzzleId) {
    const eventSource = new EventSource(`/stream/puzzle/${puzzleId}/`, {
      withCredentials: false,
    });
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

  private destroyEventSource() {
    window.clearTimeout(this.pingIntervalId);

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

  private handleStateChange(state) {
    console.log(`puzzle-stream: ${state.value}`);
    switch (state.value) {
      case "connecting":
        // Send a ping to the server every second while connecting.
        state.actions.forEach((action) => {
          switch (action.type) {
            case "setEventSource":
              this.eventSource = this.getEventSource(this.puzzleId);
              break;
            case "broadcastReconnecting":
              this.broadcast(socketReconnecting);
              break;
          }
        });
        this.sendPing(1000);
        break;
      case "connected":
        state.actions.forEach((action) => {
          switch (action.type) {
            case "startPingInterval":
              // Start sending a ping to server with the default PING_INTERVAL.
              this.sendPing();
              break;
            case "broadcastPlayerLatency":
              this.broadcastPlayerLatency();
              break;
            case "broadcastConnected":
              this.broadcast(socketConnected);
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
            case "broadcastDisconnected":
              this.broadcast(socketDisconnected);
              break;
          }
        });
        break;
      case "inactive":
        break;
      case "invalid":
        break;
      default:
        break;
    }
  }

  private handlePingEvent(messageEvent: any) {
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
  private broadcastPlayerLatency() {
    const pong = new FetchService(`/newapi/ping/puzzle/${this.puzzleId}/`);
    pong
      .patch<PongResponse>({ token: this.pingToken })
      .then((response) => {
        if (response && response.name === "success" && response.data) {
          this.broadcast(pingTopic, response.data.latency);
        }
      })
      .catch((err) => {
        console.error("error sending pong", err);
        // TODO: ignore error with sending ping?
      });
  }

  private handleMoveEvent(messageEvent: any) {
    // any = MessageEvent
    const textline = messageEvent.data;
    const lines = textline.split("\n");
    lines.forEach((line) => {
      const items = line.split(",");
      items.forEach((item) => {
        let values = item.split(":");
        if (values.length === 7) {
          // puzzle_id, piece_id, x, y, r, parent, status
          const pieceData: PieceMovementData = {
            id: Number(values[1]),
          };
          if (values[5] !== "") {
            pieceData.parent = Number(values[5]);
          }
          if (values[6] !== "") {
            // s for stacked
            pieceData.s = Number(values[6]);
          }
          if (values[2] !== "") {
            pieceData.x = Number(values[2]);
          }
          if (values[3] !== "") {
            pieceData.y = Number(values[3]);
          }
          // TODO: Add pieceData.r from values[4] when rotate of pieces is enabled
          this.broadcast(pieceUpdate, pieceData);
        } else if (values.length === 4) {
          const bitData: BitMovementData = {
            id: parseInt(values[1]),
            x: parseInt(values[2]),
            y: parseInt(values[3]),
          };
          puzzleBitsService.bitUpdate(bitData);
        }
      });
    });
  }

  private handleMessageEvent(message: Event) {
    console.log("generic message from event source", message);
  }
  private handleOpenEvent() {
    // connection to the event source has opened
    this.puzzleStreamService.send("SUCCESS");
  }
  private handleErrorEvent(message: Event) {
    console.error(
      "Failed to connect to event stream. Is Redis running?",
      message
    );
    this.puzzleStreamService.send("ERROR");
  }

  private reconnectTimeout() {
    this.broadcast(socketReconnecting);
    window.clearTimeout(this.reconnectIntervalId);
    this.reconnectIntervalId = window.setTimeout(() => {
      this.puzzleStreamService.send("RECONNECT");
    }, RECONNECT_INTERVAL);
  }

  private sendPing(interval = PING_INTERVAL) {
    window.clearTimeout(this.pingIntervalId);
    const ping = new FetchService(`/newapi/ping/puzzle/${this.puzzleId}/`);
    ping
      .postForm({})
      .then(() => {
        this.pingIntervalId = window.setTimeout(
          this.sendPing.bind(this),
          interval
        );
      })
      .catch((err) => {
        console.error("error sending ping", err);
        // TODO: ignore error with sending ping?
      });
  }
}

let lastInstanceId = 0;
class StreamService {
  static get _instanceId(): string {
    return `stream-service ${lastInstanceId++}`;
  }
  private instanceId: string;
  private puzzleStreams: PuzzleStreamMap = {};

  // topics
  [socketDisconnected]: Map<string, SocketStatusCallback> = new Map();
  [socketConnected]: Map<string, SocketStatusCallback> = new Map();
  [socketReconnecting]: Map<string, SocketStatusCallback> = new Map();
  [pieceUpdate]: Map<string, PieceUpdateCallback> = new Map();
  [pingTopic]: Map<string, PingCallback> = new Map();

  constructor() {
    this.instanceId = StreamService._instanceId;
  }

  connect(puzzleId: PuzzleId): void {
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
          console.log("Existing puzzle stream is closed. Reconnecting");
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

  _broadcast(topic: symbol, data?: any) {
    this[topic].forEach((fn /*, id*/) => {
      fn(data);
    });
  }

  subscribe(
    topicString: string,
    fn: SocketStatusCallback | PieceUpdateCallback,
    id: string
  ) {
    const topic = topics[topicString];
    if (topic === undefined) {
      throw new Error(`Cannot subscribe to the '${topicString}'`);
    }
    // Add the fn to listeners
    this[topic].set(id, fn);
  }

  unsubscribe(topicString: string, id: string) {
    const topic = topics[topicString];
    if (topic === undefined) {
      throw new Error(`Cannot unsubscribe from the '${topicString}'`);
    }
    // remove fn from listeners
    this[topic].delete(id);
  }
}
export const streamService = new StreamService();
