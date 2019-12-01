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
import { puzzleService, PieceData } from "./puzzle.service";
import { divulgerService } from "./divulger.service";

import template from "./puzzle-pieces.html";
import style from "./puzzle-pieces.css";

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
    private blocked: boolean = false;
    private blockedTimer: number = 0;
    private blockedTimeout: number | undefined;

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

      puzzleService.init(this.puzzleId);
      puzzleService.subscribe(
        "pieces/mutate",
        this.renderPieces.bind(this),
        this.instanceId
      );

      this.pieceFollow = this._pieceFollow.bind(this);

      puzzleService.subscribe(
        "piece/move/blocked",
        this.onMoveBlocked.bind(this),
        this.instanceId
      );

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
          puzzleService.selectPiece(id);
          this.$slabMassive.addEventListener(
            "mousemove",
            this.pieceFollow,
            false
          );
          // subscribe to piece/update to unfollow if active piece is updated
          divulgerService.subscribe(
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

    // update DOM for array of pieces
    renderPieces(pieces: Array<PieceData>) {
      let tmp: undefined | DocumentFragment; // = document.createDocumentFragment();
      //const startTime = new Date();
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
          $piece.classList.add("p--" + (piece.b === 0 ? "dark" : "light"));
          tmp.appendChild($piece);
        }

        // Move the piece
        if (piece.x !== undefined) {
          $piece.style.transform = `translate3d(${piece.x}px, ${piece.y}px, 0)
            rotate(${360 - piece.r === 360 ? 0 : 360 - piece.r}deg)`;
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
      if (tmp !== undefined && tmp.children.length) {
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
    }

    // Fires when an instance was inserted into the document.
    connectedCallback() {
      this.updateForegroundAndBackgroundColors();
    }

    disconnectedCallback() {
      divulgerService.unsubscribe("piece/update", this.instanceId);
      puzzleService.unsubscribe("pieces/mutate", this.instanceId);
      puzzleService.unsubscribe(
        "piece/move/rejected",
        `pieceFollow ${this.draggedPieceID} ${this.instanceId}`
      );
    }

    static get observedAttributes() {
      return [];
    }
    // Fires when an attribute was added, removed, or updated.
    //attributeChangedCallback(attrName, oldVal, newVal) {}

    render() {}
  }
);
