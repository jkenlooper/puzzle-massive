import angular from 'angular'

class userService {
  constructor($http) {
    this.$http = $http
    this.user = '2'
  }

  get() {
    let that = this
    return this.$http
      .get('/newapi/current-user-id/', {
        // No cache since it needs to call this url right after the player
        // selects a bit icon.
        cache: false,
      })
      .then(function(response) {
        that.user = response.data
        return that.user
      })
  }
}
userService.$inject = ['$http']

export default angular
  .module('site.user-service', [])
  .service('userService', userService).name
