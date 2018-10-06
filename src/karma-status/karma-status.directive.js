import './karma-status.css'
import template from './karma-status.html'
import KarmaStatusController from './karma-status.controller.js'

export default karmaStatusDirective

function karmaStatusDirective () {
  return {
    restrict: 'E',
    template: template,
    controller: KarmaStatusController,
    controllerAs: 'KarmaStatusController',
    bindToController: true,
    link: function (scope, element, attrs, ctrl) {
    }
  }
}

