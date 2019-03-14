import * as Hammer from "hammerjs";

// TODO: Exercise for the developer; refactor this mess of old javascript into
// a more manageable state.  Should start with unit test coverage.  There is
// also a lot of poorly implemented state management going on here that could be
// refactored with using redux and/or a state machine.
//
// I've added on with more terrible code (a 'small' tweak here and there) to
// make things more challenging. ;)

import { rgbToHsl } from "../site/utilities";
import hashColorService from "../hash-color/hash-color.service";
import PuzzleService from "./puzzle.service.js";
import { divulgerService } from "./divulger.service";
import PuzzlePiecesController from "./puzzle-pieces.controller.js";

import template from "./puzzle-pieces.html";
import style from "./puzzle-pieces.css";

interface PieceData {
  id: number;
  b: number; // b for background
  x: number;
  y: number;
  rotate: number;
  s?: number; // s for stacked
  active?: boolean;
  karma?: number; // response from move request
  karmaChange?: number | boolean; // response from move request
}

interface Pieces {
  [index: number]: PieceData;
}

const html = `
  <style>${style}</style>
  ${template}
  `;
const tag = "pm-puzzle-pieces";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzlePieces extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    private puzzleId: string;
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
    private pieceRejectedHandles: object;
    ctrl: PuzzlePiecesController;
    constructor() {
      super();
      const self = this;
      this.instanceId = PmPuzzlePieces._instanceId;
      const shadowRoot = this.attachShadow({ mode: "open" });
      shadowRoot.innerHTML = `<style>@import '${this.getAttribute(
        "resources"
      )}';></style>'${html}`;
      this.$collection = <HTMLElement>(
        shadowRoot.querySelector(".pm-PuzzlePieces-collection")
      );
      this.$dropZone = <HTMLElement>(
        shadowRoot.querySelector(".pm-PuzzlePieces-dropZone")
      );
      this.$container = <HTMLElement>(
        shadowRoot.querySelector(".pm-PuzzlePieces")
      );
      this.$slabMassive = this.parentElement;
      const withinSlabMassive = this.$slabMassive.tagName === "SLAB-MASSIVE";

      const puzzleId = this.attributes.getNamedItem("puzzle-id");
      this.puzzleId = puzzleId ? puzzleId.value : "";

      if (!withinSlabMassive) {
        // Not using slab-massive so we need to set the width of all parent
        // elements so the browser can properly zoom out.
        setParentWidth(this.$slabMassive.parentNode);

        // Patch in these properties from the attrs
        Object.defineProperty(this.$slabMassive, "scale", {
          get: function() {
            return Number(this.getAttribute("scale"));
          },
        });
        Object.defineProperty(this.$slabMassive, "zoom", {
          get: function() {
            return Number(this.getAttribute("zoom"));
          },
        });
        Object.defineProperty(this.$slabMassive, "offsetX", {
          get: function() {
            return Number(this.getAttribute("offset-x"));
          },
        });
        Object.defineProperty(this.$slabMassive, "offsetY", {
          get: function() {
            return Number(this.getAttribute("offset-y"));
          },
        });
      } else {
        this.$container.classList.add("pm-PuzzlePieces--withinSlabMassive");
      }

      this.slabMassiveOffsetTop = this.$slabMassive.offsetTop;
      this.slabMassiveOffsetLeft = this.$slabMassive.offsetLeft;

      const puzzleService = new PuzzleService(this.puzzleId, divulgerService);
      this.ctrl = new PuzzlePiecesController(this.puzzleId, puzzleService);
      this.ctrl.renderPieces = this.renderPieces.bind(this);
      this.pieceRejectedHandles = {};

      this.pieceFollow = this._pieceFollow.bind(this);

      // For all parent elements set the width
      function setParentWidth(node) {
        if (node.style) {
          node.style.width = self.$slabMassive.offsetWidth + "px";
        }
        if (node.parentNode) {
          setParentWidth(node.parentNode);
        }
      }

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
      mc.on("panstart panmove", function(ev) {
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
    }

    _pieceFollow(ev) {
      this.ctrl.moveBy(
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

    stopFollowing(data) {
      if (data.id === this.draggedPieceID) {
        divulgerService.unsubscribe(
          "piece/update",
          `pieceFollow ${this.instanceId}`
        );
        this.$slabMassive.removeEventListener(
          "mousemove",
          this.pieceFollow,
          false
        );
      }
    }

    dropTap(ev) {
      ev.preventDefault();
      if (typeof this.draggedPieceID === "number") {
        // @ts-ignore
        if (this.pieceRejectedHandles[this.draggedPieceID]) {
          // @ts-ignore
          window.unsubscribe(this.pieceRejectedHandles[this.draggedPieceID]);
          // @ts-ignore
          delete this.pieceRejectedHandles[this.draggedPieceID];
        }
        this.ctrl.dropSelectedPieces(
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
    }

    onTap(ev) {
      if (ev.target.classList.contains("p")) {
        this.draggedPiece = <HTMLElement>ev.target;
        this.draggedPieceID = parseInt(this.draggedPiece.id.substr(2));
        // ignore taps on the viewfinder of slab-massive
        if (ev.target.tagName === "SLAB-MASSIVE") {
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
          !this.ctrl.isImmovable(id) &&
          this.ctrl.selectedPieces.length === 0 &&
          !this.ctrl.blocked
        ) {
          // listen for piece updates to just this piece while it's being moved.
          // TODO: listen to reject as well?
          // @ts-ignore
          const rejectHandle = window.subscribe(
            "piece/move/rejected",
            this.onPieceUpdateWhileSelected.bind(this)
          );
          this.pieceRejectedHandles[this.draggedPieceID] = rejectHandle;

          // tap on piece
          this.ctrl.selectPiece(id);
          this.$slabMassive.addEventListener(
            "mousemove",
            this.pieceFollow,
            false
          );
          // TODO: subscribe to piece/update to unfollow if active piece is updated
          divulgerService.subscribe(
            "piece/update",
            this.stopFollowing.bind(this),
            `pieceFollow ${this.instanceId}`
          );
        } else {
          if (this.pieceRejectedHandles[this.draggedPieceID]) {
            // @ts-ignore
            window.unsubscribe(this.pieceRejectedHandles[this.draggedPieceID]);
            delete this.pieceRejectedHandles[this.draggedPieceID];
          }
          this.ctrl.dropSelectedPieces(
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
      if (this.pieceRejectedHandles[data.id]) {
        // @ts-ignore
        window.unsubscribe(this.pieceRejectedHandles[data.id]);
        delete this.pieceRejectedHandles[data.id];
      }

      // Just unselect the piece so the next on tap doesn't move it
      this.ctrl.unSelectPiece(data.id);
    }

    // update DOM for array of piece id's
    renderPieces(pieces: Pieces, pieceIDs) {
      let tmp = document.createDocumentFragment();
      //const startTime = new Date();
      pieceIDs.forEach((pieceID) => {
        let piece = pieces[pieceID];
        let $piece = <HTMLElement | null>(
          this.$collection.querySelector("#p-" + pieceID)
        );
        if (!$piece) {
          $piece = document.createElement("div");
          $piece.classList.add("p");
          $piece.setAttribute("id", "p-" + pieceID);
          $piece.classList.add("pc-" + pieceID);
          $piece.classList.add("p--" + (piece.b === 0 ? "dark" : "light"));
          tmp.appendChild($piece);
        }

        // Move the piece
        if (piece.x !== undefined) {
          $piece.style.transform = `translate3d(${piece.x}px, ${piece.y}px, 0)
            rotate(${360 - piece.rotate === 360 ? 0 : 360 - piece.rotate}deg)`;
        }

        // Piece status can be undefined which would mean the status should be
        // reset. This is the case when a piece is no longer stacked.
        if (piece.s === undefined) {
          // Not showing any indication of stacked pieces on the front end,
          // so no class to remove.
          //
          // Once a piece is immovable it shouldn't need to become movable
          // again. (it's part of the border pieces group)
        }
        // Set immovable
        if (piece.s === 1) {
          $piece.classList.add("is-immovable");
        }

        // Toggle the is-active class
        if (piece.active) {
          $piece.classList.add("is-active");
        } else {
          $piece.classList.remove("is-active");
        }

        // Toggle the is-up, is-down class when karma has changed
        if (piece.karmaChange) {
          if (piece.karmaChange > 0) {
            $piece.classList.add("is-up");
          } else {
            $piece.classList.add("is-down");
          }
          window.setTimeout(function cleanupKarma() {
            if ($piece) {
              $piece.classList.remove("is-up", "is-down");
            }
          }, 5000);
          piece.karmaChange = false;
        }
      });
      if (tmp.children.length) {
        this.$collection.appendChild(tmp);
      }
      //const endTime = new Date();
      //console.log("render pieces", endTime.getTime() - startTime.getTime());
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
        this.$container.style.backgroundColor = `hsla(${hsl[0]},${hsl[1]}%,${
          hsl[2]
        }%,1)`;

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
    }

    // Fires when an instance was inserted into the document.
    connectedCallback() {
      this.updateForegroundAndBackgroundColors();
    }

    disconnectedCallback() {
      this.ctrl.unsubscribe();
    }

    static get observedAttributes() {
      return [];
    }
    // Fires when an attribute was added, removed, or updated.
    //attributeChangedCallback(attrName, oldVal, newVal) {}

    render() {}
  }
);
