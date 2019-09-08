import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import { repeat } from "lit-html/directives/repeat";

import {
  PuzzleList,
  PuzzleImages,
  puzzleImagesService,
} from "./puzzle-images.service";

import "./puzzle-image-picker.css";

interface FilterGroupItem {
  name: string;
  checked: Array<string>;
}

interface TemplateData {
  errorMessage?: string;
  hasError: boolean;
  isLoadingPuzzles: boolean;
  puzzles: undefined | PuzzleImages;
  hasPagination: boolean;
  paginationLegend: string;
  pages: string;
  pieces: string;
  currentPage: number;
  totalPuzzleCount: number;
  puzzleCountFiltered: number;
  frontFragmentHref: undefined | string;
}

const piecesCountList = [
  0,
  50,
  100,
  200,
  300,
  450,
  600,
  800,
  1000,
  1500,
  2000,
  2500,
  3000,
  4000,
  5000,
  6000,
  7000,
  8000,
  9000,
  10000,
  15000,
  20000,
  30000,
  40000,
  50000,
  60000,
];

const tag = "pm-puzzle-image-picker";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPuzzleImagePicker extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private pageSize: number = 0;
    frontFragmentHref: undefined | string;
    puzzles: undefined | PuzzleImages = undefined;
    currentPage: number = 1;
    pageCount: number = 1;
    totalPuzzleCount: number = 0;
    maxPieces: number = 0;
    hasError: boolean = false;
    errorMessage: string = "";
    isLoadingPuzzles: boolean = true;

    filterStatus: undefined | Array<string>;
    filterPieces: undefined | Array<string>;
    filterType: undefined | Array<string>;
    filterPage: Array<string> = ["1"];
    orderBy: undefined | Array<string>;
    puzzleCountFiltered: number = 0;

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

      this.addEventListener(
        "filterGroupItemValueChange",
        this._onFilterGroupItemValueChange.bind(this)
      );
    }

    _setPuzzleImages() {
      const page =
        !this.filterPage || !Array.isArray(this.filterPage)
          ? 1
          : parseInt(this.filterPage[0]);

      interface MinMax {
        min?: undefined | number;
        max?: undefined | number;
      }
      let minmax: MinMax = {};
      if (this.filterPieces) {
        minmax = this.filterPieces
          .map((item) => {
            const piecesCount = parseInt(item);
            return isNaN(piecesCount) ? 0 : piecesCount;
          })
          .reduce(
            (acc, pieceCount) => {
              if (acc.min === undefined) {
                acc.min = pieceCount;
              } else {
                acc.min = Math.min(pieceCount, acc.min);
              }
              if (acc.max === undefined) {
                acc.max = pieceCount;
              } else {
                acc.max = Math.max(pieceCount, acc.max);
              }
              return acc;
            },
            <MinMax>{}
          );
      }
      const piecesMin = minmax.min || 0;
      const piecesMax = minmax.max || 0;

      const orderby: string =
        this.orderBy && this.orderBy.length ? this.orderBy[0] : "m_date";

      return puzzleImagesService
        .getPuzzleImages(
          this.filterStatus || [],
          this.filterType || [],
          piecesMin,
          piecesMax,
          page,
          orderby
        )
        .then((puzzleList: PuzzleList) => {
          this.pageSize = puzzleList.pageSize;
          this.totalPuzzleCount = puzzleList.totalPuzzleCount;
          this.maxPieces = puzzleList.maxPieces;
          const puzzles = puzzleList.puzzles;
          this.puzzleCountFiltered = puzzleList.puzzleCount;

          this.puzzles = puzzles;
          this.currentPage = puzzleList.currentPage;
          const newPageCount = Math.ceil(
            puzzleList.puzzleCount / puzzleList.pageSize
          );

          if (this.pageCount !== newPageCount) {
          }

          this.pageCount = newPageCount;
        })
        .catch(() => {
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
          <div class="pm-PuzzleImagePicker-filter">
            ${!data.isLoadingPuzzles
              ? html`
                  <strong
                    >Found ${data.puzzleCountFiltered} of
                    ${data.totalPuzzleCount} puzzles</strong
                  >
                `
              : ""}

            <div class="pm-PuzzleImagePicker-filterGroups">
              <pm-filter-group
                class="pm-PuzzleImagePicker-filterGroup"
                name="status"
                legend="Status"
                type="checkbox"
                labels="Recent, Active, New, Complete, Frozen, Unavailable"
                values="*recent, *active, new, complete, frozen, unavailable"
              ></pm-filter-group>

              <pm-filter-group
                class="pm-PuzzleImagePicker-filterGroup"
                name="type"
                legend="Type"
                type="checkbox"
                labels="Original, Other players"
                values="*original, instance"
              ></pm-filter-group>

              <pm-filter-group
                class="pm-PuzzleImagePicker-filterGroup"
                name="pieces"
                legend="Piece count"
                type="interval"
                values=${data.pieces}
              ></pm-filter-group>

              <hr />
              <pm-filter-group
                class="pm-PuzzleImagePicker-filterGroup"
                name="orderby"
                legend="Order by"
                type="radio"
                labels="Modified date, Piece count"
                values="*m_date, pieces"
              ></pm-filter-group>

              ${data.hasPagination
                ? html`
                    <pm-filter-group
                      class="pm-PuzzleImagePicker-filterGroup"
                      name="pagination"
                      legend=${data.paginationLegend}
                      type="radio"
                      values=${data.pages}
                    ></pm-filter-group>
                  `
                : ""}
            </div>

            ${data.isLoadingPuzzles
              ? html`
                  Loading puzzles...
                `
              : html`
                  ${data.puzzles && data.puzzles.length
                    ? html`
                        <div>
                          <div class="pm-PuzzleImagePicker-list" role="list">
                            ${repeat(
                              data.puzzles,
                              (puzzle) => puzzle.puzzleId,
                              (puzzle) => {
                                return listItem(puzzle);
                              }
                            )}
                          </div>
                        </div>
                      `
                    : html`
                        <p>No puzzles found that match the criteria.</p>
                      `}
                `}
          </div>
        </div>
      `;

      function listItem(puzzle) {
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
                  <span class="pm-PuzzleImagePicker-activePlayerCount"></span>
                `}
            <a
              class=${classMap({
                "pm-PuzzleImagePicker-puzzleLink": true,
                isActive: puzzle.isActive,
                isRecent: puzzle.isRecent,
                isComplete: puzzle.isComplete,
                notAvailable: !puzzle.isAvailable,
              })}
              href=${`${data.frontFragmentHref}${puzzle.puzzleId}/`}
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
              <em class="pm-PuzzleImagePicker-status">${puzzle.statusText}</em>
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
                    <a href=${puzzle.licenseSource}>${puzzle.licenseTitle}</a>
                  </small>
                `
              : html``}
            ${puzzle.isAvailable || puzzle.isFrozen
              ? html`
                  ${puzzle.timeSince
                    ? html`
                        <div class="pm-PuzzleImagePicker-timeSince">
                          <span class="pm-PuzzleImagePicker-timeSinceLabel">
                            Last active
                          </span>
                          <span class="pm-PuzzleImagePicker-timeSinceAmount"
                            >${puzzle.timeSince}</span
                          >
                          <span class="pm-PuzzleImagePicker-timeSinceLabel">
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
                    <pm-player-bit player=${puzzle.owner}></pm-player-bit>
                  </small>
                `
              : ""}
          </div>
        `;
      }
    }

    get data(): TemplateData {
      return {
        isLoadingPuzzles: this.isLoadingPuzzles,
        hasError: this.hasError,
        errorMessage: this.errorMessage,
        puzzles: this.puzzles,
        hasPagination: this.puzzleCountFiltered > this.pageSize,
        paginationLegend: `${this.pageSize} Per Page`,
        pages: getPagesString(this.pageCount),
        currentPage: this.currentPage,
        totalPuzzleCount: this.totalPuzzleCount,
        pieces: getPiecesString(this.maxPieces),
        puzzleCountFiltered: this.puzzleCountFiltered,
        frontFragmentHref: this.frontFragmentHref,
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    _onFilterGroupItemValueChange(ev) {
      const setPuzzleImages = this._setPuzzleImages.bind(this);
      const filterGroupItem = <FilterGroupItem>ev.detail;
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
        case "pagination":
          this.filterPage = filterGroupItem.checked;
          break;
        case "orderby":
          this.orderBy = filterGroupItem.checked;
          break;
      }
      if (
        this.filterStatus &&
        this.filterPieces &&
        this.filterType &&
        this.filterPage &&
        this.orderBy
      ) {
        setPuzzleImages();
      }
    }

    connectedCallback() {
      this.render();
    }
    disconnectedCallback() {}
    adoptedCallback() {}
  }
);

function getPagesString(pageCount: number): string {
  let count = 1;
  const pages: Array<number> = [];
  while (count <= pageCount) {
    pages.push(count);
    count += 1;
  }

  return `*${pages.join(", ")}`;
}

function getPiecesString(maxPieces: number): string {
  const pieces: Array<number> = piecesCountList.filter((item) => {
    return item <= maxPieces;
  });
  if (pieces.length < piecesCountList.length) {
    // add the next pieces value from piecesCountList
    pieces.push(
      piecesCountList[piecesCountList.indexOf(pieces[pieces.length - 1]) + 1]
    );
  }
  const piecesWithDefault: Array<string> = pieces.map((item) => {
    return item.toString();
  });
  // Mark the first and last as default checked
  if (piecesWithDefault.length) {
    piecesWithDefault[0] = `*${piecesWithDefault[0]}`;
    piecesWithDefault[piecesWithDefault.length - 1] = `*${
      piecesWithDefault[piecesWithDefault.length - 1]
    }`;
  }
  return piecesWithDefault.join(", ");
}
