import { divulgerService } from './divulger.service'
let lastInstanceId = 0

function _instanceId() {
  return `PuzzlePiecesController ${lastInstanceId++}`
}

export default class PuzzlePiecesController {
  constructor(puzzleId, puzzleService, $container, alerts, $karmaStatus) {
    let self = this
    // For now this is set to one to prevent feature creep
    const maxSelectedPieces = 1
    const BLOCKED_MSG_NOT_SPECIFIED =
      'It would seem that recent piece moves from you were flagged as unhelpful on this puzzle.'

    const pieceAttrsThatAreInt = ['g', 'x', 'y', 'r', 's', 'b', 'w', 'h']

    self.$container = $container
    self.alerts = alerts
    self.$karmaStatus = $karmaStatus
    self.karmaStatusIsActiveTimeout

    this.instanceId = _instanceId()
    this.puzzleId = puzzleId

    self.pieces = {}
    self.collection = []
    self.piecesTimestamp = ''
    self.selectedPieces = []
    self.karmaChange = 0
    self.karma = 0
    self.blocked = false
    init()

    function init() {
      window.subscribe('karma/updated', onKarmaUpdate) // PuzzleService
      window.subscribe('piece/move/blocked', onMoveBlocked) // PuzzleService
      window.subscribe('piece/move/rejected', onPieceMoveRejected) // PuzzleService

      // DivulgerService
      divulgerService.subscribe('piece/update', onPieceUpdate, self.instanceId)
      divulgerService.subscribe('socket/max', onMax, self.instanceId)
      divulgerService.subscribe(
        'socket/disconnected',
        onDisconnected,
        self.instanceId
      )
      divulgerService.subscribe(
        'socket/connected',
        onConnected,
        self.instanceId
      )
      divulgerService.subscribe(
        'socket/reconnecting',
        onReconnecting,
        self.instanceId
      )
      divulgerService.ping(self.puzzleId)
      puzzleService.pieces().then(handlePieces)
    }

    function handlePieces(data) {
      let pieceData = JSON.parse(data)
      self.mark = pieceData.mark
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

    self.isImmovable = function(pieceID) {
      return self.pieces[pieceID].s === 1
    }

    self.unSelectPiece = function(pieceID) {
      let index = self.selectedPieces.indexOf(pieceID)
      if (index !== -1) {
        // remove the pieceID from the array
        self.selectedPieces.splice(index, 1)
        self.pieces[pieceID].active = false
        puzzleService.cancelMove(
          pieceID,
          self.pieces[pieceID].origin,
          self.pieces[pieceID].pieceMovementId
        )
      }
    }

    self.selectPiece = function(pieceID) {
      let index = self.selectedPieces.indexOf(pieceID)
      if (index === -1 && !self.blocked) {
        // add the pieceID to the end of the array
        self.selectedPieces.push(pieceID)
        self.pieces[pieceID].karma = false
        self.pieces[pieceID].active = true
        self.pieces[pieceID].origin = {
          x: self.pieces[pieceID].x,
          y: self.pieces[pieceID].y,
          r: self.pieces[pieceID].r,
        }
      } else {
        // remove the pieceID from the array
        self.selectedPieces.splice(index, 1)
        self.pieces[pieceID].active = false
        puzzleService.cancelMove(
          pieceID,
          self.pieces[pieceID].origin,
          self.pieces[pieceID].pieceMovementId
        )
      }

      // TODO: onPieceUpdate check if piece is already active
      //self.pieces[pieceID].active = false

      // Only allow a max amount of selected pieces
      if (self.selectedPieces.length > maxSelectedPieces) {
        self.selectedPieces
          .splice(0, self.selectedPieces.length - maxSelectedPieces)
          .forEach((pieceID) => {
            // all the pieces that were unselected also set to inactive
            self.pieces[pieceID].active = false
            puzzleService.cancelMove(
              pieceID,
              self.pieces[pieceID].origin,
              self.pieces[pieceID].pieceMovementId
            )
          })
      }
      if (index === -1 && !self.blocked) {
        self.pieces[pieceID].pieceMovementId = puzzleService.token(
          pieceID,
          self.mark
        )
      }
      self.renderPieces(self.pieces, [pieceID])
    }

    self.dropSelectedPieces = function(x, y, scale) {
      // Update piece locations
      self.selectedPieces.forEach(function(pieceID) {
        let piece = self.pieces[pieceID]
        piece.x = x / scale - piece.w / 2
        piece.y = y / scale - piece.h / 2
      })

      // Display the updates
      self.renderPieces(self.pieces, self.selectedPieces)

      // Send the updates
      self.selectedPieces.forEach(function(pieceID) {
        let piece = self.pieces[pieceID]
        puzzleService.move(
          pieceID,
          piece.x,
          piece.y,
          '-',
          piece.origin,
          piece.pieceMovementId
        )
      })

      // Reset the selectedPieces
      self.selectedPieces = []
    }

    self.moveBy = function(pieceID, x, y, scale) {
      let piece = self.pieces[pieceID]
      if (!piece) {
        return
      }
      piece.x = x / scale - piece.w / 2
      piece.y = y / scale - piece.h / 2
      self.renderPieces(self.pieces, [pieceID])
    }

    function onPieceMoveRejected(data) {
      let piece = self.pieces[data.id]
      piece.x = data.x || piece.origin.x
      piece.y = data.y || piece.origin.y
      piece.active = false
      self.renderPieces(self.pieces, [data.id])
      updateKarmaValue(data.karma)
    }

    function onPieceUpdate(data) {
      let piece = self.pieces[data.id]
      if (piece.active) {
        self.unSelectPiece(data.id)
      }
      piece = Object.assign(piece, data)
      piece.active = false
      self.renderPieces(self.pieces, [data.id])
    }

    function updateKarmaValue(karma) {
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

    function onKarmaUpdate(data) {
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

    function onMoveBlocked(data) {
      // TODO: move to alerts, but set self.blocked elsewhere
      self.alerts.container.classList.add('is-active')
      self.alerts.blocked.classList.add('is-active')
      const msgEl = self.alerts.blocked.querySelector(
        '#puzzle-pieces-alert-blocked-msg'
      )
      const reasonEl = self.alerts.blocked.querySelector(
        '#puzzle-pieces-alert-blocked-reason'
      )
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
        reasonEl.innerHTML =
          reasonEl.innerHTML + ` Expires: ${expireDate.toLocaleTimeString()}`
      }
      if (data.timeout && typeof data.timeout === 'number') {
        window.setTimeout(() => {
          self.alerts.container.classList.remove('is-active')
          self.alerts.blocked.classList.remove('is-active')
          self.blocked = false // TODO: Only for karma updates?
        }, data.timeout * 1000)
      }
      self.blocked = true
    }

    function onMax() {
      // TODO: move to alerts
      self.isAtMax = true
      self.alerts.container.classList.add('is-active')
      self.alerts.max.classList.add('is-active')
    }

    function onDisconnected() {
      // TODO: move to alerts
      self.alerts.container.classList.add('is-active')
      self.alerts.disconnected.classList.add('is-active')
      self.alerts.reconnecting.classList.remove('is-active')
    }

    function onReconnecting() {
      // TODO: move to alerts
      self.alerts.container.classList.add('is-active')
      self.alerts.reconnecting.classList.add('is-active')
      self.alerts.disconnected.classList.remove('is-active')
    }

    function onConnected() {
      // TODO: move to alerts
      self.alerts.container.classList.remove('is-active')
      self.alerts.max.classList.remove('is-active')
      self.alerts.reconnecting.classList.remove('is-active')
      self.alerts.disconnected.classList.remove('is-active')
    }
  }

  unsubscribe() {
    const topics = [
      'socket/max',
      'socket/disconnected',
      'socket/connected',
      'socket/reconnecting',
    ]
    topics.forEach((topic) => {
      divulgerService.unsubscribe(topic, this.instanceId)
    })
  }
}
