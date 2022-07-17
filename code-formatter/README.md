# `puzzlemassive` Code Formatter

Reformats any code that is newer than files in
`./code-formatter/.last-modified/`

The below command will run [Prettier](https://prettier.io/) and
[Black](https://black.readthedocs.io/en/stable/) on the target directories.

```bash
# Run this makefile from the top level of the project:
make -f ./code-formatter/code-formatter.mk
```

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
