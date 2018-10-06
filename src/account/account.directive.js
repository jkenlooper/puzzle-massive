import template from './account.html'

export default accountDirective

function accountDirective () {
  return {
    restrict: 'E',
    template: template
  }
}
