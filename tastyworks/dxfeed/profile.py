from tastyworks.dxfeed.mapped_item import MappedItem


class Profile(MappedItem):
    DXFEED_TEXT = 'Profile'

    def __init__(self, data=None):
        super().__init__(data=data)
