/* global sendMovement, updater, reqwest */

class PuzzlePiecesController { // eslint-disable-line no-unused-vars
  constructor (puzzleService, $container, alerts, $karmaStatus) {
    let self = this
    // For now this is set to one to prevent feature creep
    const maxSelectedPieces = 1
    const BLOCKED_MSG_NOT_SPECIFIED = 'It would seem that recent piece moves from you were flagged as unhelpful on this puzzle.'

    const pieceAttrsThatAreInt = ['g', 'x', 'y', 'r', 's', 'b', 'w', 'h']

    self.$container = $container
    self.alerts = alerts
    self.$karmaStatus = $karmaStatus
    self.karmaStatusIsActiveTimeout

    self.pieces = {}
    self.collection = []
    self.piecesTimestamp = ''
    self.selectedPieces = []
    self.karmaChange = 0
    self.karma = 0
    self.blocked = false
    init()

    function init () {
      window.subscribe('karma/updated', onKarmaUpdate)
      window.subscribe('piece/move/blocked', onMoveBlocked)
      window.subscribe('piece/move/rejected', onPieceMoveRejected)
      window.subscribe('piece/update', onPieceUpdate)
      window.subscribe('socket/max', onMax)
      window.subscribe('socket/disconnected', onDisconnected)
      window.subscribe('socket/connected', onConnected)
      window.subscribe('socket/reconnecting', onReconnecting)
      updater.connect()
      puzzleService.pieces()
        .then(handlePieces)
    }

    function handlePieces (data) {
      let pieceData = JSON.parse(data)
      pieceData.positions.forEach((piece) => {
        // set status
        self.pieces[piece.id] = piece
        Object.keys(piece)
            .filter((key) => {
              return pieceAttrsThatAreInt.includes(key)
            })
            .forEach((key) => {
              piece[key] = Number(piece[key])
            })
      })
      self.collection = pieceData.positions.map((piece) => {
        return piece.id
      })
      self.piecesTimestamp = pieceData.timestamp.timestamp
      self.renderPieces(self.pieces, self.collection)
    }

    self.isImmovable = function (pieceID) {
      return self.pieces[pieceID].s === 1
    }

    self.unSelectPiece = function (pieceID) {
      let index = self.selectedPieces.indexOf(pieceID)
      if (index !== -1) {
        // remove the pieceID from the array
        self.selectedPieces.splice(index, 1)
        self.pieces[pieceID].active = false
      }
    }

    self.selectPiece = function (pieceID) {
      let index = self.selectedPieces.indexOf(pieceID)
      if (index === -1) {
        // add the pieceID to the end of the array
        self.selectedPieces.push(pieceID)
        self.pieces[pieceID].karma = false
        self.pieces[pieceID].active = true
        self.pieces[pieceID].origin = {
          'x': self.pieces[pieceID].x,
          'y': self.pieces[pieceID].y,
          'r': self.pieces[pieceID].r
        }
      } else {
        // remove the pieceID from the array
        self.selectedPieces.splice(index, 1)
        self.pieces[pieceID].active = false
      }

      // Only allow a max amount of selected pieces
      if (self.selectedPieces.length > maxSelectedPieces) {
        self.selectedPieces.splice(0, self.selectedPieces.length - maxSelectedPieces)
          .forEach((pieceID) => {
            // all the pieces that were unselected also set to inactive
            self.pieces[pieceID].active = false
          })
      }
      if (index === -1) {
        puzzleService.token(pieceID)
          .then((data) => {
            self.pieces[pieceID].token = data.token
          })
          .fail((data) => {
            // TODO: send off a message stating that this piece is locked
            // self.unSelectPiece(pieceID)
            let responseObj
            try {
              responseObj = JSON.parse(data.response)
            } catch (err) {
              responseObj = {
                reason: data.response
              }
            }
            switch (responseObj.type) {
              case 'piecelock':
              case 'piecequeue':
                // TODO: If piece is locked then publish a 'piece/move/delayed' instead of blocked.
                // TODO: Set a timeout and clear if piece is moved.  Maybe
                // auto-scroll to the moved piece?
                break
              case 'sameplayerconcurrent':
                break
              default:
                window.publish('piece/move/blocked', [responseObj])
            }
            window.publish('piece/move/rejected', [{id: pieceID, x: self.pieces[pieceID].origin.x, y: self.pieces[pieceID].origin.y, r: self.pieces[pieceID].origin.r}])
          })
          .always(() => {
            self.renderPieces(self.pieces, [pieceID])
          })
      } else {
        self.renderPieces(self.pieces, [pieceID])
      }
    }

    self.dropSelectedPieces = function (x, y, scale) {
      // Update piece locations
      self.selectedPieces.forEach(function (pieceID) {
        let piece = self.pieces[pieceID]
        piece.x = (x / scale) - (piece.w / 2)
        piece.y = (y / scale) - (piece.h / 2)
      })

      // Display the updates
      self.renderPieces(self.pieces, self.selectedPieces)

      // Send the updates
      self.selectedPieces.forEach(function (pieceID) {
        let piece = self.pieces[pieceID]
        sendMovement(pieceID, piece.x, piece.y, '-', piece.origin, piece.token)
      })

      // Reset the selectedPieces
      self.selectedPieces = []
    }

    self.moveBy = function (pieceID, x, y, scale) {
      let piece = self.pieces[pieceID]
      piece.x = (x / scale) - (piece.w / 2)
      piece.y = (y / scale) - (piece.h / 2)
      self.renderPieces(self.pieces, [pieceID])
    }
    self.moveTo = function (pieceID, x, y, scale) {
      let piece = self.pieces[pieceID]
      piece.x = (x / scale) - (piece.w / 2)
      piece.y = (y / scale) - (piece.h / 2)
      self.renderPieces(self.pieces, [pieceID])
      sendMovement(pieceID, piece.x, piece.y, '-', undefined, piece.token)
    }

    function onPieceMoveRejected (data) {
      let piece = self.pieces[data.id]
      piece.x = data.x
      piece.y = data.y
      piece.active = false
      self.renderPieces(self.pieces, [data.id])
      updateKarmaValue(data.karma)
    }

    function onPieceUpdate (data) {
      let piece = self.pieces[data.id]
      piece = Object.assign(piece, data)
      piece.active = false
      self.renderPieces(self.pieces, [data.id])
    }

    function updateKarmaValue (karma) {
      if (self.$karmaStatus && karma && typeof karma === 'number') {
        window.clearTimeout(self.karmaStatusIsActiveTimeout)
        self.$karmaStatus.innerHTML = karma
        const karmaLevel = Math.floor(karma / 6)
        self.$karmaStatus.setAttribute('data-karma-level', karmaLevel)
        self.$karmaStatus.classList.add('is-active')

        // Hide the karma status after a timeout when it is normal
        if (karmaLevel > 2) {
          self.karmaStatusIsActiveTimeout = window.setTimeout(() => {
            self.$karmaStatus.classList.remove('is-active')
          }, 5000)
        }
      }
    }

    function onKarmaUpdate (data) {
      let piece = self.pieces[data.id]
      Object.assign(piece, data)
      self.karma = data.karma
      self.renderPieces(self.pieces, [data.id])

      updateKarmaValue(data.karma)

      // Remove blocked alert if present when going from 0 to 2
      if (self.karma > 0 && self.blocked) {
        self.alerts.container.classList.remove('is-active')
        self.alerts.blocked.classList.remove('is-active')
        self.blocked = false
      }
    }

    function onMoveBlocked (data) {
      self.alerts.container.classList.add('is-active')
      self.alerts.blocked.classList.add('is-active')
      const msgEl = self.alerts.blocked.querySelector('#puzzle-pieces-alert-blocked-msg')
      const reasonEl = self.alerts.blocked.querySelector('#puzzle-pieces-alert-blocked-reason')
      if (data.msg) {
        msgEl.innerHTML = data.msg
      } else {
        msgEl.innerHTML = BLOCKED_MSG_NOT_SPECIFIED
      }
      if (data.reason) {
        reasonEl.innerHTML = data.reason
      } else {
        reasonEl.innerHTML = ''
      }
      if (data.expires && typeof data.expires === 'number') {
        const expireDate = new Date(data.expires * 1000)
        reasonEl.innerHTML = reasonEl.innerHTML + ` Expires: ${expireDate.toLocaleTimeString()}`
      }
      if (data.timeout && typeof data.timeout === 'number') {
        window.setTimeout(() => {
          self.alerts.container.classList.remove('is-active')
          self.alerts.blocked.classList.remove('is-active')
          // self.blocked = false // TODO: Only for karma updates?
        }, data.timeout * 1000)
      }
      self.blocked = true
    }

    function onMax () {
      self.isAtMax = true
      // console.log('at max')
      self.alerts.container.classList.add('is-active')
      self.alerts.max.classList.add('is-active')
    }

    function onDisconnected () {
      // console.log('on disconnected')
      self.alerts.container.classList.add('is-active')
      self.alerts.disconnected.classList.add('is-active')
      self.alerts.reconnecting.classList.remove('is-active')
    }

    function onReconnecting () {
      // console.log('on reconnecting')
      self.alerts.container.classList.add('is-active')
      self.alerts.reconnecting.classList.add('is-active')
      self.alerts.disconnected.classList.remove('is-active')
    }

    function onConnected () {
      // console.log('on connected')
      self.alerts.container.classList.remove('is-active')
      self.alerts.max.classList.remove('is-active')
      self.alerts.reconnecting.classList.remove('is-active')
      self.alerts.disconnected.classList.remove('is-active')
    }

  }
}
