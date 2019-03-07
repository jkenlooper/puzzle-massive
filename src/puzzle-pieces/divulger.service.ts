// proxy_read_timeout should match the config from nginx and should be greater than 10
const PROXY_READ_TIMEOUT = 60;
const MAX_PINGS = 13;

interface PieceMovementData {
  id: number;
  parent?: number;
  s?: number;
  x?: number;
  y?: number;
}

interface BitMovementData {
  id: string;
  x: string;
  y: string;
}

type SocketStatusCallback = () => any;
const socketMax = Symbol("socket/max");

class DivulgerService {
  puzzleId: string;
  // Keep track of the last message sent for keeping the connection open with a ping
  private lastMessageSent: number = 0;
  private stalePuzzleTimeout: number = 0;
  private pingServerIntervalID: number = 0;
  private pingCount: number = 0;
  ws: WebSocket;

  // topics
  [socketMax]: Map<string, SocketStatusCallback> = new Map();

  /*
      window.subscribe('piece/update', onPieceUpdate)
      window.publish("piece/update/" + pieceData.id, [pieceData]);
      window.subscribe("bit/update", this._onBitUpdate.bind(this));

      window.subscribe('socket/max', onMax)
      window.subscribe('socket/disconnected', onDisconnected)
      window.subscribe('socket/connected', onConnected)
      window.subscribe('socket/reconnecting', onReconnecting)
   */

  constructor(puzzleId) {
    this.puzzleId = puzzleId;
    this.ws = new WebSocket(
      `ws://${window.location.host}/divulge/${this.puzzleId}/`
    );
  }

  connect() {
    if (this.pingCount >= MAX_PINGS) {
      // console.log('disconnected')
      window.clearInterval(this.pingServerIntervalID);
      // @ts-ignore: minpubsub
      window.publish("socket/disconnected");
      // Reset the pingCount so it can be connected again
      this.pingCount = 0;
      // TODO: show a disconnected message
      return;
    }

    // console.log('connect new ws')
    // this.ws = new WebSocket(`ws://${window.location.host}/newapi/puzzle/${puzzleId}/updates/`)
    this.ws = new WebSocket(
      `ws://${window.location.host}/divulge/${this.puzzleId}/`
    );
    this.ws.onopen = this.onOpenSocket.bind(this);
    this.ws.onclose = this.onCloseSocket.bind(this);
    this.ws.onmessage = this.onMessageSocket.bind(this);
  }

  onOpenSocket() {
    // console.log('connected')
    // @ts-ignore: minpubsub
    window.publish("socket/connected");
    this.ws.send(this.puzzleId);
    window.clearInterval(this.pingServerIntervalID);
    this.pingServerIntervalID = this.pingServer();
  }

  onCloseSocket() {
    window.clearInterval(this.pingServerIntervalID);
    if (this.pingCount < MAX_PINGS) {
      // console.log('onCloseSocket... reconnecting in 15')
      // Try to reconnect in 15 seconds
      setTimeout(this.connect, 1000 * 15);
      // @ts-ignore: minpubsub
      window.publish("socket/reconnecting");
      // Update the pingCount so it doesn't just try to continually connect forever
      this.pingCount = this.pingCount + 1;
    } else {
      // console.log('onCloseSocket... disconnected')
      // @ts-ignore: minpubsub
      window.publish("socket/disconnected");
    }
  }

  onMessageSocket(msg) {
    this.lastMessageSent = new Date().getTime();
    window.clearTimeout(this.stalePuzzleTimeout);
    this.stalePuzzleTimeout = window.setTimeout(function() {
      // TODO: Puzzle piece data may have moved away from redis storage if the
      // puzzle has been stale for 30 minutes.
    }, 30 * 60 * 1000);

    // console.log('msg', msg, msg.data)
    if (msg.data === "MAX") {
      // @ts-ignore: minpubsub
      window.publish("socket/max");
      // TODO: this._broadcast([socketMax])
      return;
    }

    this.pingCount = 0;
    // this.ws.send('received')
    this.handleMovementString(msg.data);
  }

  pingServer(): number {
    const self = this;
    // send ping requests every 50 seconds to keep the connection to the proxied websocket open
    const checkInterval = 10;
    // Set the poll interval to be 2 seconds less than the checkInterval
    const pollIntervalMs = (checkInterval - 2) * 1000;
    const interval = (PROXY_READ_TIMEOUT - checkInterval) * 1000;
    return window.setInterval(function() {
      // Prevent keeping the connection open if nothing is happening
      const currentTime = new Date().getTime();
      if (
        !self.lastMessageSent ||
        self.lastMessageSent < currentTime - interval
      ) {
        self.pingCount = self.pingCount + 1;
        // console.log('ping', lastMessageSent, self.pingCount)
        if (self.pingCount < MAX_PINGS) {
          self.ws.send("ping");
        }
        self.lastMessageSent = new Date().getTime();
      }
      // console.log('poll', lastMessageSent)
    }, pollIntervalMs);
  }

  handleMovementString(textline) {
    let lines = textline.split("\n");
    lines.forEach(function(line) {
      // let line = String(line)
      let items = line.split(",");
      items.forEach(function(item) {
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
          // Publish on two topics. Subscribers that are only interested in
          // specific pieces, and any piece changes.
          // @ts-ignore: minpubsub
          window.publish("piece/update/" + pieceData.id, [pieceData]);
          // @ts-ignore: minpubsub
          window.publish("piece/update", [pieceData]);
        } else if (values.length === 4) {
          const bitData: BitMovementData = {
            id: values[1],
            x: values[2],
            y: values[3],
          };
          // @ts-ignore: minpubsub
          window.publish("bit/update", [bitData]); // used by PuzzleBitsService
        }
      });
    });
  }

  _broadcast(topic: symbol) {
    this[topic].forEach((fn /*, id*/) => {
      fn();
    });
  }

  subscribe(topic: symbol, fn: SocketStatusCallback, id: string) {
    //console.log("subscribe", fn, id);
    // Add the fn to listeners
    this[topic].set(id, fn);
  }

  unsubscribe(topic: symbol, id: string) {
    //console.log("unsubscribe", id);
    // remove fn from listeners
    this[topic].delete(id);
  }
}

export default DivulgerService;
