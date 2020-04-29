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

media/puzzle-massive-logo-tertiary-on-background-accent--122.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format jpg -background "#F3EDFC" -flatten -alpha off -resize 122x $@;
media/puzzle-massive-logo-tertiary-on-background-accent--272.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format jpg -background "#F3EDFC" -flatten -alpha off -resize 272x $@;
media/puzzle-massive-logo-tertiary-on-background-accent--544.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format jpg -background "#F3EDFC" -flatten -alpha off -resize 544x $@;

media/puzzle-massive-logo-tertiary-on-dark--520.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format jpg -background "#000105" -flatten -alpha off -resize 520x $@;
media/puzzle-massive-logo-tertiary-on-dark--731.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format jpg -background "#000105" -flatten -alpha off -resize 731x $@;
media/puzzle-massive-logo-tertiary-on-dark--1040.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format jpg -background "#000105" -flatten -alpha off -resize 1040x $@;
media/puzzle-massive-logo-tertiary-on-dark--1462.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-blue-on-black.png
	convert $< -format jpg -background "#000105" -flatten -alpha off -resize 1462x $@;

media/puzzle-massive-logo-white-on-dark--520.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-white-on-black.png
	convert $< -format jpg -background "#000105" -flatten -alpha off -resize 520x $@;
media/puzzle-massive-logo-white-on-dark--731.jpg :  source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-white-on-black.png
	convert $< -format jpg -background "#000105" -flatten -alpha off -resize 731x $@;
media/puzzle-massive-logo-white-on-dark--1040.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-white-on-black.png
	convert $< -format jpg -background "#000105" -flatten -alpha off -resize 1040x $@;
media/puzzle-massive-logo-white-on-dark--1462.jpg : source-media/logo-puzzle-massive/puzzle-massive-logo-mosaic/puzzle-massive-logo-mosaic-white-on-black.png
	convert $< -format jpg -background "#000105" -flatten -alpha off -resize 1462x $@;
