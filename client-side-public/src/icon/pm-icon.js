const tag = "pm-icon";
export default class PmIcon extends HTMLElement {
    constructor() {
        super();
        this.iconName = this.textContent || "";
    }
    render() {
        const iconHref = `${THEME_STATIC_PATH_FOR_ICON_SVG}icons.svg#${this.iconName}`;
        this.innerHTML = `<svg class="pm-Icon" width="100%" height="100%" fit="" preserveAspectRatio="xMidYMid meet" focusable="false"><use xlink:href="${iconHref}"/></svg>`;
    }
    connectedCallback() {
        this.render();
    }
}
customElements.define(tag, PmIcon);
