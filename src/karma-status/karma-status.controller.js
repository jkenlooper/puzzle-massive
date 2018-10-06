export default class KarmaStatusController {
  constructor ($scope, $timeout) {
    let self = this
    self.amount = 0
    init()

    function init () {
      window.subscribe('karma/updated', onKarmaUpdate)
      window.subscribe('piece/move/blocked', onMoveBlocked)
    }

    function onKarmaUpdate (data) {
      self.amount = data.karma
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
