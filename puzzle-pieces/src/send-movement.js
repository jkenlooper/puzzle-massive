/* global reqwest */

// export default sendMovement

;(function () {
  window.sendMovement = sendMovement
  const puzzleId = document.getElementById('puzzle-container').getAttribute('puzzle_id')

  /* TODO: convert to a factory */
  function sendMovement (id, x, y, r, origin, token) {
    x = Math.round(Number(x))
    y = Math.round(Number(y))

    let data = {'x': x, 'y': y}
    if (r !== '-') {
      r = parseInt(r, 10)
      data.r = r
    }

    if (window.updater.ws.readyState > 1) {
      // console.log('ws closed, reconnect')
      // Websocket is closed or closing, so reconnect
      window.updater.connect()
    } else {
      window.updater.ws.send(puzzleId)
    }

    reqwest({
      url: `/newapi/puzzle/${puzzleId}/piece/${id}/move/`,
      method: 'PATCH',
      type: 'json',
      data: data,
      headers: {'Token': token},
      error: function handlePatchError (patchError) {
        if (patchError.status === 429) {
          var responseObj
          try {
            responseObj = JSON.parse(patchError.response)
          } catch (err) {
            responseObj = {
              reason: patchError.response
            }
          }
          window.publish('piece/move/blocked', [responseObj])
          window.publish('piece/move/rejected', [{id: id, x: origin.x, y: origin.y, r: origin.r}])
        } else {
          // Reject with piece info from server and fallback to origin if that also fails
          reqwest({
            url: `/newapi/puzzle/${puzzleId}/piece/${id}/`,
            method: 'GET',
            type: 'json',
            data: data,
            headers: {'Token': '1234abcd'}, // Not used
            error: function handleGetError (data) {
              if (origin) {
                // console.log('rejected. revert to origin', data, {id: id, x: origin.x, y: origin.y, r: origin.r})
                window.publish('piece/move/rejected', [{id: id, x: origin.x, y: origin.y, r: origin.r}])
              }
            },
            success: function handlePieceInfo (data) {
              // console.log('rejected. revert to server', data)
              window.publish('piece/move/rejected', [{id: id, x: data.x, y: data.y, r: data.r}])
            }
          })
        }
      },
      success: function (d) {
        window.publish('karma/updated', [d])
        // console.log('success', d, window.updater.ws)
        if (window.updater.ws.readyState > 1) {
          // console.log('ws closed, reconnect')
          // Websocket is closed or closing, so reconnect
          window.updater.connect()
        }
      }
    })
  }
})()
