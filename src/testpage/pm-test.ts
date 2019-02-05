import { LitElement, html, css, customElement, property } from "lit-element";

// This decorator defines the element.
@customElement("pm-test")
export class PmTest extends LitElement {
  // This decorator creates a property accessor that triggers rendering and
  // an observed attribute.
  @property()
  mood = "great";

  static styles = css`
    span {
      color: green;
    }
  `;

  // Render element DOM by returning a `lit-html` template.
  render() {
    return html`
      Web Components are <span>${this.mood}</span>!
    `;
  }
}
