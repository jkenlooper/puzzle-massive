import Hammer from 'hammerjs'

export default (button, element) => {
  let _button = button
  let _element = element
  let model = {x: 0, y: 0, visible: Boolean(_button.checked)}

  init()

  function moveBy (x, y) {
    translate(model.x + x, model.y + y)
  }

  function translate (x, y) {
    _element.style.transform = 'translate(' + x + 'px, ' + y + 'px)'
  }

  function toggle (e) {
    model.visible = !model.visible
    _element.style.display = model.visible && 'block' || 'none'
  }

  function init () {
    _button.addEventListener('click', toggle)

    let hammertime = new Hammer(_element, {})
    hammertime.get('pan').set({ direction: Hammer.DIRECTION_ALL })
    hammertime.on('panmove panend', handleDragging)
  }

  function handleDragging (ev) {
    // For Hammer panmove and panend events move the element and save the new
    // position.
    switch (ev.type) {
      case 'panmove':
        // Drag the element
        moveBy(ev.deltaX, ev.deltaY)
        break
      case 'panend':
        // Save the new position
        model.x += ev.deltaX
        model.y += ev.deltaY
        break
    }
  }

  // No public methods for now
  return {
  }
}
