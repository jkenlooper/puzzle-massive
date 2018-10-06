import './ranking.css'
import template from './ranking.html'

export default rankingDirective

function rankingDirective () {
  return {
    restrict: 'E',
    template: template
  }
}
