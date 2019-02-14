export default chooseBitAdapterDirective

function chooseBitAdapterDirective() {
  return {
    restrict: 'A',
    link: function(scope, element, attr) {
      element[0].addEventListener(attr.pmChooseBitAdapter, () => {
        scope.$emit(attr.pmChooseBitAdapter)
      })
      scope.$on('$destroy', function() {
        element[0].removeEventListener(attr.pmChooseBitAdapter)
      })
    },
  }
}
