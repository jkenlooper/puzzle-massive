import angular from 'angular'
import selectedPiecesDirective from './selected-pieces.directive.js'

export default angular.module('selected-pieces', [])
  .directive('pmSelectedPieces', selectedPiecesDirective)
  .name
