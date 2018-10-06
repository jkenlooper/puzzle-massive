import angular from 'angular'
import dotRequireDirective from './dot-require.directive.js'

export default angular.module('dot-require', [])
  .directive('pmDotRequire', dotRequireDirective)
  .name
