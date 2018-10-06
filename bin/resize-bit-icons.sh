#!/bin/bash

for i in resources/bit-icons/*.png; do
convert $i -resize "64x64>" src/ui/media/bit-icons/64-${i:20};
done;
