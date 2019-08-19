# py-snap-collage
Small application that works like Window's snipping tool but can compile multiple images into one collage

There are many more things needed to be done:
## [Important]
* Positioning images in PyQt (This can be configured in [sorter.py](sorter.py))
* Clear images
* Right click on image to remove
* Left click on image to retake snip and replace that image with the new snip
* Rendering
  * Weird problem with rendering images, probably something to do with QGraphicsScene not filling window
  * Also need to handle how to display full image
  * Drag to move inspector
  * Scroll to zoom in

## [Not so important]
* Copy image to clipboard
* Save image
* Randomize collage
