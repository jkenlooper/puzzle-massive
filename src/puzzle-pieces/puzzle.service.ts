//import { interpret } from "@xstate/fsm";
import FetchService from "../site/fetch.service";
import { streamService, PieceMovementData } from "./stream.service";
//import { puzzlePieceMachine } from "./puzzle-piece-machine";

type PieceMovementId = number;

interface PieceMovement {
  id: PieceMovementId;
  piece: number;
  inProcess: boolean;
  token?: string;
  snap?: string;
  tokenRequest?: Function;
  moveRequest?: Function;
  fail?: boolean;
}

interface PieceMovements {
  [index: string]: PieceMovement;
}

interface UnprocessedPieceData {
  id: number;
  x: string;
  y: string;
  r: string;
  g: string | null;
  s: string | null;
  w: string;
  h: string;
  b: string;
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
  pending?: boolean;
  status?: string; // TODO: use when move to a state machine
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
  karmaChange: number | boolean;
}

enum PieceMoveErrorTypes {
  puzzleimmutable = "puzzleimmutable",
  sameplayerconcurrent = "sameplayerconcurrent",
  immovable = "immovable",
  piecequeue = "piecequeue",
  piecelock = "piecelock",
  invalid = "invalid",
  error = "error",
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

interface TokenData {
  token: string;
  lock: number;
  expires: number;
  snap?: string;
}
enum TokenRequestErrorTypes {
  puzzlereload = "puzzlereload",
  puzzleimmutable = "puzzleimmutable",
  immovable = "immovable",
  sameplayerconcurrent = "sameplayerconcurrent",
  bannedusers = "bannedusers",
  piecequeue = "piecequeue",
  piecelock = "piecelock",
}
export interface TokenRequestError {
  msg: string;
  type: TokenRequestErrorTypes;
  expires: number;
  timeout: number;
  reason: string;
  action: any; // {msg: string, url: string}
}

// For now this is set to one to prevent feature creep
const maxSelectedPieces = 1;

type PiecesMutateCallback = (data: Array<PieceData>) => any;
type PiecesShadowMutateCallback = (data: Array<PieceData>) => any;
type PiecesUpdateCallback = (data: Array<PieceData>) => any;
type KarmaUpdatedCallback = (data: KarmaData) => any;
type PieceMoveRejectedCallback = (data: PieceData) => any;
type PieceMoveBlockedCallback = (data: PieceMoveError) => any;
type PiecesInfoToggleMovableCallback = (toggle: any) => any;
type PiecesInfoPauseResumeCallback = (pause: any) => any;
const piecesMutate = Symbol("pieces/mutate");
const piecesShadowMutate = Symbol("pieces/shadow-mutate");
const piecesUpdate = Symbol("pieces/update");
const karmaUpdated = Symbol("karma/updated");
const pieceMoveRejected = Symbol("piece/move/rejected");
const pieceMoveBlocked = Symbol("piece/move/blocked");
const piecesInfoToggleMovable = Symbol("pieces/info/toggle-movable");
const piecesInfoPauseResume = Symbol("pieces/info/pause-resume");

const topics = {
  "pieces/mutate": piecesMutate,
  "pieces/shadow-mutate": piecesShadowMutate,
  "pieces/update": piecesUpdate,
  "karma/updated": karmaUpdated,
  "piece/move/rejected": pieceMoveRejected,
  "piece/move/blocked": pieceMoveBlocked,
  "pieces/info/toggle-movable": piecesInfoToggleMovable,
  "pieces/info/pause-resume": piecesInfoPauseResume,
};

interface UnprocessedPuzzlePiecesData {
  positions: Array<UnprocessedPieceData>;
  timestamp: string;
  mark: string;
}

interface MoveRequestData {
  x: number;
  y: number;
  r?: number;
}

const pieceAttrsThatAreInt = ["g", "x", "y", "r", "s", "b", "w", "h", "rotate"];

class TokenRequestService {
  url: string;

  constructor(url: string) {
    this.url = url;
  }

