/* global MEDIA_PATH */
export default class ChooseBitController {
  constructor ($scope, chooseBitService) {
    let self = this

    self.getBits = getBits
    self.claimBit = claimBit
    self.MEDIA_PATH = MEDIA_PATH

    init()

    function getBits () {
      chooseBitService.get()
        .then(function (bits) {
          self.bits = bits.slice(0, Number(self.limit) || undefined)
        })
    }

    function claimBit (bit) {
      chooseBitService.claim(bit)
        .then(function () {
          $scope.$emit('userDetailsChange')
        })
    }

    function init () {
      getBits()
    }
  }
}
ChooseBitController.$inject = ['$scope', 'chooseBitService']
