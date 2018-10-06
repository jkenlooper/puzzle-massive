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
import userService from './user.service.js'
import chooseBitService from './choose-bit.service.js'
import SiteController from './site.controller.js'
import dotRequire from '../dot-require'

export default angular.module('site', [userService, chooseBitService, dotRequire])
  .controller('SiteController', SiteController)
  .name
