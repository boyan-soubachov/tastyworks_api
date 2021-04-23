import abc
import logging

from tastyworks.dxfeed import mapper as mapper

LOGGER = logging.getLogger(__name__)


class MappedItem(object):
    __metaclass__ = abc.ABCMeta

    DXFEED_TEXT = None

    def _map_data(self, data) -> list:
        first_sample = True
        if isinstance(data[0], str):
            first_sample = False

        if first_sample:
            if data[0][0] != self.DXFEED_TEXT:
                raise Exception('Input JSON data does not contain a quote')
        else:
            if data[0] != self.DXFEED_TEXT:
                raise Exception('Input JSON data does not contain a quote')

        if first_sample:
            keys = data[0][1]
            # NOTE: I know this is dirty. Technical debt.
            # Stores the list of keys from the first sample since
            # subsequent ones only provide values
            mapper.KEY_MAP[self.DXFEED_TEXT] = keys
        else:
            keys = mapper.KEY_MAP[self.DXFEED_TEXT]

        res = []
        values = data[1]
        # if we have a 'multi-sample' i.e. several items subscribed to
        multiples = len(values) / len(keys)
        if not multiples.is_integer():
            raise Exception('Mapper data input values are not an integer multiple of the key size')
        for i in range(int(multiples)):
            offset = i * len(keys)
            local_values = values[offset:(i + 1) * len(keys)]
            res.append(self._process_fields(dict(zip(keys, local_values))))
        return res

    def _process_fields(self, data_dict: dict):
        """
        Used to post-process fields in the element's dictionary.
        e.g. convert Unix time to datetimes
        """
        return data_dict

    def __init__(self, data=None):
        if data:
            self.data = self._map_data(data)
        self.keys = None


'''
  POPULAR_INDICES_MAPPING = {
    SPX: '$SPX',
    SPXW: '$SPX',
    SPXPM: '$SPXPM',
    VIX: '$VIX',
    VIXW: '$VIX',
    MNX: '$MNX.X',
    OEX: '$OEX.X',
    DJX: '$DJX.X',
    DJI: '$DJX.X',
    RUT: '$RUT'
  };

  XCBT = 'XCBT';
  XCME = 'XCME';
  XNYM = 'XNYM';
  XCEC = 'XCEC';
  XCBF = 'XCBF';

  FUTURES_EXCHANGE_MAPPING = {
    '/ZB': XCBT,
    '/ZN': XCBT,
    '/ZF': XCBT,
    '/ZT': XCBT,
    '/UB': XCBT,
    '/GE': XCME,
    '/6A': XCME,
    '/6B': XCME,
    '/6C': XCME,
    '/6E': XCME,
    '/6J': XCME,
    '/6M': XCME,
    '/ZC': XCBT,
    '/ZS': XCBT,
    '/ZW': XCBT,
    '/HE': XCBT,
    '/CL': XNYM,
    '/NG': XNYM,
    '/GC': XCEC,
    '/SI': XCEC,
    '/HG': XCEC,
    '/ES': XCME,
    '/NQ': XCME,
    '/YM': XCBT,
    '/RTY': XCME,
    '/VX': XCBF,
    '/VXM': XCBF,
    '/BTC': XCME
  };
  '''