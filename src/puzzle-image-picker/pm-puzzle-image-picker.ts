import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";

import filterGroupService from "./filter-group.service";
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

    //filtersInitialized: undefined | Promise<boolean>;
    filterStatus: undefined | Array<string>;
    filterPieces: undefined | Array<string>;
    filterType: undefined | Array<string>;
    orderBy: undefined | string;

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
    }

    _setPuzzleImages() {
      //const filterPuzzleImages = _filterPuzzleImages.bind(this);
      console.log(
        "_filterPuzzleImages",
        this,
        this.filterStatus,
        this.filterPieces,
        this.filterType,
        this.orderBy
      );
      return puzzleImagesService
        .getPuzzleImages()
        .then((puzzleImages: PuzzleImages) => {
          this.puzzles = puzzleImages.filter((puzzle) => {
            if (Array.isArray(this.filterStatus)) {
              return this.filterStatus.some((status) => {
                let accept = false;
                switch (status) {
                  case "recent":
                    accept = puzzle.isRecent;
                    break;
                  case "active":
                    accept = puzzle.isActive;
                    break;
                  case "new":
                    accept = puzzle.isNew;
                    break;
                  case "complete":
                    accept = puzzle.isComplete;
                    break;
                  case "frozen":
                    accept = puzzle.isFrozen;
                    break;
                  case "unavailable":
                    accept = !puzzle.isAvailable && !puzzle.isFrozen;
                    break;
                }
                return accept;
              });
            }
            console.warn("filterStatus is not an array; ignoring");
            return true;
          });
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

            <pm-filter-group
              name="status"
              legend="Status"
              type="checkbox"
              labels="Recent, Active, New, Complete, Frozen, Unavailable"
              values="recent, active, new, complete, frozen, unavailable"
            ></pm-filter-group>

            <pm-filter-group
              name="pieces"
              legend="Piece count"
              type="checkbox"
              labels="Less than 300, 300 to 600, 600 to 1000, 1000 to 2000, 2000 to 3000, Greater than 3000"
              values="0-300, 300-600, 600-1000, 1000-2000, 2000-3000, 3000-60000"
            ></pm-filter-group>

            <pm-filter-group
              name="type"
              legend="Type"
              type="checkbox"
              labels="Originals, Instances"
              values="original, instances"
            ></pm-filter-group>

            <pm-filter-group
              name="orderby"
              legend="Order by"
              type="radio"
              labels="Modified date, Pieces"
              values="m_date, pieces"
            ></pm-filter-group>
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
      const setPuzzleImages = this._setPuzzleImages.bind(this);

      const replay = true;
      filterGroupService.subscribe(
        (filterGroupItem) => {
          switch (filterGroupItem.name) {
            case "status":
              this.filterStatus = filterGroupItem.checked;
              break;
            case "pieces":
              this.filterPieces = filterGroupItem.checked;
              break;
            case "type":
              this.filterType = filterGroupItem.checked;
              break;
          }
          if (this.filterStatus && this.filterPieces && this.filterType) {
            setPuzzleImages();
          }
        },
        this.instanceId,
        replay
      );
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      filterGroupService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
  }
);
