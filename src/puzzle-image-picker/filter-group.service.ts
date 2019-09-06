type FilterGroupCallback = (ev: any) => any;

const FilterGroupItems: Array<any> = [
  {
    name: "status",
    checked: ["recent", "active"],
  },
  {
    name: "pieces",
    checked: ["0", "600"],
  },
  {
    name: "type",
    checked: ["original"],
  },
  {
    name: "orderby",
    checked: ["m_date"],
  },
  {
    name: "pagination",
    checked: ["1"],
  },
];

class FilterGroupService {
  listeners: Map<string, FilterGroupCallback> = new Map();
  static prefix = "filter-group-";
  private filterGroupItems: Array<any> = [];

  constructor() {
    this.filterGroupItems = FilterGroupItems.map((item) => {
      let checked: Array<string> = [];
      const value = window.localStorage.getItem(
        `${FilterGroupService.prefix}${item.name}`
      );
      if (value === null) {
        checked = item.checked;
      } else {
        try {
          checked = JSON.parse(value);
        } catch (err) {
          // Use default if checked value is a string and not json
          // parseable.
          checked = item.checked;
          console.warn(`Using default value for filter group ${item.name}`);
        }
      }
      return {
        name: item.name,
        checked,
      };
    });
    this.filterGroupItems.forEach((item) => {
      // set localStorage on item
      window.localStorage.setItem(
        `${FilterGroupService.prefix}${item.name}`,
        JSON.stringify(item.checked)
      );
      this._broadcast(item);
    });

    document.addEventListener(
      "filterGroupItemValueChange",
      this._onFilterGroupItemValueChange.bind(this)
    );
  }

  isItemChecked(name, value) {
    const filterGroupItem = this.filterGroupItems.find((filterGroup) => {
      return filterGroup.name === name;
    });
    if (filterGroupItem) {
      return filterGroupItem.checked.some((item) => {
        return item === value;
      });
    } else {
      return false;
    }
  }

  _onFilterGroupItemValueChange(ev) {
    const item = ev.detail;

    window.localStorage.setItem(
      `${FilterGroupService.prefix}${item.name}`,
      JSON.stringify(item.checked)
    );
    this._broadcast(item);
  }

  _broadcast(filterGroupItem) {
    this.listeners.forEach((fn /*, id*/) => {
      fn(filterGroupItem);
    });
  }

  subscribe(fn: FilterGroupCallback, id: string, replay: boolean) {
    // Add the fn to listeners
    this.listeners.set(id, fn);

    if (replay) {
      this.filterGroupItems.forEach((item) => {
        this._broadcast(item);
      });
    }
  }

  unsubscribe(id: string) {
    // remove fn from listeners
    this.listeners.delete(id);
  }
}

const filterGroupService = new FilterGroupService();
export default filterGroupService;
