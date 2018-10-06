export default class ProfilepageController {
  constructor ($scope, userService) {
    let self = this
    self.bitLink = ''
    self.generateBitLink = generateBitLink

    function generateBitLink () {
      userService.save()
        .then(function (data) {
          self.bitLink = data.bit
        })
        .catch(function () {
          self.bitLink = ''
        })
    }
  }

}
ProfilepageController.$inject = ['$scope', 'userService']
