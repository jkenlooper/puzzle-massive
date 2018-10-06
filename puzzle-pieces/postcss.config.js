module.exports = {
  use: [
    'postcss-import',
    'postcss-custom-properties',
    'postcss-custom-media',
    'postcss-calc',
    'autoprefixer',
    'postcss-url',
    'cssnano'
  ],
  cssnano: {
    safe: true
  }
}
