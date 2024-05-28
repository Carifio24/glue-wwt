from __future__ import absolute_import, division, print_function

from .version import __version__  # noqa


def setup_qt():
    # The following needs to be imported before the application is constructed
    from qtpy.QtWebEngineWidgets import QWebEnginePage  # noqa
    from .viewer.qt_data_viewer import WWTQtViewer
    from glue.config import qt_client

    qt_client.add(WWTQtViewer)


def setup():
    try:
        setup_qt()
    except:
        pass
