import './header.css'
import '../logo'
import '../choose-bit'

import angular from 'angular'
import profileBitDirective from '../profile-bit/profile-bit.directive.js'
export default angular
  .module('header', [])
  .directive('pmProfileBit', profileBitDirective).name
