import template from './hash-color.html'
import './hash-color.css'
import HashColorController from './hash-color.controller.js'

export default hashColorDirective

function hashColorDirective () {
  return {
    restrict: 'E',
    template: template,
    scope: {
      'backgroundColor': '@',
      'vertical': '<'
    },
    controller: HashColorController,
    controllerAs: '$ctrl',
    bindToController: true,
    transclude: true
  }
}
