const webpack = require('webpack')
const path = require('path')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const TerserPlugin = require('terser-webpack-plugin')
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin')
const postcssImport = require('postcss-import')
const postcssPresetEnv = require('postcss-preset-env')
const postcssCustomMedia = require('postcss-custom-media')

const srcEntry = require('./src/index.js')

process.traceDeprecation = true

/**
 * Config
 * Reference: http://webpack.github.io/docs/configuration.html
 * This is the object where all configuration gets set
 */
const config = {}

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
  path: path.resolve(__dirname, 'dist'),
  filename: '[name].bundle.js',
}

config.resolve = {
  extensions: ['.ts', '.js'],
  modules: ['src', 'node_modules'],
}

config.externals = {
  'webcomponents.js': 'WebComponents',
  angular: 'angular',
  lazysizes: 'lazysizes',
  'slab-massive.js': 'slabMassive',
  hammerjs: 'Hammer',
  reqwest: 'reqwest',
  modernizr: 'Modernizr',
}

config.module = {
  rules: [
    {
      test: /\.ts$/,
      exclude: /node_modules/,
      use: {
        loader: 'ts-loader',
      },
    },
    {
      test: /fonts\/.*\.(eot|svg|ttf|woff)$/,
      use: [
        {
          loader: 'file-loader',
          options: { name: '[name].[ext]' },
        },
      ],
      exclude: /node_modules/,
    },
    {
      test: /\.(png|gif|jpg)$/,
      use: [
        {
          loader: 'file-loader',
          options: { name: '[name].[ext]' },
        },
      ],
      exclude: /node_modules/,
    },
    {
      test: /.*sprite\.svg$/,
      loader: 'svg-sprite-loader',
    },
    {
      test: /\.css$/,
      exclude: /node_modules|puzzle-pieces.css/,
      use: [
        MiniCssExtractPlugin.loader,
        'css-loader',
        {
          loader: 'postcss-loader',
          options: {
            ident: 'postcss',
            plugins: (loader) => [
              postcssImport(),
              postcssCustomMedia(),
              postcssPresetEnv(),
            ],
          },
        },
      ],
    },
    {
      test: /\puzzle-pieces.css$/,
      exclude: /node_modules/,
      use: [
        'css-loader',
        {
          loader: 'postcss-loader',
          options: {
            ident: 'postcss',
            plugins: (loader) => [
              postcssImport(),
              postcssCustomMedia(),
              postcssPresetEnv(),
            ],
          },
        },
      ],
    },
    {
      test: /\.svg$/,
      use: [
        {
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
          },
        },
        'svgo-loader',
      ],
      exclude: /(node_modules|fonts|.*sprite\.svg)/,
    },
    {
      test: /\.html$/,
      use: 'raw-loader',
    },
  ],
}

config.plugins = [new MiniCssExtractPlugin({ filename: '[name].css' })]

config.stats = 'minimal'

config.optimization = {
  minimizer: [
    new TerserPlugin({
      cache: true,
      parallel: true,
      sourceMap: true, // set to true if you want JS source maps
      terserOptions: {
        compress: {
          drop_console: true,
        },
      },
    }),
    new OptimizeCSSAssetsPlugin({}),
  ],
}

config.performance = {
  hints: 'warning',
  maxAssetSize: 500000,
  maxEntrypointSize: 800000,
}

module.exports = (env, argv) => {
  if (argv.mode !== 'production') {
    config.devtool = 'source-map'
    config.watch = argv.watch
    config.watchOptions = {
      aggregateTimeout: 300,
    }
    config.optimization = {}
  }

  return config
}
