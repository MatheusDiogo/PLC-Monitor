import socket


def resolve_hostname(ip, timeout=0.3):
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        name, _, _ = socket.gethostbyaddr(ip)
        return name.split(".")[0]
    except Exception:
        return "-"
    finally:
        socket.setdefaulttimeout(old_timeout)
