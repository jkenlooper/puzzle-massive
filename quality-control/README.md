# `puzzlemassive` Quality Control

Reformats any file that is newer than the `./quality-control/.modified-files.tar`
file.

The below command will run [Prettier](https://prettier.io/) and
[Black](https://black.readthedocs.io/en/stable/) on the target directories. The
configuration for this script is the '.quality-control-rc.json' file.

```bash
./qc.sh
```

Use the 'clean' makefile target in order to try reformatting all files again
without checking which are newer than the last time it was run.

```bash
./qc.sh clean
```

* TODO: Add in static code analysis tool like https://semgrep.dev/
* TODO: Finish integration with stylelint and eslint linting tools
* TODO: Add shellcheck?


## Updating Generated Files

* TODO: Push these changes back upstream to the original cookiecutter
    code-formatter.

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
