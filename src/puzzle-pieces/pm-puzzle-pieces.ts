//import * as Hammer from "hammerjs";
//import Hammer from "hammerjs";

// TODO: Exercise for the developer; refactor this mess of old javascript into
// a more manageable state.  Should start with unit test coverage.  There is
// also a lot of poorly implemented state management going on here that could be
// refactored with using redux and/or a state machine.
//
// I've added on with more terrible code (a 'small' tweak here and there) to
// make things more challenging. ;)

import { rgbToHsl } from "../site/utilities";
import hashColorService from "../hash-color/hash-color.service";
import { puzzleService, PieceData } from "./puzzle.service";
import { streamService, KarmaData, PieceMovementData } from "./stream.service";
import FetchService from "../site/fetch.service";
import { Status } from "../site/puzzle-images.service";

import "./puzzle-pieces.css";

interface PieceProps {
  [index: number]: PieceData;
}

const html = `
  <div class="pm-PuzzlePieces">
    <div class="pm-PuzzlePieces-collection"></div>
    <div class="pm-PuzzlePieces-dropZone"></div>
    <div class="pm-PuzzlePieces-outlineContainer" id="puzzle-outline">
      <div class="pm-PuzzlePieces-outline">
        <div class="pm-PuzzlePieces-outlineTop">
          <div class="pm-PuzzlePieces-outlineTopContent">
            <slot name="outline-top-content"></slot>
          </div>
        </div>
        <div class="pm-PuzzlePieces-outlineBottom">
          <div class="pm-PuzzlePieces-outlineBottomContent">
            <slot name="outline-bottom-content"></slot>
          </div>
        </div>
      </div>
    </div>
  </div>
  `;
const tag = "pm-puzzle-pieces";
let lastInstanceId = 0;

interface RenderedShadowPieces {
  [index: number]: PieceData;
}

