import io
import os
import sys

from mock import patch

from glue.core import ComponentLink, Data
from glue.core.tests.test_state import clone
from glue.tests.helpers import requires_qt

from .test_wwt_viewer import BaseTestWWTDataViewer, DATA


@requires_qt
class TestWWTQtViewer(BaseTestWWTDataViewer):

    from ..qt_data_viewer import WWTQtViewer
    class WWTQtViewerBlocking(WWTQtViewer):

        def _initialize_wwt(self):
            from pywwt.qt import WWTQtClient
            self._wwt = WWTQtClient(block_until_ready=sys.platform != 'win32')

    def setup_method(self, method):
        from glue_qt.app import GlueApplication
        self.d = Data(x=[1, 2, 3], y=[2, 3, 4], z=[4, 5, 6])
        self.ra_dec_data = Data(ra=[-10, 0, 10], dec=[0, 10, 20])
        self.bad_data_short = Data(x=[-100, 100], y=[-10, 10])
        self.bad_data_long = Data(x=[-100, -90, -80, 80, 90, 100], y=[-10, -7, -3, 3, 7, 10])
        self.application = GlueApplication()
        self.dc = self.application.data_collection
        self.dc.append(self.d)
        self.dc.append(self.ra_dec_data)
        self.dc.append(self.bad_data_short)
        self.dc.append(self.bad_data_long)
        self.dc.add_link(ComponentLink([self.d.id['x']], self.d.id['y']))
        self.hub = self.dc.hub
        self.session = self.application.session
        self.viewer = self.application.new_data_viewer(WWTQtViewerBlocking)
        self.options = self.viewer.options_widget()

    def teardown_method(self, method):
        self.viewer.close(warn=False)
        self.viewer = None
        self.application.close()
        self.application = None

    def test_clone(self):

        self.viewer.add_data(self.d)
        self.viewer.state.layers[0].ra_att = self.d.id['y']
        self.viewer.state.layers[0].dec_att = self.d.id['x']

        application2 = clone(self.application)

        application2.viewers[0][0]

    def test_load_session_back_compat(self):

        # Make sure that old session files continue to work

        app = GlueApplication.restore_session(os.path.join(DATA, 'wwt_simple.glu'))
        viewer_state = app.viewers[0][0].state
        assert viewer_state.lon_att.label == 'a'
        assert viewer_state.lat_att.label == 'b'
        assert viewer_state.frame == 'Galactic'

    # @pytest.mark.skipif(sys.platform == 'win32', reason="Test causes issues on Windows")
    @pytest.mark.xfail(reason="'asynchronous' keyword unsupported by some JavaScript versions")
    def test_save_tour(self, tmpdir):

        from qtpy import compat

        filename = tmpdir.join('mytour.wtt').strpath
        self.viewer.add_data(self.d)
        with patch.object(compat, 'getsavefilename', return_value=(filename, None)):
            self.viewer.toolbar.tools['save'].subtools[1].activate()

        assert os.path.exists(filename)
        with io.open(filename, newline='') as f:
            assert f.read().startswith("<?xml version='1.0' encoding='UTF-8'?>\r\n<FileCabinet")
