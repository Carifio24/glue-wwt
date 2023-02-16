from __future__ import absolute_import, division, print_function

import io
import time
from qtpy import compat

from glue.viewers.common.tool import Tool, CheckableTool
from glue.utils.qt import get_qapp
from glue.config import viewer_tool

from glue.core import Data, Subset
from glue.core.subset import ElementSubsetState
from .image_layer import WWTImageLayerArtist
from .table_layer import WWTTableLayerArtist


@viewer_tool
class SaveTool(Tool):

    icon = 'glue_filesave'
    tool_id = 'wwt:save'
    action_text = 'Save the view to a file'
    tool_tip = 'Save the view to a file'

    def activate(self):

        filename, _ = compat.getsavefilename(caption='Save File',
                                             filters='PNG Files (*.png);;'
                                             'JPEG Files (*.jpeg);;'
                                             'TIFF Files (*.tiff);;',
                                             selectedfilter='PNG Files (*.png);;')

        # This indicates that the user cancelled
        if not filename:
            return

        self.viewer._wwt.render(filename)


SAVE_TOUR_CODE = """
function getViewAsTour() {

  // Get current view as XML and save to the tourxml variable

  wwtlib.WWTControl.singleton.createTour()
  editor = wwtlib.WWTControl.singleton.tourEdit
  editor.addSlide()
  tour = editor.get_tour()
  blb = tour.saveToBlob()

  const reader = new FileReader();

  reader.addEventListener('loadend', (e) => {
  const text = e.srcElement.result;
  tourxml += text;
  });

  // Start reading the blob as text.
  reader.readAsText(blb);

}

getViewAsTour()
"""


@viewer_tool
class SaveTourTool(Tool):

    icon = 'glue_filesave'
    tool_id = 'wwt:savetour'
    action_text = 'Save the view to a tour file'
    tool_tip = 'Save the view to a tour file'

    def activate(self):

        app = get_qapp()

        filename, _ = compat.getsavefilename(caption='Save File',
                                             basedir='mytour.wtt',
                                             filters='WWT Tour File (*.wtt);;',
                                             selectedfilter='WWT Tour File (*.wtt);;')

        # This indicates that the user cancelled
        if not filename:
            return

        if not filename.endswith('.wtt'):
            filename = filename + '.wtt'

        self.viewer._wwt.widget.page.runJavaScript("tourxml = '';", asynchronous=False)
        tourxml = self.viewer._wwt.widget.page.runJavaScript('tourxml;', asynchronous=False)

        self.viewer._wwt.widget.page.runJavaScript(SAVE_TOUR_CODE)

        start = time.time()
        tourxml = None
        while time.time() - start < 10:
            time.sleep(0.1)
            app.processEvents()
            tourxml = self.viewer._wwt.widget.page.runJavaScript('tourxml;', asynchronous=False)
            if tourxml:
                break

        if not tourxml:
            raise Exception("Failed to save tour")

        # Patch the altUnit so that it is correct for the Windows client (since
        # the web client currently has other bugs with relation to loading tours).
        # https://github.com/WorldWideTelescope/wwt-web-client/issues/248
        for unit_int in range(1, 11):
            altunit_str = 'AltUnit="{0}"'.format(unit_int)
            if altunit_str in tourxml:
                altunit_str_new = 'AltUnit="{0}"'.format(unit_int - 1)
                print('Changing {0} to {1} in {2}'.format(altunit_str, altunit_str_new, filename))
                tourxml = tourxml.replace(altunit_str, altunit_str_new)

        with io.open(filename, 'w', newline='') as f:
            f.write(tourxml)


@viewer_tool
class PointSourceSelectionTool(CheckableTool):
    icon = 'glue_filesave' # Use glue_point from glue-vispy-viewers
    tool_id = 'wwt:pointselect'
    action_text = 'Select point source(s)'
    tool_tip = 'Select point sources by clicking. Click a source again to remove it.'

    active_layer_artist = None

    def activate(self):
        # Get the values of the currently active layer artist - we
        # specifically pick the layer artist that is selected in the layer
        # artist view in the left since we have to pick one.
        layer_artist = self.viewer._view.layer_list.current_artist()

        # If the layer artist is for a Subset not Data, pick the first Data
        # one instead (where the layer artist is a volume artist)
        # We also want to make sure that the layer is a table layer
        if isinstance(layer_artist.layer, (Subset, WWTImageLayerArtist)):
            for layer_artist in self.iter_data_layer_artists():
                if isinstance(layer_artist, WWTTableLayerArtist) and isinstance(layer_artist.layer, Data):
                    break
            else:
                return

        self.active_layer_artist = layer_artist
        layer_artist.selectable = True

        def _get_index(self, item):
            data = self.active_layer_artist.layer
            return next((i for i in range(data.size) if all(data[c][i] == item[c] for c in data.main_components)), None)

        def on_selected(wwt, updated):
            if "most_recent_source" in updated:
                index = self._get_index(wwt.most_recent_source)
                new_state = ElementSubsetState([index], self.active_layer_artist.layer)
                self.viewer.apply_subset_state(new_state)

        wwt = self.viewer._wwt
        wwt.set_selection_change_callback(on_selected)

        return super().activate()

    def deactivate(self):
        if self.active_layer_artist is not None:
            self.active_layer_artist.selectable = False
        self.active_layer_artist = None
        return super().deactivate()
