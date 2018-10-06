/* global MEDIA_PATH, PLAYER_PROFILE_URL */

export default class SiteController {
  constructor ($scope, userService) {
    let self = this
    self.MEDIA_PATH = MEDIA_PATH
    self.PLAYER_PROFILE_URL = PLAYER_PROFILE_URL
    self.hasBit = false
    self.hasUserCookie = false
    self.detailsReady = false
    self.user
    self.userDetails

    setUser()
    $scope.$on('userDetailsChange', setUser)

    window.subscribe('player/earned/point', addPoint)

    function addPoint () {
      $scope.userDetails.score += 1
    }

    function setUser (notClaimRandomBit) {
      userService.get()
        .then(function (user) {
          self.user = user
          // If cookies are disabled by user then don't show the bit icon in header
          self.noCookieSupport = !userService.hasCookieSupport()
          if (!self.noCookieSupport) {
            userService.details()
              .then(function (details) {
                self.userDetails = $scope.userDetails = details
                $scope.userDetails.score = Number($scope.userDetails.score)
                self.hasBit = details.icon && Boolean(details.icon.trim())
                if (!self.hasBit && !notClaimRandomBit) {
                  // Set a random bit icon.
                  userService.claimRandomBit()
                    .then(function () {
                      // Prevent endlessly trying to pick a random bit icon if none are available
                      setUser(true)
                    })
                }
                self.hasUserCookie = document.cookie.length >= 1 && document.cookie.indexOf('user=') !== -1
                self.detailsReady = true
              })
          } else {
            self.userDetails = $scope.userDetails = {
              score: 0,
              dots: 0
            }
            self.detailsReady = true
          }
        })
    }
  }
}
SiteController.$inject = ['$scope', 'userService']
