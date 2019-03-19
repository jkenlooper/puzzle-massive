import reqwest from "reqwest";
import { divulgerService, PieceMovementData } from "./divulger.service";

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
  rotate: string;
  r?: number;
  s?: number | null; // s for stacked
  b: number; // b for background
  w: number;
  h: number;
  // TODO: others
}

export interface PieceData extends DefaultPiece {
  id: number;
  //rotate: number;
  active?: boolean;
  karma?: number; // response from move request
  karmaChange?: number | boolean; // response from move request
}

interface Pieces {
  [index: number]: PieceData;
}

export interface KarmaData {
  id: number;
  karma: number;
  karmaChange: boolean;
}

    // For now this is set to one to prevent feature creep
    const maxSelectedPieces = 1

type PiecesUpdateCallback = (data: Array<PieceData>) => any;
type KarmaUpdatedCallback = (data: KarmaData) => any;
const piecesMutate = Symbol("pieces/mutate");
const karmaUpdated = Symbol("karma/updated");

const topics = {
  "pieces/mutate": piecesMutate,
  "karma/updated": karmaUpdated,
};

interface MoveRequestData {
  x: number;
  y: number;
  r?: number;
}

const pieceAttrsThatAreInt = ["g", "x", "y", "r", "s", "b", "w", "h"];

let _pieceMovementId = 0;

class PuzzleService {
  // Pass in the url to the puzzle pieces
  private puzzleId: string = "";
  private pieceMovementQueue: Array<PieceMovementId> = [];
  private pieceMovements: PieceMovements = {};
  private pieceMovementProcessInterval: number | undefined = undefined;
  private pieces: Pieces = {};
  private collection: Array<number> = [];
  private piecesTimestamp = "";
  private mark: string = "";
  private selectedPieces: Array<number> = [];
  private instanceId = 'puzzleService';

  [piecesMutate]: Map<string, PiecesUpdateCallback> = new Map();
  [karmaUpdated]: Map<string, KarmaUpdatedCallback> = new Map();
  constructor() {
    divulgerService.subscribe('piece/update', this.onPieceUpdate.bind(this), this.instanceId)
  }

