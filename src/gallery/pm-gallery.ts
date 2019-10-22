import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";

import {
  GalleryPuzzleListResponse,
  PuzzleImageData,
  puzzleImagesService,
} from "../site/puzzle-images.service";

import "./gallery.css";

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isLoadingPuzzles: boolean;
  puzzles: undefined | Array<PuzzleImageData>;
  frontFragmentHref: undefined | string;
}

// Copied SKILL_LEVEL_RANGES from api/api/constants.py
const SKILL_LEVEL_RANGES = [
  [0, 400],
  [400, 800],
  [800, 1600],
  [1600, 2200],
  [2200, 4000],
  [4000, 60000],
];

const tag = "pm-gallery";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmGallery extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    frontFragmentHref: undefined | string;
    skipPuzzleId: string = "";
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

      const skipAttr = this.attributes.getNamedItem("skip") || "";
      if (skipAttr && skipAttr.value) {
        this.skipPuzzleId = skipAttr.value;
      }
    }

    setPuzzleImages() {
      return puzzleImagesService
        .getGalleryPuzzleImages()
        .then((puzzleList: GalleryPuzzleListResponse) => {
          // Filter out the skip puzzle and then select one puzzle from each
          // skill level range.
          const selected_range = Array(SKILL_LEVEL_RANGES.length);
          this.puzzles = puzzleList.puzzles
            .filter((puzzle) => {
              return puzzle.puzzle_id !== this.skipPuzzleId;
            })
            .filter((puzzle) => {
              const levelIndex = SKILL_LEVEL_RANGES.findIndex((range) => {
                return range[0] >= puzzle.pieces && puzzle.pieces < range[1];
              });
              if (selected_range[levelIndex]) {
                return false;
              } else {
                selected_range[levelIndex] = true;
                return true;
              }
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

    template(data: TemplateData) {
      if (data.hasError) {
        return html`
          ${data.errorMessage}
        `;
      }
      return html`
        <div class="pm-Gallery">
          ${data.isLoadingPuzzles
            ? html`
                Loading puzzles&hellip;
              `
            : html`
                ${data.puzzles && data.puzzles.length
                  ? html`
                      <div class="pm-PuzzleList" role="list">
                        ${repeat(
                          data.puzzles,
                          (puzzle) => puzzle.puzzle_id,
                          (puzzle) => html`
                            <pm-puzzle-image-card
                              .puzzle=${puzzle}
                              front-fragment-href=${data.frontFragmentHref}
                            ></pm-puzzle-image-card>
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
