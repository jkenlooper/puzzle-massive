import { html, render } from "lit-html";
import { classMap } from "lit-html/directives/class-map.js";
import userDetailsService from "../site/user-details.service";
import { PuzzleInstanceList } from "../site/user-details.service";
import "./player-puzzle-instance-list.css";

interface TemplateData {
  isReady: boolean;
  hasPuzzleSlots: boolean;
  puzzleInstanceList: PuzzleInstanceList;
  emptySlotCount: number;
  puzzleInstanceCount: number;
  playerPuzzleListHref: string;
}

const tag = "pm-player-puzzle-instance-list";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmPlayerPuzzleInstanceList extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    playerPuzzleListHref: string = "";

    isReady: boolean = false;
    puzzleInstanceList: PuzzleInstanceList = [];
    emptySlotCount = 0;
    puzzleInstanceCount = 0;

    constructor() {
      super();
      this.instanceId = PmPlayerPuzzleInstanceList._instanceId;

      // Set the attribute values
      const playerPuzzleListHrefAttr = this.attributes.getNamedItem(
        "player-puzzle-list-href"
      );
      if (!playerPuzzleListHrefAttr || !playerPuzzleListHrefAttr.value) {
        throw new Error("no player-puzzle-list-href attribute has been set");
      } else {
        this.playerPuzzleListHref = playerPuzzleListHrefAttr.value;
      }

      userDetailsService.subscribe(
        this._setPuzzleInstanceList.bind(this),
        this.instanceId
      );
    }

    _setPuzzleInstanceList() {
      this.emptySlotCount = userDetailsService.userDetails.emptySlotCount;
      this.puzzleInstanceCount =
        userDetailsService.userDetails.puzzleInstanceCount;
      if (
        userDetailsService.userDetails.puzzle_instance_list &&
        userDetailsService.userDetails.puzzle_instance_list.length
      ) {
        this.puzzleInstanceList =
          userDetailsService.userDetails.puzzle_instance_list;
      }
      this.isReady = true;
      this.render();
    }

    template(data: TemplateData) {
      if (!data.isReady) {
        return html``;
      }
      if (!data.hasPuzzleSlots) {
        return html``;
      }
      return html`
        <div class="pm-PlayerPuzzleInstanceList">
          <small class="u-block">Puzzle Instance Slots</small>
          <ul class="pm-PlayerPuzzleInstanceList-list">
            <li class="pm-PlayerPuzzleInstanceList-listItem">
              <a
                href=${data.playerPuzzleListHref}
                title=${puzzleInstancesAndSlotsText()}
                class=${classMap({
                  "pm-PlayerPuzzleInstanceList-available": true,
                  "pm-PlayerPuzzleInstanceList-available--overTen":
                    data.puzzleInstanceCount + data.emptySlotCount > 10,
                })}
              >
                <span class="pm-PlayerPuzzleInstanceList-availableCount"
                  >${data.puzzleInstanceCount}</span
                >
                <span class="pm-PlayerPuzzleInstanceList-availableCount"
                  >${data.puzzleInstanceCount + data.emptySlotCount}</span
                >
              </a>
            </li>
            ${data.puzzleInstanceList.map(
              (puzzleInstanceItem) => html`
                <li class="pm-PlayerPuzzleInstanceList-listItem">
                  <a
                    class="pm-PlayerPuzzleInstanceList-instanceLink"
                    href=${puzzleInstanceItem.front_url}
                    title="player puzzle instance"
                  >
                    ${!puzzleInstanceItem.src
                      ? html`
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            version="1.0"
                            width="50"
                            height="50"
                            viewBox="0 0 50 50"
                            class="pm-PlayerPuzzleInstanceList-imageUnknown"
                          >
                            <rect
                              x="0"
                              y="0"
                              width="50"
                              height="50"
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
                      : html`
                          <img
                            width="50"
                            height="50"
                            src=${puzzleInstanceItem.src}
                            alt=""
                          />
                        `}
                  </a>
                </li>
              `
            )}
          </ul>
        </div>
      `;

      function puzzleInstancesAndSlotsText(): string {
        if (data.puzzleInstanceCount > 0) {
          return `You own ${data.puzzleInstanceCount} puzzle ${pluralize(
            "instance",
            data.puzzleInstanceCount
          )} ${
            data.emptySlotCount > 0
              ? `and have ${data.emptySlotCount} empty ${pluralize(
                  "slot",
                  data.puzzleInstanceCount
                )}`
              : `and no empty slots`
          }`;
        } else {
          return `You have ${data.emptySlotCount} puzzle instance ${pluralize(
            "slot",
            data.emptySlotCount
          )}`;
        }
      }

      function pluralize(word: string, count: number) {
        if (count > 1) {
          return `${word}s`;
        } else {
          return word;
        }
      }
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        hasPuzzleSlots: !!(this.emptySlotCount + this.puzzleInstanceCount),
        puzzleInstanceList: this.puzzleInstanceList,
        emptySlotCount: this.emptySlotCount,
        puzzleInstanceCount: this.puzzleInstanceCount,
        playerPuzzleListHref: this.playerPuzzleListHref,
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    disconnectedCallback() {
      userDetailsService.unsubscribe(this.instanceId);
    }
  }
);
