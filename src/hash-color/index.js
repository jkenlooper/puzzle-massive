import angular from 'angular'
import 'jscolor'
import hashColorDirective from './hash-color.directive.js'

export default angular.module('dot-require', [])
  .directive('pmHashColor', hashColorDirective)
  .name
