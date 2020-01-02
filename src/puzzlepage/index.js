import 'slab-massive'

import PuzzlePreviewBox from './puzzle-preview-box.js'
import ScrollJump from './scroll-jump.js'

import '../puzzle-pieces'
import '../rebuild-form'
import '../puzzle-bits'
import '../puzzle-karma-alert'
import '../puzzle-alert'
import '../hash-color'
//import '../karma-status'
import '../toggle-movable-pieces'
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
