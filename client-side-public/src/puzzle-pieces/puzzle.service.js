var _a, _b, _c, _d, _e, _f, _g;
//import { interpret } from "@xstate/fsm";
import { nanoid } from "nanoid/non-secure";
import FetchService from "../site/fetch.service";
import { streamService } from "./stream.service";
var PieceMoveErrorTypes;
(function (PieceMoveErrorTypes) {
    PieceMoveErrorTypes["puzzleimmutable"] = "puzzleimmutable";
    PieceMoveErrorTypes["immovable"] = "immovable";
    PieceMoveErrorTypes["piecequeue"] = "piecequeue";
    PieceMoveErrorTypes["piecelock"] = "piecelock";
    PieceMoveErrorTypes["invalid"] = "invalid";
    PieceMoveErrorTypes["error"] = "error";
    PieceMoveErrorTypes["missing"] = "missing";
    PieceMoveErrorTypes["expiredtoken"] = "expiredtoken";
    PieceMoveErrorTypes["bannedusers"] = "bannedusers";
    PieceMoveErrorTypes["invalidpiecemove"] = "invalidpiecemove";
    PieceMoveErrorTypes["blockedplayer"] = "blockedplayer";
    PieceMoveErrorTypes["proximity"] = "proximity";
})(PieceMoveErrorTypes || (PieceMoveErrorTypes = {}));
var TokenRequestErrorTypes;
(function (TokenRequestErrorTypes) {
    TokenRequestErrorTypes["puzzlereload"] = "puzzlereload";
    TokenRequestErrorTypes["puzzleimmutable"] = "puzzleimmutable";
    TokenRequestErrorTypes["immovable"] = "immovable";
    TokenRequestErrorTypes["bannedusers"] = "bannedusers";
    TokenRequestErrorTypes["piecequeue"] = "piecequeue";
    TokenRequestErrorTypes["piecelock"] = "piecelock";
})(TokenRequestErrorTypes || (TokenRequestErrorTypes = {}));
// For now this is set to one to prevent feature creep
const maxSelectedPieces = 1;
const piecesMutate = Symbol("pieces/mutate");
const piecesShadowMutate = Symbol("pieces/shadow-mutate");
const piecesUpdate = Symbol("pieces/update");
const pieceMoveRejected = Symbol("piece/move/rejected");
const pieceMoveBlocked = Symbol("piece/move/blocked");
const piecesInfoToggleMovable = Symbol("pieces/info/toggle-movable");
const piecesInfoPauseResume = Symbol("pieces/info/pause-resume");
const topics = {
    "pieces/mutate": piecesMutate,
    "pieces/shadow-mutate": piecesShadowMutate,
    "pieces/update": piecesUpdate,
    "piece/move/rejected": pieceMoveRejected,
    "piece/move/blocked": pieceMoveBlocked,
    "pieces/info/toggle-movable": piecesInfoToggleMovable,
    "pieces/info/pause-resume": piecesInfoPauseResume,
};
const pieceAttrsThatAreInt = ["g", "x", "y", "r", "s", "b", "w", "h", "rotate"];
class TokenRequestService {
    constructor(url) {
        this.url = url;
    }
    get() {
        return fetch(this.url, {
            method: "GET",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
            },
        }).then((response) => {
            return response.json().then((data) => {
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
    constructor() {
        // Pass in the url to the puzzle pieces
        this.puzzleId = "";
        this.pieceMovementQueue = [];
        this.pieceMovements = {};
        this.pieceMovementProcessInterval = undefined;
        this.pieces = {};
        // @ts-ignore: piecesTimestamp will be used in the future
        this.piecesTimestamp = "";
        this.mark = "";
        this.selectedPieces = [];
        this.instanceId = "puzzleService";
        this._showMovable = false;
        this._piecesPaused = false;
        this.isWaitingOnMoveRequest = false;
        this[_a] = new Map();
        this[_b] = new Map();
        this[_c] = new Map();
        this[_d] = new Map();
        this[_e] = new Map();
        this[_f] = new Map();
        this[_g] = new Map();
    }
    //private handlePieceStateChange(state) {
    //  console.log(`puzzle-piece: ${state.value}`);
    //  if (state.matches("unknown")) {
    //    console.log(state.context);
    //  }
    //}
    init(puzzleId) {
        streamService.subscribe("piece/update", this.onPieceUpdate.bind(this), this.instanceId);
        this.puzzleId = puzzleId;
        const fetchPuzzlePiecesService = new FetchService(`/newapi/puzzle-pieces/${puzzleId}/`);
        return fetchPuzzlePiecesService
            .get()
            .then((pieceData) => {
            this.mark = nanoid(10);
            pieceData.positions.forEach((piece) => {
                // set status
                Object.keys(piece)
                    .filter((key) => {
                    return pieceAttrsThatAreInt.includes(key);
                })
                    .forEach((key) => {
                    piece[key] = Number(piece[key]);
                });
                const defaultPiece = {
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
            return {
                pieces: Object.values(this.pieces),
                timestamp: this.piecesTimestamp,
            };
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
    token(piece, mark) {
        const self = this;
        const puzzleId = this.puzzleId;
        const pieceMovementId = PuzzleService.nextPieceMovementId;
        const pieceMovement = {
            id: pieceMovementId,
            piece: piece,
            inProcess: false,
        };
        pieceMovement.tokenRequest = function tokenRequest() {
            const tokenRequestService = new TokenRequestService(`/newapi/puzzle/${puzzleId}/piece/${piece}/token/?mark=${mark}`);
            return tokenRequestService
                .get()
                .then((tokenData) => {
                pieceMovement.token = tokenData.token;
                pieceMovement.snap = tokenData.snap;
            })
                .catch((responseObj) => {
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
    inPieceMovementQueue(piece) {
        return Object.values(this.pieceMovements).some((pieceMovement) => {
            return piece === pieceMovement.piece;
        });
    }
    cancelMove(id, origin, pieceMovementId) {
        const self = this;
        const pieceMovement = this.pieceMovements[pieceMovementId];
        const puzzleId = this.puzzleId;
        if (!pieceMovement) {
            return;
        }
        //pieceMovement.fail = true
        pieceMovement.moveRequest = function cancelMoveRequest() {
            const fetchPuzzlePieceService = new FetchService(`/newapi/puzzle/${puzzleId}/piece/${id}/`);
            return fetchPuzzlePieceService
                .get({
                Mark: self.mark,
            })
                .then((pieceData) => {
                const pieceMovementData = {
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
            let data = { x: x, y: y };
            if (r !== "-") {
                r = parseInt(r, 10);
                data.r = r;
            }
            const movePuzzlePieceService = new FetchService(`/newapi/puzzle/${puzzleId}/piece/${id}/move/`);
            return movePuzzlePieceService
                .patchNoContent(data, {
                Token: pieceMovement.token,
                Snap: pieceMovement.snap,
                Mark: self.mark,
            })
                .catch((patchError) => {
                //responseObj = {
                //  msg: "Unable to move that piece at this time.",
                //  reason: patchError.response,
                //};
                if (!patchError.body) {
                    console.error(patchError);
                }
                else {
                    const responseObj = patchError.body;
                    if (patchError.status === 429) {
                        self._broadcast(pieceMoveBlocked, responseObj);
                        self.onPieceMoveRejected({
                            id: id,
                            x: origin.x,
                            y: origin.y,
                            r: origin.r,
                        });
                    }
                    else {
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
                        const pieceMovementData = {
                            id: id,
                            x: origin.x,
                            y: origin.y,
                            r: origin.r,
                        };
                        self.onPieceMoveRejected(pieceMovementData);
                    }
                }
                // Reject with piece info from server and fallback to origin if that also fails
                const fetchPuzzlePieceService = new FetchService(`/newapi/puzzle/${puzzleId}/piece/${id}/`);
                return fetchPuzzlePieceService
                    .get({
                    Mark: self.mark,
                })
                    .then((pieceData) => {
                    const pieceMovementData = {
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
            this.pieces[pieceID].dragging = false;
            this.cancelMove(pieceID, this.pieces[pieceID].origin, this.pieces[pieceID].pieceMovementId);
        }
    }
    selectPiece(pieceID) {
        this.togglePieceMovements(true);
        // TODO: move selectPiece to pm-puzzle-pieces?
        const index = this.selectedPieces.indexOf(pieceID);
        if (index === -1) {
            // add the pieceID to the end of the array
            this.selectedPieces.push(pieceID);
            // TODO: status is set to active
            this.pieces[pieceID].active = true;
            this.pieces[pieceID].dragging = true;
            this.pieces[pieceID].origin = {
                x: this.pieces[pieceID].x,
                y: this.pieces[pieceID].y,
                r: this.pieces[pieceID].r,
            };
        }
        else {
            // remove the pieceID from the array
            this.selectedPieces.splice(index, 1);
            this.pieces[pieceID].active = false;
            this.cancelMove(pieceID, this.pieces[pieceID].origin, this.pieces[pieceID].pieceMovementId);
        }
        // Only allow a max amount of selected pieces
        if (this.selectedPieces.length > maxSelectedPieces) {
            this.selectedPieces
                .splice(0, this.selectedPieces.length - maxSelectedPieces)
                .forEach((pieceID) => {
                // all the pieces that were unselected also set to inactive
                this.pieces[pieceID].active = false;
                this.cancelMove(pieceID, this.pieces[pieceID].origin, this.pieces[pieceID].pieceMovementId);
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
        this.isWaitingOnMoveRequest = this.selectedPieces[0];
        // Update piece locations
        this.selectedPieces.forEach((pieceID) => {
            let piece = this.pieces[pieceID];
            piece.x = x / scale - piece.w / 2;
            piece.y = y / scale - piece.h / 2;
            piece.pending = true;
            piece.active = false;
            piece.dragging = false;
        });
        // Display the updates
        const pieces = this.selectedPieces.map((pieceID) => {
            return this.pieces[pieceID];
        });
        this._broadcast(piecesUpdate, pieces);
        // Send the updates
        Promise.allSettled(this.selectedPieces.map((pieceID) => {
            let piece = this.pieces[pieceID];
            return this.move(pieceID, piece.x, piece.y, "-", piece.origin, piece.pieceMovementId);
        })).then(() => {
            this.togglePieceMovements(false);
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
    togglePieceMovements(pause) {
        this._piecesPaused = pause;
        this._broadcast(piecesInfoPauseResume, this._piecesPaused);
    }
    onPieceUpdate(data) {
        // TODO: rename
        let pieceMovements = data.map((pieceMovementData) => {
            let piece = this.pieces[pieceMovementData.id];
            if (piece.pending) {
                this.unSelectPiece(pieceMovementData.id);
            }
            if (pieceMovementData.id === this.isWaitingOnMoveRequest) {
                window.clearTimeout(this.resetTimeoutForOnMoveRequest);
                this.resetTimeoutForOnMoveRequest = window.setTimeout(() => {
                    this.isWaitingOnMoveRequest = false;
                }, 1);
            }
            piece = Object.assign(piece, pieceMovementData);
            piece.pending = false;
            return piece;
        });
        this._broadcast(piecesMutate, pieceMovements);
        if (this.piecesPaused) {
            this._broadcast(piecesShadowMutate, pieceMovements);
        }
    }
    onPieceMoveRejected(data) {
        let piece = this.pieces[data.id];
        piece.x = data.x || piece.origin.x;
        piece.y = data.y || piece.origin.y;
        piece.pending = false;
        piece.active = false;
        if (data.id === this.isWaitingOnMoveRequest) {
            this.isWaitingOnMoveRequest = false;
        }
        this._broadcast(pieceMoveRejected, data);
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
                        const tokenRequest = pieceMovement.tokenRequest;
                        tokenRequest().finally(() => {
                            pieceMovement.tokenRequest = undefined;
                            pieceMovement.inProcess = false;
                        });
                    }
                    else if (hasMoveRequest) {
                        // ready to send movement
                        const moveRequest = pieceMovement.moveRequest;
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
_a = piecesMutate, _b = piecesShadowMutate, _c = piecesUpdate, _d = pieceMoveRejected, _e = pieceMoveBlocked, _f = piecesInfoToggleMovable, _g = piecesInfoPauseResume;
export const puzzleService = new PuzzleService();
