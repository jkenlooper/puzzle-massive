require("file-loader?name=[name].[ext]!not-supported-browser-message.js");

require("file-loader?name=[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/webcomponents-loader.js");
// require('file-loader?name=[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/webcomponents-bundle.js') // Not used
require("file-loader?name=bundles/[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-ce.js");
require("file-loader?name=bundles/[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd-ce-pf.js");
require("file-loader?name=bundles/[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd-ce.js");
require("file-loader?name=bundles/[name].[ext]!../node_modules/@webcomponents/webcomponentsjs/bundles/webcomponents-sd.js");

require("file-loader?name=[name].[ext]!../node_modules/hammerjs/hammer.min.js");
require("file-loader?name=[name].[ext]!../node_modules/lazysizes/lazysizes.min.js");
require("file-loader?name=[name].[ext]!../node_modules/reqwest/reqwest.min.js");
require("file-loader?name=[name].[ext]!./modernizr.build.min.js");

// Alpine.js see the ./alpine/README.md
import "./alpine";

// site includes all the things
/* 0 Generic */
/* 1 Elements */
/* 2 Objects */
import "./site";

// import pages which will include their components
/* 3 Components */
import "./base";
import "./icon";
import "./dot-require";
import "./puzzle-list";
import "./total-active-player-count";
import "./player-bit";
import "./response-message";
import "./site-wide-message";
import "./swatch.css";
import "./home-intro.css";
import "./puzzle-status-reload";

import "./frontpage";
import "./profilepage";
import "./puzzleuploadpage";
import "./scorespage";
import "./docspage";
import "./puzzlepage";
import "./puzzlelistpage";

/* 4 Theme */

// Import the utils css last
/* 5 Utilities */
import "./site/5-utils.css";

// Root settings for custom properties
/* Root Settings */
import "./settings/settings.css";
