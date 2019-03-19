import { divulgerService } from './divulger.service'
let lastInstanceId = 0

function _instanceId() {
  return `PuzzlePiecesController ${lastInstanceId++}`
}

export default class PuzzlePiecesController {
  constructor(puzzleId, puzzleService) {
    let self = this
    // For now this is set to one to prevent feature creep
    const maxSelectedPieces = 1

    //const pieceAttrsThatAreInt = ['g', 'x', 'y', 'r', 's', 'b', 'w', 'h']

    this.instanceId = _instanceId()
    this.puzzleId = puzzleId

    self.pieces = {}
    self.collection = []
    self.selectedPieces = []
    self.blocked = false

    //window.subscribe('karma/updated', onKarmaUpdate) // PuzzleService
    window.subscribe('piece/move/rejected', onPieceMoveRejected) // PuzzleService

    // DivulgerService
    divulgerService.ping(this.puzzleId)
    //divulgerService.subscribe('piece/update', onPieceUpdate, this.instanceId)
    //puzzleService.pieces().then(handlePieces)

    //function handlePieces(data) {
    //  let pieceData = JSON.parse(data)
    //  self.mark = pieceData.mark
    //  pieceData.positions.forEach((piece) => {
    //    // set status
    //    self.pieces[piece.id] = piece
    //    Object.keys(piece)
    //      .filter((key) => {
    //        return pieceAttrsThatAreInt.includes(key)
    //      })
    //      .forEach((key) => {
    //        piece[key] = Number(piece[key])
    //      })
    //  })
    //  self.collection = pieceData.positions.map((piece) => {
    //    return piece.id
    //  })
    //  self.piecesTimestamp = pieceData.timestamp.timestamp
    //  self.renderPieces(self.pieces, self.collection)
    //}

    //self.unSelectPiece = function(pieceID) {
    //  let index = self.selectedPieces.indexOf(pieceID)
    //  if (index !== -1) {
    //    // remove the pieceID from the array
    //    self.selectedPieces.splice(index, 1)
    //    self.pieces[pieceID].active = false
    //    puzzleService.cancelMove(
    //      pieceID,
    //      self.pieces[pieceID].origin,
    //      self.pieces[pieceID].pieceMovementId
    //    )
    //  }
    //}

    //self.selectPiece = function(pieceID) {
    //  // TODO: move selectPiece to pm-puzzle-pieces?
    //  const index = self.selectedPieces.indexOf(pieceID)
    //  if (index === -1) {
    //    // add the pieceID to the end of the array
    //    self.selectedPieces.push(pieceID)
    //    self.pieces[pieceID].karma = false
    //    self.pieces[pieceID].active = true
    //    self.pieces[pieceID].origin = {
    //      x: self.pieces[pieceID].x,
    //      y: self.pieces[pieceID].y,
    //      r: self.pieces[pieceID].r,
    //    }
    //  } else {
    //    // remove the pieceID from the array
    //    self.selectedPieces.splice(index, 1)
    //    self.pieces[pieceID].active = false
    //    puzzleService.cancelMove(
    //      pieceID,
    //      self.pieces[pieceID].origin,
    //      self.pieces[pieceID].pieceMovementId
    //    )
    //  }

    //  // TODO: onPieceUpdate check if piece is already active
    //  //self.pieces[pieceID].active = false

    //  // Only allow a max amount of selected pieces
    //  if (self.selectedPieces.length > maxSelectedPieces) {
    //    self.selectedPieces
    //      .splice(0, self.selectedPieces.length - maxSelectedPieces)
    //      .forEach((pieceID) => {
    //        // all the pieces that were unselected also set to inactive
    //        self.pieces[pieceID].active = false
    //        puzzleService.cancelMove(
    //          pieceID,
    //          self.pieces[pieceID].origin,
    //          self.pieces[pieceID].pieceMovementId
    //        )
    //      })
    //  }
    //  if (!puzzleService.inPieceMovementQueue(pieceID)) {
    //    // Only get a new token if this piece movement isn't already in the
    //    // queue.
    //    self.pieces[pieceID].pieceMovementId = puzzleService.token(
    //      pieceID,
    //      self.mark
    //    )
    //  }
    //  self.renderPieces(self.pieces, [pieceID])
    //}

    //self.dropSelectedPieces = function(x, y, scale) {
    //  // Update piece locations
    //  self.selectedPieces.forEach(function(pieceID) {
    //    let piece = self.pieces[pieceID]
    //    piece.x = x / scale - piece.w / 2
    //    piece.y = y / scale - piece.h / 2
    //  })

    //  // Display the updates
    //  self.renderPieces(self.pieces, self.selectedPieces)

    //  // Send the updates
    //  self.selectedPieces.forEach(function(pieceID) {
    //    let piece = self.pieces[pieceID]
    //    puzzleService.move(
    //      pieceID,
    //      piece.x,
    //      piece.y,
    //      '-',
    //      piece.origin,
    //      piece.pieceMovementId
    //    )
    //  })

    //  // Reset the selectedPieces
    //  self.selectedPieces = []
    //}

    // TODO: moved to puzzleService
    //self.moveBy = function(pieceID, x, y, scale) {
    //  let piece = self.pieces[pieceID]
    //  if (!piece) {
    //    return
    //  }
    //  piece.x = x / scale - piece.w / 2
    //  piece.y = y / scale - piece.h / 2
    //  self.renderPieces(self.pieces, [pieceID])
    //}

    function onPieceMoveRejected(data) {
      let piece = self.pieces[data.id]
      piece.x = data.x || piece.origin.x
      piece.y = data.y || piece.origin.y
      piece.active = false
      self.renderPieces(self.pieces, [data.id])
    }

//    function onPieceUpdate(data) {
//      let piece = self.pieces[data.id]
//      if (piece.active) {
//        self.unSelectPiece(data.id)
//      }
//      piece = Object.assign(piece, data)
//      piece.active = false
//      self.renderPieces(self.pieces, [data.id])
//    }
  }

  unsubscribe() {
    const topics = ['piece/update']
    topics.forEach((topic) => {
      divulgerService.unsubscribe(topic, this.instanceId)
    })
  }
}
