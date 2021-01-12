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
  external: ["alpinejs", "hammerjs", "modernizr"],
  input: {
    admin: "src/admin/index.js",
  },
  output: {
    entryFileNames: "[name].bundle.js",
    dir: "dist",
    format: "module",
    sourcemap: true,
    globals: {
      hammerjs: "Hammer",
    },
  },
  plugins: [
    postcss({
      to: "dist/admin.bundle.css",
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
    commonjs(),
    isProduction &&
      terser({
        compress: {
          drop_console: true,
        },
      }), // minify, but only in production
  ],
};
