// require('file-loader?name=[name].[ext]!../../node_modules/webcomponents.js/webcomponents.min.js')
// require('file-loader?name=[name].[ext]!../puzzlepage/webcomponents-patch.min.js')
require('file-loader?name=[name].[ext]!../../node_modules/@webcomponents/shadydom/shadydom.min.js')
require('file-loader?name=[name].[ext]!../../node_modules/@webcomponents/custom-elements/custom-elements.min.js')
require('file-loader?name=[name].[ext]!../../node_modules/angular/angular.min.js')
require('file-loader?name=[name].[ext]!../../node_modules/minpubsub/minpubsub.js')
require('file-loader?name=[name].[ext]!../../node_modules/hammerjs/hammer.min.js')
require('file-loader?name=[name].[ext]!../../node_modules/lazysizes/lazysizes.min.js')
require('file-loader?name=[name].[ext]!../../node_modules/reqwest/reqwest.min.js')
require('file-loader?name=[name].[ext]!./modernizr.build.min.js')

import angular from 'angular'
import './site.css'

import base from '../base'
import userService from './user.service.js'
import SiteController from './site.controller.js'
import dotRequire from '../dot-require'

import '../frontpage'
import profilepage from '../profilepage'
import '../queuepage'
import '../puzzleuploadpage'
import scorespage from '../scorespage'
import '../docspage'
import puzzlepage from '../puzzlepage'

angular
  .module('site', [
    base,
    userService,
    dotRequire,
    profilepage,
    scorespage,
    puzzlepage,
  ])
  .controller('SiteController', SiteController).name
