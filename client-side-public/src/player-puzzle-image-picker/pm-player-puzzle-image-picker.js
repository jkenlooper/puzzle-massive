import { html, render } from "lit";
import { repeat } from "lit/directives/repeat.js";
import { puzzleImagesService, } from "../site/puzzle-images.service";
import "./player-puzzle-image-picker.css";
const tag = "pm-player-puzzle-image-picker";
let lastInstanceId = 0;
customElements.define(tag, class PmPlayerPuzzleImagePicker extends HTMLElement {
    constructor() {
        super();
        this.puzzles = undefined;
        this.hasError = false;
        this.errorMessage = "";
        this.isLoadingPuzzles = true;
        // Set the attribute values
        const frontFragmentHref = this.attributes.getNamedItem("front-fragment-href");
        if (!frontFragmentHref || !frontFragmentHref.value) {
            this.hasError = true;
            this.errorMessage = "No front-fragment-href has been set.";
        }
        else {
            this.frontFragmentHref = frontFragmentHref.value;
        }
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    setPuzzleImages() {
        return puzzleImagesService
            .getPlayerPuzzleImages()
            .then((puzzleList) => {
            this.puzzles = puzzleList.puzzles;
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
        return html `
        <div class="pm-PlayerPuzzleImagePicker">
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
                            ${puzzle.puzzle_id
                    ? html `
                                  <pm-puzzle-image-card
                                    .puzzle=${puzzle}
                                    hide-owner
                                    front-fragment-href=${data.frontFragmentHref}
                                  ></pm-puzzle-image-card>
                                `
                    : html `
                                  <div
                                    class="pm-PlayerPuzzleImagePicker-emptySlot"
                                  >
                                    Empty Slot
                                  </div>
                                `}
                          `)}
                      </div>
                    `
                : html ` <p>No puzzles.</p> `}
              `}
        </div>
      `;
    }
    get data() {
        return {
            isLoadingPuzzles: this.isLoadingPuzzles,
            hasError: this.hasError,
            errorMessage: this.errorMessage,
            puzzles: this.puzzles,
            frontFragmentHref: this.frontFragmentHref,
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
