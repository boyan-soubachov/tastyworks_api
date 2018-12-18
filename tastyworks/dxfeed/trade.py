from tastyworks.dxfeed.mapped_item import MappedItem


class Trade(MappedItem):
    DXFEED_TEXT = 'Trade'

    def __init__(self, data=None):
        super().__init__(data=data)
