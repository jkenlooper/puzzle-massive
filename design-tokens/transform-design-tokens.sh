#!/usr/bin/env sh

# This file in the parent directory design-tokens was generated from the design-tokens directory in https://github.com/jkenlooper/cookiecutters . Any modifications needed to this file should be done on that originating file.
# Version: 0.0.2-alpha.1

set -eu -o pipefail

rm -rf tmp/
mkdir -p tmp/

themes_settings=$(find src -depth -mindepth 2 -maxdepth 2 -type f -name settings.yaml)

for settings_path in $themes_settings; do
  # Get just the theme name by removing first and last part of the settings_path.
  theme_name=${settings_path##src/}
  theme_name=${theme_name%/settings.yaml}

  # Generate the tmp/${theme_name}/settings.custom-properties-selector.css file.
  theo $settings_path \
    --setup custom-properties-selector.cjs \
    --transform web \
    --format custom-properties-selector.css \
    --dest tmp/$theme_name
done
