import reqwest from "reqwest";
import { streamService, PieceMovementData } from "./stream.service";

type PieceMovementId = number;

interface PieceMovement {
  id: PieceMovementId;
  piece: number;
  inProcess: boolean;
  token?: string;
  tokenRequest?: Function;
  moveRequest?: Function;
  fail?: boolean;
}

interface PieceMovements {
  [index: string]: PieceMovement;
}

interface DefaultPiece {
  g?: number;
  x: number;
  y: number;
  r: number;
  s?: number | null; // s for stacked
  b: number; // b for background
  w: number;
  h: number;
  // TODO: others
}

export interface PieceData extends DefaultPiece {
  id: number;
  active?: boolean;
  karma?: number | boolean; // response from move request
  karmaChange?: number | boolean; // response from move request
  origin?: any; // updated after piece movements
  pieceMovementId?: number; // updated after piece movements
}

interface Pieces {
  [index: number]: PieceData;
}

export interface KarmaData {
  id: number;
  karma: number;
  karmaChange: boolean;
}

enum PieceMoveErrorTypes {
  puzzleimmutable = "puzzleimmutable",
  sameplayerconcurrent = "sameplayerconcurrent",
  immovable = "immovable",
  piecequeue = "piecequeue",
  piecelock = "piecelock",
  invalid = "invalid",
  missing = "missing",
  expiredtoken = "expiredtoken",
  bannedusers = "bannedusers",
  invalidpiecemove = "invalidpiecemove",
  blockedplayer = "blockedplayer",
  proximity = "proximity",
}
export interface PieceMoveError {
  msg: string;
  type: PieceMoveErrorTypes;
  expires: number;
  timeout: number;
  reason: string;
  action: any; // {msg: string, url: string}
}

// For now this is set to one to prevent feature creep
const maxSelectedPieces = 1;

type PiecesUpdateCallback = (data: Array<PieceData>) => any;
type KarmaUpdatedCallback = (data: KarmaData) => any;
type PieceMoveRejectedCallback = (data: PieceData) => any;
type PieceMoveBlockedCallback = (data: PieceMoveError) => any;
type PiecesInfoToggleMovableCallback = (toggle: any) => any;
const piecesMutate = Symbol("pieces/mutate");
const karmaUpdated = Symbol("karma/updated");
const pieceMoveRejected = Symbol("piece/move/rejected");
const pieceMoveBlocked = Symbol("piece/move/blocked");
const piecesInfoToggleMovable = Symbol("pieces/info/toggle-movable");

const topics = {
  "pieces/mutate": piecesMutate,
  "karma/updated": karmaUpdated,
  "piece/move/rejected": pieceMoveRejected,
  "piece/move/blocked": pieceMoveBlocked,
  "pieces/info/toggle-movable": piecesInfoToggleMovable,
};

interface MoveRequestData {
  x: number;
  y: number;
  r?: number;
}

const pieceAttrsThatAreInt = ["g", "x", "y", "r", "s", "b", "w", "h", "rotate"];

let _pieceMovementId = 0;

class PuzzleService {
  // Pass in the url to the puzzle pieces
  private puzzleId: string = "";
  private pieceMovementQueue: Array<PieceMovementId> = [];
  private pieceMovements: PieceMovements = {};
  private pieceMovementProcessInterval: number | undefined = undefined;
  private pieces: Pieces = {};
  // @ts-ignore: piecesTimestamp will be used in the future
  private piecesTimestamp = "";
  private mark: string = "";
  private selectedPieces: Array<number> = [];
  private instanceId = "puzzleService";
  private _showMovable = false;

  [piecesMutate]: Map<string, PiecesUpdateCallback> = new Map();
  [karmaUpdated]: Map<string, KarmaUpdatedCallback> = new Map();
  [pieceMoveRejected]: Map<string, PieceMoveRejectedCallback> = new Map();
  [pieceMoveBlocked]: Map<string, PieceMoveBlockedCallback> = new Map();
  [piecesInfoToggleMovable]: Map<
    string,
    PiecesInfoToggleMovableCallback
  > = new Map();
  constructor() {
    streamService.subscribe(
      "piece/update",
      this.onPieceUpdate.bind(this),
      this.instanceId
    );
  }

