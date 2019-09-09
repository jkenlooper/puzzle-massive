import { html, render } from "lit-html";
import { repeat } from "lit-html/directives/repeat";

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
  disabled: boolean;
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

const prefix = "filter-group-";
const tag = "pm-filter-group";
let lastInstanceId = 0;

export default class PmFilterGroup extends HTMLElement {
  static get _instanceId(): string {
    return `${tag} ${lastInstanceId++}`;
  }

  static get observedAttributes() {
    return ["values", "legend"];
  }

  private instanceId: string;
  isReady: boolean = false;
  readonly name: string;
  private readonly labelList: Array<string>;
  private _legend: string;

  private _labelList: Array<string> = [];
  private _valueList: Array<string>;
  private _checkedList: Array<string>;
  private readonly filtertype: string = FilterGroupType.Checkbox;

  constructor() {
    super();
    this.instanceId = PmFilterGroup._instanceId;

    // Set the attribute values
    const nameAttr = this.attributes.getNamedItem("name");
    if (!nameAttr || !nameAttr.value) {
      throw new Error(
        `${this.legend} ${this.instanceId} name attribute not set.`
      );
    } else {
      this.name = nameAttr.value;
    }

    const filtertypeAttr = this.attributes.getNamedItem("type");
    if (
      filtertypeAttr &&
      filterGroupTypeStrings.includes(filtertypeAttr.value)
    ) {
      this.filtertype = filtertypeAttr.value;
    }

    const legendAttr = this.attributes.getNamedItem("legend");
    if (legendAttr && legendAttr.value) {
      this._legend = legendAttr.value;
    } else {
      this._legend = "";
    }

    this.labelList = this.buildArrayFromAttr("labels");
    this._labelList = [...this.labelList];
    const _valueList = this.buildArrayFromAttr("values");
    this._checkedList = _valueList
      .filter((item) => {
        return item.startsWith("*");
      })
      .map((item) => item.substr(1));

    const checkedValues = window.localStorage.getItem(`${prefix}${this.name}`);
    if (checkedValues !== null) {
      try {
        this._checkedList = JSON.parse(checkedValues);
      } catch (err) {
        // Use default if checked value is a string and not json
        // parseable.
        console.warn(
          `Error: ${err}. Using default value for filter group ${name}`
        );
      }
    }

    this._valueList = _valueList.map((item) => item.replace(/^\*/, ""));

    if (
      this.labelList.length &&
      this.labelList.length !== this._valueList.length
    ) {
      throw new Error(
        `${this.legend} ${
          this.instanceId
        } must have same number of labels and values. (${this.labelList}) (${
          this._valueList
        })`
      );
    }
  }

  get legend() {
    return this._legend;
  }
  set legend(value: string) {
    this._legend = value;
    this.render();
  }

  get valueList(): string {
    return this._valueList.join(", ");
  }
  set valueList(value: string) {
    if (value === this.valueList) {
      return;
    }
    let _valueList = value ? value.split(",").map((item) => item.trim()) : [];

    let _checkedValueList = _valueList
      .filter((item) => {
        return item.startsWith("*");
      })
      .map((item) => item.substr(1));
    let storedCheckedList = [];
    const checkedValues = window.localStorage.getItem(`${prefix}${this.name}`);
    if (checkedValues !== null) {
      try {
        storedCheckedList = JSON.parse(checkedValues);
      } catch (err) {
        // Use default if checked value is a string and not json
        // parseable.
        console.warn(
          `Error: ${err}. Using default value for filter group ${name}`
        );
      }
    }

    _valueList = _valueList.map((item) => item.replace(/^\*/, ""));

    this._checkedList = storedCheckedList.length
      ? storedCheckedList
      : _checkedValueList;

    window.localStorage.setItem(
      `${prefix}${this.name}`,
      JSON.stringify(this._checkedList)
    );

    this._valueList = _valueList;

    // Sync with label
    if (this.labelList.length === 0) {
      this._labelList = [...this._valueList];
    }

    this.render();
  }

  get checked() {
    return this._checkedList;
  }

  get disabled() {
    let _disabled: Array<string> = [];
    if (this.filtertype === FilterGroupType.Interval) {
      const minIndex = this._valueList
        .map((value) => this.checked.includes(value))
        .indexOf(true);
      const maxIndex = this._valueList
        .map((value) => this.checked.includes(value))
        .lastIndexOf(true);
      _disabled = this._valueList.filter((_, index) => {
        if (minIndex === maxIndex) {
          return false;
        }
        if (minIndex < index && index < maxIndex) {
          return true;
        }
        return false;
      });
    }
    return _disabled;
  }

  handleItemValueChange(e) {
    e.preventDefault();
    const el = e.target;
    const name = el.getAttribute("group");
    const value = el.value;

    const isChecked = !this.checked.includes(value);

    let checked;
    if (this.filtertype === FilterGroupType.Radio) {
      checked = [value];
    } else if (this.filtertype === FilterGroupType.Interval) {
      // two numbers sorted
      checked = this._valueList
        .reduce(
          (acc, item) => {
            if (value === item) {
              if (isChecked) {
                acc.push(item);
              }
            } else if (this.checked.includes(item)) {
              acc.push(item);
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
      checked = this._valueList.reduce(
        (acc, item) => {
          if (value === item) {
            if (isChecked) {
              acc.push(value);
            }
          } else if (this.checked.includes(item)) {
            acc.push(item);
          }
          return acc;
        },
        <Array<string>>[]
      );
    }

    this._checkedList = checked;

    window.localStorage.setItem(
      `${prefix}${this.name}`,
      JSON.stringify(this._checkedList)
    );

    this.render();

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
                  ?disabled=${item.disabled}
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
    const filterItems = this._valueList.map((value, index) => {
      return {
        label: this._labelList[index],
        value: value,
        checked: this.checked.includes(value),
        disabled: this.disabled.includes(value),
      };
    });

    return {
      isReady: this.isReady,
      legend: this.legend,
      inputtype: [FilterGroupType.Checkbox, FilterGroupType.Radio].includes(<
        FilterGroupType
      >this.filtertype)
        ? <FilterGroupType>this.filtertype
        : FilterGroupType.Checkbox,
      filterItems: filterItems,
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

    window.setTimeout(() => {
      // Need to set the checked prop here since can't only be done at the
      // template for input type radio and checkbox.
      const inputElNodeList = this.querySelectorAll("input");
      inputElNodeList.forEach((item) => {
        item.checked = this.checked.includes(item.value);
      });
    }, 1);
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

  connectedCallback() {
    const filterGroupItemValueChangeEvent = new CustomEvent(
      "filterGroupItemValueChange",
      {
        detail: {
          name: this.name,
          checked: this.checked,
        },
        bubbles: true,
      }
    );
    this.dispatchEvent(filterGroupItemValueChangeEvent);
    this.isReady = true;
    this.render();
  }

  disconnectedCallback() {}
  adoptedCallback() {}

  attributeChangedCallback(
    attr: string,
    _oldValue: string | null,
    _newValue: string | null
  ) {
    if (_newValue && _oldValue !== _newValue) {
      switch (attr) {
        case "values":
          this.valueList = _newValue;
          const filterGroupItemValueChangeEvent = new CustomEvent(
            "filterGroupItemValueChange",
            {
              detail: {
                name: this.name,
                checked: this.checked,
              },
              bubbles: true,
            }
          );
          this.dispatchEvent(filterGroupItemValueChangeEvent);
          break;
        case "legend":
          this.legend = _newValue;
          break;
      }
    }
  }
}

customElements.define(tag, PmFilterGroup);
