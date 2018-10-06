import './dot-require.css'

export default dotRequireDirective

function dotRequireDirective () {
  return {
    restrict: 'A',
    link: function (scope, element, attrs, ctrl) {
      let requiredDots = Number(attrs.pmDotRequire)
      scope.$watch('SiteController.detailsReady', function (newValue, oldValue) {
        if (newValue === true && scope.SiteController.userDetails.dots >= requiredDots) {
          element[0].classList.remove('is-dotted')
        }
      })
    }
  }
}
