# `puzzlemassive` Code Formatter

Reformats any file that is newer than the `./code-formatter/.modified-files.tar`
file.

The below command will run [Prettier](https://prettier.io/) and
[Black](https://black.readthedocs.io/en/stable/) on the target directories.

```bash
# Run the code formatter shell script to reformat the source code.
# This script should be at the top level of the project:
./code-formatter.sh
```

* TODO: Rename code-formatter to quality-check
* TODO: Add in static code analysis tool like https://semgrep.dev/
* TODO: Finish integration with stylelint and eslint linting tools

## Updating Generated Files

Run the cookiecutter command again to update any generated files with newer
versions from the [cookiecutter code-formatter](https://github.com/jkenlooper/cookiecutters).

```bash
# From the top level of the project.
# The 'targets' are usually all top level directories.
cookiecutter --directory code-formatter \
  --overwrite-if-exists \
  --config-file .cookiecutter-config.yaml \
  https://github.com/jkenlooper/cookiecutters.git
```
