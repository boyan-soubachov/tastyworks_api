from tastyworks.dxfeed.mapped_item import MappedItem
import datetime


class Quote(MappedItem):
    DXFEED_TEXT = 'Quote'

    def _process_fields(self, data_dict: dict):
        for key in ('askTime', 'bidTime', 'time'):
            if key in data_dict:
                data_dict[key] = str(datetime.datetime.fromtimestamp(data_dict[key] / 1000))

        if 'timeNanos' in data_dict:
            data_dict['timeNanos'] = str(datetime.datetime.fromtimestamp(data_dict['timeNanos'] / 1000_000_000))
        return data_dict

    def __init__(self, data=None):
        super().__init__(data=data)
