/* global reqwest */
// import reqwest from 'reqwest'

class PuzzleService { // eslint-disable-line no-unused-vars
  // Pass in the url to the puzzle pieces
  constructor (puzzleid) {
    this.puzzleid = puzzleid
  }

  pieces () {
    const puzzleid = this.puzzleid
    return reqwest({
      url: `/newapi/puzzle-pieces/${puzzleid}/`,
      method: 'get'
    })
  }

  token (piece, mark) {
    const puzzleid = this.puzzleid
    return reqwest({
      url: `/newapi/puzzle/${puzzleid}/piece/${piece}/token/`,
      data: {'mark': mark},
      method: 'get',
      type: 'json'
    })
  }

  move (id, x, y, r, origin, token) {
    const puzzleid = this.puzzleid
    x = Math.round(Number(x))
    y = Math.round(Number(y))

    let data = {'x': x, 'y': y}
    if (r !== '-') {
      r = parseInt(r, 10)
      data.r = r
    }

    if (window.updater.ws.readyState > 1) {
      // Websocket is closed or closing, so reconnect
      window.updater.connect()
    } else {
      window.updater.ws.send(puzzleid)
    }

    return reqwest({
      url: `/newapi/puzzle/${puzzleid}/piece/${id}/move/`,
      method: 'PATCH',
      type: 'json',
      data: data,
      headers: {'Token': token},
      error: function handlePatchError (patchError) {
        let responseObj
        try {
          responseObj = JSON.parse(patchError.response)
        } catch (err) {
          responseObj = {
            reason: patchError.response
          }
        }
        if (patchError.status === 429) {
          window.publish('piece/move/blocked', [responseObj])
          window.publish('piece/move/rejected', [{id: id, x: origin.x, y: origin.y, r: origin.r}])
        } else {
          window.publish('piece/move/rejected', [{id: id, x: origin.x, y: origin.y, r: origin.r, karma: responseObj.karma}])
          // Reject with piece info from server and fallback to origin if that also fails
          reqwest({
            url: `/newapi/puzzle/${puzzleid}/piece/${id}/`,
            method: 'GET',
            type: 'json',
            data: data,
            error: function handleGetError (data) {
              if (origin) {
                window.publish('piece/move/rejected', [{id: id, x: origin.x, y: origin.y, r: origin.r}])
              }
            },
            success: function handlePieceInfo (data) {
              window.publish('piece/move/rejected', [{id: id, x: data.x, y: data.y, r: data.r}])
            }
          })
        }
      },
      success: function (d) {
        window.publish('karma/updated', [d])
        if (window.updater.ws.readyState > 1) {
          // Websocket is closed or closing, so reconnect
          window.updater.connect()
        }
      }
    })
  }
}

// export default PuzzleService
