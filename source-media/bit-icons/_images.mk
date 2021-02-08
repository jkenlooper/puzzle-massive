# Bit Icons Makefile
#
# Take any .png files in source-media/bit-icons/ directory and resize them to be
# 64 pixel square images and place in media/bit-icons/ directory.

.PHONY : all clean

bit_icons := $(patsubst source-media/bit-icons/%, media/bit-icons/64-%, $(wildcard source-media/bit-icons/*.png))

bit_icon_groups := $(patsubst source-media/bit-icons/source-%.yaml, media/bit-icons/group-%.jpg, $(wildcard source-media/bit-icons/source-*.yaml))

objects := $(bit_icons) $(bit_icon_groups)

all : $(objects)

clean :
	echo $(objects) | xargs rm -f

media/bit-icons/64-%.png : source-media/bit-icons/%.png
	convert $< -resize "64x64>" $@

media/bit-icons/group-%.jpg : source-media/bit-icons/source-%.yaml $(wildcard media/bit-icons/64-%-*.png)
	montage media/bit-icons/64-$*-*.png \
		-tile 18x \
		-geometry 32x32+1+1 \
		-background white \
		$@
	mogrify -trim +repage $@
