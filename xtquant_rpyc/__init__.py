"""
XtQuant RPyC - Transparent remote proxy for xtquant library

Allows using xtquant on macOS/Linux by proxying calls to a Windows server.
"""

__version__ = "1.0.0"
__author__ = "Jason Hu"

from .client import (
    XtQuantRemote,
    connect,
    disconnect,
    get_client,
    xtdata,
    xttrader,
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
    "ConnectionError",
    "AuthenticationError",
    "CallbackError",
]