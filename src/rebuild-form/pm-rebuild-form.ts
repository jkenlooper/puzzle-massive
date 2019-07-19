/* global HTMLElement, customElements */

import { html, render } from "lit-html";

import userDetailsService from "../site/user-details.service";

interface TemplateData {
  dots: number;
  maxPointCost: number;
  minPieceCount: number;
  maxPieceCountForDots: number;
  pieceCount: number;
  puzzleId: string;
  canRebuild: boolean;
}

const maxPieceCount = 50000;

const tag = "pm-rebuild-form";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmRebuildForm extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }
    private instanceId: string;
    private maxPointCost: number;
    private minPieceCount: number;
    private pieceCount: number;
    private puzzleId: string;
    private isOriginal: boolean;
    private owner: number;

    constructor() {
      super();
      this.instanceId = PmRebuildForm._instanceId;

      const maxPointCost = this.attributes.getNamedItem("max-point-cost");
      this.maxPointCost = maxPointCost ? parseInt(maxPointCost.value) : 0;

      const minPieceCount = this.attributes.getNamedItem("min-piece-count");
      this.minPieceCount = minPieceCount ? parseInt(minPieceCount.value) : 0;

      const pieceCount = this.attributes.getNamedItem("piece-count");
      this.pieceCount = pieceCount ? parseInt(pieceCount.value) : 0;

      const puzzleId = this.attributes.getNamedItem("puzzle-id") || {
        value: "",
      };
      this.puzzleId = typeof puzzleId.value === "string" ? puzzleId.value : "";
      if (!this.puzzleId) {
        throw new Error("no puzzle id set in rebuild form");
      }

      const isOriginal = this.attributes.getNamedItem("is-original");
      this.isOriginal = isOriginal ? parseInt(isOriginal.value) === 1 : true;

      const owner = this.attributes.getNamedItem("owner");
      this.owner = owner ? parseInt(owner.value) : 0;

      userDetailsService.subscribe(this.render.bind(this), this.instanceId);
      this.render();
    }

    template(data: TemplateData) {
      if (data.canRebuild) {
        return html`
          <p>
            You have earned
            <strong>${data.dots}</strong>
            dots by putting together puzzles. Rebuilding puzzles will decrease
            the number of dots depending on the piece count selected up to
            ${data.maxPointCost} dots.
          </p>
          <form method="post" action="/newapi/puzzle-rebuild/">
            <input type="hidden" name="puzzle_id" value=${data.puzzleId} />
            <label for="pieces">
              Piece Count
            </label>
            <input
              type="number"
              min=${data.minPieceCount}
              max=${data.maxPieceCountForDots}
              name="pieces"
              id="pieces"
              value=${data.pieceCount}
            />
            <input type="submit" value="Rebuild the puzzle" />
          </form>
        `;
      } else {
        return html`
          <p>
            Only the owner of this puzzle instance can rebuild it.
          </p>
        `;
      }
    }

    get data(): TemplateData {
      return {
        dots: userDetailsService.userDetails.dots,
        maxPointCost: this.maxPointCost,
        minPieceCount: this.minPieceCount,
        maxPieceCountForDots: Math.min(
          userDetailsService.userDetails.dots,
          maxPieceCount
        ),
        pieceCount: this.pieceCount,
        puzzleId: this.puzzleId,
        canRebuild:
          this.isOriginal || userDetailsService.userDetails.id === this.owner,
      };
    }

    render() {
      render(this.template(this.data), this);
    }
  }
);
