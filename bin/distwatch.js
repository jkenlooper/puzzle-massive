#!/usr/bin/env node

/* distwatch.js
 * Watches the dist directory for any changes and then runs the devsync.sh
 * script that uploads those files to the development machine.
 */

const child_process = require("child_process");

// watchpack is used in webpack as well.
const Watchpack = require("watchpack");

const wp = new Watchpack({
  aggregateTimeout: 300,

  poll: undefined,
  // poll: true - use polling with the default interval
  // poll: 10000 - use polling with an interval of 10s
  // poll defaults to undefined, which prefer native watching methods
  // Note: enable polling when watching on a network path
});

wp.watch(
  [
    "chill-data*.yaml",
    "Makefile",
    "MANIFEST",
    "package.json",
    "port-registry.cfg",
    "site.cfg.sh",
    "site-data.sql",
  ],
  [
    "dist",
    "api/api",
    "divulger/divulger",
    "documents",
    "media",
    "queries",
    "resources",
    "root",
    "source-media",
    "stream/stream",
    "templates",
    "web",
  ],
  Date.now() - 10000
);

wp.on("aggregated", () => {
  child_process.execSync("./bin/devsync.sh", {
    cwd: "./",
    stdio: [0, 1, 2],
  });
});
