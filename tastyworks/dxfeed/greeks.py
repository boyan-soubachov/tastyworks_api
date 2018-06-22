from tastyworks.dxfeed.mapped_item import MappedItem


class Greeks(MappedItem):
    DXFEED_TEXT = 'Greeks'

    def __init__(self, data=None):
        super().__init__(data=data)
