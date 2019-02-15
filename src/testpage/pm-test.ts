import { LitElement, html, css, customElement, property } from "lit-element";
import "./pm-test.css";

// This decorator defines the element.
@customElement("pm-test")
export class PmTest extends LitElement {
  // This decorator creates a property accessor that triggers rendering and
  // an observed attribute.
  @property()
  mood = "great";

  static styles = css`
    span {
      color: var(--pm-test-color);
    }
  `;

  // Render element DOM by returning a `lit-html` template.
  render() {
    return html`
      <div class="pm-test">Web Components are <span>${this.mood}</span>!</div>
    `;
  }
}
