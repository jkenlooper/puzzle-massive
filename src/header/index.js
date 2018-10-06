import './header.css'
import '../logo'
import chooseBit from '../choose-bit'

import angular from 'angular'
import profileBitDirective from '../profile-bit/profile-bit.directive.js'
export default angular.module('header', [chooseBit])
  .directive('pmProfileBit', profileBitDirective)
  .name
