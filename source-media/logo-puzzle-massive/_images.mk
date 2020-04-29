# Non-clever Makefile

.PHONY : all clean

objects = $(shell cat source-media/logo-puzzle-massive/_images.manifest)

all : $(objects)

clean :
	echo $(objects) | xargs rm -f

root/puzzle-massive-logo-600.png : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format png -resize 600x $@;

root/puzzle-massive-logo-600.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format jpg -background white -flatten -alpha off -resize 600x $@;

media/puzzle-massive-logo-600.png : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-white.png
	convert $< -format png -resize 600x $@;

media/puzzle-massive-logo-600.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-white.png
	convert $< -format jpg -background white -flatten -alpha off -resize 600x $@;

media/puzzle-massive-logo-blue-on-black--440.png : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	#convert $< -format png -resize 440x $@;
	convert $< -format png -resize 840x $@;

media/puzzle-massive-logo-darkblue-on-black--440.png : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-darkblue-on-black.png
	#convert $< -format png -resize 440x $@;
	convert $< -format png -resize 840x $@;

media/puzzle-massive-logo-blue-on-white--440.png : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-white.png
	convert $< -format png -resize 440x $@;
