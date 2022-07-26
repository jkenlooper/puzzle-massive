import { html, render } from "lit";
import FetchService from "../site/fetch.service";
import userDetailsService from "../site/user-details.service";
import "./player-name-register.css";
const tag = "pm-player-name-register";
let lastInstanceId = 0;
// TODO: Validate name to be unique before it is submitted
customElements.define(
  tag,
  class PmPlayerNameRegister extends HTMLElement {
    constructor() {
      super();
      this.responseMessage = "";
      this.responseName = "";
      this.instanceId = PmPlayerNameRegister._instanceId;
      userDetailsService.subscribe(this.render.bind(this), this.instanceId);
    }
    static get _instanceId() {
      return `${tag} ${lastInstanceId++}`;
    }
    submit(form) {
      const fetchService = new FetchService(form.action);
      const data = new FormData(form);
      fetchService
        .postForm(data)
        .then((response) => {
          this.responseMessage = response.message;
          this.responseName = response.name;
        })
        .catch((err) => {
          if (err.message && err.name) {
            this.responseMessage = err.message;
            this.responseName = err.name;
          }
        })
        .finally(() => {
          const userDetailsChangeEvent = new Event("userDetailsChange", {
            bubbles: true,
          });
          this.dispatchEvent(userDetailsChangeEvent);
        });
    }
    template(data) {
      // forminput.setCustomValidity(...)
      // TODO: submit button is disabled if name not valid
      return html`
        <form
          class="pm-PlayerNameRegister"
          id="player-name-register-form"
          method="POST"
          action="/newapi/player-name-register/"
        >
          <label for="player-name-input"> Player Name </label>
          <input
            id="player-name-input"
            type="text"
            maxlength="26"
            name="name"
            value=${data.username}
            placeholder="Hedgewig von Bitty"
          />
          <button
            class="Button"
            form="player-name-register-form"
            @click=${data.submitNameHandler}
          >
            Submit Name
          </button>

          ${data.responseMessage
            ? html`
                <pm-response-message
                  name=${data.responseName}
                  message=${data.responseMessage}
                ></pm-response-message>
              `
            : ""}
        </form>
      `;
    }
    get data() {
      return {
        username: userDetailsService.userDetails.name,
        usernameApproved: userDetailsService.userDetails.nameApproved,
        usernameRejected: userDetailsService.userDetails.nameRejected,
        submitNameHandler: {
          handleEvent: (e) => {
            // Prevent the form from submitting
            e.preventDefault();
            const formEl = e.currentTarget.form;
            this.submit(formEl);
          },
          capture: true,
        },
        responseMessage: this.responseMessage,
        responseName: this.responseName,
      };
    }
    render() {
      //console.log("render", this.instanceId, this.data);
      render(this.template(this.data), this);
    }
    connectedCallback() {
      //console.log("connectedCallback");
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      userDetailsService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
  }
);
