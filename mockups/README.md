# Puzzle Massive Mockups

Directory that only contains HTML, CSS, and Javascript files in order to quickly
show the various components that are used on the Puzzle Massive site. They are
not directly used when the site is compiled, but can be integrated back in as
needed.

## How to Use

Use git to make a fork of this git repository hosted on GitHub. Open the
mockups directory in your web browser of choice. Edit the files and save your
changes. When all the changes are ready, commit them and make a pull request.

Or, if you have the Docker application on your computer, then you can use Docker to
run a tiny web server to serve these files in the mockups directory.

```bash
# Serve the mockups directory locally on port 3000.
# http://localhost:3000/

# From within the mockups/ directory build and run the docker image.
docker build -t puzzle-massive-mockups .
docker run -it --rm \
  -p 3000:3000 \
  -v "$(pwd)":/home/static \
  --name puzzle-massive-mockups \
  puzzle-massive-mockups
```

##
