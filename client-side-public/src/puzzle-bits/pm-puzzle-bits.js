import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";
import { classMap } from "lit-html/directives/class-map.js";
import { styleMap } from "lit-html/directives/style-map.js";
import { rgbToHsl } from "../site/utilities";
import { puzzleBitsService } from "./puzzle-bits.service";
import hashColorService from "../hash-color/hash-color.service";
import "./puzzle-bits.css";
const tag = "pm-puzzle-bits";
let lastInstanceId = 0;
customElements.define(tag, class PmPuzzleBits extends HTMLElement {
    constructor() {
        super();
        this.instanceId = PmPuzzleBits._instanceId;
        const bgColorAttr = this.attributes.getNamedItem("bg-color");
        this.fgcolor = bgColorAttr ? bgColorAttr.value : "#000000";
        this.showOtherPlayerBits = !!this.attributes.getNamedItem("show-other-players");
        const bitActiveTimeoutAttr = this.attributes.getNamedItem("bit-active-timeout");
        const bitActiveTimeout = bitActiveTimeoutAttr
            ? parseInt(bitActiveTimeoutAttr.value)
            : 5;
        puzzleBitsService.setBitActiveTimeout(bitActiveTimeout);
        const recentTimeoutAttr = this.attributes.getNamedItem("recent-timeout");
        const recentTimeout = recentTimeoutAttr
            ? parseInt(recentTimeoutAttr.value)
            : 60;
        puzzleBitsService.setBitRecentTimeout(recentTimeout);
        this.updateColor();
        puzzleBitsService.subscribe(this.render.bind(this), this.instanceId);
        hashColorService.subscribe(this.updateColor.bind(this), this.instanceId);
    }
    static get _instanceId() {
        return `${tag} ${lastInstanceId++}`;
    }
    template(data) {
        return html `
        <div
          class="pm-PuzzleBits"
          role="list"
          style=${styleMap({
            color: data.fgcolor,
        })}
        >
          ${bits()}
        </div>
      `;
        function bits() {
            return html `
          ${repeat(data.collection, (bit) => bit.id, // Key fn
            (bit) => {
                if (!data.showOtherPlayerBits && !bit.ownBit) {
                    return "";
                }
                return html `
                <div
                  style=${styleMap({
                    transform: `translate(${bit.x}px, ${bit.y}px)`,
                })}
                  class=${classMap({
                    "pm-PuzzleBits-bit": true,
                    "is-active": bit.active,
                    "is-recent": bit.recent,
                    "pm-PuzzleBits-bit--ownBit": bit.ownBit,
                })}
                  role="listitem"
                >
                  <pm-player-bit player=${bit.id}></pm-player-bit>
                </div>
              `;
            })}
        `;
        }
    }
    updateColor() {
        const hash = hashColorService.backgroundColor || this.fgcolor; /*(this.name)*/
        const hashRGBColorRe = /#([a-f0-9]{2})([a-f0-9]{2})([a-f0-9]{2})/i;
        if (!hash) {
            return;
        }
        let RGBmatch = hash.match(hashRGBColorRe);
        if (RGBmatch) {
            let hsl = rgbToHsl(RGBmatch[1], RGBmatch[2], RGBmatch[3]);
            //this.$container.style.backgroundColor = `hsla(${hsl[0]},${hsl[1]}%,${hsl[2]}%,1)`;
            // let hue = hsl[0]
            // let sat = hsl[1]
            let light = hsl[2];
            /*
            let opposingHSL = [
              hue > 180 ? hue - 180 : hue + 180,
              100 - sat,
              100 - light
            ]
            */
            let contrast = light > 50 ? 0 : 100;
            this.fgcolor = `hsla(0,0%,${contrast}%,0.8)`;
        }
        this.render();
    }
    get data() {
        return {
            collection: puzzleBitsService.collection,
            fgcolor: this.fgcolor,
            showOtherPlayerBits: this.showOtherPlayerBits,
        };
    }
    render() {
        render(this.template(this.data), this);
    }
});
