import { playerBitImgService, colorForPlayer } from "./player-bit-img.service";
import "./player-bit.css";

const tag = "pm-player-bit";

customElements.define(
  tag,
  class PmPlayerBit extends HTMLElement {
    private player: undefined | number;

    constructor() {
      super();
    }

    render() {
      if (this.player) {
        playerBitImgService
          .getPlayerBitForPlayer(this.player)
          .then((fragment) => {
            if (this.player && typeof this.player === "number") {
              fragment = fragment.replace(
                `[[${this.player.toString()}]]`,
                this.player.toString(36)
              );
              this.style.setProperty(
                "--pm-PlayerBit-color",
                colorForPlayer(this.player)
              );
              this.innerHTML = fragment;
            }
          });
      }
    }

    connectedCallback() {
      const player = this.attributes.getNamedItem("player");
      if (player && player.value) {
        this.player = parseInt(player.value);
        this.render();
      }
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      //userDetailsService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
    attributeChangedCallback(
      name: string,
      _oldValue: string | null,
      _newValue: string | null
    ) {
      if (name === "player") {
        if (_newValue) {
          this.player = parseInt(_newValue);
          this.render();
        }
      }
    }
  }
);
