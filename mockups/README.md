# Puzzle Massive Mockups

Directory that has mockup HTML files in order to quickly show the various
components that are used on the Puzzle Massive site. They are not directly used
when the site is compiled, but can be integrated back in as needed.

## How to Use

Use git to make a fork of this git repository hosted on GitHub. Edit the files
referenced in the mockups directory and save your changes. When all the changes
are ready, commit them and make a pull request.

Use the Docker application on your computer to run a tiny web server to serve
all the files in the puzzle-massive project directory. This method doesn't
require any compilation step and HTML pages in the mockups directory are
designed to load resources directly from the files in the project directory.

**The `docker` commands will serve the project directory on port 3000.**

```bash
# View the mockups directory.
# http://localhost:3000/mockups/

# From within the mockups/ directory build and run the docker image.
# A bindmount volume is used to serve the parent directory.
docker build -t puzzle-massive-mockups .
docker run -it --rm \
  -p 127.0.0.1:3000:3000 \
  -v "$(pwd)/..":/home/static \
  --name puzzle-massive-mockups \
  puzzle-massive-mockups
```