customElements.define(
  tag,
  class PmPuzzlePieces extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    private puzzleId: string;
    private maxPausePiecesTimeout: number;
    private puzzleStatus: Status | undefined;
    $collection: HTMLElement;
    $dropZone: HTMLElement;
    $container: HTMLElement;
    // TODO: types for SlabMassive element
    private $slabMassive: any;

    private draggedPiece: HTMLElement | null = null;
    private draggedPieceID: number | null = null;
    private slabMassiveOffsetTop: number;
    private slabMassiveOffsetLeft: number;
    private pieceFollow: Function;
    private blocked: boolean = false;
    private blockedTimer: number = 0;
    private blockedTimeout: number | undefined;
    private piecesPaused: boolean = false;
    private renderPiecesBuffer: Array<PieceData>;
    private batchRenderPiecesTimeout: number | undefined;
    private renderedShadowPieces: RenderedShadowPieces = {};
    private isWaitingOnMoveRequestTimeout: number | undefined;
    private removeShadowedPiecesTimeout: number | undefined;
    private audioPuzzlePieceClick: HTMLAudioElement;

    //private pauseStop: number = 0;

    constructor() {
      super();
      const self = this;
      this.instanceId = PmPuzzlePieces._instanceId;
      this.renderPiecesBuffer = [];
      this.innerHTML = html;
      this.$collection = <HTMLElement>(
        this.querySelector(".pm-PuzzlePieces-collection")
      );
      this.$dropZone = <HTMLElement>(
        this.querySelector(".pm-PuzzlePieces-dropZone")
      );
      this.$container = <HTMLElement>this.querySelector(".pm-PuzzlePieces");
      this.$slabMassive = this.parentElement;
      const withinSlabMassive = this.$slabMassive.tagName === "SLAB-MASSIVE";

      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      this.puzzleId = puzzleId ? puzzleId.value : "";

      // The player can pause piece movements on their end for this max time in seconds.
      const maxPausePiecesTimeout = this.attributes.getNamedItem(
        "max-pause-pieces-timeout"
      );
      this.maxPausePiecesTimeout = parseFloat(
        maxPausePiecesTimeout ? maxPausePiecesTimeout.value : "0"
      );

      const puzzleStatus = this.attributes.getNamedItem("status");
      this.puzzleStatus = puzzleStatus
        ? <Status>(<unknown>parseInt(puzzleStatus.value))
        : undefined;

      if (!withinSlabMassive) {
        // Patch in these properties from the attrs
        Object.defineProperty(this.$slabMassive, "scale", {
          get: function () {
            return Number(this.getAttribute("scale"));
          },
        });
        Object.defineProperty(this.$slabMassive, "zoom", {
          get: function () {
            return Number(this.getAttribute("zoom"));
          },
        });
        Object.defineProperty(this.$slabMassive, "offsetX", {
          get: function () {
            return Number(this.getAttribute("offset-x"));
          },
        });
        Object.defineProperty(this.$slabMassive, "offsetY", {
          get: function () {
            return Number(this.getAttribute("offset-y"));
          },
        });
      } else {
        this.$container.classList.add("pm-PuzzlePieces--withinSlabMassive");
      }

      // Should only connect to puzzle stream and puzzle service if the status
      // of the puzzle is active.
      puzzleService
        .init(this.puzzleId)
        .then((obj) => {
          this.renderPieces(obj.pieces);
          // Request any piece updates since the timestamp
          const pieceUpdatesService = new FetchService(
            `/newapi/puzzle-piece-updates/${obj.timestamp}/`
          );
          return pieceUpdatesService
            .getText()
            .then((data) => {
              if (data) {
                streamService.injectMoves(this.puzzleId, data);
              }
            })
            .catch((err) => {
              // Ignore errors when getting piece updates.
              console.error(err);
            });
        })
        .catch((err) => {
          console.error(err);
          this.$container.innerHTML = "Failed to get puzzle pieces.";
        });
      if (
        this.puzzleStatus &&
        [Status.ACTIVE, Status.BUGGY_UNLISTED].includes(this.puzzleStatus)
      ) {
        streamService.connect(this.puzzleId);

        streamService.subscribe(
          "puzzle/status",
          this.onPuzzleStatus.bind(this),
          this.instanceId
        );
        streamService.subscribe(
          "karma/updated",
          this.onKarmaUpdated.bind(this),
          `karmaUpdated ${this.instanceId}`
        );

        puzzleService.connect();
        puzzleService.subscribe(
          "pieces/mutate",
          this.batchRenderPieces.bind(this),
          this.instanceId
        );
        puzzleService.subscribe(
          "pieces/shadow-mutate",
          this.renderShadowPieces.bind(this),
          this.instanceId
        );
        puzzleService.subscribe(
          "pieces/update",
          this.renderPieces.bind(this),
          this.instanceId
        );

        puzzleService.subscribe(
          "piece/move/blocked",
          this.onMoveBlocked.bind(this),
          this.instanceId
        );

        puzzleService.subscribe(
          "pieces/info/toggle-movable",
          this.onToggleMovable.bind(this),
          this.instanceId
        );
        puzzleService.subscribe(
          "pieces/info/pause-resume",
          this.onPiecesPauseResume.bind(this),
          this.instanceId
        );
      }

      this.slabMassiveOffsetTop = this.$slabMassive.offsetTop;
      this.slabMassiveOffsetLeft = this.$slabMassive.offsetLeft;

      this.pieceFollow = this._pieceFollow.bind(this);

      this.$dropZone.addEventListener(
        "mousedown",
        this.dropTap.bind(this),
        false
      );

      // Enable panning of the puzzle
      let panStartX = 0;
      let panStartY = 0;

      let mc = new Hammer.Manager(this.$dropZone, {});
      // touch device can use native panning
      mc.add(
        new Hammer.Pan({
          direction: Hammer.DIRECTION_ALL,
          enable: () => this.$slabMassive.zoom !== 1,
        })
      );
      mc.on("panstart panmove", function (ev) {
        if (ev.target.tagName === "SLAB-MASSIVE") {
          return;
        }
        switch (ev.type) {
          case "panstart":
            panStartX = Number(self.$slabMassive.offsetX);
            panStartY = Number(self.$slabMassive.offsetY);
            break;
          case "panmove":
            self.$slabMassive.scrollTo(
              panStartX + ev.deltaX * -1,
              panStartY + ev.deltaY * -1
            );
            break;
        }
      });

      this.$collection.addEventListener(
        "mousedown",
        this.onTap.bind(this),
        false
      );

      hashColorService.subscribe(
        this.updateForegroundAndBackgroundColors.bind(this),
        this.instanceId
      );

      this.audioPuzzlePieceClick = new Audio("/media/536108__eminyildirim__ui-click.wav");
    }

    onPuzzleStatus(status: Status) {
      switch (status) {
        case Status.ACTIVE:
          this.blocked = false;
          break;
        case Status.COMPLETED:
        case Status.IN_QUEUE:
        case Status.FROZEN:
        case Status.DELETED_REQUEST:
        default:
          this.blocked = true;
          break;
      }
    }

    onKarmaUpdated(data: KarmaData) {
      this.renderPieceKarma(null, data);
    }

    onMoveBlocked(data) {
      if (data.timeout && typeof data.timeout === "number") {
        const now = new Date().getTime();
        const remainingTime = Math.max(0, this.blockedTimer - now);
        const timeout = data.timeout * 1000 + remainingTime;
        window.clearTimeout(this.blockedTimeout);
        this.blockedTimer = now + timeout;
        this.blockedTimeout = window.setTimeout(() => {
          this.blocked = false;
        }, timeout);
      }
      this.blocked = true;
    }

    _pieceFollow(ev) {
      puzzleService.moveBy(
        this.draggedPieceID,
        Number(this.$slabMassive.offsetX) +
          ev.pageX -
          this.slabMassiveOffsetLeft,
        Number(this.$slabMassive.offsetY) +
          ev.pageY -
          this.slabMassiveOffsetTop,
        this.$slabMassive.scale * this.$slabMassive.zoom
      );
    }

    stopFollowing(data: Array<PieceMovementData>) {
      data.forEach((pieceMovementData) => {
        // TODO: clean this up when a state machine is used. Checking the
        // classList for is-pending is not ideal.
        if (
          pieceMovementData.id === this.draggedPieceID &&
          this.draggedPiece &&
          this.draggedPiece.classList.contains("is-pending")
        ) {
          streamService.unsubscribe(
            "piece/update",
            `pieceFollow ${this.instanceId}`
          );

          this.$slabMassive.removeEventListener(
            "mousemove",
            this.pieceFollow,
            false
          );
        }
      });
    }

    dropTap(ev) {
      ev.preventDefault();
      this.slabMassiveOffsetTop = this.$slabMassive.offsetTop;
      this.slabMassiveOffsetLeft = this.$slabMassive.offsetLeft;

      if (typeof this.draggedPieceID === "number") {
        puzzleService.unsubscribe(
          "piece/move/rejected",
          `pieceFollow ${this.draggedPieceID} ${this.instanceId}`
        );
        puzzleService.dropSelectedPieces(
          Number(this.$slabMassive.offsetX) +
            ev.pageX -
            this.slabMassiveOffsetLeft,
          Number(this.$slabMassive.offsetY) +
            ev.pageY -
            this.slabMassiveOffsetTop,
          this.$slabMassive.scale * this.$slabMassive.zoom
        );
        this.draggedPieceID = null;
      }
      document.addEventListener("keydown", (event) => {
        if (event.key == "Enter") {
          puzzleService.unSelectPiece(this.id);
          this.$slabMassive.removeEventListener(
            "mousemove",
            this.pieceFollow,
            false
          );
          // Stop listening for any updates to this piece
          puzzleService.unsubscribe(
            "piece/move/rejected",
            `pieceFollow ${this.id} ${this.instanceId}`
          );

          // Just unselect the piece so the next on tap doesn't move it

          this.onKarmaUpdated.bind(ev);
        }
      });
    }

    onTap(ev) {
      this.slabMassiveOffsetTop = this.$slabMassive.offsetTop;
      this.slabMassiveOffsetLeft = this.$slabMassive.offsetLeft;
      if (ev.target.classList.contains("p")) {
        this.draggedPiece = <HTMLElement>ev.target;
        this.draggedPieceID = parseInt(this.draggedPiece.id.substr(2));
        // ignore taps on the viewfinder of slab-massive
        if (ev.target.tagName === "SLAB-MASSIVE") {
          // TODO: is this check still needed?
          return;
        }
        this.$slabMassive.removeEventListener(
          "mousemove",
          this.pieceFollow,
          false
        );

        // Only select a tapped on piece if there are no other selected pieces.
        let id = Number(ev.target.id.substr("p-".length));
        if (
          ev.target.classList.contains("p") &&
          puzzleService.isSelectable(id) &&
          !this.blocked
        ) {
          // listen for piece updates to just this piece while it's being moved.
          puzzleService.subscribe(
            "piece/move/rejected",
            this.onPieceUpdateWhileSelected.bind(this),
            `pieceFollow ${id} ${this.instanceId}`
          );

          // tap on piece
          //window.clearTimeout(this.isWaitingOnMoveRequestTimeout);
          //this.$collection.classList.add("is-waitingOnMoveRequest");
          puzzleService.selectPiece(id);
          this.pieceFollow(ev); // show initial tap by moving piece to center
          this.$slabMassive.addEventListener(
            "mousemove",
            this.pieceFollow,
            false
          );
          // subscribe to piece/update to unfollow if active piece is updated
          streamService.subscribe(
            "piece/update",
            this.stopFollowing.bind(this),
            `pieceFollow ${this.instanceId}`
          );
        } else {
          puzzleService.unsubscribe(
            "piece/move/rejected",
            `pieceFollow ${this.draggedPieceID} ${this.instanceId}`
          );

          puzzleService.dropSelectedPieces(
            Number(this.$slabMassive.offsetX) +
              ev.pageX -
              this.slabMassiveOffsetLeft,
            Number(this.$slabMassive.offsetY) +
              ev.pageY -
              this.slabMassiveOffsetTop,
            this.$slabMassive.scale * this.$slabMassive.zoom
          );
          this.draggedPieceID = null;
        }
        document.addEventListener("keydown", (event) => {
          if (event.key == "Enter") {
            puzzleService.unSelectPiece(this.id);
            this.$slabMassive.removeEventListener(
              "mousemove",
              this.pieceFollow,
              false
            );
            // Stop listening for any updates to this piece
            puzzleService.unsubscribe(
              "piece/move/rejected",
              `pieceFollow ${this.id} ${this.instanceId}`
            );

            // Just unselect the piece so the next on tap doesn't move it

            this.onKarmaUpdated.bind(ev);
          }
        });
      }
    }

    onPieceUpdateWhileSelected(data) {
      // The selected piece has been updated while the player has it selected.
      // If it's immovable then drop it -- edit: if some other player has moved it, then drop it.
      // Stop following the mouse
      this.$slabMassive.removeEventListener(
        "mousemove",
        this.pieceFollow,
        false
      );

      // Stop listening for any updates to this piece
      puzzleService.unsubscribe(
        "piece/move/rejected",
        `pieceFollow ${data.id} ${this.instanceId}`
      );

      // Just unselect the piece so the next on tap doesn't move it
      puzzleService.unSelectPiece(data.id);
    }

    renderPieceKarma($piece: HTMLElement | null, karmaData: KarmaData) {
      let $_piece: HTMLElement | null =
        $piece || this.$collection.querySelector("#p-" + karmaData.id);
      // Toggle the is-up, is-down class when karma has changed
      if ($_piece !== null && karmaData.karmaChange) {
        if (karmaData.karmaChange > 0) {
          $_piece.classList.add("is-up");
          this.audioPuzzlePieceClick.play();
        } else if (karmaData.karmaChange < 0 && karmaData.karma < 18) {
          // Only show is-down icon if risk of player being blocked.
          $_piece.classList.add("is-down");
        }
        window.setTimeout(function cleanupKarma() {
          if ($_piece) {
            $_piece.classList.remove("is-up", "is-down");
          }
        }, 5000);
      }
    }

    batchRenderPieces(pieces: Array<PieceData>) {
      this.renderPiecesBuffer = this.renderPiecesBuffer.concat(pieces);
      if (!this.piecesPaused) {
        window.clearTimeout(this.batchRenderPiecesTimeout);
        this.batchRenderPiecesTimeout = undefined;
        let _buffer = this.renderPiecesBuffer.concat();
        this.renderPiecesBuffer = [];
        this.renderPieces(_buffer);
        return;
      }
      if (this.batchRenderPiecesTimeout === undefined) {
        //let _buffer = this.renderPiecesBuffer.concat();
        //this.renderPiecesBuffer = [];
        //this.renderPieces(_buffer);
        //this.pauseStop = Date.now() + this.maxPausePiecesTimeout * 1000;
        this.batchRenderPiecesTimeout = window.setTimeout(() => {
          this.batchRenderPiecesTimeout = undefined;
          puzzleService.togglePieceMovements(false);
          if (this.renderPiecesBuffer.length === 0) {
            return;
          }
          let _buffer = this.renderPiecesBuffer.concat();
          this.renderPiecesBuffer = [];
          this.renderPieces(_buffer);
        }, this.maxPausePiecesTimeout * 1000);
      }
    }

    _reducePieces(pieces: Array<PieceData>) {
      if (pieces.length > 1) {
        const pieceProps: PieceProps = {};
        pieces = Object.entries(
          pieces.reduce((acc, piece) => {
            if (acc[piece.id]) {
              Object.assign(acc[piece.id], piece);
            } else {
              acc[piece.id] = piece;
            }
            return acc;
          }, pieceProps)
        ).map(([, piece]) => {
          return piece;
        });
      }
      return pieces;
    }

    // update DOM for array of pieces
    renderPieces(pieces: Array<PieceData>) {
      let tmp: undefined | DocumentFragment; // = document.createDocumentFragment();
      //const startTime = new Date();
      pieces = this._reducePieces(pieces);
      pieces.forEach((piece) => {
        const pieceID = piece.id;
        let $piece = <HTMLElement | null>(
          this.$collection.querySelector("#p-" + pieceID)
        );
        if (!$piece) {
          if (tmp === undefined) {
            tmp = document.createDocumentFragment();
          }
          $piece = document.createElement("div");
          $piece.classList.add("p");
          $piece.setAttribute("id", "p-" + pieceID);
          $piece.classList.add("pc-" + pieceID);
          /* TODO: show id on piece when debugging
          const $pieceID = document.createElement("span");
          $pieceID.classList.add("p-id");
          $pieceID.innerText = "" + pieceID;
          $piece.appendChild($pieceID);
           */
          // dark/light pieces not used at the moment.
          //$piece.classList.add("p--" + (piece.b === 0 ? "dark" : "light"));
          tmp.appendChild($piece);
        }

        // Move the piece
        if (piece.x !== undefined) {
          $piece.style.transform = `translate3d(${piece.x}px, ${piece.y}px, 0)
            rotate(${360 - piece.r === 360 ? 0 : 360 - piece.r}deg)`;
        }

        // Set piece status
        if (piece.s === 1) {
          $piece.classList.add("is-immovable");
          $piece.classList.remove("is-stacked");
        } else if (piece.s === 2) {
          $piece.classList.add("is-stacked");
        } else if (piece.s === 0) {
          // Piece status can be '0' which would mean the status should be
          // reset. This is the case when a piece is no longer stacked.
          $piece.classList.remove("is-stacked");
        }

        // Toggle the is-active class
        if (piece.active) {
          $piece.classList.add("is-active");
        } else {
          $piece.classList.remove("is-active");
        }
        // Toggle the is-pending class
        if (piece.pending) {
          $piece.classList.add("is-pending");
        } else {
          $piece.classList.remove("is-pending");
        }
        // Toggle the is-dragging class
        if (piece.dragging) {
          $piece.classList.add("is-dragging");
        } else {
          $piece.classList.remove("is-dragging");
        }
      });
      if (tmp !== undefined && tmp.children.length) {
        this.$collection.appendChild(tmp);
      }
      //const endTime = new Date();
      //console.log("render pieces", endTime.getTime() - startTime.getTime());
    }

    // Update DOM for array of shadow pieces
    renderShadowPieces(pieces: Array<PieceData>) {
      let tmp: undefined | DocumentFragment; // = document.createDocumentFragment();
      const unrenderedShadowPieces: Array<PieceData> = [];
      pieces = pieces.reduce((acc, piece) => {
        if (!this.renderedShadowPieces[piece.id]) {
          acc.push(piece);
        }
        return acc;
      }, unrenderedShadowPieces);
      pieces = this._reducePieces(pieces);
      //const startTime = new Date();
      pieces.forEach((piece) => {
        const pieceID = piece.id;
        let $piece = <HTMLElement | null>(
          this.$collection.querySelector(".s-" + pieceID)
        );
        if (!$piece) {
          if (tmp === undefined) {
            tmp = document.createDocumentFragment();
          }
          $piece = document.createElement("div");
          $piece.classList.add("s");
          $piece.classList.add("s-" + pieceID);
          $piece.classList.add("pc-" + pieceID);
          // Grab current transform from real piece
          let $realPiece = <HTMLElement | null>(
            this.$collection.querySelector("#p-" + pieceID)
          );
          if ($realPiece) {
            $realPiece.classList.add("is-shadowed");
            const realPieceStyle = window.getComputedStyle($realPiece);
            const bbox = $realPiece.getBoundingClientRect();
            $piece.style.transform = realPieceStyle.transform + " scale(1.2)";
            //$piece.style.transitionDuration =
            //  Math.max(this.pauseStop - Date.now(), 0) + "ms";
            // Using a mask of the piece shape is too confusing visually.
            //$piece.style.maskImage = realPieceStyle.backgroundImage;
            //$piece.style.maskPosition = realPieceStyle.backgroundPosition;
            if (bbox) {
              $piece.setAttribute("x", String(bbox.left));
              $piece.setAttribute("y", String(bbox.top));
            }
          }
          tmp.appendChild($piece);
        }
        this.renderedShadowPieces[pieceID] = piece;
      });
      if (tmp !== undefined && tmp.children.length) {
        this.$collection.appendChild(tmp);
      }

      // Moving the shadow around is also too confusing visually.
      //window.setTimeout(() => {
      //  pieces.forEach((piece) => {
      //    const pieceID = piece.id;
      //    let $piece = <HTMLElement | null>(
      //      this.$collection.querySelector(".s-" + pieceID)
      //    );
      //    if ($piece) {
      //      // Move the piece
      //      if (piece.x !== undefined) {
      //        const originX = parseFloat($piece.getAttribute("x") || "0");
      //        const originY = parseFloat($piece.getAttribute("y") || "0");
      //        $piece.style.marginLeft = piece.x < originX ? "-50px" : "+50px";
      //        $piece.style.marginTop = piece.y < originY ? "-50px" : "+50px";
      //        /*
      //        $piece.style.transform = `translate3d(${piece.x}px, ${
      //          piece.y
      //        }px, 0)
      //          rotate(${360 - piece.r === 360 ? 0 : 360 - piece.r}deg)`;
      //        */
      //      }
      //    }
      //  });
      //}, 100);
    }

    removeShadowPieces() {
      const shadowPieces = this.$collection.querySelectorAll(".s");
      for (const sp of shadowPieces.values()) {
        try {
          sp.remove();
        } catch (error) {
          // ignore errors here
        }
      }
      this.renderedShadowPieces = {};
      // Delay removing is-shadowed so the transition can complete first
      window.clearTimeout(this.removeShadowedPiecesTimeout);
      this.removeShadowedPiecesTimeout = window.setTimeout(() => {
        const shadowedPieces =
          this.$collection.querySelectorAll(".is-shadowed.p");
        for (const sp of shadowedPieces.values()) {
          sp.classList.remove("is-shadowed");
        }
      }, 1200);
    }

    onToggleMovable(showMovable: boolean) {
      this.$container.classList.toggle("show-movable", showMovable);
    }

    onPiecesPauseResume(pause: boolean) {
      this.piecesPaused = pause;
      if (!this.piecesPaused) {
        this.removeShadowPieces();
        window.clearTimeout(this.isWaitingOnMoveRequestTimeout);
        this.isWaitingOnMoveRequestTimeout = window.setTimeout(() => {
          this.$collection.classList.remove("is-waitingOnMoveRequest");
        }, 1000);
        //this.$collection.classList.remove("is-waitingOnMoveRequest");
      } else {
        window.clearTimeout(this.isWaitingOnMoveRequestTimeout);
        this.$collection.classList.add("is-waitingOnMoveRequest");
      }
    }

    updateForegroundAndBackgroundColors() {
      const hash = hashColorService.backgroundColor; /*(this.name)*/
      const hashRGBColorRe = /#([a-f0-9]{2})([a-f0-9]{2})([a-f0-9]{2})/i;
      if (!hash) {
        return;
      }
      let RGBmatch = hash.match(hashRGBColorRe);

      if (RGBmatch) {
        let hsl = rgbToHsl(RGBmatch[1], RGBmatch[2], RGBmatch[3]);
        this.$container.style.backgroundColor = `hsla(${hsl[0]},${hsl[1]}%,${hsl[2]}%,1)`;

        // let hue = hsl[0]
        // let sat = hsl[1]
        let light = hsl[2];
        /*
              let opposingHSL = [
                hue > 180 ? hue - 180 : hue + 180,
                100 - sat,
                100 - light
              ]
              */
        let contrast = light > 50 ? 0 : 100;
        this.$container.style.color = `hsla(0,0%,${contrast}%,1)`;
      }
      this.$container.style.setProperty("--pm-PuzzlePieces-shadowColor", hash);
    }

    // Fires when an instance was inserted into the document.
    connectedCallback() {
      this.updateForegroundAndBackgroundColors();
    }

    disconnectedCallback() {
      streamService.unsubscribe("piece/update", this.instanceId);
      streamService.unsubscribe("puzzle/status", this.instanceId);
      puzzleService.unsubscribe("pieces/mutate", this.instanceId);
      puzzleService.unsubscribe("pieces/shadow-mutate", this.instanceId);
      puzzleService.unsubscribe("pieces/update", this.instanceId);
      puzzleService.unsubscribe(
        "piece/move/rejected",
        `pieceFollow ${this.draggedPieceID} ${this.instanceId}`
      );
      puzzleService.unsubscribe("piece/move/blocked", this.instanceId);
      puzzleService.unsubscribe("pieces/info/toggle-movable", this.instanceId);
      hashColorService.unsubscribe(this.instanceId);
    }

    static get observedAttributes() {
      return [];
    }

    // Fires when an attribute was added, removed, or updated.
    //attributeChangedCallback(attrName, oldVal, newVal) {}

    render() {}
  }
);
