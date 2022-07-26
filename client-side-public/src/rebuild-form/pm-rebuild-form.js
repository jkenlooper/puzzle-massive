/* global HTMLElement, customElements */
import { html, render } from "lit";
import userDetailsService from "../site/user-details.service";
const maxPieceCount = 50000;
const tag = "pm-rebuild-form";
let lastInstanceId = 0;
customElements.define(
  tag,
  class PmRebuildForm extends HTMLElement {
    constructor() {
      super();
      this.instanceId = PmRebuildForm._instanceId;
      const maxPointCost = this.attributes.getNamedItem("max-point-cost");
      this.maxPointCost = maxPointCost ? parseInt(maxPointCost.value) : 0;
      const newUserStartingPointsAttr = this.attributes.getNamedItem(
        "new-user-starting-points"
      );
      this.newUserStartingPoints = newUserStartingPointsAttr
        ? parseInt(newUserStartingPointsAttr.value)
        : 0;
      const pointsCapAttr = this.attributes.getNamedItem("points-cap");
      this.pointsCap = pointsCapAttr ? parseInt(pointsCapAttr.value) : 0;
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
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }
    template(data) {
      if (data.canRebuild) {
        return html`
          ${data.playerOwnsPuzzleInstance
            ? html`
                <p>
                  You are the owner of this puzzle instance and you can rebuild
                  it without using any dots.
                </p>
              `
            : html`
                <p>
                  You have earned
                  <strong>${data.dots}</strong>
                  dots by putting together puzzles. All players start with a
                  minimum of ${data.newUserStartingPoints} dots each day and
                  have a maximum of ${data.pointsCap} that can be earned.
                  Rebuilding puzzles will decrease the number of dots depending
                  on the piece count selected up to ${data.maxPointCost} dots.
                </p>
              `}
          <form method="post" action="/newapi/puzzle-rebuild/">
            <input type="hidden" name="puzzle_id" value=${data.puzzleId} />
            <label for="pieces"> Piece Count </label>
            <input
              type="number"
              min=${data.minPieceCount}
              max=${data.playerOwnsPuzzleInstance
                ? data.maxPieceCount
                : data.maxPieceCountForDots}
              name="pieces"
              id="pieces"
              value=${data.pieceCount}
            />
            <input
              class="Button Button--primary"
              type="submit"
              value="Rebuild the puzzle"
            />
          </form>
        `;
      } else {
        return html`
          <p>Only the owner of this puzzle instance can rebuild it.</p>
        `;
      }
    }
    get data() {
      return {
        dots: userDetailsService.userDetails.dots,
        maxPointCost: this.maxPointCost,
        newUserStartingPoints: this.newUserStartingPoints,
        pointsCap: this.pointsCap,
        minPieceCount: this.minPieceCount,
        maxPieceCount: maxPieceCount,
        maxPieceCountForDots: Math.min(
          userDetailsService.userDetails.dots,
          maxPieceCount
        ),
        pieceCount: this.pieceCount,
        puzzleId: this.puzzleId,
        playerOwnsPuzzleInstance:
          userDetailsService.userDetails.id === this.owner && !this.isOriginal,
        canRebuild:
          this.isOriginal || userDetailsService.userDetails.id === this.owner,
      };
    }
    render() {
      render(this.template(this.data), this);
    }
  }
);
