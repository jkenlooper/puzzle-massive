// Depends on webcomponents.js polyfill to be in head
require('file?name=[name].[ext]!../../node_modules/webcomponents.js/webcomponents.min.js')
require('file?name=[name].[ext]!../../node_modules/hammerjs/hammer.min.js')

import PuzzlePieces from './puzzle-pieces.js'

document.registerElement('pm-puzzle-pieces', PuzzlePieces)
