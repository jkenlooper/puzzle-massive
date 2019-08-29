import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";

import userDetailsService from "../site/user-details.service";
import { PuzzleImages, puzzleImagesService } from "./puzzle-images.service";

import "./puzzle-image-picker.css";

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isReady: boolean;
  puzzles: undefined | PuzzleImages;
  frontFragmentHref: undefined | string;
}

const tag = "pm-puzzle-image-picker";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleImagePicker extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    frontFragmentHref: undefined | string;
    puzzles: undefined | PuzzleImages = undefined;
    hasError: boolean = false;
    errorMessage: string = "";
    isReady: boolean = false;

    constructor() {
      super();
      this.instanceId = PmPuzzleImagePicker._instanceId;

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

      userDetailsService.subscribe(
        this._setPuzzleImages.bind(this),
        this.instanceId
      );
    }

    _setPuzzleImages() {
      return puzzleImagesService
        .getPuzzleImages()
        .then((puzzleImages: PuzzleImages) => {
          this.puzzles = puzzleImages;
        })
        .catch(() => {
          this.hasError = true;
          this.errorMessage = "Error getting the puzzle images.";
        })
        .finally(() => {
          this.isReady = true;
          this.render();
        });
    }

    template(data: TemplateData) {
      if (!data.isReady) {
        return html``;
      }
      if (data.hasError) {
        return html`
          ${data.errorMessage}
        `;
      }
      return html`
        <div class="pm-PuzzleImagePicker">
          <div>
            <strong>Filter images</strong>
            <div>
              <label for="puzzle-image-picker--pieces"
                >Maximum piece count</label
              >
              <input
                type="range"
                min="100"
                max="6000"
                step="100"
                list="puzzle-image-picker--pieces-list"
              />
              <datalist id="puzzle-image-picker--pieces-list">
                {#
                <!-- No FF support, Chrome supports tickmarks -->
                #}
                <option value="100" label="100"> </option>
                <option value="1000" label="1000"> </option>
                <option value="2000" label="2000"> </option>
                <option value="6000" label="6000+"> </option>
              </datalist>

              <p>
                <em
                  >Show only images that are big enough to have this many
                  pieces</em
                >
              </p>
            </div>
          </div>

              <div class="pm-PuzzleImagePicker-list" role="list">
                ${
                  data.puzzles
                    ? data.puzzles.map((puzzle) => {
                        return html`
                          <div class="pm-PuzzleImagePicker-listItem">
                            ${puzzle.isRecent && !puzzle.isComplete
                              ? html`
                                  <pm-active-player-count
                                    class="pm-PuzzleImagePicker-activePlayerCount"
                                    puzzle-id=${puzzle.puzzleId}
                                  ></pm-active-player-count>
                                `
                              : html`
                                  <span
                                    class="pm-PuzzleImagePicker-activePlayerCount"
                                  ></span>
                                `}
                            <a
                              class=${classMap({
                                "pm-PuzzleImagePicker-puzzleLink": true,
                                isActive: puzzle.isActive,
                                isComplete: puzzle.isComplete,
                              })}
                              href=${`${data.frontFragmentHref}${
                                puzzle.puzzleId
                              }/`}
                            >
                              <div class="pm-PuzzleImagePicker-pieceCount">
                                <strong>${puzzle.pieces}</strong>
                                <small>Pieces</small>
                              </div>
                              <img
                                class="lazyload pm-PuzzleImagePicker-image"
                                width="160"
                                height="160"
                                data-src=${puzzle.src}
                                alt=""
                              />
                              <em class="pm-PuzzleImagePicker-status"
                                >${puzzle.statusText}</em
                              >
                            </a>

                            ${puzzle.licenseName === "unsplash"
                              ? html`
                                  <small>
                                    <a href=${puzzle.source}>${puzzle.title}</a>
                                    by
                                    <a
                                      xmlns:cc="http://creativecommons.org/ns#"
                                      href=${puzzle.authorLink}
                                      property="cc:attributionName"
                                      rel="cc:attributionURL"
                                      >${puzzle.authorName}</a
                                    >
                                    on
                                    <a href=${puzzle.licenseSource}
                                      >${puzzle.licenseTitle}</a
                                    >
                                  </small>
                                `
                              : html``}
                            ${puzzle.isAvailable
                              ? html`
                                  ${puzzle.timeSince
                                    ? html`
                                        <div
                                          class="pm-PuzzleImagePicker-timeSince"
                                        >
                                          <span
                                            class="pm-PuzzleImagePicker-timeSinceLabel"
                                          >
                                            Last active
                                          </span>
                                          <span
                                            class="pm-PuzzleImagePicker-timeSinceAmount"
                                            >${puzzle.timeSince}</span
                                          >
                                          <span
                                            class="pm-PuzzleImagePicker-timeSinceLabel"
                                          >
                                            ago
                                          </span>
                                        </div>
                                      `
                                    : ""}
                                `
                              : html`
                                  <div class="pm-PuzzleImagePicker-infoMessage">
                                    Puzzle currently not available
                                  </div>
                                `}
                            ${!puzzle.isOriginal
                              ? html`
                                  <small>
                                    Instance by
                                    <pm-player-bit
                                      player=${puzzle.owner}
                                    ></pm-player-bit>
                                  </small>
                                `
                              : ""}
                          </div>
                        `;
                      })
                    : html``
                }
              </div>
            </div>
          </div>
        </div>
      `;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
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
      //console.log("connectedCallback");
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      userDetailsService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
  }
);
