import './puzzle-bits.css'
import template from './puzzle-bits.html'
import PuzzleBitsController from './puzzle-bits.controller.js'

export default puzzleBitsDirective

function puzzleBitsDirective () {
  return {
    restrict: 'E',
    template: template,
    controller: PuzzleBitsController,
    controllerAs: 'PuzzleBitsController',
    bindToController: true,
    link: function (scope, element, attrs, ctrl) {
    }
  }
}

