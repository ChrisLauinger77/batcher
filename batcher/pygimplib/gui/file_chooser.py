"""Widget for choosing a single file or folder."""

from typing import Union

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
from gi.repository import Gio
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Pango

__all__ = [
  'FileChooser',
]


class FileChooser(Gtk.Box):
  """Class defining a GTK widget for choosing a single file or folder.

  Signals:
    changed:
      The user changed the selected file or folder.

      Signal arguments:
        selected_file: The currently selected file as a `GFile` instance.
  """

  __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, (Gio.File,))}

  def __init__(self, file_action, initial_value=None, title='', width_chars=30, *args, **kwargs):
    super().__init__(*args, **kwargs)

    self.set_orientation(Gtk.Orientation.HORIZONTAL)

    self._text_entry = None
    self._file_chooser_open = None
    self._folder_chooser_select = None
    self._file_chooser_save = None

    # We allow the use of `Gimp.FileChooserAction.ANY`, for which we need to
    # create a separate widget (a plain text entry since it is unknown
    # whether the user wants open or save files or folders).
    # Also, we use custom widgets for selecting a file or folder for opening.
    # It seems that the native file dialog on Windows causes the plug-in to
    # freeze for some reason.
    if file_action == Gimp.FileChooserAction.ANY:
      self._widget_type = 'text_entry'

      if initial_value is not None and initial_value.get_path() is not None:
        initial_text = initial_value.get_path()
      else:
        initial_text = ''

      self._text_entry = Gtk.Entry(text=initial_text)
      self._text_entry.set_position(-1)

      self._text_entry.connect('changed', self._emit_changed_event)

      self.pack_start(self._text_entry, False, False, 0)
    elif file_action == Gimp.FileChooserAction.OPEN:
      self._widget_type = 'file_chooser_open'

      self._file_chooser_open = self._create_file_chooser_button_for_opening(
        file_action, initial_value, title, width_chars)

      self.pack_start(self._file_chooser_open, False, False, 0)
    elif file_action == Gimp.FileChooserAction.SELECT_FOLDER:
      self._widget_type = 'folder_chooser_select'

      self._folder_chooser_select = self._create_file_chooser_button_for_opening(
        file_action, initial_value, title, width_chars)

      self.pack_start(self._folder_chooser_select, False, False, 0)
    else:
      self._widget_type = 'file_chooser_save'

      self._file_chooser_save = GimpUi.FileChooser(
        action=file_action,
        title=title,
        file=initial_value,
      )
      self._file_chooser_save.get_children()[1].connect('notify::text', self._emit_changed_event)

      self.pack_start(self._file_chooser_save, False, False, 0)

    self.show_all()

  def _create_file_chooser_button_for_opening(
        self, file_action, initial_value, title, width_chars):
    button = Gtk.FileChooserButton(
      title=title,
      action=file_action,
    )

    if initial_value is not None:
      button.set_file(initial_value)

    self._set_width_chars(button, width_chars)

    button.connect('file-set', self._emit_changed_event)

    return button

  @staticmethod
  def _set_width_chars(button, width_chars):
    combo_box = next(iter(child for child in button if isinstance(child, Gtk.ComboBox)), None)

    if combo_box is not None:
      cell_renderer = next(
        iter(cr for cr in combo_box.get_cells() if isinstance(cr, Gtk.CellRendererText)), None)

      if cell_renderer is not None:
        # This should force each row to not take extra vertical space after
        # reducing the number of characters to render.
        cell_renderer.set_property(
          'height', cell_renderer.get_preferred_height(combo_box).natural_size)

        cell_renderer.set_property('max-width-chars', width_chars)
        cell_renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
        cell_renderer.set_property('wrap-width', -1)

  def _emit_changed_event(self, *_args, **_kwargs):
    self.emit('changed', self.get_file())

  def get_file(self) -> Union[Gio.File, None]:
    if self._widget_type == 'file_chooser_save':
      return self._file_chooser_save.get_file()
    elif self._widget_type == 'file_chooser_open':
      return self._file_chooser_open.get_file()
    elif self._widget_type == 'folder_chooser_select':
      return self._folder_chooser_select.get_file()
    elif self._widget_type == 'text_entry':
      return Gio.file_new_for_path(self._text_entry.get_text())

    return None

  def set_file(self, file_or_path: Union[Gio.File, str, None]):
    if file_or_path is None:
      file_ = Gio.file_new_for_path('')
    elif isinstance(file_or_path, str):
      file_ = Gio.file_new_for_path(file_or_path)
    else:
      file_ = file_or_path

    if self._widget_type == 'file_chooser_save':
      self._file_chooser_save.set_file(file_)
    elif self._widget_type == 'file_chooser_open':
      self._file_chooser_open.set_file(file_)
    elif self._widget_type == 'folder_chooser_select':
      self._folder_chooser_select.set_file(file_)
    elif self._widget_type == 'text_entry':
      self._text_entry.set_text(file_.get_path() if file_.get_path() is not None else '')
      # Place the cursor at the end of the text entry.
      self._text_entry.set_position(-1)


GObject.type_register(FileChooser)
