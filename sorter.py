def sort(images):
    result = []
    prevItem = None

    i = 0
    total_x = 0
    total_y = 0

    for img in images:
        size = (img.width(), img.height())
        item = SortItem(img, size)
        
        if prevItem is not None:
            _item = prevItem
            item.pos = (_item.size[0] + _item.pos[0], item.pos[1])

        result.append(item)
        prevItem = item
        
        i += 1

    return [
        tuple(result),
        (total_x, total_y)
    ]

class SortItem:
    def __init__(self, img, size=(0, 0), pos=(0, 0)):
        self.image = img
        self.size = size
        self.pos = pos