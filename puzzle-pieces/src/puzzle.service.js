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

}

// export default PuzzleService
