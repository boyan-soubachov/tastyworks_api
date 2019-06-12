from tastyworks.dxfeed.mapped_item import MappedItem


class Summary(MappedItem):
    DXFEED_TEXT = 'Summary'

    def __init__(self, data=None):
        super().__init__(data=data)
