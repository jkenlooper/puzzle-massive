export default chooseBitAdapterDirective

function chooseBitAdapterDirective() {
  console.log('chooseBitAdapterDirective')
  return {
    restrict: 'A',
    scope: {},
    link: function(scope, element) {
      element[0].addEventListener('userDetailsChange', () => {
        scope.$emit('userDetailsChange')
      })
      scope.$on('$destroy', function() {
        element[0].removeEventListener('userDetailsChange')
      })
    },
  }
}
