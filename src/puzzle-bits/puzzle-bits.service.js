import angular from 'angular'

class puzzleBitsService {
  constructor ($http) {
    this.$http = $http
  }

  get (id) {
    return this.$http.get('/newapi/bit-icon/' + id + '/').then(function (response) {
      return response.data
    })
  }

}
puzzleBitsService.$inject = ['$http']

export default angular.module('puzzle-pieces.puzzle-bits-service', [])
  .service('puzzleBitsService', puzzleBitsService)
  .name
