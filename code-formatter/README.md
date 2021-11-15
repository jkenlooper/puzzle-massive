```bash
docker build -f code-formatter.dockerfile \
  -t puzzle-massive-code-formatter \
  ./

docker run -it \
  --mount type=bind,src=$(pwd)/code-formatter/.last-modified,dst=/code/.last-modified \
  --mount type=bind,src=$(pwd)/api,dst=/code/api \
  --mount type=bind,src=$(pwd)/client-side-public/src,dst=/code/client-side-public/src \
  --mount type=bind,src=$(pwd)/design-tokens/src,dst=/code/design-tokens/src \
  --mount type=bind,src=$(pwd)/divulger,dst=/code/divulger \
  --mount type=bind,src=$(pwd)/docs,dst=/code/docs \
  --mount type=bind,src=$(pwd)/documents,dst=/code/documents \
  --mount type=bind,src=$(pwd)/enforcer,dst=/code/enforcer \
  --mount type=bind,src=$(pwd)/mockups,dst=/code/mockups \
  --mount type=bind,src=$(pwd)/queries,dst=/code/queries \
  --mount type=bind,src=$(pwd)/root,dst=/code/root \
  --mount type=bind,src=$(pwd)/stream,dst=/code/stream \
  --mount type=bind,src=$(pwd)/templates,dst=/code/templates \
  --name puzzle-massive-code-formatter \
  puzzle-massive-code-formatter \
  sh
```
