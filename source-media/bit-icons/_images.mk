# Bit Icons Makefile
#
# Take any .png files in source-media/bit-icons/ directory and resize them to be
# 64 pixel square images and place in media/bit-icons/ directory.

.PHONY : all clean

objects := $(patsubst source-media/bit-icons/%, media/bit-icons/64-%, $(wildcard source-media/bit-icons/*.png))

all : $(objects)

clean :
	echo $(objects) | xargs rm -f

media/bit-icons/64-%.png : source-media/bit-icons/%.png
	convert $< -resize "64x64>" $@