  init(puzzleId) {
    this.puzzleId = puzzleId;
    fetchPieces(this.puzzleId).then((data) => {
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
          rotate: "0",
          s: null,
          b: 1,
          w: 1,
          h: 1,
        };
        this.pieces[piece.id] = Object.assign(defaultPiece, piece);
      });
      this.collection = pieceData.positions.map((piece) => {
        return piece.id;
      });
      this.piecesTimestamp = pieceData.timestamp.timestamp;
      //self.renderPieces(self.pieces, this.collection);
    });

    function fetchPieces(puzzleId) {
      return reqwest({
        url: `/newapi/puzzle-pieces/${puzzleId}/`,
        method: "get",
      });
    }
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
    //self.renderPieces(self.pieces, [pieceID]);
  }

  onKarmaUpdate(data: KarmaData) {
    let piece = this.pieces[data.id];
    Object.assign(piece, data);
    this._broadcast(piecesMutate, [piece]);
    this._broadcast(karmaUpdated, data);
    //self.renderPieces(self.pieces, [data.id])
  }

  _broadcast(topic: symbol, data?: any) {
    this[topic].forEach((fn /*, id*/) => {
      fn(data);
    });
  }

  subscribe(
    topicString: string,
    fn: PiecesUpdateCallback | KarmaUpdatedCallback,
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

  token(piece, mark) {
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
            case "piecelock":
            case "piecequeue":
              // TODO: If piece is locked then publish a 'piece/move/delayed' instead of blocked.
              // TODO: Set a timeout and clear if piece is moved.  Maybe
              // auto-scroll to the moved piece?
              break;
            case "sameplayerconcurrent":
              if (responseObj.action) {
                reqwest({ url: responseObj.action.url, method: "POST" });
              }
              break;
            case "bannedusers":
            case "expiredtoken":
            default:
              // @ts-ignore: minpubsub
              window.publish("piece/move/blocked", [responseObj]);
          }
          pieceMovement.fail = true;
          // TODO: still need to publish the piece/move/rejected
          try {
            // @ts-ignore: minpubsub
            window.publish("piece/move/rejected", [{ id: piece }]);
          } catch (err) {
            console.log("ignoring error with minpubsub", err);
          }
        });
    };

    this.pieceMovements[pieceMovementId] = pieceMovement;
    this.pieceMovementQueue.push(pieceMovementId);

    this.processNextPieceMovement();

    return pieceMovementId;
  }

  inPieceMovementQueue(piece) {
    return Object.values(this.pieceMovements).some((pieceMovement) => {
      return piece === pieceMovement.piece;
    });
  }

  cancelMove(id, origin, pieceMovementId) {
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
            // @ts-ignore: minpubsub
            window.publish("piece/move/rejected", [
              { id: id, x: origin.x, y: origin.y, r: origin.r },
            ]);
          }
        },
        success: function handlePieceInfo(data) {
          // @ts-ignore: minpubsub
          window.publish("piece/move/rejected", [
            { id: id, x: data.x, y: data.y, r: data.r },
          ]);
        },
      });
    };
  }

  move(id, x, y, r, origin, pieceMovementId) {
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

      divulgerService.ping(puzzleId);
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
            // @ts-ignore: minpubsub
            window.publish("piece/move/blocked", [responseObj]);
            // @ts-ignore: minpubsub
            window.publish("piece/move/rejected", [
              { id: id, x: origin.x, y: origin.y, r: origin.r },
            ]);
          } else {
            // @ts-ignore: minpubsub
            window.publish("piece/move/rejected", [
              {
                id: id,
                x: origin.x,
                y: origin.y,
                r: origin.r,
                karma: responseObj.karma,
              },
            ]);
          }
          // Reject with piece info from server and fallback to origin if that also fails
          return reqwest({
            url: `/newapi/puzzle/${puzzleId}/piece/${id}/`,
            method: "GET",
            type: "json",
            data: data,
            error: function handleGetError() {
              if (origin) {
                // @ts-ignore: minpubsub
                window.publish("piece/move/rejected", [
                  { id: id, x: origin.x, y: origin.y, r: origin.r },
                ]);
              }
            },
            success: function handlePieceInfo(data) {
              // @ts-ignore: minpubsub
              window.publish("piece/move/rejected", [
                { id: id, x: data.x, y: data.y, r: data.r },
              ]);
            },
          });
        },
        success: function(d) {
          // @ts-ignore: minpubsub
          //window.publish("karma/updated", [d]);
          self.onKarmaUpdate(d);
          divulgerService.ping(puzzleId);
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
      let index = this.selectedPieces.indexOf(pieceID)
      if (index !== -1) {
        // remove the pieceID from the array
        this.selectedPieces.splice(index, 1)
        this.pieces[pieceID].active = false
        this.cancelMove(
          pieceID,
          this.pieces[pieceID].origin,
          this.pieces[pieceID].pieceMovementId
        )
      }
    }

    selectPiece(pieceID) {
      // TODO: move selectPiece to pm-puzzle-pieces?
      const index = this.selectedPieces.indexOf(pieceID)
      if (index === -1) {
        // add the pieceID to the end of the array
        this.selectedPieces.push(pieceID)
        this.pieces[pieceID].karma = false
        this.pieces[pieceID].active = true
        this.pieces[pieceID].origin = {
          x: this.pieces[pieceID].x,
          y: this.pieces[pieceID].y,
          r: this.pieces[pieceID].r,
        }
      } else {
        // remove the pieceID from the array
        this.selectedPieces.splice(index, 1)
        this.pieces[pieceID].active = false
        this.cancelMove(
          pieceID,
          this.pieces[pieceID].origin,
          this.pieces[pieceID].pieceMovementId
        )
      }

      // TODO: onPieceUpdate check if piece is already active
      //this.pieces[pieceID].active = false

      // Only allow a max amount of selected pieces
      if (this.selectedPieces.length > maxSelectedPieces) {
        this.selectedPieces
          .splice(0, this.selectedPieces.length - maxSelectedPieces)
          .forEach((pieceID) => {
            // all the pieces that were unselected also set to inactive
            this.pieces[pieceID].active = false
            this.cancelMove(
              pieceID,
              this.pieces[pieceID].origin,
              this.pieces[pieceID].pieceMovementId
            )
          })
      }
      if (!this.inPieceMovementQueue(pieceID)) {
        // Only get a new token if this piece movement isn't already in the
        // queue.
        this.pieces[pieceID].pieceMovementId = this.token(
          pieceID,
          this.mark
        )
      }
      //self.renderPieces(self.pieces, [pieceID])
      this._broadcast(piecesMutate, [this.pieces[pieceID]]);
    }

    dropSelectedPieces(x, y, scale) {
      // Update piece locations
      this.selectedPieces.forEach(function(pieceID) {
        let piece = this.pieces[pieceID]
        piece.x = x / scale - piece.w / 2
        piece.y = y / scale - piece.h / 2
      })

      // Display the updates
      //self.renderPieces(self.pieces, self.selectedPieces)
      const pieces = this.selectedPieces.map((pieceID) => {
        return this.pieces[pieceID];
      })
      this._broadcast(piecesMutate, pieces);

      // Send the updates
      this.selectedPieces.forEach(function(pieceID) {
        let piece = this.pieces[pieceID]
        this.move(
          pieceID,
          piece.x,
          piece.y,
          '-',
          piece.origin,
          piece.pieceMovementId
        )
      })

      // Reset the selectedPieces
      this.selectedPieces = []
    }

    onPieceUpdate(data: PieceMovementData) {
      let piece = this.pieces[data.id]
      if (piece.active) {
        this.unSelectPiece(data.id)
      }
      piece = Object.assign(piece, data)
      piece.active = false
      //self.renderPieces(self.pieces, [data.id])
      this._broadcast(piecesMutate, [piece]);
    }

  processNextPieceMovement() {
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
