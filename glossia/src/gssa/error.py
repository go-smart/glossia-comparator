from enum import Enum


# These are the canonical errors for client use - wherever possible, the most
# applicable of these should be returned. They indicate where the fault is
# likely to lie.
class Error(Enum):
    SUCCESS, E_UNKNOWN, E_CLIENT, E_SERVER, E_MODEL, IN_PROGRESS, E_CANCELLED = range(7)


class ErrorException(RuntimeError):
    _error = None

    def __init__(self, ref, message, *args, **kwargs):
        self._error = makeError(ref, message)
        super(self).__init__(*args, **kwargs)

    def get_error(self):
        return self._error


class ErrorMessage(dict):
    pass


# A full error message (as returned via WAMP) has an id, corresponding textual
# code and the message itself
def makeError(ref, message):
    id = ref.value if isinstance(ref, Error) else Error[ref].value
    code = ref.name if isinstance(ref, Error) else Error[ref].name

    return ErrorMessage({'id': id, 'code': code, 'message': message})
