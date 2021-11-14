import "./puzzle-time.css";

const tag = "pm-puzzle-time";

class PmPuzzleTime extends HTMLElement {
  private time: number;
  private seconds: number;

  constructor() {
    super();
    this.time = 0;
    this.seconds = 0;
  }

  render() {
    var time = new Date(this.time * 1000).toISOString().substr(11, 8);
    this.innerHTML = `
    <div class = "pm-PuzzleTime">
      <small class="pm-PuzzleTime-label">time elapsed:</small>
      <span class="pm-PuzzleTime-value">${time}</span>
    </div>`;

    setInterval(() => this.timer(), 1000);
  }

  timer() {
    this.seconds = this.time++;
    var time = new Date(this.seconds * 1000).toISOString().substr(11, 8);
    this.innerHTML = `
    <div class = "pm-PuzzleTime">
      <small class="pm-PuzzleTime-label">time elapsed:</small>
      <span class="pm-PuzzleTime-value">${time}</span>
    </div>`;
  }

  connectedCallback() {
    this.render();
  }
}

customElements.define(tag, PmPuzzleTime);
