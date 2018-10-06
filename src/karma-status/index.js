import angular from 'angular'
import karmaStatusDirective from './karma-status.directive.js'

export default angular.module('karma-status', [])
  .directive('pmKarmaStatus', karmaStatusDirective)
  .name
