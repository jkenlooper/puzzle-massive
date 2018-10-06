/* global reqwest */
// import reqwest from 'reqwest'

class PuzzleService { // eslint-disable-line no-unused-vars
  // Pass in the url to the puzzle pieces
  constructor (url) {
    this.url = url
  }

  pieces () {
    return reqwest({
      url: this.url,
      method: 'get'
    })
  }
}

// export default PuzzleService
