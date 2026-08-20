class Doc:
    """Attribute-access wrapper around a Mongo document dict.

    Lets existing router code use `user.id`, `user.skills`, `job.title`, etc.
    """

    __slots__ = ("_data",)

    def __init__(self, data: dict):
        self._data = data or {}

    def __getattr__(self, name):
        data = self.__dict__.get("_data", {})
        if name in data:
            return data[name]
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name == "_data":
            object.__setattr__(self, name, value)
        else:
            self._data[name] = value

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    @property
    def id(self):
        return self._data.get("id")

    @property
    def as_dict(self):
        return dict(self._data)

    def __repr__(self):
        return f"Doc({self._data!r})"