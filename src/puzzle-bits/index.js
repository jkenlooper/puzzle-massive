import angular from 'angular'
import puzzleBitsService from './puzzle-bits.service.js'
import puzzleBitsDirective from './puzzle-bits.directive.js'

export default angular.module('puzzle-bits', [puzzleBitsService])
  .directive('pmPuzzleBits', puzzleBitsDirective)
  .name
