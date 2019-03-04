;(function() {
  var message = 'This web browser is not supported.'
  var el = document.createElement('a')
  var body = document.querySelector('body')
  var script = document.getElementById('not-supported-browser-message')
  el.setAttribute(
    'style',
    'font-size: 1.3em; font-weight: bold; border: 1px solid var(--color-accent); margin: 1em; padding: 10px; box-shadow: 3px 3px 0px 0px var(--color-dark); background-color: var(--color-light-accent);'
  )
  el.style.maxWidth = Math.round(message.length * 0.765) + 'em'
  el.classList.add('u-block')
  el.setAttribute('href', script.getAttribute('data-info-link'))
  el.innerText = message
  body.insertBefore(el, body.childNodes[0])
})()
