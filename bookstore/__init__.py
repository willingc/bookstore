import os

from ._version import __version__, version_info
from .archive import ArchiveRecord, BookstoreContentsArchiver
from .bookstore_config import BookstoreSettings
from .clone import BookstoreCloneHandler
from .handlers import BookstoreVersionHandler, load_jupyter_server_extension
from .publish import BookstorePublishHandler

PACKAGE_DIR = os.path.realpath(os.path.dirname(__file__))
EXT_NAME = "bookstore"


def _jupyter_server_extension_paths():
    return [{"module": EXT_NAME}]
