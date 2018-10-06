import angular from 'angular'
import RankingController from './ranking.controller.js'
import rankingDirective from './ranking.directive.js'
import rankingService from './ranking.service.js'

export default angular.module('ranking', [rankingService])
  .controller('RankingController', RankingController)
  .directive('pmRanking', rankingDirective)
  .name
