/*
This file in the parent directory design-tokens was generated from the design-tokens directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.
Version: 0.0.2-alpha.5
*/
const isProduction = process.env.NODE_ENV === 'production';

module.exports = {
  plugins: [
    require('postcss-import')({}),
    isProduction &&
    require('cssnano')({
      preset: 'default',
    }),
  ],
};
