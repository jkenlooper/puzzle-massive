import angular from 'angular'
// import ChooseBitController from './choose-bit.controller.js'
import chooseBitDirective from './choose-bit.directive.js'

export default angular.module('choose-bit', [])
  // .controller('ChooseBitController', ChooseBitController)
  .directive('pmChooseBit', chooseBitDirective)
  .name
