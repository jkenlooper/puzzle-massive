# Non-clever Makefile

.PHONY : all clean

small_pngs = source-media/favicon/.favicon-32x32.png source-media/favicon/.favicon-48x48.png source-media/favicon/.favicon-64x64.png

objects = $(shell cat source-media/favicon/_favicon.manifest) $(small_pngs)

all : $(objects)

clean :
	echo $(objects) | xargs rm -f

source-media/favicon/.favicon-32x32.png : source-media/favicon/paper-and-chalk-656x656.png
	convert $< -resize 32x32 $@;

source-media/favicon/.favicon-48x48.png : source-media/favicon/paper-and-chalk-656x656.png
	convert $< -resize 48x48 $@;

source-media/favicon/.favicon-64x64.png : source-media/favicon/paper-and-chalk-656x656.png
	convert $< -resize 64x64 $@;

root/favicon.ico : source-media/favicon/paper-and-chalk-16x16.png $(small_pngs)
	convert $^ $@;
