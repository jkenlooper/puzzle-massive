const webpack = require('webpack')
const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const UglifyJsPlugin = require('uglifyjs-webpack-plugin')
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin')
const postcssImport = require('postcss-import')
const postcssPresetEnv = require('postcss-preset-env')
const postcssCustomMedia = require('postcss-custom-media')

const srcEntry = require('./src/index.js')

process.traceDeprecation = true

module.exports = function makeWebpackConfig () {

  /**
   * Config
   * Reference: http://webpack.github.io/docs/configuration.html
   * This is the object where all configuration gets set
   */
  var config = {}

  config.mode = 'development'

  config.bail = true

  /**
   * Entry
   * Reference: http://webpack.github.io/docs/configuration.html#entry
   */
  config.entry = srcEntry

  /**
   * Output
   * Reference: http://webpack.github.io/docs/configuration.html#output
   */
  config.output = {
    path: __dirname + '/dist',
    filename: '[name].bundle.js'
  }

  config.resolve = {
    modules: ['src', 'node_modules']
  }

  config.externals = {
    'webcomponents.js': 'WebComponents',
    'angular': 'angular',
    'lazysizes': 'lazysizes',
    'slab-massive.js': 'slabMassive',
    'hammerjs': 'Hammer',
    'reqwest': 'reqwest'
  }

  config.module = {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules|\.min\.js/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              'env'
            ]
          }
        }
      },
      {
        test: /fonts\/.*\.(eot|svg|ttf|woff)$/,
        use: [
          {
            loader: 'file-loader',
            options: { name: '[name].[ext]' }
          }
        ],
        exclude: /node_modules/
      },
      {
        test: /\.(png|gif|jpg)$/,
        use: [
          {
            loader: 'file-loader',
            options: { name: '[name].[ext]' }
          }
        ],
        exclude: /node_modules/
      },
      {
        test: /.*sprite\.svg$/,
        loader: 'svg-sprite-loader'
      },
      {
        test: /\.css$/,
        exclude: /node_modules|puzzle-pieces.css/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          {
            'loader': 'postcss-loader',
            'options': {
              'ident': 'postcss',
              'plugins': (loader) => [
                postcssImport(),
                postcssCustomMedia(),
                postcssPresetEnv()
              ]
            }
          }
        ]
      },
      {
        test: /\.svg$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: '[name].[ext]'
            }
          },
          'svgo-loader'
        ],
        exclude: /(node_modules|fonts|.*sprite\.svg)/
      },
      {
        test: /\.html$/,
        use: 'raw-loader'
      }
    ]
  }

  config.plugins = [
    new MiniCssExtractPlugin({filename: '[name].css'})
  ]

  config.optimization = {
    minimizer: [
      new UglifyJsPlugin({
        cache: true,
        parallel: true,
        sourceMap: true // set to true if you want JS source maps
      }),
      new OptimizeCSSAssetsPlugin({})
    ]
  }

  return config
}()
