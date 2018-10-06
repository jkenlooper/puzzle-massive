import angular from 'angular'
import accountDirective from './account.directive.js'

export default angular.module('account', [])
  .directive('pmAccount', accountDirective)
  .name
