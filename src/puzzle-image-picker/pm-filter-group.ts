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
  group: string;
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

      const filtertype = this.attributes.getNamedItem("type");
      if (filtertype && filterGroupTypeStrings.includes(filtertype.value)) {
        this.filtertype = filtertype.value;
      }
    }

    handleItemValueChange(e) {
      const el = e.target;
      const name = el.getAttribute("group");
      const value = el.value;
      const isChecked = el.checked;
      let checked;
      if (this.filtertype === "radio") {
        checked = [value];
      } else {
        checked = this.filterItems.reduce(
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
      }
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
                  group=${data.group}
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
        group: this.name,
        name: `${this.name}-${this.instanceId}`,
        itemValueChangeHandler: {
          handleEvent: this.handleItemValueChange.bind(this),
          capture: true,
        },
      };
    }

    render() {
      render(this.template(this.data), this);
    }

    attributeChangedCallback(
      name: string,
      _oldValue: string | null,
      _newValue: string | null
    ) {
      const value: string = _newValue !== null ? _newValue : "";
      let labels = this.buildArrayFromAttr("labels");
      let values = this.buildArrayFromAttr("values");
      switch (name) {
        case "legend":
          this.legend = value;
          this.render();
          break;
        case "labels":
          labels = this.buildArrayFromAttr("labels", value);
          break;
        case "values":
          values = this.buildArrayFromAttr("values", value);
          break;
      }
      if (name === "labels" || name === "values") {
        if (labels.length === 0 || labels.length === values.length) {
          // TODO: update filterItems with new labels, values if labels length same
          // as values length
          [labels, values] = this.buildFilterItems(labels, values);
          this.render();
        }
      }
    }

    buildArrayFromAttr(name: string, value?: string): Array<string> {
      const attr = this.attributes.getNamedItem(name);
      const _value: string =
        value !== undefined
          ? value
          : attr && attr.value && typeof attr.value === "string"
          ? attr.value
          : "";

      return _value ? _value.split(",").map((item) => item.trim()) : [];
    }

    buildFilterItems(
      labels: Array<string>,
      values: Array<string>
    ): Array<Array<string>> {
      const _labels =
        labels.length !== values.length && labels.length === 0
          ? [...values]
          : [...labels];
      const _values = [...values];

      if (_labels.length !== _values.length) {
        throw new Error(
          `${this.legend} ${
            this.instanceId
          } must have same number of labels and values. (${_labels}) (${_values})`
        );
      }

      this.filterItems = _labels.map((label, index) => {
        return {
          label: label,
          value: _values[index],
          checked: filterGroupService.isItemChecked(this.name, _values[index]),
        };
      });

      return [_labels, _values];
    }

    connectedCallback() {
      //console.log("connectedCallback");
      const legend = this.attributes.getNamedItem("legend");
      if (legend && legend.value) {
        this.legend = legend.value;
      }

      let labels = this.buildArrayFromAttr("labels");
      let values = this.buildArrayFromAttr("values");

      [labels, values] = this.buildFilterItems(labels, values);

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
