import { html, render } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { getTimePassed } from "../site/utilities";
import { puzzleImagesService, Status, PuzzleAvailableStatuses, } from "../site/puzzle-images.service";
import "./puzzle-image-card.css";
const tag = "pm-puzzle-image-card";
customElements.define(tag, class PmPuzzleImageCard extends HTMLElement {
    constructor() {
        super();
        this.puzzle = {
            src: "",
            puzzle_id: "",
            status: 0,
            pieces: 0,
            permission: 0,
            queue: 0,
            is_active: 0,
            is_new: 0,
            is_recent: 0,
            is_original: 0,
            is_in_puzzle_instance_slot: 0,
            seconds_from_now: null,
            owner: 0,
            title: "",
            author_link: "",
            author_name: "",
            source: "",
            license_source: "",
            license_name: "",
            license_title: "",
        };
        this.frontFragmentHref = "";
        this.variant = "card";
    }
    template(data) {
        if (data.variant === "inline") {
            return inlineView();
        }
        else {
            return cardView();
        }
        function inlineView() {
            return html `
          <div class="pm-PuzzleImageCard pm-PuzzleImageCard--inline">
            <a
              class=${classMap({
                "pm-PuzzleImageCard-puzzleLink": true,
                isActive: data.isActive,
                isRecent: data.isRecent,
                isComplete: data.isComplete,
                isQueue: data.isQueue,
                notAvailable: !data.isAvailable,
            })}
              href=${`${data.frontFragmentHref}${data.puzzleId}/`}
            >
              <span class="u-intrinsicRatio1:1">
                ${!data.src
                ? html `
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        version="1.0"
                        width="160"
                        height="160"
                        viewBox="0 0 160 160"
                        class="pm-PuzzleImageCard-imageUnknown"
                      >
                        <rect
                          x="0"
                          y="0"
                          width="160"
                          height="160"
                          fill="#000"
                        />
                        <text
                          x="50%"
                          y="50%"
                          dominate-baseline="middle"
                          text-anchor="middle"
                          fill="#fff"
                        >
                          ?
                        </text>
                      </svg>
                    `
                : html `
                      <img
                        class="lazyload pm-PuzzleImageCard-image"
                        width="160"
                        height="160"
                        data-src=${data.src}
                        alt=""
                      />
                    `}
              </span>
              <small class="pm-PuzzleImageCard-pieceCount">
                ${data.pieces}
              </small>
              ${data.isRecent && !data.isComplete
                ? html `
                    <pm-active-player-count
                      class="pm-PuzzleImageCard-activePlayerCount"
                      puzzle-id=${data.puzzleId}
                    ></pm-active-player-count>
                  `
                : html ``}
            </a>
          </div>
        `;
        }
        function cardView() {
            return html `
          <div class="pm-PuzzleImageCard pm-PuzzleImageCard--card">
            ${data.isRecent && !data.isComplete
                ? html `
                  <pm-active-player-count
                    class="pm-PuzzleImageCard-activePlayerCount"
                    puzzle-id=${data.puzzleId}
                  ></pm-active-player-count>
                `
                : html `
                  <span class="pm-PuzzleImageCard-activePlayerCount"></span>
                `}
            <a
              class=${classMap({
                "pm-PuzzleImageCard-puzzleLink": true,
                isActive: data.isActive,
                isRecent: data.isRecent,
                isComplete: data.isComplete,
                isQueue: data.isQueue,
                notAvailable: !data.isAvailable,
            })}
              href=${`${data.frontFragmentHref}${data.puzzleId}/`}
            >
              <div class="pm-PuzzleImageCard-pieceCount">
                <strong>${data.pieces}</strong>
                <small>Pieces</small>
              </div>
              ${!data.src
                ? html `
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      version="1.0"
                      width="160"
                      height="160"
                      viewBox="0 0 160 160"
                      class="pm-PuzzleImageCard-imageUnknown"
                    >
                      <rect x="0" y="0" width="160" height="160" fill="#000" />
                      <text
                        x="50%"
                        y="50%"
                        dominate-baseline="middle"
                        text-anchor="middle"
                        fill="#fff"
                      >
                        ?
                      </text>
                    </svg>
                  `
                : html `
                    <img
                      class="lazyload pm-PuzzleImageCard-image"
                      width="160"
                      height="160"
                      data-src=${data.src}
                      alt=""
                    />
                  `}
              <em class="pm-PuzzleImageCard-status">${data.statusText}</em>
            </a>

            ${data.licenseName === "unsplash"
                ? html `
                  <small>
                    <a href=${data.source}>${data.title}</a>
                    by
                    <a
                      xmlns:cc="http://creativecommons.org/ns#"
                      href=${data.authorLink}
                      property="cc:attributionName"
                      rel="cc:attributionURL"
                      >${data.authorName}</a
                    >
                    on
                    <a href=${data.licenseSource}>${data.licenseTitle}</a>
                  </small>
                `
                : html ``}
            ${data.isAvailable || data.isFrozen || data.isQueue
                ? html `
                  ${data.timeSince
                    ? html `
                        <div class="pm-PuzzleImageCard-timeSince">
                          <span class="pm-PuzzleImageCard-timeSinceLabel">
                            Last active
                          </span>
                          <span class="pm-PuzzleImageCard-timeSinceAmount"
                            >${data.timeSince}</span
                          >
                          <span class="pm-PuzzleImageCard-timeSinceLabel">
                            ago
                          </span>
                        </div>
                      `
                    : ""}
                `
                : html `
                  <div class="pm-PuzzleImageCard-infoMessage">
                    Currently not available
                  </div>
                `}
            ${!data.isOriginal && !data.hideOwner
                ? html `
                  <small>
                    Instance by
                    <pm-player-bit player=${data.owner}></pm-player-bit>
                  </small>
                `
                : ""}
            ${data.isPrivate
                ? html `<span
                  class="pm-PuzzleImageCard-oneWordAttr pm-PuzzleImageCard-oneWordAttr--unlisted"
                  >Unlisted</span
                >`
                : ""}
            ${data.isPlayerPuzzleInstance
                ? html `<span
                  class="pm-PuzzleImageCard-oneWordAttr pm-PuzzleImageCard-oneWordAttr--instance"
                  >Instance</span
                >`
                : ""}
          </div>
        `;
        }
    }
    get data() {
        return {
            src: this.puzzle.src,
            puzzleId: this.puzzle.puzzle_id,
            pieces: this.puzzle.pieces,
            isPrivate: this.puzzle.permission === -1,
            isPlayerPuzzleInstance: this.puzzle.is_in_puzzle_instance_slot === 1,
            queue: this.puzzle.queue,
            isOriginal: !!this.puzzle.is_original,
            owner: this.puzzle.owner,
            hideOwner: this.getAttribute("hide-owner") !== null,
            title: this.puzzle.title,
            authorLink: this.puzzle.author_link,
            authorName: this.puzzle.author_name,
            source: this.puzzle.source,
            licenseSource: this.puzzle.license_source,
            licenseName: this.puzzle.license_name,
            licenseTitle: this.puzzle.license_title,
            frontFragmentHref: this.frontFragmentHref,
            variant: this.variant,
            isActive: !!this.puzzle.is_active,
            isRecent: !!this.puzzle.is_recent,
            isComplete: this.puzzle.status === Status.COMPLETED,
            isQueue: this.puzzle.status === Status.IN_QUEUE && !!this.puzzle.is_original,
            isAvailable: PuzzleAvailableStatuses.includes(this.puzzle.status),
            isNew: !!this.puzzle.is_new,
            isFrozen: this.puzzle.status == Status.FROZEN,
            statusText: puzzleImagesService.statusToStatusText(this.puzzle.status, !!this.puzzle.is_recent, this.puzzle.seconds_from_now != null),
            timeSince: this.puzzle.seconds_from_now != null
                ? getTimePassed(this.puzzle.seconds_from_now)
                : "",
            secondsFromNow: this.puzzle.seconds_from_now,
        };
    }
    render() {
        render(this.template(this.data), this);
    }
    connectedCallback() {
        this.frontFragmentHref = this.getAttribute("front-fragment-href") || "";
        this.variant = this.getAttribute("variant") || this.variant;
        this.render();
    }
});
