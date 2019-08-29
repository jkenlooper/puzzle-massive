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

const StatusFilterItems = [
  {
    label: "Recent",
    value: "recent",
    id: "puzzle-image-picker-status--recent",
    checked: true,
  },
  {
    label: "Active",
    value: "active",
    id: "puzzle-image-picker-status--active",
    checked: true,
  },
  {
    label: "New", // TODO: Show status label for puzzles that have not been modified
    value: "new",
    id: "puzzle-image-picker-status--new",
    checked: false,
  },
  {
    label: "Complete",
    value: "complete",
    id: "puzzle-image-picker-status--complete",
    checked: false,
  },
  {
    label: "Unavailable",
    value: "unavailable",
    id: "puzzle-image-picker-status--unavailable",
    checked: false,
  },
];

const PieceCountFilterItems = [
  {
    label: "Less than 300",
    value: "0-300",
    id: "puzzle-image-picker-pieces--0",
    checked: false,
  },
  {
    label: "300 to 600",
    value: "300-600",
    id: "puzzle-image-picker-pieces--1",
    checked: true,
  },
  {
    label: "600 to 1000",
    value: "600-1000",
    id: "puzzle-image-picker-pieces--2",
    checked: false,
  },
  {
    label: "1000 to 2000",
    value: "1000-2000",
    id: "puzzle-image-picker-pieces--3",
    checked: false,
  },
  {
    label: "2000 to 3000",
    value: "2000-3000",
    id: "puzzle-image-picker-pieces--4",
    checked: false,
  },
  {
    label: "Greater than 3000",
    value: "3000-60000",
    id: "puzzle-image-picker-pieces--5",
    checked: false,
  },
];

const TypeFilterItems = [
  {
    label: "Originals",
    value: "original",
    id: "puzzle-image-picker-type--original",
    checked: true,
  },
  {
    label: "Instances",
    value: "instances",
    id: "puzzle-image-picker-type--instances",
    checked: true,
  },
];

const OrderByItems = [
  {
    label: "Modified date",
    value: "m_date",
    id: "puzzle-image-picker-orderby--m_date",
    checked: true,
  },
  {
    label: "Pieces",
    value: "pieces",
    id: "puzzle-image-picker-orderby--pieces",
    checked: false,
  },
];

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
            <strong>Filter puzzles</strong>

            <fieldset>
              <legend>Status</legend>
              ${StatusFilterItems.map((item) => {
                return html`
                  <div>
                    <input
                      type="checkbox"
                      name="status"
                      id=${item.id}
                      ?checked=${item.checked}
                      value=${item.value}
                    />
                    <label for=${item.id}>${item.label}</label>
                  </div>
                `;
              })}
            </fieldset>

            <fieldset>
              <legend>Piece count</legend>
              ${PieceCountFilterItems.map((item) => {
                return html`
                  <div>
                    <input
                      type="checkbox"
                      name="pieces"
                      id=${item.id}
                      ?checked=${item.checked}
                      value=${item.value}
                    />
                    <label for=${item.id}>${item.label}</label>
                  </div>
                `;
              })}
            </fieldset>

            <fieldset>
              <legend>Type</legend>
              ${TypeFilterItems.map((item) => {
                return html`
                  <div>
                    <input
                      type="checkbox"
                      name="type"
                      id=${item.id}
                      ?checked=${item.checked}
                      value=${item.value}
                    />
                    <label for=${item.id}>${item.label}</label>
                  </div>
                `;
              })}
            </fieldset>

            <fieldset>
              <legend>
                Order by
              </legend>
              ${OrderByItems.map((item) => {
                return html`
                  <div>
                    <input
                      type="radio"
                      name="orderby"
                      id=${item.id}
                      ?checked=${item.checked}
                      value=${item.value}
                    />
                    <label for=${item.id}>${item.label}</label>
                  </div>
                `;
              })}
            </fieldset>
          </div>

          ${data.puzzles && data.puzzles.length
            ? html`
                <div>
                  Found ${data.puzzles.length} puzzles<br />

                  <em>TODO: pagination</em><br />
                  Page 1 of 5

                  <div class="pm-PuzzleImagePicker-list" role="list">
                    ${data.puzzles.map((puzzle) => {
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
                              notAvailable: !puzzle.isAvailable,
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
                          ${puzzle.isAvailable || puzzle.isFrozen
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
                                  Currently not available
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
                    })}
                  </div>
                </div>
              `
            : html`
                <p>No puzzles found that match the criteria.</p>
              `}
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
