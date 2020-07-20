import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import nodeResolve from "@rollup/plugin-node-resolve";
import { terser } from "rollup-plugin-terser";
import typescript from "@rollup/plugin-typescript";
import postcss from "rollup-plugin-postcss";
import postcssImport from "postcss-import";
import postcssURL from "postcss-url";
import postcssPresetEnv from "postcss-preset-env";
import postcssCustomMedia from "postcss-custom-media";

const isProduction =
  !process.env.ROLLUP_WATCH && process.env.NODE_ENV === "production";

export default {
  input: "src/index.js",
  output: {
    file: "dist/bundle.js",
    format: "module",
    sourcemap: true,
  },
  plugins: [
    postcss({
      extract: true,
      minimize: isProduction,
      plugins: [
        postcssImport(/*{ root: loader.resourcePath }*/),
        postcssCustomMedia(),
        postcssURL(),
        postcssPresetEnv(),
      ],
    }),
    nodeResolve(),
    typescript(),
    resolve(), // tells Rollup how to find date-fns in node_modules
    commonjs(), // converts date-fns to ES modules
    isProduction && terser(), // minify, but only in production
  ],
};

/*
require("file-loader?name=[name].[ext]!not-supported-browser-message.js");

require("file-loader?name=[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/webcomponents-loader.js");
require("file-loader?name=bundles/[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-ce.js");
require("file-loader?name=bundles/[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd-ce-pf.js");
require("file-loader?name=bundles/[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd-ce.js");
require("file-loader?name=bundles/[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd.js");

require("file-loader?name=[name].[ext]!../node_modules/hammerjs/hammer.min.js");
require("file-loader?name=[name].[ext]!../node_modules/lazysizes/lazysizes.min.js");
require("file-loader?name=[name].[ext]!../node_modules/reqwest/reqwest.min.js");
require("file-loader?name=[name].[ext]!./modernizr.build.min.js");

*/
