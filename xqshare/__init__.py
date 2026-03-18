"""
XtQuant Share (xqshare) - Transparent remote proxy for xtquant library

Allows using xtquant on macOS/Linux by proxying calls to a Windows server.
"""

__version__ = "1.1.1"
__author__ = "Jason Hu"

from .client import (
    XtQuantRemote,
    connect,
    disconnect,
    get_client,
    xtdata,
    xttrader,
    xttype,
    xtview,
    ConnectionError,
    AuthenticationError,
    CallbackError,
)

__all__ = [
    "XtQuantRemote",
    "connect",
    "disconnect",
    "get_client",
    "xtdata",
    "xttrader",
    "xttype",
    "xtview",
    "ConnectionError",
    "AuthenticationError",
    "CallbackError",
]