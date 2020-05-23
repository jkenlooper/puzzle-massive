Taken from the [Alpine.js README](https://github.com/alpinejs/alpine#readme)

# Alpine.js

Alpine.js offers you the reactive and declarative nature of big frameworks like Vue or React at a much lower cost.

You get to keep your DOM, and sprinkle in behavior as you see fit.

## Learn

There are 13 directives available to you:

| Directive                                                         | Description                                                                                 |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| [`x-data`](https://github.com/alpinejs/alpine#x-data)             | Declares a new component scope.                                                             |
| [`x-init`](https://github.com/alpinejs/alpine#x-init)             | Runs an expression when a component is initialized.                                         |
| [`x-show`](https://github.com/alpinejs/alpine#x-show)             | Toggles `display: none;` on the element depending on expression (true or false).            |
| [`x-bind`](https://github.com/alpinejs/alpine#x-bind)             | Sets the value of an attribute to the result of a JS expression                             |
| [`x-on`](https://github.com/alpinejs/alpine#x-on)                 | Attaches an event listener to the element. Executes JS expression when emitted.             |
| [`x-model`](https://github.com/alpinejs/alpine#x-model)           | Adds "two-way data binding" to an element. Keeps input element in sync with component data. |
| [`x-text`](https://github.com/alpinejs/alpine#x-text)             | Works similarly to `x-bind`, but will update the `innerText` of an element.                 |
| [`x-html`](https://github.com/alpinejs/alpine#x-html)             | Works similarly to `x-bind`, but will update the `innerHTML` of an element.                 |
| [`x-ref`](https://github.com/alpinejs/alpine#x-ref)               | Convenient way to retrieve raw DOM elements out of your component.                          |
| [`x-if`](https://github.com/alpinejs/alpine#x-if)                 | Remove an element completely from the DOM. Needs to be used on a `<template>` tag.          |
| [`x-for`](https://github.com/alpinejs/alpine#x-for)               | Create new DOM nodes for each item in an array. Needs to be used on a `<template>` tag.     |
| [`x-transition`](https://github.com/alpinejs/alpine#x-transition) | Directives for applying classes to various stages of an element's transition                |
| [`x-cloak`](https://github.com/alpinejs/alpine#x-cloak)           | This attribute is removed when Alpine initializes. Useful for hiding pre-initialized DOM.   |

And 6 magic properties:

| Magic Properties                                           | Description                                                                         |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| [`$el`](https://github.com/alpinejs/alpine#el)             | Retrieve the root component DOM node.                                               |
| [`$refs`](https://github.com/alpinejs/alpine#refs)         | Retrieve DOM elements marked with `x-ref` inside the component.                     |
| [`$event`](https://github.com/alpinejs/alpine#event)       | Retrieve the native browser "Event" object within an event listener.                |
| [`$dispatch`](https://github.com/alpinejs/alpine#dispatch) | Create a `CustomEvent` and dispatch it using `.dispatchEvent()` internally.         |
| [`$nextTick`](https://github.com/alpinejs/alpine#nexttick) | Execute a given expression AFTER Alpine has made its reactive DOM updates.          |
| [`$watch`](https://github.com/alpinejs/alpine#watch)       | Will fire a provided callback when a component property you "watched" gets changed. |
