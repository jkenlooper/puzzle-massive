import { html, render } from "lit-html";

import filterGroupService from "./filter-group.service";

enum FilterGroupType {
  Checkbox = "checkbox",
  Radio = "radio",
}
const filterGroupTypeStrings: Array<string> = [
  FilterGroupType.Checkbox,
  FilterGroupType.Radio,
];

interface FilterItem {
  label: string;
  value: string;
  checked: boolean;
}

interface TemplateData {
  isReady: boolean;
  legend: string;
  filtertype: string;
  name: string;
  filterItems: Array<FilterItem>;
  itemValueChangeHandler: any; // event listener object
}

const tag = "pm-filter-group";
let lastInstanceId = 0;

customElements.define(
  tag,
  class PmFilterGroup extends HTMLElement {
    static get _instanceId(): string {
      return `${tag} ${lastInstanceId++}`;
    }

    private instanceId: string;
    isReady: boolean = false;
    name: string = "";
    legend: string = "";
    filtertype: string = FilterGroupType.Checkbox;
    filterItems: Array<FilterItem> = [];

    constructor() {
      super();
      this.instanceId = PmFilterGroup._instanceId;

      // Set the attribute values
      const name = this.attributes.getNamedItem("name");
      if (!name || !name.value) {
        throw new Error(
          `${this.legend} ${this.instanceId} name attribute not set.`
        );
      } else {
        this.name = name.value;
      }

      const legend = this.attributes.getNamedItem("legend");
      if (legend && legend.value) {
        this.legend = legend.value;
      }

      const filtertype = this.attributes.getNamedItem("filtertype");
      if (filtertype && filterGroupTypeStrings.includes(filtertype.value)) {
        this.filtertype = filtertype.value;
      }

      let labels: Array<string> = [];
      const labelsAttr = this.attributes.getNamedItem("labels");
      if (
        labelsAttr &&
        labelsAttr.value &&
        typeof labelsAttr.value === "string"
      ) {
        labels = labelsAttr.value.split(",").map((item) => item.trim());
      }

      let values: Array<string> = [];
      const valuesAttr = this.attributes.getNamedItem("values");
      if (
        valuesAttr &&
        valuesAttr.value &&
        typeof valuesAttr.value === "string"
      ) {
        values = valuesAttr.value.split(",").map((item) => item.trim());
      }
      if (labels.length !== values.length) {
        throw new Error(
          `${this.legend} ${
            this.instanceId
          } must have same number of labels and values.`
        );
      }

      this.filterItems = labels.map((label, index) => {
        return {
          label: label,
          value: values[index],
          checked: filterGroupService.isItemChecked(this.name, values[index]),
        };
      });

      const replay = false;
      filterGroupService.subscribe(
        (filterGroupItem) => {
          if (filterGroupItem.name === this.name) {
            this.filterItems = this.filterItems.map((item) => {
              const newItem = {
                label: item.label,
                value: item.value,
                checked: filterGroupItem.checked.includes(item.value),
              };
              return newItem;
            });
            this.render();
          }
        },
        this.instanceId,
        replay
      );
    }

    handleItemValueChange(e) {
      const el = e.target;
      const name = el.getAttribute("name");
      const value = el.value;
      const isChecked = el.checked;
      const checked = this.filterItems.reduce(
        (acc, item) => {
          if (value === item.value) {
            item.checked = isChecked;
          }
          if (item.checked) {
            acc.push(item.value);
          }
          return acc;
        },
        <Array<string>>[]
      );
      const filterGroupItemValueChangeEvent = new CustomEvent(
        "filterGroupItemValueChange",
        {
          detail: {
            name,
            checked,
          },
          bubbles: true,
        }
      );
      this.dispatchEvent(filterGroupItemValueChangeEvent);
    }

    template(data: TemplateData) {
      if (!data.isReady) {
        return html``;
      }
      return html`
        <fieldset>
          <legend>${data.legend}</legend>
          ${data.filterItems.map((item) => {
            return html`
              <label>
                <input
                  @click=${data.itemValueChangeHandler}
                  type=${data.filtertype}
                  name=${data.name}
                  ?checked=${item.checked}
                  value=${item.value}
                />
                ${item.label}</label
              >
            `;
          })}
        </fieldset>
      `;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        legend: this.legend,
        filtertype: this.filtertype,
        filterItems: this.filterItems,
        name: this.name,
        itemValueChangeHandler: {
          handleEvent: this.handleItemValueChange.bind(this),
          capture: true,
        },
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    connectedCallback() {
      //console.log("connectedCallback");
      this.isReady = true;
      this.render();
    }
    disconnectedCallback() {
      //console.log("disconnectedCallback", this.instanceId);
      filterGroupService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {
      //console.log("adoptedCallback");
    }
  }
);
