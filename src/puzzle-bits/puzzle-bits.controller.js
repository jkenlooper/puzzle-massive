/* global MEDIA_PATH */
const BIT_ACTIVE_TIMEOUT = 5000

export default class PuzzleBitsController {
  constructor($scope, $timeout, puzzleBitsService, userService) {
    let self = this
    self.bits = {}
    self.collection = []
    self.MEDIA_PATH = MEDIA_PATH
    userService.get()

    init()

    function init() {
      window.subscribe('bit/update', onBitUpdate)
    }

    function onBitUpdate(data) {
      if (!self.bits[data.id]) {
        // add this bit
        self.bits[data.id] = {
          icon: 'unknown-bit',
          x: data.x,
          y: data.y,
        }
        puzzleBitsService.get(data.id).then(function(data) {
          self.bits[data.id] = {
            icon: data.icon,
          }
          self.collection.push(data.id)
          $timeout(function() {
            $scope.$apply()
          })
        })
      } else {
        // set ownbit
        if (userService.user === data.id) {
          self.bits[data.id].ownBit = true
        }

        // update the bit position
        self.bits[data.id].x = data.x
        self.bits[data.id].y = data.y

        // set the active flag with the timeout to remove it
        self.bits[data.id].active = true
        $timeout.cancel(self.bits[data.id].moveTimeout)
        self.bits[data.id].moveTimeout = $timeout(function() {
          self.bits[data.id].active = false
        }, BIT_ACTIVE_TIMEOUT)

        $scope.$apply()
      }
    }
  }
}
PuzzleBitsController.$inject = [
  '$scope',
  '$timeout',
  'puzzleBitsService',
  'userService',
]
