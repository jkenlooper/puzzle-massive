import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";

import { getTimePassed } from "../site/utilities";
import {
  puzzleImagesService,
  PuzzleImageData,
  Status,
  PuzzleAvailableStatuses,
} from "../site/puzzle-images.service";
import "./puzzle-image-card.css";

interface TemplateData {
  src: string;
  puzzleId: string;
  pieces: number;
  queue: number;
  isActive: boolean;
  isRecent: boolean;
  isComplete: boolean;
  isAvailable: boolean;
  isNew: boolean;
  isFrozen: boolean;
  isOriginal: boolean;
  statusText: string;
  timeSince: string;
  secondsFromNow: null | number;
  owner: number;
  title: string;
  authorLink: string;
  authorName: string;
  source: string;
  licenseSource: string;
  licenseName: string;
  licenseTitle: string;
  hideOwner: boolean;
  frontFragmentHref: string;
}

const tag = "pm-puzzle-image-card";
customElements.define(
  tag,
  class PmPuzzleImageCard extends HTMLElement {
    private readonly puzzle: PuzzleImageData = {
      src: "",
      puzzle_id: "",
      status: 0,
      pieces: 0,
      queue: 0,
      is_active: 0,
      is_new: 0,
      is_recent: 0,
      is_original: 0,
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
    private frontFragmentHref: string = "";
    constructor() {
      super();
    }

    template(data: TemplateData) {
      return html`
        <div class="pm-PuzzleImageCard">
          ${data.isRecent && !data.isComplete
            ? html`
                <pm-active-player-count
                  class="pm-PuzzleImageCard-activePlayerCount"
                  puzzle-id=${data.puzzleId}
                ></pm-active-player-count>
              `
            : html`
                <span class="pm-PuzzleImageCard-activePlayerCount"></span>
              `}
          <a
            class=${classMap({
              "pm-PuzzleImageCard-puzzleLink": true,
              isActive: data.isActive,
              isRecent: data.isRecent,
              isComplete: data.isComplete,
              notAvailable: !data.isAvailable,
            })}
            href=${`${data.frontFragmentHref}${data.puzzleId}/`}
          >
            <div class="pm-PuzzleImageCard-pieceCount">
              <strong>${data.pieces}</strong>
              <small>Pieces</small>
            </div>
            <img
              class="lazyload pm-PuzzleImageCard-image"
              width="160"
              height="160"
              data-src=${data.src}
              alt=""
            />
            <em class="pm-PuzzleImageCard-status">${data.statusText}</em>
          </a>

          ${data.licenseName === "unsplash"
            ? html`
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
            : html``}
          ${data.isAvailable || data.isFrozen
            ? html`
                ${data.timeSince
                  ? html`
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
            : html`
                <div class="pm-PuzzleImageCard-infoMessage">
                  Currently not available
                </div>
              `}
          ${!data.isOriginal && !data.hideOwner
            ? html`
                <small>
                  Instance by
                  <pm-player-bit player=${data.owner}></pm-player-bit>
                </small>
              `
            : ""}
          q ${data.queue}
        </div>
      `;
    }

    get data(): TemplateData {
      return {
        src: this.puzzle.src,
        puzzleId: this.puzzle.puzzle_id,
        pieces: this.puzzle.pieces,
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

        isActive: !!this.puzzle.is_active,
        isRecent: !!this.puzzle.is_recent,
        isComplete: this.puzzle.status === Status.COMPLETED,
        isAvailable: PuzzleAvailableStatuses.includes(this.puzzle.status),
        isNew: !!this.puzzle.is_new,
        isFrozen: this.puzzle.status == Status.FROZEN,

        statusText: puzzleImagesService.statusToStatusText(
          this.puzzle.status,
          !!this.puzzle.is_recent,
          this.puzzle.seconds_from_now != null
        ),
        timeSince:
          this.puzzle.seconds_from_now != null
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
      this.render();
    }
  }
);
