from glue.core import Data
from glue_jupyter import JupyterApplication

from .test_wwt_viewer import BaseTestWWTDataViewer
from ..jupyter_viewer import WWTJupyterViewer


class TestWWTJupyterViewer(BaseTestWWTDataViewer):

    def setup_method(self, method):
        self.d = Data(x=[1, 2, 3], y=[2, 3, 4], z=[4, 5, 6])
        self.ra_dec_data = Data(ra=[-10, 0, 10], dec=[0, 10, 20])
        self.bad_data_short = Data(x=[-100, 100], y=[-10, 10])
        self.bad_data_long = Data(x=[-100, -90, -80, 80, 90, 100], y=[-10, -7, -3, 3, 7, 10])
        self.application = JupyterApplication()
        self.dc = self.application.data_collection
        self.dc.append(self.d)
        self.dc.append(self.ra_dec_data)
        self.dc.append(self.bad_data_short)
        self.dc.append(self.bad_data_long)
        self.application.add_link(self.d, self.d.id['x'], self.d, self.d.id['y'])
        self.hub = self.dc.hub
        self.session = self.application.session
        self.viewer = self.application.new_data_viewer(WWTJupyterViewer)
        self.options = self.viewer.options_widget()

    def teardown_method(self, method):
        self.viewer.close(warn=False)
        self.viewer = None
        # TODO: Do we need to close the Jupyter application here?

    def test_clone(self):

        self.viewer.add_data(self.d)
        self.viewer.state.layers[0].ra_att = self.d.id['y']
        self.viewer.state.layers[0].dec_att = self.d.id['x']

        application2 = clone(self.application)
        application2.viewers[0]

    def test_load_session_back_compat(self):

        # Make sure that old session files continue to work

        app = JupyterApplication.restore_session(os.path.join(DATA, 'wwt_simple.glu'))
        viewer_state = app.viewers[0].state
        assert viewer_state.lon_att.label == 'a'
        assert viewer_state.lat_att.label == 'b'
        assert viewer_state.frame == 'Galactic'
