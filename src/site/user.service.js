import angular from 'angular'

function areCookiesEnabled () {
  document.cookie = '__verify=1'
  let supportsCookies = document.cookie.length >= 1 && document.cookie.indexOf('__verify=1') !== -1
  let thePast = new Date(2011, 9, 26)
  document.cookie = '__verify=1;expires=' + thePast.toUTCString()
  return supportsCookies
}

class userService {
  constructor ($http) {
    this.$http = $http
    this.user = '2'
  }

  get () {
    let that = this
    return this.$http.get('/newapi/current-user-id/', {
      // No cache since it needs to call this url right after the player
      // selects a bit icon.
      'cache': false
    }).then(function (response) {
      that.user = response.data
      return that.user
    })
  }

  hasCookieSupport () {
    return areCookiesEnabled()
  }

  save () {
    return this.$http.get('/newapi/generate-anonymous-login/').then(function (response) {
      return response.data
    })
  }

  details () {
    return this.$http.get('/newapi/user-details/').then(function (response) {
      response.data.bit_expired = Boolean(Number(response.data.bit_expired))
      return response.data
    })
  }

  claimRandomBit () {
    return this.$http.post('/newapi/claim-random-bit/').then(function (response) {
    })
  }
}
userService.$inject = ['$http']

export default angular.module('site.user-service', [])
  .service('userService', userService)
  .name
