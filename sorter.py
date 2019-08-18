def sort(images):
    result = []
    prevItem = None

    for img in images:
        size = (img.width(), img.height())
        item = SortItem(img, size)
        if prevItem is not None:
            item.pos = (item.pos[0], prevItem.size[1] + prevItem.pos[1])

        result.append(item)
        prevItem = item

    return tuple(result)

class SortItem:
    def __init__(self, img, size=(0, 0), pos=(0, 0)):
        self.image = img
        self.size = size
        self.pos = pos