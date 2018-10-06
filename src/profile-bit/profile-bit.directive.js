import './profile-bit.css'
import template from './profile-bit.html'

export default profileBitDirective

function profileBitDirective () {
  return {
    restrict: 'E',
    template: template
  }
}
