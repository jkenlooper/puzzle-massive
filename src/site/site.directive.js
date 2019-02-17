import SiteController from './site.controller.js'

export default siteDirective

function siteDirective() {
  return {
    restrict: 'E',
    scope: {},
    controller: SiteController,
    controllerAs: 'SiteController',
  }
}
