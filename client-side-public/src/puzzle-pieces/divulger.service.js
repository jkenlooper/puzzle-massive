/* Deprecated.  Use stream.service instead. */

import { puzzleBitsService } from "../puzzle-bits/puzzle-bits.service";

// proxy_read_timeout should match the config from nginx and should be greater than 10
const PROXY_READ_TIMEOUT = 60;
const MAX_PINGS = 13;

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

type SocketStatusCallback = () => any;
type PieceUpdateCallback = (data: PieceMovementData) => any;
const socketMax = Symbol("socket/max");
const socketDisconnected = Symbol("socket/disconnected");
const socketConnected = Symbol("socket/connected");
const socketReconnecting = Symbol("socket/reconnecting");
const pieceUpdate = Symbol("piece/update");
const topics = {
  "socket/max": socketMax,
  "socket/disconnected": socketDisconnected,
  "socket/connected": socketConnected,
  "socket/reconnecting": socketReconnecting,
  "piece/update": pieceUpdate,
};

class DivulgerService {
  puzzleId: string | undefined;
  // Keep track of the last message sent for keeping the connection open with a ping
  private lastMessageSent: number = 0;
  private stalePuzzleTimeout: number = 0;
  private pingServerIntervalID: number = 0;
  private pingCount: number = 0;
  ws: WebSocket | undefined;

  // topics
  [socketMax]: Map<string, SocketStatusCallback> = new Map();
  [socketDisconnected]: Map<string, SocketStatusCallback> = new Map();
  [socketConnected]: Map<string, SocketStatusCallback> = new Map();
  [socketReconnecting]: Map<string, SocketStatusCallback> = new Map();
  [pieceUpdate]: Map<string, PieceUpdateCallback> = new Map();

  constructor() {}

  _init(puzzleId) {
    if (this.puzzleId === undefined) {
      this.puzzleId = puzzleId;
      this.ws = new WebSocket(
        `ws://${window.location.host}/divulge/${this.puzzleId}/`
      );
      this._connect();
    }
  }

  _connect() {
    if (this.ws === undefined || this.puzzleId === undefined) {
      return;
    }
    if (this.pingCount >= MAX_PINGS) {
      window.clearInterval(this.pingServerIntervalID);
      this._broadcast(socketDisconnected);
      // Reset the pingCount so it can be connected again
      this.pingCount = 0;
      // TODO: show a disconnected message
      return;
    }

    this.ws.onopen = this.onOpenSocket.bind(this);
    this.ws.onclose = this.onCloseSocket.bind(this);
    this.ws.onmessage = this.onMessageSocket.bind(this);
  }

  ping(puzzleId) {
    this._init(puzzleId);
    if (this.ws === undefined || this.puzzleId === undefined) {
      return;
    }
    if (this.ws.readyState > 1) {
      // Websocket is closed or closing, so reconnect
      this._connect();
    }
    if (this.ws.readyState === 0) {
      window.setTimeout(() => {
        this.ping(puzzleId);
      }, 500);
    } else {
      // websocket is connected (readyState === 1)
      this.ws.send(this.puzzleId);
    }
  }

  onOpenSocket() {
    if (this.ws === undefined || this.puzzleId === undefined) {
      return;
    }
    this._broadcast(socketConnected);
    this.ws.send(this.puzzleId);
    window.clearInterval(this.pingServerIntervalID);
    this.pingServerIntervalID = this._pingServer();
  }

  onCloseSocket() {
    window.clearInterval(this.pingServerIntervalID);
    if (this.pingCount < MAX_PINGS) {
      // Try to reconnect in 15 seconds
      setTimeout(this._connect, 1000 * 15);
      this._broadcast(socketReconnecting);
      // Update the pingCount so it doesn't just try to continually connect forever
      this.pingCount = this.pingCount + 1;
    } else {
      this._broadcast(socketDisconnected);
    }
  }

  onMessageSocket(msg) {
    this.lastMessageSent = new Date().getTime();
    window.clearTimeout(this.stalePuzzleTimeout);
    this.stalePuzzleTimeout = window.setTimeout(function () {
      // TODO: Puzzle piece data may have moved away from redis storage if the
      // puzzle has been stale for 30 minutes.
    }, 30 * 60 * 1000);

    if (msg.data === "MAX") {
      this._broadcast(socketMax);
      return;
    }

    this.pingCount = 0;
    // this.ws.send('received')
    this.handleMovementString(msg.data);
  }

  _pingServer(): number {
    const self = this;
    // send ping requests every 50 seconds to keep the connection to the proxied websocket open
    const checkInterval = 10;
    // Set the poll interval to be 2 seconds less than the checkInterval
    const pollIntervalMs = (checkInterval - 2) * 1000;
    const interval = (PROXY_READ_TIMEOUT - checkInterval) * 1000;
    return window.setInterval(function () {
      // Prevent keeping the connection open if nothing is happening
      const currentTime = new Date().getTime();
      if (
        !self.lastMessageSent ||
        self.lastMessageSent < currentTime - interval
      ) {
        self.pingCount = self.pingCount + 1;
        if (self.pingCount < MAX_PINGS) {
          if (self.ws !== undefined && self.puzzleId !== undefined) {
            self.ws.send("ping");
          }
        }
        self.lastMessageSent = new Date().getTime();
      }
    }, pollIntervalMs);
  }

  handleMovementString(textline) {
    let lines = textline.split("\n");
    lines.forEach((line) => {
      // let line = String(line)
      let items = line.split(",");
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
          this._broadcast(pieceUpdate, pieceData);
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
export const divulgerService = new DivulgerService();
