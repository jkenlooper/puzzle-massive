import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";

import filterGroupService from "./filter-group.service";
import "./filter-group.css";

enum FilterGroupType {
  Checkbox = "checkbox",
  Radio = "radio",
  Interval = "interval",
}
const filterGroupTypeStrings: Array<string> = [
  FilterGroupType.Checkbox,
  FilterGroupType.Radio,
  FilterGroupType.Interval,
];

interface FilterItem {
  label: string;
  value: string;
  checked: boolean;
}

interface TemplateData {
  isReady: boolean;
  legend: string;
  inputtype: FilterGroupType;
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

    /*
    static get observedAttributes() {
      return ["values", "legend"];
    }
     */

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

      const filterItem = this.filterItems.find((item) => {
        return item.value === value;
      });
      const isChecked = filterItem ? !filterItem.checked : el.checked;

      let checked;
      if (this.filtertype === FilterGroupType.Radio) {
        checked = [value];
      } else if (this.filtertype === FilterGroupType.Interval) {
        // two numbers sorted
        checked = this.filterItems
          .reduce(
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
          )
          .map((item) => parseInt(item))
          .filter((item) => {
            return !isNaN(item);
          })
          .reduce(
            (acc, item) => {
              if (acc.length === 0) {
                acc.push(item);
                acc.push(item);
              } else {
                if (item < acc[0]) {
                  acc[0] = item;
                } else if (item > acc[1]) {
                  acc[1] = item;
                }
              }
              return acc;
            },
            <Array<number>>[]
          )
          .map((item) => String(item));
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
        <fieldset class="pm-FilterGroup">
          <legend class="pm-FilterGroup-legend">${data.legend}</legend>
          ${repeat(
            data.filterItems,
            (item) => item.value,
            (item) => {
              return html`
                <label class="pm-FilterGroup-label">
                  <input
                    class="pm-FilterGroup-input"
                    @click=${data.itemValueChangeHandler}
                    type=${data.inputtype}
                    group=${data.group}
                    name=${data.name}
                    ?checked=${item.checked}
                    value=${item.value}
                  />
                  <span class="pm-FilterGroup-text">${item.label}</span></label
                >
              `;
            }
          )}
        </fieldset>
      `;
    }

    get data(): TemplateData {
      return {
        isReady: this.isReady,
        legend: this.legend,
        inputtype: [FilterGroupType.Checkbox, FilterGroupType.Radio].includes(<
          FilterGroupType
        >this.filtertype)
          ? <FilterGroupType>this.filtertype
          : FilterGroupType.Checkbox,
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

    /* Need to set observedAttributes if using attributeChangedCallback,
     * but it seems to have an issue with lit-html here
     */
    /*
    attributeChangedCallback(
      name: string,
      _oldValue: string | null,
      _newValue: string | null
    ) {
    }
         */

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
      const legend = this.attributes.getNamedItem("legend");
      if (legend && legend.value) {
        this.legend = legend.value;
      }

      let labels = this.buildArrayFromAttr("labels");
      let values = this.buildArrayFromAttr("values");

      [labels, values] = this.buildFilterItems(labels, values);

      const replay = false;
      filterGroupService.subscribe(
        this.updateFilterItem.bind(this),
        this.instanceId,
        replay
      );
      this.isReady = true;
      this.render();
    }

    updateFilterItem(filterGroupItem) {
      if (filterGroupItem.name === this.name) {
        let labels = this.buildArrayFromAttr("labels");
        let values = this.buildArrayFromAttr("values");

        [labels, values] = this.buildFilterItems(labels, values);
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
    }

    disconnectedCallback() {
      filterGroupService.unsubscribe(this.instanceId);
    }
    adoptedCallback() {}
  }
);
