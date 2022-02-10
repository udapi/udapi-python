"""DualDict is a dict with lazily synchronized string representation."""
import collections.abc
import copy


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

    A value can be deleted with any of the following three ways:
    >>> del ddict['Case']
    >>> ddict['Case'] = None
    >>> ddict['Case'] = ''
    and it works even if the value was already missing.
    """
    __slots__ = ['_string', '_dict']

    def __init__(self, value=None, **kwargs):
        if value is not None and kwargs:
            raise ValueError('If value is specified, no other kwarg is allowed ' + str(kwargs))
        self._dict = dict(**kwargs)
        self._string = None
        if value is not None:
            self.set_mapping(value)

    def __str__(self):
        if self._string is None:
            serialized = []
            for name, value in sorted(self._dict.items(), key=lambda s: s[0].lower()):
                if value is True:
                    serialized.append(name)
                else:
                    serialized.append(f"{name}={value}")
            self._string = '|'.join(serialized) if serialized else '_'
        return self._string

    def _deserialize_if_empty(self):
        if not self._dict and self._string is not None and self._string != '_':
            for raw_feature in self._string.split('|'):
                namevalue = raw_feature.split('=', 1)
                if len(namevalue) == 2:
                    name, value = namevalue
                else:
                    name, value = namevalue[0], True
                self._dict[name] = value

    def __getitem__(self, key):
        self._deserialize_if_empty()
        return self._dict.get(key, '')

    def __setitem__(self, key, value):
        self._deserialize_if_empty()
        self._string = None
        if value is not None and value != '':
            self._dict[key] = value
        else:
            self.__delitem__(key)

    def __delitem__(self, key):
        self._deserialize_if_empty()
        try:
            del self._dict[key]
            self._string = None
        except KeyError:
            pass

    def __iter__(self):
        self._deserialize_if_empty()
        return self._dict.__iter__()

    def __len__(self):
        self._deserialize_if_empty()
        return len(self._dict)

    def __contains__(self, key):
        self._deserialize_if_empty()
        return self._dict.__contains__(key)

    def clear(self):
        self._string = '_'
        self._dict.clear()

    def copy(self):
        """Return a deep copy of this instance."""
        return copy.deepcopy(self)

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
