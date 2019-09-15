import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";

import {
  PuzzleListResponse,
  PuzzleImageData,
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
  puzzles: undefined | Array<PuzzleImageData>;
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
    puzzles: undefined | Array<PuzzleImageData> = undefined;
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
        .then((puzzleList: PuzzleListResponse) => {
          this.pageSize = puzzleList.pageSize;
          this.totalPuzzleCount = puzzleList.totalPuzzleCount;
          this.maxPieces = puzzleList.maxPieces;
          this.puzzles = puzzleList.puzzles;
          this.puzzleCountFiltered = puzzleList.puzzleCount;
          this.currentPage = puzzleList.currentPage;
          this.pageCount = Math.ceil(
            puzzleList.puzzleCount / puzzleList.pageSize
          );
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
          <div class="pm-PuzzleImagePicker-filter">
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
                labels="Original, Instance"
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
              ${!data.isLoadingPuzzles
                ? html`
                    <h2>
                      <small>Found </small
                      ><strong>${data.puzzleCountFiltered}</strong
                      ><small> of</small> ${data.totalPuzzleCount}<small>
                        puzzles</small
                      >
                    </h2>
                  `
                : ""}
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
                              <pm-puzzle-image-card
                                .puzzle=${puzzle}
                                front-fragment-href=${data.frontFragmentHref}
                              ></pm-puzzle-image-card>
                            `
                          )}
                        </div>
                      `
                    : html`
                        <p>No puzzles found that match the criteria.</p>
                      `}
                `}
          </div>
        </div>
      `;
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
      let hasChanged = false;
      switch (filterGroupItem.name) {
        case "status":
          hasChanged = getHasChanged(this.filterStatus);
          this.filterStatus = filterGroupItem.checked;
          break;
        case "pieces":
          hasChanged = getHasChanged(this.filterPieces);
          this.filterPieces = filterGroupItem.checked;
          break;
        case "type":
          hasChanged = getHasChanged(this.filterType);
          this.filterType = filterGroupItem.checked;
          break;
        case "pagination":
          hasChanged = getHasChanged(this.filterPage);
          this.filterPage = filterGroupItem.checked;
          break;
        case "orderby":
          hasChanged = getHasChanged(this.orderBy);
          this.orderBy = filterGroupItem.checked;
          break;
      }
      if (
        this.filterStatus &&
        this.filterPieces &&
        this.filterType &&
        this.filterPage &&
        this.orderBy &&
        hasChanged
      ) {
        setPuzzleImages();
      }
      function getHasChanged(item: Array<string> | undefined): boolean {
        const hasChanged = item
          ? item.toString() !== filterGroupItem.checked.toString()
          : true;
        return hasChanged;
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
