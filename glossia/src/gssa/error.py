from enum import Enum


class Error(Enum):
    """Go-Smart error families.

    These are the canonical errors for client use - wherever possible, the most
    applicable of these should be returned. They indicate where the fault is
    likely to lie.

    """
    SUCCESS, E_UNKNOWN, E_CLIENT, E_SERVER, E_MODEL, IN_PROGRESS, E_CANCELLED = range(7)


class ErrorException(RuntimeError):
    """An exception wrapping :py:class:`~gssa.error.Error`."""
    _error = None

    def __init__(self, ref, message, *args, **kwargs):
        self._error = makeError(ref, message)
        super(self).__init__(*args, **kwargs)

    def get_error(self):
        return self._error


class ErrorMessage(dict):
    """A trivial subclass of dict marking an ErrorMessage."""
    pass


def makeError(ref, message):
    """A full error message (as returned via WAMP).

    Args:
        ref (gssa.error.Error|str): a enum (or enum name)
            to categorize the error.
        message (str): free-form error information string.

    Returns:
        :py:class:`~gssa.error.ErrorMessage`: a dictionary with entries
            ``id`` (int), ``code`` (str) and ``message``. The former
            two are representations of the :py:class:`~gssa.error.Error`
            enum, the integer (ordinal) value and string name respectively.

    """

    id = ref.value if isinstance(ref, Error) else Error[ref].value
    code = ref.name if isinstance(ref, Error) else Error[ref].name

    return ErrorMessage({'id': id, 'code': code, 'message': message})
