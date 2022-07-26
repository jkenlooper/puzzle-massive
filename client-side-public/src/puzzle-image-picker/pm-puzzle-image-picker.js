import { html, render } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { repeat } from "lit/directives/repeat.js";
import { puzzleImagesService } from "../site/puzzle-images.service";
import "./puzzle-image-picker.css";
// Set a minimum delay to prevent getting a too many requests error (429).  The
// puzzle-list endpoint is rate-limited per ip at one request every 2 seconds
// with a burst/bucket of 20. The burst here is set to half of that limit and is
// used to limit requests on the client side without triggering the rate limit.
const minDelay = 2000; // web/legacy-cache--up.nginx.conf: puzzle_list_limit_per_ip
const burst = 10; // web/legacy-cache--up.nginx.conf: puzzle_list_limit_per_ip
const tag = "pm-puzzle-image-picker";
let lastInstanceId = 0;
customElements.define(
  tag,
  class PmPuzzleImagePicker extends HTMLElement {
    constructor() {
      super();
      this.pageSize = 0;
      this.puzzles = undefined;
      this.currentPage = 1;
      this.pageCount = 1;
      this.totalPuzzleCount = 0;
      this.maxPieces = 0;
      this.hasError = false;
      this.errorMessage = "";
      this.isLoadingPuzzles = false;
      this.burstCount = 0;
      this.piecesCountList = [];
      this.filterPage = ["1"];
      this.puzzleCountFiltered = 0;
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
      const piecesCountListAttr =
        this.attributes.getNamedItem("pieces-count-list");
      if (!piecesCountListAttr || !piecesCountListAttr.value) {
        this.hasError = true;
        this.errorMessage = "Missing pieces-count-list attribute";
      } else {
        this.piecesCountList = piecesCountListAttr.value
          .split(/\s+/)
          .map((v) => {
            return parseInt(v);
          });
      }
      this.addEventListener(
        "filterGroupItemValueChange",
        this._onFilterGroupItemValueChange.bind(this)
      );
    }
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }
    _setPuzzleImages() {
      this.isLoadingPuzzles = true;
      this.render();
      const page =
        !this.filterPage || !Array.isArray(this.filterPage)
          ? 1
          : parseInt(this.filterPage[0]);
      let minmax = {};
      if (this.filterPieces) {
        minmax = this.filterPieces
          .map((item) => {
            const piecesCount = parseInt(item);
            return isNaN(piecesCount) ? 0 : piecesCount;
          })
          .reduce((acc, pieceCount) => {
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
          }, {});
      }
      const piecesMin = minmax.min || 0;
      const piecesMax = minmax.max || 0;
      const orderby =
        this.orderBy && this.orderBy.length ? this.orderBy[0] : "m_date";
      if (piecesMin === piecesMax) {
        return new Promise((resolve) => {
          this.isLoadingPuzzles = false;
          this.render();
          resolve();
        });
      }
      this.burstCount++;
      const timeStart = new Date();
      return puzzleImagesService
        .getPuzzleImages(
          this.filterStatus || [],
          this.filterType || [],
          piecesMin,
          piecesMax,
          page,
          orderby
        )
        .then((puzzleList) => {
          this.pageSize = puzzleList.pageSize;
          this.totalPuzzleCount = puzzleList.totalPuzzleCount;
          this.maxPieces = puzzleList.maxPieces;
          this.puzzles = puzzleList.puzzles;
          this.puzzleCountFiltered = puzzleList.puzzleCount;
          this.currentPage = puzzleList.currentPage;
          this.pageCount = Math.ceil(
            puzzleList.puzzleCount / puzzleList.pageSize
          );
          this.render();
          return true;
        })
        .then(() => {
          const timeEnd = new Date();
          const timePassed = timeEnd.getTime() - timeStart.getTime();
          const delay = Math.max(minDelay - timePassed, 0);
          window.setTimeout(() => this.burstCount--, delay * this.burstCount);
          return new Promise((resolve) => {
            if (this.burstCount >= burst && delay > 0) {
              window.setTimeout(() => {
                resolve();
              }, delay);
            } else {
              resolve();
            }
          });
        })
        .catch((err) => {
          console.error(err);
          this.hasError = true;
          this.errorMessage = err || "Error getting the puzzle images.";
        })
        .finally(() => {
          this.isLoadingPuzzles = false;
          this.render();
        });
    }
    template(data) {
      if (data.hasError) {
        return html` ${data.errorMessage} `;
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
                ?disabled=${data.isLoadingPuzzles}
                labels="Recent, Active, Queue, Complete, Frozen, Unavailable"
                values="*recent, *active, in_queue, complete, frozen, unavailable"
              ></pm-filter-group>

              <pm-filter-group
                class="pm-PuzzleImagePicker-filterGroup"
                name="type"
                legend="Type"
                type="checkbox"
                ?disabled=${data.isLoadingPuzzles}
                labels="Original, Instance"
                values="*original, instance"
              ></pm-filter-group>

              <pm-filter-group
                class="pm-PuzzleImagePicker-filterGroup"
                name="pieces"
                legend="Piece count"
                type="interval"
                ?disabled=${data.isLoadingPuzzles}
                values=${data.pieces}
              ></pm-filter-group>

              <hr />
              <h2>
                <small>Found </small><strong>${data.puzzleCountFiltered}</strong
                ><small> of</small> ${data.totalPuzzleCount}<small>
                  puzzles</small
                >
              </h2>
              <pm-filter-group
                class="pm-PuzzleImagePicker-filterGroup"
                name="orderby"
                legend="Order by"
                type="radio"
                ?disabled=${data.isLoadingPuzzles}
                labels="Modified date, Piece count, Queue"
                values="*m_date, pieces, queue"
              ></pm-filter-group>

              <pm-filter-group
                class=${classMap({
                  "pm-PuzzleImagePicker-filterGroup": true,
                  "u-hidden": !data.hasPagination,
                })}
                name="pagination"
                legend=${data.paginationLegend}
                type="pagination"
                ?disabled=${data.isLoadingPuzzles}
                values=${data.pages}
              ></pm-filter-group>
            </div>

            ${data.puzzles && data.puzzles.length
              ? html`
                  <div class="pm-PuzzleList pm-PuzzleList--card" role="list">
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
              : html` <p>No puzzles found that match the criteria.</p> `}
          </div>
        </div>
      `;
    }
    get data() {
      return {
        isLoadingPuzzles: this.isLoadingPuzzles,
        hasError: this.hasError,
        errorMessage: this.errorMessage,
        puzzles: this.puzzles,
        hasPagination: this.puzzleCountFiltered > this.pageSize,
        paginationLegend: `Page ${this.currentPage} of ${this.pageCount}`,
        pages: getPagesString(this.pageCount),
        currentPage: this.currentPage,
        totalPuzzleCount: this.totalPuzzleCount,
        pieces: getPiecesString(this.maxPieces || 1000, this.piecesCountList),
        puzzleCountFiltered: this.puzzleCountFiltered,
        frontFragmentHref: this.frontFragmentHref,
      };
    }
    render() {
      render(this.template(this.data), this);
    }
    _onFilterGroupItemValueChange(ev) {
      const setPuzzleImages = this._setPuzzleImages.bind(this);
      const filterGroupItem = ev.detail;
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
      function getHasChanged(item) {
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
function getPagesString(pageCount) {
  let count = 1;
  const pages = [];
  while (count <= pageCount) {
    pages.push(count);
    count += 1;
  }
  return `*${pages.join(", ")}`;
}
function getPiecesString(maxPieces, piecesCountList) {
  const pieces = piecesCountList.filter((item) => {
    return item <= maxPieces;
  });
  if (pieces.length < piecesCountList.length) {
    // add the next pieces value from piecesCountList
    pieces.push(
      piecesCountList[piecesCountList.indexOf(pieces[pieces.length - 1]) + 1]
    );
  }
  const piecesWithDefault = pieces.map((item) => {
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
