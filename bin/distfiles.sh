#!/usr/bin/bash

rm -rf dist
mkdir -p dist

npm run rollup -- -c rollup-admin.config.js

npm run rollup -- node_modules/alpinejs/dist/alpine.js --file dist/alpine.js --format es --silent --plugin rollup-plugin-terser

npm run rollup -- src/not-supported-browser-message.js --file dist/not-supported-browser-message.js --format iife --plugin rollup-plugin-terser

cp node_modules/@webcomponents/webcomponentsjs/webcomponents-loader.js \
  dist/
mkdir -p dist/bundles
cp node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-ce.js \
  node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd-ce-pf.js \
  node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd-ce.js \
  node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd.js \
  dist/bundles/

cp src/modernizr.build.min.js \
  node_modules/hammerjs/hammer.min.js \
  node_modules/hammerjs/hammer.min.js.map \
  node_modules/lazysizes/lazysizes.min.js \
  node_modules/reqwest/reqwest.min.js \
  dist/
