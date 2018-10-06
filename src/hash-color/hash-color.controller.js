/* global location, Modernizr */
export default class HashColorController {
  constructor ($scope, $timeout) {
    let self = this
    self.handleChange = handleChange
    self.hasInputtypesColor = Modernizr.inputtypes.color

    init()

    function init () {
      if (location.hash.startsWith('#background=')) {
        $timeout(function () {
          self.backgroundColor = '#' + location.hash.substr(12)
        }, 1)
      }
    }

    function handleChange () {
      location.hash = 'background=' + self.backgroundColor.substr(1)
    }
  }
}
HashColorController.$inject = ['$scope', '$timeout']
