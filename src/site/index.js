require('file-loader?name=[name].[ext]!../../node_modules/@webcomponents/webcomponentsjs/webcomponents-loader.js')
// require('file-loader?name=[name].[ext]!../../node_modules/@webcomponents/webcomponentsjs/webcomponents-bundle.js') // Not used
require('file-loader?name=bundles/[name].[ext]!../../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-ce.js')
require('file-loader?name=bundles/[name].[ext]!../../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd-ce-pf.js')
require('file-loader?name=bundles/[name].[ext]!../../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd-ce.js')
require('file-loader?name=bundles/[name].[ext]!../../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd.js')

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
import '../dot-require'
import siteDirective from './site.directive.js'

import '../frontpage'
import profilepage from '../profilepage'
import '../queuepage'
import '../puzzleuploadpage'
import '../scorespage'
import '../docspage'
import puzzlepage from '../puzzlepage'

angular
  .module('site', [base, userService, profilepage, puzzlepage])
  .directive('pmSite', siteDirective).name
