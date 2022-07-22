# `puzzlemassive` Quality Control

Reformats any file that is newer than the `./quality-control/.modified-files.tar`
file.

The below command will run [Prettier](https://prettier.io/) and
[Black](https://black.readthedocs.io/en/stable/) on the target directories.

```bash
# Run the code formatter shell script to reformat the source code.
# This script should be at the top level of the project:
./quality-control.sh
```

* TODO: Add in static code analysis tool like https://semgrep.dev/
* TODO: Finish integration with stylelint and eslint linting tools
* TODO: Add shellcheck


## Updating Generated Files

Run the cookiecutter command again to update any generated files with newer
versions from the [cookiecutter quality-control](https://github.com/jkenlooper/cookiecutters).

```bash
# From the top level of the project.
# The 'targets' are usually all top level directories.
cookiecutter --directory quality-control \
  --overwrite-if-exists \
  --config-file .cookiecutter-config.yaml \
  https://github.com/jkenlooper/cookiecutters.git
```
