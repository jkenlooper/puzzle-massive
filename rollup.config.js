import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import nodeResolve from "@rollup/plugin-node-resolve";
import { terser } from "rollup-plugin-terser";
import typescript from "@rollup/plugin-typescript";
import url from "@rollup/plugin-url";
import postcss from "rollup-plugin-postcss";
import postcssImport from "postcss-import";
import postcssURL from "postcss-url";
import postcssPresetEnv from "postcss-preset-env";
import postcssCustomMedia from "postcss-custom-media";

const isProduction =
  !process.env.ROLLUP_WATCH && process.env.NODE_ENV === "production";

export default {
  external: [
    //"alpinejs"
  ],
  //input: "src/index.js",
  input: {
    app: "src/index.js",
    //admin: "src/admin/index.js",
  },
  output: {
    entryFileNames: "[name].bundle.js",
    dir: "dist",
    format: "module",
    sourcemap: true,
  },
  plugins: [
    postcss({
      //to: "dist/app.bundle.css",
      sourceMap: !isProduction,
      extract: true,
      minimize: isProduction,
      plugins: [
        postcssImport({ root: "src/" }),
        postcssCustomMedia(),
        postcssURL({
          url: "copy",
          basePath: "./",
          assetsPath: "dist",
        }),
        postcssPresetEnv(),
      ],
    }),
    nodeResolve(),
    url({
      include: ["**/*.svg"],
      limit: 0,
      fileName: "[name][extname]",
    }),
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
