/* global HTMLElement, customElements */

import userDetailsService from "../site/user-details.service";
import "./dot-require.css";

/*
 * <pm-dot-require min="10" type="hidden">
 * ...contents...
 * </pm-dot-require>
 */

const tag = "pm-dot-require";

const HIDDEN = "hidden";
const BLUR = "blur";
const INFO = "info";
const NONE = "none";

const dotRequireTypes = [HIDDEN, BLUR, INFO, NONE];
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmDotRequire extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    private dotsRequired: number; // Set from min attribute
    private wrapperEl: any;

    constructor() {
      super();
      this.instanceId = PmDotRequire._instanceId;
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

      userDetailsService.subscribe(
        this.updateIsDottedClass.bind(this),
        this.instanceId
      );
    }

    updateIsDottedClass() {
      this.wrapperEl.classList.toggle(
        "is-dotted",
        userDetailsService.userDetails.dots < this.dotsRequired
      );
    }
  }
);
