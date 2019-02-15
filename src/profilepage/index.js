import angular from 'angular'
import ProfilepageController from './profilepage.controller.js'
import account from '../account'
import './profilepage.css'
import '../previewFullImg.css'
import '../queue'

export default angular
  .module('profilepage', [account])
  .controller('ProfilepageController', ProfilepageController).name
