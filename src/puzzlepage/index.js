require('file-loader?name=[name].[ext]!../../node_modules/slab-massive/dist/slab-massive.min.js')

import PuzzlePreviewBox from './puzzle-preview-box.js'
import ScrollJump from './scroll-jump.js'

import '../puzzle-pieces'
import '../rebuild-form'
import '../puzzle-bits'
import '../hash-color'
import '../karma-status'
import './puzzlepage.css'

// Patch in the old PuzzlePreviewBox
const previewButton = document.getElementById('puzzle-preview-button')
const previewBox = document.getElementById('puzzle-preview-box')
if (previewButton && previewBox) {
  PuzzlePreviewBox(previewButton, previewBox)
}

const scrollJumpElement = document.querySelector('[scroll-jump]')
if (scrollJumpElement) {
  ScrollJump(scrollJumpElement)
}
