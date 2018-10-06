import './choose-bit.css'
import ChooseBitController from './choose-bit.controller.js'
import template from './choose-bit.html'

export default chooseBitDirective

function chooseBitDirective () {
  return {
    restrict: 'E',
    scope: {
      message: '@',
      limit: '@'
    },
    controller: ChooseBitController,
    controllerAs: 'ChooseBitController',
    bindToController: true,
    template: template
  }
}
