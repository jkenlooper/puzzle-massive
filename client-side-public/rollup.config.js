import nodeResolve from "@rollup/plugin-node-resolve";
import { terser } from "rollup-plugin-terser";
import url from "@rollup/plugin-url";
import postcss from "rollup-plugin-postcss";
import postcssImport from "postcss-import";
import postcssURL from "postcss-url";
import postcssPresetEnv from "postcss-preset-env";
import postcssCustomMedia from "postcss-custom-media";

const isProduction =
  !process.env.ROLLUP_WATCH && process.env.NODE_ENV === "production";

export default {
  external: ["alpinejs", "hammerjs", "modernizr"],
  input: {
    app: "src/index.js",
  },
  output: {
    entryFileNames: "[name].bundle.js",
    dir: "dist",
    format: "module",
    sourcemap: isProduction ? false : "inline",
    globals: {
      hammerjs: "Hammer",
    },
  },
  plugins: [
    postcss({
      to: "dist/app.bundle.css",
      sourcemap: false, // sourcemap not working correctly for CSS
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
    isProduction &&
      terser({
        compress: {
          drop_console: true,
        },
      }), // minify, but only in production
  ],
};
