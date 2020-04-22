# Source Media

This directory holds the source images and other media files not directly
accessible from the website. The scripts to handle automatic cropping and
resizing of the source images and saving those to the `media/` directory are
placed here along with the source media files.

Any file ending with `.mk` is included when the `make` command is run. See the
`Makefile` in the project for more. The order of these can be shown by
inspecting the `source_media_mk` variable.

```bash
# Show the order that *.mk files in source-media will be used.
make inspect.source_media_mk;
```

See examples included in the
[jkenlooper/cookiecutter-website](https://github.com/jkenlooper/cookiecutter-website)
`source-media/` directory for more.
