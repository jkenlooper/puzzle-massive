import angular from 'angular'
import site from '../site'
import header from '../header'
import '../menu'
import '../post-comment-form'
import '../footer'
import './base.css'

export default angular.module('base', [site, header])
  .name
