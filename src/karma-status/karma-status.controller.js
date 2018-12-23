export default class KarmaStatusController {
  constructor ($scope, $timeout) {
    let self = this
    const max = 25
    self.amount = 0
    init()

    function init () {
      window.subscribe('karma/updated', onKarmaUpdate)
      window.subscribe('piece/move/blocked', onMoveBlocked)
    }

    function onKarmaUpdate (data) {
      self.amount = (Math.min(data.karma, max) / max) * 100
      $timeout(function () {
        $scope.$apply()
      })
    }

    function onMoveBlocked (data) {
      self.amount = 0
      $timeout(function () {
        $scope.$apply()
      })
    }
  }
}
KarmaStatusController.$inject = ['$scope', '$timeout']
