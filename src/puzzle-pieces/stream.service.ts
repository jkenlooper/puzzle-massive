import { interpret } from "@xstate/fsm";

import FetchService from "../site/fetch.service";
import { puzzleBitsService } from "../puzzle-bits/puzzle-bits.service";
import { puzzleStreamMachine } from "./puzzle-stream-machine";

const PING_INTERVAL = 5 * 60 * 1000;
//const PING_INTERVAL = 10 * 1000;

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

type Broadcaster = (topic: symbol, data?: any) => void;

type PuzzleId = string;
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
  private readonly eventSource: EventSource;
  private readonly puzzleId: PuzzleId;
  private broadcast: Broadcaster;
  private pingIntervalId: number | undefined;
  private puzzleStreamService: any;

  constructor(puzzleId: PuzzleId, broadcast: Broadcaster) {
    this.puzzleId = puzzleId;
    this.puzzleStreamService = interpret(puzzleStreamMachine).start();
    this.puzzleStreamService.subscribe((state) => {
      console.log(`state: ${state}`, state);
      switch (state.value) {
        case "connecting":
          this.pollReadyState();
          break;
        case "connected":
          state.actions.forEach((action) => {
            if (action.type === "startPing") {
              this.sendPing();
            }
          });
          break;
        default:
          break;
      }
    });
    this.broadcast = broadcast;

    // TODO: does the CORS withCredentials mean it passes the cookies or not?
    this.eventSource = new EventSource(`/stream/puzzle/${puzzleId}/`, {
      withCredentials: false,
    });

    this.eventSource.addEventListener(
      EventType.ping,
      this.handlePingEvent.bind(this),
      false
    );

    this.eventSource.addEventListener(
      EventType.move,
      this.handleMoveEvent.bind(this),
      false
    );

    this.eventSource.addEventListener(
      EventType.message,
      this.handleMessageEvent.bind(this),
      false
    );
    this.eventSource.addEventListener(
      EventType.open,
      this.handleOpenEvent.bind(this),
      false
    );
    this.eventSource.addEventListener(
      EventType.error,
      this.handleErrorEvent.bind(this),
      false
    );
    console.log("readyState", this.readyState);
  }

  get readyState() {
    console.log("get readyState", this, this.eventSource);
    if (!this.eventSource) {
      return EventSource.CONNECTING;
    }
    return this.eventSource.readyState;
  }

  disconnect() {
    console.log("disconnect", this.puzzleId);
    window.clearTimeout(this.pingIntervalId);
    this.eventSource.removeEventListener(
      EventType.ping,
      this.handlePingEvent,
      false
    );
    this.eventSource.close();
    this.puzzleStreamService.stop();
  }

  private handlePingEvent(message: Event) {
    console.log("The ping is:", message);
    this.broadcast(pingTopic, message);
    // TODO: parse the message and find matching ping from the user if there
    // is one.  Send a pong request.
  }

  private handleMoveEvent(message: Event) {
    const textline = ""; // TODO: get textline from message
    console.log("The move is:", message);

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
  private handleOpenEvent(message: Event) {
    // connection to the event source has opened
    console.log("open event", message);
    //this.sendPing();
  }
  private handleErrorEvent(message: Event) {
    console.log(
      "Failed to connect to event stream. Is Redis running?",
      message
    );
    window.clearTimeout(this.pingIntervalId);
  }
  private sendPing() {
    console.log("pinging", this.puzzleId);
    const ping = new FetchService(`/newapi/ping/puzzle/${this.puzzleId}/`);
    ping
      .postForm({})
      .then(() => {
        this.pingIntervalId = window.setTimeout(
          this.sendPing.bind(this),
          PING_INTERVAL
        );
      })
      .catch((err) => {
        console.error("error sending ping", err);
        // TODO: ignore error with sending ping?
      });
  }
  private pollReadyState() {
    console.log("pollReadyState");
    switch (this.readyState) {
      case EventSource.CONNECTING:
        window.setTimeout(this.pollReadyState.bind(this), 100);
        break;
      case EventSource.OPEN:
        this.puzzleStreamService.send("SUCCESS");
        break;
      case EventSource.CLOSED:
        break;
    }
    const ping = new FetchService(`/newapi/ping/puzzle/${this.puzzleId}/`);
    ping.postForm({});
  }
}

class StreamService {
  private puzzleStreams: PuzzleStreamMap = {};

  //private pingServerIntervalID: number = 0;

  // topics
  [socketDisconnected]: Map<string, SocketStatusCallback> = new Map();
  [socketConnected]: Map<string, SocketStatusCallback> = new Map();
  [socketReconnecting]: Map<string, SocketStatusCallback> = new Map();
  [pieceUpdate]: Map<string, PieceUpdateCallback> = new Map();
  [pingTopic]: Map<string, PingCallback> = new Map();

  constructor() {}

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
