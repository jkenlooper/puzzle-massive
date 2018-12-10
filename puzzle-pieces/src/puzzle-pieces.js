/* global HTMLElement, Hammer, style, pieceHTML, template, PuzzleService, PuzzlePiecesController */

let pieceTemplate = document.createElement('div')
pieceTemplate.innerHTML = pieceHTML

const html = `
  <style>${style}</style>
  ${template}
  `

window.customElements.define('pm-puzzle-pieces', class extends HTMLElement {
  constructor () {
    super()
    const shadowRoot = this.attachShadow({mode: 'open'})
    shadowRoot.innerHTML = `<style>@import '${this.getAttribute('resources')}';></style>'${html}`
    this.$collection = shadowRoot.querySelector('.pm-PuzzlePieces-collection')
    this.$dropZone = shadowRoot.querySelector('.pm-PuzzlePieces-dropZone')
    const $container = shadowRoot.querySelector('.pm-PuzzlePieces')
    let $slabMassive = this.parentElement

    if ($slabMassive.tagName !== 'SLAB-MASSIVE') {
      // Not using slab-massive so we need to set the width of all parent
      // elements so the browser can properly zoom out.
      setParentWidth($slabMassive.parentNode)

      // Patch in these properties from the attrs
      Object.defineProperty($slabMassive, 'scale', {
        get: function () { return Number(this.getAttribute('scale')) }
      })
      Object.defineProperty($slabMassive, 'zoom', {
        get: function () { return Number(this.getAttribute('zoom')) }
      })
      Object.defineProperty($slabMassive, 'offsetX', {
        get: function () { return Number(this.getAttribute('offset-x')) }
      })
      Object.defineProperty($slabMassive, 'offsetY', {
        get: function () { return Number(this.getAttribute('offset-y')) }
      })
    }

    let offsetTop = $slabMassive.offsetTop
    let offsetLeft = $slabMassive.offsetLeft

    let puzzleService = new PuzzleService(this.getAttribute('puzzleid'))
    let alerts = {
      container: shadowRoot.querySelector('#puzzle-pieces-alert'),
      max: shadowRoot.querySelector('#puzzle-pieces-alert-max'),
      reconnecting: shadowRoot.querySelector('#puzzle-pieces-alert-reconnecting'),
      disconnected: shadowRoot.querySelector('#puzzle-pieces-alert-disconnected'),
      blocked: shadowRoot.querySelector('#puzzle-pieces-alert-blocked')
    }
    let ctrl = this.ctrl = new PuzzlePiecesController(puzzleService, this.$collection, alerts)
    ctrl.renderPieces = renderPieces.bind(this)
    ctrl.status = this.getAttribute('status')
    ctrl.parentoftopleft = Number(this.getAttribute('parentoftopleft'))
    ctrl.puzzleid = this.getAttribute('puzzleid')
    ctrl.player = this.getAttribute('player')

    let draggedPiece = null
    let draggedPieceID = null

    // For all parent elements set the width
    function setParentWidth (node) {
      if (node.style) {
        node.style.width = $slabMassive.offsetWidth + 'px'
      }
      if (node.parentNode) {
        setParentWidth(node.parentNode)
      }
    }

    function pieceFollow (ev) {
      ctrl.moveBy(draggedPieceID, (Number($slabMassive.offsetX) + ev.pageX) - offsetLeft, (Number($slabMassive.offsetY) + ev.pageY) - offsetTop, $slabMassive.scale * $slabMassive.zoom)
    }

    this.$dropZone.addEventListener('mousedown', dropTap, false)
    function dropTap (ev) {
      ev.preventDefault()
      if (draggedPieceID !== null) {
        ctrl.dropSelectedPieces((Number($slabMassive.offsetX) + ev.pageX) - offsetLeft, (Number($slabMassive.offsetY) + ev.pageY) - offsetTop, $slabMassive.scale * $slabMassive.zoom)
        draggedPieceID = null
      }
    }
    function onTap (ev) {
      if (ev.target.classList.contains('p')) {
        draggedPiece = ev.target
        draggedPieceID = draggedPiece.id.substr(2)
        // ignore taps on the viewfinder of slab-massive
        if (ev.target.tagName === 'SLAB-MASSIVE') {
          return
        }
        $slabMassive.removeEventListener('mousemove', pieceFollow, false)

        // Only select a tapped on piece if there are no other selected pieces.
        let id = Number(ev.target.id.substr('p-'.length))
        if (ev.target.classList.contains('p') &&
          !ctrl.isImmovable(id) &&
          ctrl.selectedPieces.length === 0) {
          // listen for piece updates to just this piece while it's being moved.
          pieceUpdateHandle = window.subscribe('piece/update/' + draggedPieceID, onPieceUpdateWhileSelected)

          // tap on piece
          ctrl.selectPiece(id)
          $slabMassive.addEventListener('mousemove', pieceFollow, false)
        } else {
          window.unsubscribe(pieceUpdateHandle)
          ctrl.dropSelectedPieces((Number($slabMassive.offsetX) + ev.pageX) - offsetLeft, (Number($slabMassive.offsetY) + ev.pageY) - offsetTop, $slabMassive.scale * $slabMassive.zoom)
          draggedPieceID = null
        }
      }
    }

    function onPieceUpdateWhileSelected (data) {
      // The selected piece has been updated while the player has it selected.
      // If it's immovable then drop it -- edit: if some other player has moved it, then drop it.
      // Stop following the mouse
      $slabMassive.removeEventListener('mousemove', pieceFollow, false)

      // Stop listening for any updates to this piece
      window.unsubscribe(pieceUpdateHandle)

      // Just unselect the piece so the next on tap doesn't move it
      ctrl.unSelectPiece(data.id)
    }

    // Enable panning of the puzzle
    let panStartX = 0
    let panStartY = 0

    let mc = new Hammer.Manager(this.$dropZone, {})
    // touch device can use native panning
    mc.add(new Hammer.Pan({ direction: Hammer.DIRECTION_ALL,
      enable: () => $slabMassive.zoom !== 1
    }))
    mc.on('panstart panmove', function (ev) {
      if (ev.target.tagName === 'SLAB-MASSIVE') {
        return
      }
      switch (ev.type) {
        case 'panstart':
          panStartX = Number($slabMassive.offsetX)
          panStartY = Number($slabMassive.offsetY)
          break
        case 'panmove':
          $slabMassive.scrollTo(
            panStartX + (ev.deltaX * -1),
            panStartY + (ev.deltaY * -1)
            )
          break
      }
    })

    // the pieceUpdateHandle is used to subscribe/unsubscribe from specific piece movements
    let pieceUpdateHandle
    this.$collection.addEventListener('mousedown', onTap, false)

    // update DOM for array of piece id's
    function renderPieces (pieces, pieceIDs) {
      let tmp = document.createDocumentFragment()
      pieceIDs.forEach((pieceID) => {
        let piece = pieces[pieceID]
        let $piece = this.$collection.querySelector('#p-' + pieceID)
        if (!$piece) {
          $piece = pieceTemplate.firstChild.cloneNode(true)
          $piece.setAttribute('id', 'p-' + pieceID)
          $piece.classList.add('pc-' + pieceID)
          $piece.classList.add('p--' + ((piece.b === 0) ? 'dark' : 'light'))
          tmp.appendChild($piece)
        }

        // Move the piece
        if (piece.x !== undefined) {
          $piece.style.transform = `translate3d(${piece.x}px, ${piece.y}px, 0)
            rotate(${360 - piece.rotate === 360 ? 0 : 360 - piece.rotate}deg)`
        }

        // Piece status can be undefined which would mean the status should be
        // reset. This is the case when a piece is no longer stacked.
        if (piece.s === undefined) {
            // Not showing any indication of stacked pieces on the front end,
            // so no class to remove.
            //
            // Once a piece is immovable it shouldn't need to become movable
            // again. (it's part of the border pieces group)
        }
        // Set immovable
        if (piece.s === 1) {
          $piece.classList.add('is-immovable')
        }

        // Toggle the is-active class
        if (piece.active) {
          $piece.classList.add('is-active')
        } else {
          $piece.classList.remove('is-active')
        }

        // Toggle the is-up, is-down class when karma has changed
        if (piece.karmaChange) {
          if (piece.karmaChange > 0) {
            $piece.classList.add('is-up')
          } else {
            $piece.classList.add('is-down')
          }
          window.setTimeout(function cleanupKarma () {
            $piece.classList.remove('is-up', 'is-down')
          }, 2000)
          piece.karmaChange = false
        }
      })
      if (tmp.children.length) {
        this.$collection.appendChild(tmp)
      }
    }

    const hashRGBColorRe = /background=([a-f0-9]{2})([a-f0-9]{2})([a-f0-9]{2})/i
    window.addEventListener('hashchange', function handleHashChange () {
      let hash = window.location.hash
      updateForegroundAndBackgroundColors(hash)
    }, false)

    /**
     * Converts an RGB color value to HSL. Conversion formula
     * adapted from http://en.wikipedia.org/wiki/HSL_color_space.
     * Assumes r, g, and b are contained in the set [0, 255] and
     * returns h, s, and l in the set [0, 1].
     *
     * @param   {number}  r       The red color value
     * @param   {number}  g       The green color value
     * @param   {number}  b       The blue color value
     * @return  {Array}           The HSL representation
     */
    function rgbToHsl (r16, g16, b16) {
      let r = parseInt(r16, 16) / 255.0
      let g = parseInt(g16, 16) / 255.0
      let b = parseInt(b16, 16) / 255.0
      let max = Math.max(r, g, b)
      let min = Math.min(r, g, b)
      let h = 0
      let s = 0
      let l = (max + min) / 2.0

      if (max === min) {
        h = s = 0 // achromatic
      } else {
        let d = max - min
        s = l > 0.5 ? d / (2.0 - max - min) : d / (max + min)
        switch (max) {
          case r:
            h = (g - b) / d + (g < b ? 6 : 0)
            break
          case g:
            h = (b - r) / d + 2
            break
          case b:
            h = (r - g) / d + 4
            break
        }
      }

      // Convert to degrees
      h = h * 60.0
      if (h < 0) {
        h = h + 360
      }
      // Convert to percentage
      s = s * 100
      l = l * 100

      return [h, s, l]
    }

    updateForegroundAndBackgroundColors(window.location.hash)
    function updateForegroundAndBackgroundColors (hash) {
      let RGBmatch = hash.match(hashRGBColorRe)

      if (RGBmatch) {
        let hsl = rgbToHsl(RGBmatch[1], RGBmatch[2], RGBmatch[3])
        $container.style.backgroundColor = `hsla(${hsl[0]},${hsl[1]}%,${hsl[2]}%,1)`

        // let hue = hsl[0]
        // let sat = hsl[1]
        let light = hsl[2]
        /*
        let opposingHSL = [
          hue > 180 ? hue - 180 : hue + 180,
          100 - sat,
          100 - light
        ]
        */
        let contrast = light > 50 ? 0 : 100
        $container.style.color = `hsla(0,0%,${contrast}%,1)`
      }
    }
  }

  // Fires when an instance was inserted into the document.
  connectedCallback () {}

  static get observedAttributes () {
    return [
      'player'
    ]
  }
  // Fires when an attribute was added, removed, or updated.
  attributeChangedCallback (attrName, oldVal, newVal) {
    if (oldVal !== newVal) {
      this[attrName] = newVal
      switch (attrName) {
        case 'player':
          this.ctrl.player = this.getAttribute('player')
          break
      }
    }
  }

  render () {
  }
})

// export default PuzzlePieces