  get<T>(): Promise<T> {
    return fetch(this.url, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
      },
    }).then((response: Response) => {
      return response.json().then((data: T) => {
        if (!response.ok) {
          return Promise.reject(data);
        }
        return data;
      });
    });
  }
}

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
  private _piecesPaused = false;
  public isWaitingOnMoveRequest = false;

  [piecesMutate]: Map<string, PiecesMutateCallback> = new Map();
  [piecesShadowMutate]: Map<string, PiecesShadowMutateCallback> = new Map();
  [piecesUpdate]: Map<string, PiecesUpdateCallback> = new Map();
  [karmaUpdated]: Map<string, KarmaUpdatedCallback> = new Map();
  [pieceMoveRejected]: Map<string, PieceMoveRejectedCallback> = new Map();
  [pieceMoveBlocked]: Map<string, PieceMoveBlockedCallback> = new Map();
  [piecesInfoToggleMovable]: Map<
    string,
    PiecesInfoToggleMovableCallback
  > = new Map();
  [piecesInfoPauseResume]: Map<
    string,
    PiecesInfoPauseResumeCallback
  > = new Map();
  constructor() {}
  //private handlePieceStateChange(state) {
  //  console.log(`puzzle-piece: ${state.value}`);
  //  if (state.matches("unknown")) {
  //    console.log(state.context);
  //  }
  //}

  init(puzzleId): Promise<PieceData[]> {
    streamService.subscribe(
      "piece/update",
      this.onPieceUpdate.bind(this),
      this.instanceId
    );
    this.puzzleId = puzzleId;

    const fetchPuzzlePiecesService = new FetchService(
      `/newapi/puzzle-pieces/${puzzleId}/`
    );
    return fetchPuzzlePiecesService
      .get<UnprocessedPuzzlePiecesData>()
      .then((pieceData) => {
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
          // TODO:
          //puzzlePieceService = interpret(puzzlePieceMachine).start();
          // TODO: the pm-puzzle-pieces would subscribe?
          //puzzlePieceService.subscribe(this.handlePieceStateChange.bind(this));
          this.pieces[piece.id] = Object.assign(defaultPiece, piece);
        });
        this.piecesTimestamp = pieceData.timestamp;
        return Object.values(this.pieces);
      });
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

    this._broadcast(piecesUpdate, [piece]);
  }

  private _broadcast(topic: symbol, data?: any) {
    this[topic].forEach((fn /*, id*/) => {
      fn(data);
    });
  }

  subscribe(
    topicString: string,
    fn:
      | PiecesMutateCallback
      | PiecesShadowMutateCallback
      | PiecesUpdateCallback
      | KarmaUpdatedCallback
      | PieceMoveRejectedCallback
      | PiecesInfoToggleMovableCallback
      | PiecesInfoPauseResumeCallback,
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
      const tokenRequestService = new TokenRequestService(
        `/newapi/puzzle/${puzzleId}/piece/${piece}/token/?mark=${mark}`
      );
      return tokenRequestService
        .get<TokenData>()
        .then((tokenData) => {
          pieceMovement.token = tokenData.token;
          pieceMovement.snap = tokenData.snap;
        })
        .catch((responseObj: TokenRequestError) => {
          //let responseObj;
          //try {
          //  responseObj = JSON.parse(tokenError.response);
          //} catch (err) {
          //  responseObj = {
          //    msg: "Unable to move that piece at this time.",
          //    reason: tokenError.status,
          //  };
          //}
          switch (responseObj.type) {
            case TokenRequestErrorTypes.piecelock:
            case TokenRequestErrorTypes.piecequeue:
              // TODO: If piece is locked then publish a 'piece/move/delayed' instead of blocked.
              // TODO: Set a timeout and clear if piece is moved.  Maybe
              // auto-scroll to the moved piece?
              break;
            case TokenRequestErrorTypes.sameplayerconcurrent:
              if (responseObj.action && responseObj.action.url) {
                fetch(responseObj.action.url, {
                  method: "POST",
                  credentials: "same-origin",
                  headers: {
                    "Content-Type": "application/json",
                  },
                });
              }
              break;
            case TokenRequestErrorTypes.bannedusers:
            case TokenRequestErrorTypes.puzzleimmutable:
              self._broadcast(pieceMoveBlocked, responseObj);
              break;
            default:
              if (!responseObj.timeout) {
                const expire = new Date().getTime() / 1000 + 5;
                responseObj.expires = expire;
                responseObj.timeout = 5;
              }
              self._broadcast(pieceMoveBlocked, responseObj);
              break;
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
      const fetchPuzzlePieceService = new FetchService(
        `/newapi/puzzle/${puzzleId}/piece/${id}/`
      );
      return fetchPuzzlePieceService
        .get<UnprocessedPieceData>()
        .then((pieceData) => {
          const pieceMovementData: PieceMovementData = {
            id: id,
            x: parseInt(pieceData.x),
            y: parseInt(pieceData.y),
            r: parseInt(pieceData.r),
          };
          self.onPieceMoveRejected(pieceMovementData);
        })
        .catch(() => {
          if (origin) {
            self.onPieceMoveRejected({
              id: id,
              x: origin.x,
              y: origin.y,
              r: origin.r,
            });
          }
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

    this.isWaitingOnMoveRequest = true;
    pieceMovement.moveRequest = function moveRequest() {
      x = Math.round(Number(x));
      y = Math.round(Number(y));

      let data: MoveRequestData = { x: x, y: y };
      if (r !== "-") {
        r = parseInt(r, 10);
        data.r = r;
      }

      const movePuzzlePieceService = new FetchService(
        `/newapi/puzzle/${puzzleId}/piece/${id}/move/`
      );
      return movePuzzlePieceService
        .patchNoContent(data, {
          Token: pieceMovement.token,
          Snap: pieceMovement.snap,
        })
        .catch((patchError) => {
          //responseObj = {
          //  msg: "Unable to move that piece at this time.",
          //  reason: patchError.response,
          //};
          const responseObj = patchError.body;
          if (patchError.status === 429) {
            self._broadcast(pieceMoveBlocked, responseObj);
            self.onPieceMoveRejected({
              id: id,
              x: origin.x,
              y: origin.y,
              r: origin.r,
            });
          } else {
            switch (responseObj.type) {
              case PieceMoveErrorTypes.invalid:
              case PieceMoveErrorTypes.missing:
              case PieceMoveErrorTypes.error:
              case PieceMoveErrorTypes.bannedusers:
              case PieceMoveErrorTypes.blockedplayer:
                self._broadcast(pieceMoveBlocked, responseObj);
                break;
              case PieceMoveErrorTypes.expiredtoken: // TODO: should handle expiredtoken better
              case PieceMoveErrorTypes.immovable: // piece may have become immovable after token request
              case PieceMoveErrorTypes.invalidpiecemove:
              case PieceMoveErrorTypes.proximity:
                // Skip broadcasting these errors so no alert message is shown.
                break;
              default:
                if (!responseObj.timeout) {
                  const expire = new Date().getTime() / 1000 + 5;
                  responseObj.expires = expire;
                  responseObj.timeout = 5;
                }
                self._broadcast(pieceMoveBlocked, responseObj);
                break;
            }
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
          const fetchPuzzlePieceService = new FetchService(
            `/newapi/puzzle/${puzzleId}/piece/${id}/`
          );
          return fetchPuzzlePieceService
            .get<UnprocessedPieceData>()
            .then((pieceData) => {
              const pieceMovementData: PieceMovementData = {
                id: id,
                x: parseInt(pieceData.x),
                y: parseInt(pieceData.y),
                r: parseInt(pieceData.r),
              };
              self.onPieceMoveRejected(pieceMovementData);
            })
            .catch(() => {
              if (origin) {
                self.onPieceMoveRejected({
                  id: id,
                  x: origin.x,
                  y: origin.y,
                  r: origin.r,
                });
              }
            });
        })
        .finally(() => {
          self.isWaitingOnMoveRequest = false;
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
    this.togglePieceMovements(true);
    // TODO: move selectPiece to pm-puzzle-pieces?
    const index = this.selectedPieces.indexOf(pieceID);
    if (index === -1) {
      // add the pieceID to the end of the array
      this.selectedPieces.push(pieceID);
      this.pieces[pieceID].karma = false; // TODO: why set to false?
      // TODO: status is set to active
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
    this._broadcast(piecesUpdate, [this.pieces[pieceID]]);
  }

  dropSelectedPieces(x, y, scale) {
    // Update piece locations
    this.selectedPieces.forEach((pieceID) => {
      let piece = this.pieces[pieceID];
      piece.x = x / scale - piece.w / 2;
      piece.y = y / scale - piece.h / 2;
      piece.pending = true;
      piece.active = false;
    });

    // Display the updates
    const pieces = this.selectedPieces.map((pieceID) => {
      return this.pieces[pieceID];
    });
    this._broadcast(piecesUpdate, pieces);

    // Send the updates
    this.togglePieceMovements(false);
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

  get piecesPaused() {
    return this._piecesPaused;
  }

  togglePieceMovements(pause: boolean) {
    this._piecesPaused = pause;
    this._broadcast(piecesInfoPauseResume, this._piecesPaused);
  }

  private onPieceUpdate(data: PieceMovementData) {
    // TODO: rename
    let piece = this.pieces[data.id];
    if (piece.pending) {
      this.unSelectPiece(data.id);
    }
    piece = Object.assign(piece, data);
    piece.pending = false;
    this._broadcast(piecesMutate, [piece]);
    if (this.piecesPaused) {
      this._broadcast(piecesShadowMutate, [piece]);
    }
  }

  private onPieceMoveRejected(data: PieceMovementData) {
    let piece = this.pieces[data.id];
    piece.x = data.x || piece.origin.x;
    piece.y = data.y || piece.origin.y;
    piece.pending = false;
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
            tokenRequest().finally(() => {
              pieceMovement.tokenRequest = undefined;
              pieceMovement.inProcess = false;
            });
          } else if (hasMoveRequest) {
            // ready to send movement
            const moveRequest = <Function>pieceMovement.moveRequest;
            moveRequest().finally(() => {
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
