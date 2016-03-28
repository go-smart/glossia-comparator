try:
    import pyroute2
except:
    pyroute2 = False

# With thanks to http://stackoverflow.com/questions/20908287/is-there-a-method-to-get-default-network-interface-on-local-using-python3
# User: svinota


def get_default_gateway():
    """Returns the default gateway of this machine (container).

    This method is primarily intended for use communicating with
    ad-hoc Glot HTTP servers for file transfer (not an intended
    application of WAMP, so an alternative approach must be used).

    """
    if not pyroute2:
        return None

    ip = pyroute2.IPDB()
    gateway = ip.routes['default']['gateway']
    ip.release()

    return gateway
