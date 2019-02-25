require('file-loader?name=[name].[ext]!../../node_modules/slab-massive/dist/slab-massive.min.js')

import angular from 'angular'
import PuzzlePreviewBox from './puzzle-preview-box.js'
import ScrollJump from './scroll-jump.js'

import '../puzzle-pieces'
import '../rebuild-form'
import puzzleBits from '../puzzle-bits'
import hashColor from '../hash-color'
import karmaStatus from '../karma-status'
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

export default angular.module('puzzlepage', [
  puzzleBits,
  hashColor,
  karmaStatus,
]).name
