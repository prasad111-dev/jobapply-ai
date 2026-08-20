class Doc:
    """Attribute-access wrapper around a Mongo document dict.

    Lets existing router code use `user.id`, `user.skills`, `job.title`, etc.
    """

    def __init__(self, data: dict):
        object.__setattr__(self, "_data", data or {})

    def __getattr__(self, name):
        data = object.__getattribute__(self, "_data")
        if name in data:
            return data[name]
        return None

    def __setattr__(self, name, value):
        if name == "_data":
            object.__setattr__(self, name, value)
        else:
            object.__getattribute__(self, "_data")[name] = value

    def __getitem__(self, key):
        return object.__getattribute__(self, "_data")[key]

    def __setitem__(self, key, value):
        object.__getattribute__(self, "_data")[key] = value

    def __contains__(self, key):
        return key in object.__getattribute__(self, "_data")

    def get(self, key, default=None):
        return object.__getattribute__(self, "_data").get(key, default)

    @property
    def id(self):
        return object.__getattribute__(self, "_data").get("id")

    @property
    def as_dict(self):
        return dict(object.__getattribute__(self, "_data"))

    def __repr__(self):
        return f"Doc({object.__getattribute__(self, '_data')!r})"