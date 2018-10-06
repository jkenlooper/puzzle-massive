import angular from 'angular'

class chooseBitService {
  constructor ($http) {
    this.$http = $http
  }

  get () {
    return this.$http.get('/newapi/choose-bit/').then(function (response) {
      return response.data.data
    })
  }

  claim (bit) {
    return this.$http({
      method: 'POST',
      url: '/newapi/claim-bit/',
      params: {icon: bit} })
      .then(function (response) {
        return response.data.data
      })
  }
}
chooseBitService.$inject = ['$http']

export default angular.module('site.chooseBit-service', [])
  .service('chooseBitService', chooseBitService)
  .name
