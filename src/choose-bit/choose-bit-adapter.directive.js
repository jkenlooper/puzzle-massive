export default chooseBitAdapterDirective

chooseBitAdapterDirective.$inject = ['$rootScope']
function chooseBitAdapterDirective($rootScope) {
  return {
    restrict: 'A',
    link: function(scope, element, attr) {
      element[0].addEventListener(attr.pmChooseBitAdapter, () => {
        $rootScope.$emit(attr.pmChooseBitAdapter)
      })
      scope.$on('$destroy', function() {
        element[0].removeEventListener(attr.pmChooseBitAdapter)
      })
    },
  }
}
