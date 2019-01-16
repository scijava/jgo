_major = 0
_minor = 4
_patch = 1
_extension = 'dev0'

_version_string = '%d.%d.%d%s' % (_major, _minor, _patch, _extension)

class Version(object):
    def major(self):
        return _major

    def minor(self):
        return _minor

    def patch(self):
        return _patch

    def extension(self):
        return _extension

    def __str__(self):
        return _version_string

_version = Version()
