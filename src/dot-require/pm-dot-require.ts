/* global HTMLElement, customElements */

import "./dot-require.css";

/*
 * <pm-dot-require min="10" dots="2" type="hidden">
 * ...contents...
 * </pm-dot-require>
 */

const tag = "pm-dot-require";

const HIDDEN = "hidden";
const BLUR = "blur";
const INFO = "info";
const NONE = "none";

const dotRequireTypes = [HIDDEN, BLUR, INFO, NONE];

customElements.define(
  tag,
  class PmDotRequire extends HTMLElement {
    static get observedAttributes() {
      return ["dots"];
    }

    private dotsRequired: number; // Set from min attribute
    private wrapperEl: any;

    constructor() {
      super();
      const dotsRequired = this.attributes.getNamedItem("min");
      this.dotsRequired = dotsRequired ? parseInt(dotsRequired.value) : -1;

      const typeAttr = this.attributes.getNamedItem("type");
      const typeAttrValue = typeAttr ? typeAttr.value : NONE;
      const _type =
        dotRequireTypes.indexOf(typeAttrValue) != -1 ? typeAttrValue : NONE;

      // Wrap contents with styled div
      this.wrapperEl = document.createElement("div");
      if (this.hasChildNodes()) {
        while (this.firstChild) {
          this.wrapperEl.appendChild(this.removeChild(this.firstChild));
        }
      }
      this.appendChild(this.wrapperEl);
      this.wrapperEl.classList.add(`pm-DotRequire--${_type}`);
      this.wrapperEl.classList.add("pm-DotRequire");
    }

    attributeChangedCallback(
      name: string,
      _oldValue: string | null,
      _newValue: string | null
    ) {
      if (name === "dots") {
        if (_newValue && !isNaN(parseInt(_newValue))) {
          // Toggle the is-dotted class
          this.wrapperEl.classList.toggle(
            "is-dotted",
            parseInt(_newValue) < this.dotsRequired
          );
        }
      }
    }
  }
);
