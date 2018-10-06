// Depends on webcomponents.js polyfill to be in head
// require('file-loader?name=[name].[ext]!./webcomponents-patch.min.js') // TODO: used patched fix until #615 resolved
require('file-loader?name=[name].[ext]!../../node_modules/slab-massive/dist/slab-massive.min.js')
require('file-loader?name=[name].[ext]!../../node_modules/puzzle-pieces/dist/puzzle-pieces.min.js')
require('file-loader?name=[name].[ext]!../../node_modules/angular-bind-polymer/angular_bind_polymer.js')

import angular from 'angular'
import base from '../base'
import PuzzlePreviewBox from './puzzle-preview-box.js'
import ScrollJump from './scroll-jump.js'

// import '../puzzle-pieces' // TODO:
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

angular.module('puzzlepage', [base, puzzleBits, hashColor, karmaStatus, 'eee-c.angularBindPolymer'])
    .name
