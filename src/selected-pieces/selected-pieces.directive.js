import template from './selected-pieces.html'
import './selected-pieces.css'
import SelectedPiecesController from './selected-pieces.controller.js'

export default selectedPiecesDirective

function selectedPiecesDirective () {
  return {
    restrict: 'E',
    template: template,
    controller: SelectedPiecesController,
    controllerAs: 'SelectedPiecesController'
  }
}
