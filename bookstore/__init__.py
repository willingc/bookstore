from ._version import __version__, version_info
from .archive import ArchiveRecord, BookstoreContentsArchiver
from .bookstore_config import BookstoreSettings
from .clone import BookstoreCloneHandler
from .handlers import BookstoreVersionHandler, load_jupyter_server_extension
from .publish import BookstorePublishHandler


def _jupyter_server_extension_paths():
    return [dict(module="bookstore")]
