/* global WebSocket */

;(function () {
  let updater = {
    connect: connect
  }

  window.updater = updater
  // export {updater}

  // proxy_read_timeout should match the config from nginx and should be greater than 10
  const PROXY_READ_TIMEOUT = 60
  const MAX_PINGS = 13
  // Keep track of the last message sent for keeping the connection open with a ping
  let lastMessageSent = 0
  let stalePuzzleTimeout = 0
  let pingServerIntervalID = 0
  let pingCount = 0

  const puzzleId = document.getElementById('puzzle-container').getAttribute('puzzle_id')

  function connect () {
    if (pingCount >= MAX_PINGS) {
        // console.log('disconnected')
      window.clearInterval(pingServerIntervalID)
      window.publish('socket/disconnected')
        // Reset the pingCount so it can be connected again
      pingCount = 0
        // TODO: show a disconnected message
      return
    }

    // console.log('connect new ws')
    // updater.ws = new WebSocket(`ws://${window.location.host}/newapi/puzzle/${puzzleId}/updates/`)
    updater.ws = new WebSocket(`ws://${window.location.host}/divulge/${puzzleId}/`)
    updater.ws.onopen = onOpenSocket
    updater.ws.onclose = onCloseSocket
    updater.ws.onmessage = onMessageSocket
  }

  function onOpenSocket () {
    // console.log('connected')
    window.publish('socket/connected')
    updater.ws.send(puzzleId)
    window.clearInterval(pingServerIntervalID)
    pingServerIntervalID = pingServer()
  }

  function onCloseSocket () {
    window.clearInterval(pingServerIntervalID)
    if (pingCount < MAX_PINGS) {
        // console.log('onCloseSocket... reconnecting in 15')
        // Try to reconnect in 15 seconds
      setTimeout(connect, 1000 * 15)
      window.publish('socket/reconnecting')
        // Update the pingCount so it doesn't just try to continually connect forever
      pingCount = pingCount + 1
    } else {
        // console.log('onCloseSocket... disconnected')
      window.publish('socket/disconnected')
    }
  }

  function onMessageSocket (msg) {
    lastMessageSent = new Date().getTime()
    window.clearTimeout(stalePuzzleTimeout)
    stalePuzzleTimeout = window.setTimeout(function () {
      // TODO: Puzzle piece data may have moved away from redis storage if the
      // puzzle has been stale for 30 minutes.
    }, 30 * 60 * 1000)

    // console.log('msg', msg, msg.data)
    if (msg.data === 'MAX') {
      window.publish('socket/max')
      return
    }

    pingCount = 0
    // updater.ws.send('received')
    handleMovementString(msg.data)
  }

  function pingServer () {
    // send ping requests every 50 seconds to keep the connection to the proxied websocket open
    const checkInterval = 10
    // Set the poll interval to be 2 seconds less than the checkInterval
    const pollIntervalMs = (checkInterval - 2) * 1000
    const interval = (PROXY_READ_TIMEOUT - checkInterval) * 1000
    return setInterval(function () {
      // Prevent keeping the connection open if nothing is happening
      const currentTime = new Date().getTime()
      if (!lastMessageSent || lastMessageSent < currentTime - interval) {
        pingCount = pingCount + 1
        // console.log('ping', lastMessageSent, pingCount)
        if (pingCount < MAX_PINGS) {
          updater.ws.send('ping')
        }
        lastMessageSent = new Date().getTime()
      }
      // console.log('poll', lastMessageSent)
    }, pollIntervalMs)
  }

  function handleMovementString (textline) {
    let lines = textline.split('\n')
    lines.forEach(function (line) {
      // let line = String(line)
      let items = line.split(',')
      items.forEach(function (item) {
        let values = item.split(':')
        if (values.length === 7) { // puzzle_id, piece_id, x, y, r, parent, status
          // if (values[2] !== '') {
          let pieceData = {
            id: Number(values[1])
          }
          if (values[5] !== '') {
            pieceData.parent = Number(values[5])
          }
          if (values[6] !== '') {
            pieceData.s = Number(values[6])
          }
          if (values[2] !== '') {
            pieceData.x = Number(values[2])
          }
          if (values[3] !== '') {
            pieceData.y = Number(values[3])
          }
          // Publish on two topics. Subscribers that are only interested in
          // specific pieces, and any piece changes.
          window.publish('piece/update/' + pieceData.id, [pieceData])
          window.publish('piece/update', [pieceData])
        } else if (values.length === 4) {
          window.publish('bit/update', [{
            id: values[1],
            x: values[2],
            y: values[3]
          }])
        }
      })
    })
  }
})()
