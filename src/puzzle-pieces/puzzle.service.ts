import reqwest from "reqwest";
import { divulgerService } from "./divulger.service";

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

interface MoveRequestData {
  x: number;
  y: number;
  r?: number;
}

let _pieceMovementId = 0;

export default class PuzzleService {
  // Pass in the url to the puzzle pieces
  private puzzleid: string;
  private pieceMovementQueue: Array<PieceMovementId> = [];
  private pieceMovements: PieceMovements = {};
  private pieceMovementProcessInterval: number | undefined = undefined;
  constructor(puzzleid) {
    this.puzzleid = puzzleid;
  }

  static get nextPieceMovementId() {
    _pieceMovementId++;
    return _pieceMovementId;
  }

  pieces() {
    const puzzleid = this.puzzleid;
    return reqwest({
      url: `/newapi/puzzle-pieces/${puzzleid}/`,
      method: "get",
    });
  }

  token(piece, mark) {
    const puzzleid = this.puzzleid;
    const pieceMovementId = PuzzleService.nextPieceMovementId;
    const pieceMovement: PieceMovement = {
      id: pieceMovementId,
      piece: piece,
      inProcess: false,
    };

    pieceMovement.tokenRequest = function tokenRequest() {
      return reqwest({
        url: `/newapi/puzzle/${puzzleid}/piece/${piece}/token/`,
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
    const puzzleid = this.puzzleid;
    if (!pieceMovement) {
      return;
    }
    //pieceMovement.fail = true
    pieceMovement.moveRequest = function cancelMoveRequest() {
      return reqwest({
        url: `/newapi/puzzle/${puzzleid}/piece/${id}/`,
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
    const puzzleid = this.puzzleid;
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

      divulgerService.ping(puzzleid);
      return reqwest({
        url: `/newapi/puzzle/${puzzleid}/piece/${id}/move/`,
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
            url: `/newapi/puzzle/${puzzleid}/piece/${id}/`,
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
          window.publish("karma/updated", [d]);
          divulgerService.ping(puzzleid);
        },
      });
    };
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