  init(puzzleId) {
    this.puzzleId = puzzleId;
    return fetchPieces(this.puzzleId).then((data) => {
      let pieceData = JSON.parse(data);
      this.mark = pieceData.mark;
      pieceData.positions.forEach((piece) => {
        // set status
        Object.keys(piece)
          .filter((key) => {
            return pieceAttrsThatAreInt.includes(key);
          })
          .forEach((key) => {
            piece[key] = Number(piece[key]);
          });
        const defaultPiece: DefaultPiece = {
          x: 0,
          y: 0,
          r: 0,
          s: null,
          b: 1,
          w: 1,
          h: 1,
        };
        this.pieces[piece.id] = Object.assign(defaultPiece, piece);
      });
      this.piecesTimestamp = pieceData.timestamp.timestamp;
      //this._broadcast(piecesMutate, Object.values(this.pieces));
      return Object.values(this.pieces);
    });

    function fetchPieces(puzzleId) {
      return reqwest({
        url: `/newapi/puzzle-pieces/${puzzleId}/`,
        method: "get",
      });
    }
  }
  connect() {
    streamService.connect(this.puzzleId);
  }

  static get nextPieceMovementId() {
    _pieceMovementId++;
    return _pieceMovementId;
  }

  moveBy(pieceID, x, y, scale) {
    let piece = this.pieces[pieceID];
    if (!piece) {
      return;
    }
    piece.x = x / scale - piece.w / 2;
    piece.y = y / scale - piece.h / 2;

    this._broadcast(piecesMutate, [piece]);
  }

  private onKarmaUpdate(data: KarmaData) {
    let piece = this.pieces[data.id];
    Object.assign(piece, data);
    this._broadcast(piecesMutate, [piece]);
    this._broadcast(karmaUpdated, data);
  }

  private _broadcast(topic: symbol, data?: any) {
    this[topic].forEach((fn /*, id*/) => {
      fn(data);
    });
  }

