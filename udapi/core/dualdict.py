"""DualDict is a dict with lazily synchronized string representation."""
import collections.abc

class DualDict(collections.abc.MutableMapping):
    """DualDict class serves as dict with lazily synchronized string representation.

    >>> ddict = DualDict('Number=Sing|Person=1')
    >>> ddict['Case'] = 'Nom'
    >>> str(ddict)
    'Case=Nom|Number=Sing|Person=1'
    >>> ddict['NonExistent']
    ''

    This class provides access to both
    * a structured (dict-based, deserialized) representation,
      e.g. {'Number': 'Sing', 'Person': '1'}, and
    * a string (serialized) representation of the mapping, e.g. `Number=Sing|Person=1`.
    There is a clever mechanism that makes sure that users can read and write
    both of the representations which are always kept synchronized.
    Moreover, the synchronization is lazy, so the serialization and deserialization
    is done only when needed. This speeds up scenarios where access to dict is not needed.
    """
    __slots__ = ['_string', '_dict']

    def __init__(self, string=None, *args, **kwargs):
        if string is not None:
            if args:
                raise ValueError('If string is specified, no other arg is allowed ' + str(args))
            if kwargs:
                raise ValueError('If string is specified, no other kwarg is allowed ' +str(kwargs))
        self._dict = dict(args, **kwargs)
        self._string = string

    def __str__(self):
        if self._string is None:
            serialized = []
            for name in sorted(self._dict):
                serialized.append('%s=%s' % (name, self._dict[name]))
            self._string = '|'.join(serialized) if serialized else '_'
        return self._string

    def _deserialize_if_empty(self):
        if not self._dict and self._string is not None and self._string != '_':
            for raw_feature in self._string.split('|'):
                name, value = raw_feature.split('=')
                self._dict[name] = value

    def __getitem__(self, key):
        self._deserialize_if_empty()
        return self._dict.get(key, '')

    def __setitem__(self, key, value):
        self._deserialize_if_empty()
        self._string = None
        self._dict[key] = value

    def __delitem__(self, key):
        self._deserialize_if_empty()
        self._string = None
        del self._dict[key]

    def __iter__(self):
        self._deserialize_if_empty()
        return self._dict.__iter__()

    def __len__(self):
        self._deserialize_if_empty()
        return len(self._dict)

    def clear(self):
        self._string = '_'
        self._dict.clear()

    def set_mapping(self, value):
        """Set the mapping from a dict or string.

        If the `value` is None or an empty string, it is converted to storing string `_`
        (which is the CoNLL-U way of representing an empty value).
        If the `value` is a string, it is stored as is.
        If the `value` is a dict (or any instance of `collections.abc.Mapping`),
        its copy is stored.
        Other types of `value` raise an `ValueError` exception.
        """
        if value is None:
            self.clear()
        elif isinstance(value, str):
            self._dict.clear()
            self._string = value if value != '' else '_'
        elif isinstance(value, collections.abc.Mapping):
            self._string = None
            self._dict = dict(value)
        else:
            raise ValueError("Unsupported value type " + str(value))
