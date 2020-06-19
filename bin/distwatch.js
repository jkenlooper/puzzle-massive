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

// Only watch the dist directory with a start time of 10 seconds in the past.
wp.watch([], ["dist"], Date.now() - 10000);

wp.on("aggregated", () => {
  child_process.execSync("./bin/devsync.sh", {
    cwd: "./",
    stdio: [0, 1, 2],
  });
});