  subscribe(
    topicString: string,
    fn:
      | PiecesUpdateCallback
      | KarmaUpdatedCallback
      | PieceMoveRejectedCallback
      | PiecesInfoToggleMovableCallback,
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

  private token(piece, mark) {
    const self = this;
    const puzzleId = this.puzzleId;
    const pieceMovementId = PuzzleService.nextPieceMovementId;
    const pieceMovement: PieceMovement = {
      id: pieceMovementId,
      piece: piece,
      inProcess: false,
    };

    pieceMovement.tokenRequest = function tokenRequest() {
      return reqwest({
        url: `/newapi/puzzle/${puzzleId}/piece/${piece}/token/`,
        data: { mark: mark },
        method: "get",
        type: "json",
      })
        .then((data) => {
          pieceMovement.token = data.token;
        })
        .fail((data) => {
          let responseObj;
          try {
            responseObj = JSON.parse(data.response);
          } catch (err) {
            responseObj = {
              reason: data.response,
            };
          }
          if (!responseObj.timeout) {
            const expire = new Date().getTime() / 1000 + 10;
            responseObj.expires = expire;
            responseObj.timeout = 10;
          }
          switch (responseObj.type) {
            case PieceMoveErrorTypes.piecelock:
            case PieceMoveErrorTypes.piecequeue:
              // TODO: If piece is locked then publish a 'piece/move/delayed' instead of blocked.
              // TODO: Set a timeout and clear if piece is moved.  Maybe
              // auto-scroll to the moved piece?
              break;
            case PieceMoveErrorTypes.sameplayerconcurrent:
              if (responseObj.action) {
                reqwest({ url: responseObj.action.url, method: "POST" });
              }
              break;
            case PieceMoveErrorTypes.bannedusers:
            case PieceMoveErrorTypes.expiredtoken:
            case PieceMoveErrorTypes.puzzleimmutable:
            default:
              self._broadcast(pieceMoveBlocked, responseObj);
          }
          pieceMovement.fail = true;
          self.onPieceMoveRejected({ id: piece });
        });
    };

    this.pieceMovements[pieceMovementId] = pieceMovement;
    this.pieceMovementQueue.push(pieceMovementId);

    this.processNextPieceMovement();

    return pieceMovementId;
  }

  private inPieceMovementQueue(piece) {
    return Object.values(this.pieceMovements).some((pieceMovement) => {
      return piece === pieceMovement.piece;
    });
  }

  private cancelMove(id, origin, pieceMovementId) {
    const self = this;
    const pieceMovement = this.pieceMovements[pieceMovementId];
    const puzzleId = this.puzzleId;
    if (!pieceMovement) {
      return;
    }
    //pieceMovement.fail = true
    pieceMovement.moveRequest = function cancelMoveRequest() {
      return reqwest({
        url: `/newapi/puzzle/${puzzleId}/piece/${id}/`,
        method: "GET",
        type: "json",
        error: function handleGetError() {
          if (origin) {
            const pieceMovementData: PieceMovementData = {
              id: id,
              x: origin.x,
              y: origin.y,
              r: origin.r,
            };
            self.onPieceMoveRejected(pieceMovementData);
          }
        },
        success: function handlePieceInfo(data) {
          const pieceMovementData: PieceMovementData = {
            id: id,
            x: data.x,
            y: data.y,
            r: data.r,
          };
          self.onPieceMoveRejected(pieceMovementData);
        },
      });
    };
  }

  private move(id, x, y, r, origin, pieceMovementId) {
    const pieceMovement = this.pieceMovements[pieceMovementId];
    const puzzleId = this.puzzleId;
    const self = this;
    if (!pieceMovement) {
      return;
    }

    pieceMovement.moveRequest = function moveRequest() {
      x = Math.round(Number(x));
      y = Math.round(Number(y));

      let data: MoveRequestData = { x: x, y: y };
      if (r !== "-") {
        r = parseInt(r, 10);
        data.r = r;
      }

      return reqwest({
        url: `/newapi/puzzle/${puzzleId}/piece/${id}/move/`,
        method: "PATCH",
        type: "json",
        data: data,
        headers: { Token: pieceMovement.token },
        error: function handlePatchError(patchError) {
          let responseObj;
          try {
            responseObj = JSON.parse(patchError.response);
          } catch (err) {
            responseObj = {
              reason: patchError.response,
            };
          }
          if (patchError.status === 429) {
            self._broadcast(pieceMoveBlocked, responseObj);
            self.onPieceMoveRejected({
              id: id,
              x: origin.x,
              y: origin.y,
              r: origin.r,
            });
          } else {
            const pieceMovementData: PieceMovementData = {
              id: id,
              x: origin.x,
              y: origin.y,
              r: origin.r,
              karma: responseObj.karma,
            };
            self.onPieceMoveRejected(pieceMovementData);
          }
          // Reject with piece info from server and fallback to origin if that also fails
          return reqwest({
            url: `/newapi/puzzle/${puzzleId}/piece/${id}/`,
            method: "GET",
            type: "json",
            data: data,
            error: function handleGetError() {
              if (origin) {
                self.onPieceMoveRejected({
                  id: id,
                  x: origin.x,
                  y: origin.y,
                  r: origin.r,
                });
              }
            },
            success: function handlePieceInfo(data) {
              const pieceMovementData: PieceMovementData = {
                id: id,
                x: data.x,
                y: data.y,
                r: data.r,
              };
              self.onPieceMoveRejected(pieceMovementData);
            },
          });
        },
        success: function(d) {
          self.onKarmaUpdate(d);
        },
      });
    };
  }

  isImmovable(pieceID) {
    return this.pieces[pieceID].s === 1;
  }
  isSelectable(pieceID) {
    return !this.isImmovable(pieceID) && this.selectedPieces.length === 0;
  }

  unSelectPiece(pieceID) {
    let index = this.selectedPieces.indexOf(pieceID);
    if (index !== -1) {
      // remove the pieceID from the array
      this.selectedPieces.splice(index, 1);
      this.pieces[pieceID].active = false;
      this.cancelMove(
        pieceID,
        this.pieces[pieceID].origin,
        this.pieces[pieceID].pieceMovementId
      );
    }
  }

  selectPiece(pieceID) {
    // TODO: move selectPiece to pm-puzzle-pieces?
    const index = this.selectedPieces.indexOf(pieceID);
    if (index === -1) {
      // add the pieceID to the end of the array
      this.selectedPieces.push(pieceID);
      this.pieces[pieceID].karma = false; // TODO: why set to false?
      this.pieces[pieceID].active = true;
      this.pieces[pieceID].origin = {
        x: this.pieces[pieceID].x,
        y: this.pieces[pieceID].y,
        r: this.pieces[pieceID].r,
      };
    } else {
      // remove the pieceID from the array
      this.selectedPieces.splice(index, 1);
      this.pieces[pieceID].active = false;
      this.cancelMove(
        pieceID,
        this.pieces[pieceID].origin,
        this.pieces[pieceID].pieceMovementId
      );
    }

    // Only allow a max amount of selected pieces
    if (this.selectedPieces.length > maxSelectedPieces) {
      this.selectedPieces
        .splice(0, this.selectedPieces.length - maxSelectedPieces)
        .forEach((pieceID) => {
          // all the pieces that were unselected also set to inactive
          this.pieces[pieceID].active = false;
          this.cancelMove(
            pieceID,
            this.pieces[pieceID].origin,
            this.pieces[pieceID].pieceMovementId
          );
        });
    }
    if (!this.inPieceMovementQueue(pieceID)) {
      // Only get a new token if this piece movement isn't already in the
      // queue.
      this.pieces[pieceID].pieceMovementId = this.token(pieceID, this.mark);
    }
    this._broadcast(piecesMutate, [this.pieces[pieceID]]);
  }

  dropSelectedPieces(x, y, scale) {
    // Update piece locations
    this.selectedPieces.forEach((pieceID) => {
      let piece = this.pieces[pieceID];
      piece.x = x / scale - piece.w / 2;
      piece.y = y / scale - piece.h / 2;
    });

    // Display the updates
    const pieces = this.selectedPieces.map((pieceID) => {
      return this.pieces[pieceID];
    });
    this._broadcast(piecesMutate, pieces);

    // Send the updates
    this.selectedPieces.forEach((pieceID) => {
      let piece = this.pieces[pieceID];
      this.move(
        pieceID,
        piece.x,
        piece.y,
        "-",
        piece.origin,
        piece.pieceMovementId
      );
    });

    // Reset the selectedPieces
    this.selectedPieces = [];
  }

  get showMovable() {
    return this._showMovable;
  }

  toggleMovable() {
    this._showMovable = !this._showMovable;
    this._broadcast(piecesInfoToggleMovable, this._showMovable);
  }

  private onPieceUpdate(data: PieceMovementData) {
    let piece = this.pieces[data.id];
    if (piece.active) {
      this.unSelectPiece(data.id);
    }
    piece = Object.assign(piece, data);
    piece.active = false;
    this._broadcast(piecesMutate, [piece]);
  }

  private onPieceMoveRejected(data: PieceMovementData) {
    let piece = this.pieces[data.id];
    piece.x = data.x || piece.origin.x;
    piece.y = data.y || piece.origin.y;
    piece.active = false;
    this._broadcast(pieceMoveRejected, data);
    this._broadcast(piecesMutate, [piece]);
  }

  private processNextPieceMovement() {
    if (!this.pieceMovementProcessInterval) {
      this.pieceMovementProcessInterval = window.setInterval(() => {
        // All done processing movements on the queue
        if (this.pieceMovementQueue.length === 0) {
          window.clearInterval(this.pieceMovementProcessInterval);
          this.pieceMovementProcessInterval = undefined;
          return;
        }

        const pieceMovementId = this.pieceMovementQueue[0];
        const pieceMovement = this.pieceMovements[pieceMovementId];

        const hasMoveRequest = !!pieceMovement.moveRequest;
        const hasTokenRequest = !!pieceMovement.tokenRequest;
        if (pieceMovement.fail) {
          this.pieceMovementQueue.shift();
          delete this.pieceMovements[pieceMovementId];
          return;
        }

        if (!pieceMovement.inProcess) {
          if (hasTokenRequest || hasMoveRequest) {
            // Mark that this pieceMovement is being processed
            pieceMovement.inProcess = true;
          }

          if (hasTokenRequest) {
            // need token
            const tokenRequest = <Function>pieceMovement.tokenRequest;
            tokenRequest().always(() => {
              pieceMovement.tokenRequest = undefined;
              pieceMovement.inProcess = false;
            });
          } else if (hasMoveRequest) {
            // ready to send movement
            const moveRequest = <Function>pieceMovement.moveRequest;
            moveRequest().always(() => {
              pieceMovement.moveRequest = undefined;
              this.pieceMovementQueue.shift();
              delete this.pieceMovements[pieceMovementId];
            });
          }
        }
      }, 100);
    }
  }
}
export const puzzleService = new PuzzleService();
