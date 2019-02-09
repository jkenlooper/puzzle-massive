import template from './account.html'

export default accountDirective

function accountDirective() {
  return {
    restrict: 'E',
    template: template,
    link: function(scope, element, attrs, ctrl) {
      scope.baseUrl = `${window.location.protocol}//${window.location.host}`
    },
  }
}
