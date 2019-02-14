import './pm-choose-bit'

import angular from 'angular'
import chooseBitAdapterDirective from './choose-bit-adapter.directive.js'

export default angular
  .module('choose-bit', [])
  .directive('pmChooseBitAdapter', chooseBitAdapterDirective).name
