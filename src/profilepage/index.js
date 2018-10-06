import angular from 'angular'
import base from '../base'
import ProfilepageController from './profilepage.controller.js'
import account from '../account'
import './profilepage.css'
import '../previewFullImg.css'
import '../queue'

angular.module('profilepage', [base, account])
  .controller('ProfilepageController', ProfilepageController)
  .name
