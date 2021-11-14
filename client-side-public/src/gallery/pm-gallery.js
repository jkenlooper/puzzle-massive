import { html, render } from "lit";
import { repeat } from "lit/directives/repeat.js";
import { puzzleImagesService, } from "../site/puzzle-images.service";
import "./gallery.css";
const tag = "pm-gallery";
let lastInstanceId = 0;
customElements.define(tag, class PmGallery extends HTMLElement {
    constructor() {
        super();
        this.skipPuzzleId = "";
        this.puzzles = undefined;
        this.puzzlesOrderedByPieceCount = undefined;
        this.hasError = false;
        this.errorMessage = "";
        this.isLoadingPuzzles = true;
        this.variant = "card";
        this.skillLevelRanges = [];
        // Set the attribute values
        const frontFragmentHref = this.attributes.getNamedItem("front-fragment-href");
        if (!frontFragmentHref || !frontFragmentHref.value) {
            this.hasError = true;
            this.errorMessage = "No front-fragment-href has been set.";
        }
        else {
            this.frontFragmentHref = frontFragmentHref.value;
        }
        const puzzlePieceGroupsAttr = this.attributes.getNamedItem("puzzle-piece-groups");
        if (!puzzlePieceGroupsAttr || !puzzlePieceGroupsAttr.value) {
            this.hasError = true;
            this.errorMessage = "Missing puzzle-piece-groups attribute";
        }
        else {
            const puzzlePieceGroups = puzzlePieceGroupsAttr.value
                .split(/\s+/)
                .map((v) => {
                return parseInt(v);
            });
            this.skillLevelRanges = puzzlePieceGroups.reduce((acc, v, index) => {
                acc[index].push(v);
                acc.push([v]);
                return acc;
            }, [[0]]);
            this.skillLevelRanges.pop();
        }
        const skipAttr = this.attributes.getNamedItem("skip") || "";
        if (skipAttr && skipAttr.value) {
            this.skipPuzzleId = skipAttr.value;
        }
        const variantAttr = this.attributes.getNamedItem("variant") || "";
        if (variantAttr && variantAttr.value) {
            this.variant = variantAttr.value;
        }
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    setPuzzleImages() {
        return puzzleImagesService
            .getGalleryPuzzleImages()
            .then((puzzleList) => {
            // Filter out the skip puzzle and then select one puzzle from each
            // skill level range.
            const selected_range = Array(this.skillLevelRanges.length);
            this.puzzles = puzzleList.puzzles
                .filter((puzzle) => {
                return puzzle.puzzle_id !== this.skipPuzzleId;
            })
                .filter((puzzle) => {
                const levelIndex = this.skillLevelRanges.findIndex((range) => {
                    return range[0] >= puzzle.pieces && puzzle.pieces < range[1];
                });
                if (selected_range[levelIndex]) {
                    return false;
                }
                else {
                    selected_range[levelIndex] = true;
                    return true;
                }
            });
            this.puzzlesOrderedByPieceCount = puzzleList.puzzles.filter((puzzle) => {
                return puzzle.puzzle_id !== this.skipPuzzleId;
            });
            this.puzzlesOrderedByPieceCount.sort((puzzleA, puzzleB) => {
                return puzzleA.pieces - puzzleB.pieces;
            });
        })
            .catch((err) => {
            console.error(err);
            this.hasError = true;
            this.errorMessage = "Error getting the puzzle images.";
        })
            .finally(() => {
            this.isLoadingPuzzles = false;
            this.render();
        });
    }
    template(data) {
        if (data.hasError) {
            return html ` ${data.errorMessage} `;
        }
        if (data.variant === "card") {
            return html `
          <div class="pm-Gallery">
            ${data.isLoadingPuzzles
                ? html ` Loading puzzles&hellip; `
                : html `
                  ${data.puzzles && data.puzzles.length
                    ? html `
                        <div
                          class="pm-PuzzleList pm-PuzzleList--card"
                          role="list"
                        >
                          ${repeat(data.puzzles, (puzzle) => puzzle.puzzle_id, (puzzle) => html `
                              <pm-puzzle-image-card
                                variant=${data.variant}
                                .puzzle=${puzzle}
                                front-fragment-href=${data.frontFragmentHref}
                              ></pm-puzzle-image-card>
                            `)}
                        </div>
                      `
                    : html ` <p>No puzzles.</p> `}
                `}
          </div>
        `;
        }
        else if (data.variant === "inline") {
            return html `
          <div class="pm-Gallery">
            ${data.isLoadingPuzzles
                ? html ` &hellip; `
                : html `
                  ${data.puzzlesOrderedByPieceCount &&
                    data.puzzlesOrderedByPieceCount.length
                    ? html `
                        <span class="u-block u-textRight">
                          Active Jigsaw Puzzles from
                          <strong class="u-textNoWrap">
                            ${data.puzzlesOrderedByPieceCount[0].pieces} to
                            ${data.puzzlesOrderedByPieceCount[data.puzzlesOrderedByPieceCount.length - 1].pieces}
                          </strong>
                          Pieces
                        </span>
                        <div
                          class="pm-PuzzleList pm-PuzzleList--inline"
                          role="list"
                        >
                          ${repeat(data.puzzlesOrderedByPieceCount, (puzzle) => puzzle.puzzle_id, (puzzle) => html `
                              <pm-puzzle-image-card
                                variant=${data.variant}
                                .puzzle=${puzzle}
                                front-fragment-href=${data.frontFragmentHref}
                              ></pm-puzzle-image-card>
                            `)}
                        </div>
                      `
                    : html ` <p>No puzzles.</p> `}
                `}
          </div>
        `;
        }
        else {
            return html ``;
        }
    }
    get data() {
        return {
            isLoadingPuzzles: this.isLoadingPuzzles,
            hasError: this.hasError,
            errorMessage: this.errorMessage,
            puzzles: this.puzzles,
            puzzlesOrderedByPieceCount: this.puzzlesOrderedByPieceCount,
            frontFragmentHref: this.frontFragmentHref,
            variant: this.variant,
        };
    }
    render() {
        render(this.template(this.data), this);
    }
    connectedCallback() {
        this.setPuzzleImages();
        this.render();
    }
    disconnectedCallback() { }
    adoptedCallback() { }
});
