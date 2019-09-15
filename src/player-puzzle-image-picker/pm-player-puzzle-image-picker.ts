import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";

import {
  PlayerPuzzleListResponse,
  PuzzleImageData,
  puzzleImagesService,
} from "../puzzle-image-picker/puzzle-images.service";

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isLoadingPuzzles: boolean;
  puzzles: undefined | Array<PuzzleImageData>;
  frontFragmentHref: undefined | string;
}

const tag = "pm-player-puzzle-image-picker";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPlayerPuzzleImagePicker extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    frontFragmentHref: undefined | string;
    puzzles: undefined | Array<PuzzleImageData> = undefined;
    hasError: boolean = false;
    errorMessage: string = "";
    isLoadingPuzzles: boolean = true;

    constructor() {
      super();

      // Set the attribute values
      const frontFragmentHref = this.attributes.getNamedItem(
        "front-fragment-href"
      );
      if (!frontFragmentHref || !frontFragmentHref.value) {
        this.hasError = true;
        this.errorMessage = "No front-fragment-href has been set.";
      } else {
        this.frontFragmentHref = frontFragmentHref.value;
      }
    }

    setPuzzleImages() {
      return puzzleImagesService
        .getPlayerPuzzleImages()
        .then((puzzleList: PlayerPuzzleListResponse) => {
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

    template(data: TemplateData) {
      if (data.hasError) {
        return html`
          ${data.errorMessage}
        `;
      }
      return html`
        <div class="pm-PuzzleImagePicker">
          ${data.isLoadingPuzzles
            ? html`
                Loading puzzles&hellip;
              `
            : html`
                ${data.puzzles && data.puzzles.length
                  ? html`
                      <div class="pm-PuzzleImagePicker-list" role="list">
                        ${repeat(
                          data.puzzles,
                          (puzzle) => puzzle.puzzle_id,
                          (puzzle) => html`
                            ${puzzle.puzzle_id
                              ? html`
                                  <pm-puzzle-image-card
                                    .puzzle=${puzzle}
                                    front-fragment-href=${data.frontFragmentHref}
                                  ></pm-puzzle-image-card>
                                `
                              : html`
                                  <div class="pm-PuzzleImagePicker-listItem">
                                    <div
                                      class="pm-PuzzleImagePicker-puzzleLink"
                                    >
                                      +
                                    </div>
                                  </div>
                                `}
                          `
                        )}
                      </div>
                    `
                  : html`
                      <p>No puzzles.</p>
                    `}
              `}
        </div>
      `;
    }

    get data(): TemplateData {
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
    disconnectedCallback() {}
    adoptedCallback() {}
  }
);
