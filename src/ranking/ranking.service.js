/* global PLAYER_RANKS_URL */
import angular from 'angular'

class rankingService {
  constructor ($http) {
    this.$http = $http
  }

  getRanks () {
    return this.$http.get(PLAYER_RANKS_URL).then(function (response) {
      return response.data
    })
  }
}
rankingService.$inject = ['$http']

export default angular.module('ranking-service', [])
  .service('rankingService', rankingService)
  .name
