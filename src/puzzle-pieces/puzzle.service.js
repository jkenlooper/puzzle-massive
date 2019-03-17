import reqwest from 'reqwest'

export default class PuzzleService {
  // Pass in the url to the puzzle pieces
  constructor(puzzleid, divulgerService) {
    this.puzzleid = puzzleid
    this.divulgerService = divulgerService
    this.pieceMovementQueue = []
    this.pieceMovements = {}
    this._pieceMovementId = 0
    this.pieceMovementProcessInterval = undefined
  }

  get nextPieceMovementId() {
    this._pieceMovementId++
    return this._pieceMovementId
  }

  pieces() {
    const puzzleid = this.puzzleid
    return reqwest({
      url: `/newapi/puzzle-pieces/${puzzleid}/`,
      method: 'get',
    })
  }

  token(piece, mark) {
    const puzzleid = this.puzzleid
    const pieceMovementId = this.nextPieceMovementId
    const pieceMovement = {
      id: pieceMovementId,
      piece: piece,
      inProcess: false,
    }

    pieceMovement.tokenRequest = function tokenRequest() {
      return reqwest({
        url: `/newapi/puzzle/${puzzleid}/piece/${piece}/token/`,
        data: { mark: mark },
        method: 'get',
        type: 'json',
      })
        .then((data) => {
          pieceMovement.token = data.token
        })
        .fail((data) => {
          let responseObj
          try {
            responseObj = JSON.parse(data.response)
          } catch (err) {
            responseObj = {
              reason: data.response,
            }
          }
          if (!responseObj.timeout) {
            const expire = new Date().getTime() / 1000 + 10
            responseObj.expires = expire
            responseObj.timeout = 10
          }
          switch (responseObj.type) {
            case 'piecelock':
            case 'piecequeue':
              // TODO: If piece is locked then publish a 'piece/move/delayed' instead of blocked.
              // TODO: Set a timeout and clear if piece is moved.  Maybe
              // auto-scroll to the moved piece?
              break
            case 'sameplayerconcurrent':
              if (responseObj.action) {
                reqwest({ url: responseObj.action.url, method: 'POST' })
              }
              break
            case 'bannedusers':
            case 'expiredtoken':
            default:
              window.publish('piece/move/blocked', [responseObj])
          }
          pieceMovement.fail = true
          // TODO: still need to publish the piece/move/rejected
          try {
            window.publish('piece/move/rejected', [{ id: piece }])
          } catch (err) {
            console.log('ignoring error with minpubsub', err)
          }
        })
    }

    this.pieceMovements[pieceMovementId] = pieceMovement
    this.pieceMovementQueue.push(pieceMovementId)

    this.processNextPieceMovement()

    return pieceMovementId
  }

  inPieceMovementQueue(piece) {
    return Object.values(this.pieceMovements).some((pieceMovement) => {
      return piece === pieceMovement.piece
    })
  }

  cancelMove(id, origin, pieceMovementId) {
    const pieceMovement = this.pieceMovements[pieceMovementId]
    const puzzleid = this.puzzleid
    if (!pieceMovement) {
      return
    }
    //pieceMovement.fail = true
    pieceMovement.moveRequest = function cancelMoveRequest() {
      return reqwest({
        url: `/newapi/puzzle/${puzzleid}/piece/${id}/`,
        method: 'GET',
        type: 'json',
        error: function handleGetError(data) {
          if (origin) {
            window.publish('piece/move/rejected', [
              { id: id, x: origin.x, y: origin.y, r: origin.r },
            ])
          }
        },
        success: function handlePieceInfo(data) {
          window.publish('piece/move/rejected', [
            { id: id, x: data.x, y: data.y, r: data.r },
          ])
        },
      })
    }
  }

  move(id, x, y, r, origin, pieceMovementId) {
    const pieceMovement = this.pieceMovements[pieceMovementId]
    const puzzleid = this.puzzleid
    const divulgerService = this.divulgerService
    if (!pieceMovement) {
      return
    }

    pieceMovement.moveRequest = function moveRequest() {
      x = Math.round(Number(x))
      y = Math.round(Number(y))

      let data = { x: x, y: y }
      if (r !== '-') {
        r = parseInt(r, 10)
        data.r = r
      }

      divulgerService.ping(puzzleid)
      return reqwest({
        url: `/newapi/puzzle/${puzzleid}/piece/${id}/move/`,
        method: 'PATCH',
        type: 'json',
        data: data,
        headers: { Token: pieceMovement.token },
        error: function handlePatchError(patchError) {
          let responseObj
          try {
            responseObj = JSON.parse(patchError.response)
          } catch (err) {
            responseObj = {
              reason: patchError.response,
            }
          }
          if (patchError.status === 429) {
            window.publish('piece/move/blocked', [responseObj])
            window.publish('piece/move/rejected', [
              { id: id, x: origin.x, y: origin.y, r: origin.r },
            ])
          } else {
            window.publish('piece/move/rejected', [
              {
                id: id,
                x: origin.x,
                y: origin.y,
                r: origin.r,
                karma: responseObj.karma,
              },
            ])
          }
          // Reject with piece info from server and fallback to origin if that also fails
          return reqwest({
            url: `/newapi/puzzle/${puzzleid}/piece/${id}/`,
            method: 'GET',
            type: 'json',
            data: data,
            error: function handleGetError(data) {
              if (origin) {
                window.publish('piece/move/rejected', [
                  { id: id, x: origin.x, y: origin.y, r: origin.r },
                ])
              }
            },
            success: function handlePieceInfo(data) {
              window.publish('piece/move/rejected', [
                { id: id, x: data.x, y: data.y, r: data.r },
              ])
            },
          })
        },
        success: function(d) {
          window.publish('karma/updated', [d])
          divulgerService.ping(puzzleid)
        },
      })
    }
  }

  processNextPieceMovement() {
    if (!this.pieceMovementProcessInterval) {
      this.pieceMovementProcessInterval = window.setInterval(() => {
        // All done processing movements on the queue
        if (this.pieceMovementQueue.length === 0) {
          window.clearInterval(this.pieceMovementProcessInterval)
          this.pieceMovementProcessInterval = undefined
          return
        }

        const pieceMovementId = this.pieceMovementQueue[0]
        const pieceMovement = this.pieceMovements[pieceMovementId]

        const hasMoveRequest = !!pieceMovement.moveRequest
        const hasTokenRequest = !!pieceMovement.tokenRequest
        if (pieceMovement.fail) {
          this.pieceMovementQueue.shift()
          delete this.pieceMovements[pieceMovementId]
          return
        }

        if (!pieceMovement.inProcess) {
          if (hasTokenRequest || hasMoveRequest) {
            // Mark that this pieceMovement is being processed
            pieceMovement.inProcess = true
          }

          if (hasTokenRequest) {
            // need token
            pieceMovement.tokenRequest().always(() => {
              pieceMovement.tokenRequest = undefined
              pieceMovement.inProcess = false
            })
          } else if (hasMoveRequest) {
            // ready to send movement
            pieceMovement.moveRequest().always(() => {
              pieceMovement.moveRequest = undefined
              this.pieceMovementQueue.shift()
              delete this.pieceMovements[pieceMovementId]
            })
          }
        }
      }, 100)
    }
  }
}
