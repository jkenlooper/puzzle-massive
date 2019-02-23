/* global MEDIA_PATH */

export default class SiteController {
  constructor($rootScope, $scope, userService) {
    $rootScope.MEDIA_PATH = MEDIA_PATH
    $rootScope.hasBit = false
    $rootScope.detailsReady = false

    setUser()
    $rootScope.$on('userDetailsChange', setUser)

    window.subscribe('player/earned/point', addPoint)

    function addPoint() {
      $rootScope.userDetails.score += 1
    }

    function setUser(notClaimRandomBit) {
      console.log('angular setUser userDetailsChange')
      userService.get().then(function(user) {
        // If cookies are disabled by user then don't show the bit icon in header
        $rootScope.noCookieSupport = !userService.hasCookieSupport()
        if (!$rootScope.noCookieSupport) {
          userService.details().then(function(details) {
            $rootScope.userDetails = details
            $rootScope.userDetails.score = Number($rootScope.userDetails.score)
            $rootScope.hasBit = details.icon && Boolean(details.icon.trim())
            if (!$rootScope.hasBit && !notClaimRandomBit) {
              // Set a random bit icon.
              userService.claimRandomBit().then(function() {
                // Prevent endlessly trying to pick a random bit icon if none are available
                setUser(true)
              })
            }
            $rootScope.detailsReady = true
          })
        } else {
          $rootScope.userDetails = {
            score: 0,
            dots: 0,
          }
          $rootScope.detailsReady = true
        }
      })
    }
  }
}
SiteController.$inject = ['$rootScope', '$scope', 'userService']
