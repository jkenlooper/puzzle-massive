import '../choose-bit/pm-choose-bit.ts'
import './choose-bit.css'

import angular from 'angular'
import chooseBitAdapterDirective from './choose-bit-adapter.directive.js'

export default angular
  .module('choose-bit', [])
  .directive('pmChooseBitAdapter', chooseBitAdapterDirective).name
