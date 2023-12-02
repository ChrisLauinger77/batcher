"""Combo box widget for `Gimp.Item` objects."""

import collections
from typing import Optional

import gi
from gi.repository import GObject
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi

__all__ = [
  'GimpItemComboBox',
]


class GimpItemComboBox(Gtk.Box):
  """Class defining a GTK widget for `Gimp.Item` instances acting as an
  abstraction over GIMP objects - layers, channels and vectors.
  
  Signals:
    changed:
      The user changed the selection either in the combo box containing
      available item types or in the combo box for the selected item type.

      Signal arguments:
        selected_item: The currently selected `Gimp.Item` instance.
  """
  
  __gsignals__ = {'changed': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_PYOBJECT,))}
  
  _GimpItemComboBox = collections.namedtuple(
    '_GimpItemComboBox',
    ['name', 'widget', 'get_active_item_func', 'set_active_item_func', 'gimp_item_type'])
  
  _COMBO_BOX_SPACING = 4
  
  def __init__(self, constraint=None, data=None, **kwargs):
    super().__init__(
      homogeneous=False,
      orientation=Gtk.Orientation.HORIZONTAL,
      spacing=self._COMBO_BOX_SPACING,
      **kwargs,
    )
    
    self._layer_combo_box = GimpUi.LayerComboBox.new(constraint=constraint, data=data)
    self._channel_combo_box = GimpUi.ChannelComboBox.new(constraint=constraint, data=data)
    self._vectors_combo_box = GimpUi.VectorsComboBox.new(constraint=constraint, data=data)
    
    self._item_combo_boxes = [
      self._GimpItemComboBox(
        _('Layer'),
        self._layer_combo_box,
        self._layer_combo_box.get_active,
        self._layer_combo_box.set_active,
        Gimp.Layer),
      self._GimpItemComboBox(
        _('Channel'),
        self._channel_combo_box,
        self._channel_combo_box.get_active,
        self._channel_combo_box.set_active,
        Gimp.Channel),
      self._GimpItemComboBox(
        _('Vectors'),
        self._vectors_combo_box,
        self._vectors_combo_box.get_active,
        self._vectors_combo_box.set_active,
        Gimp.Vectors)]

    self._displayed_item_combo_box = self._item_combo_boxes[0]
    
    self._item_types_combo_box = Gtk.ComboBoxText.new()
    
    self.pack_start(self._item_types_combo_box, True, True, 0)
    
    for combo_box in self._item_combo_boxes:
      combo_box.widget.show_all()
      combo_box.widget.hide()
      combo_box.widget.set_no_show_all(True)
      
      self._item_types_combo_box.append_text(combo_box.name)
      
      self.pack_start(combo_box.widget, True, True, 0)
      
      combo_box.widget.connect(0, self._on_combo_box_changed)

    self._item_types_combo_box.connect('changed', self._on_item_types_combo_box_changed)
    
    self._item_types_combo_box.set_active(0)
  
  def get_active(self) -> Optional[int]:
    if self._displayed_item_combo_box is not None:
      return self._displayed_item_combo_box.get_active_item_func()
    else:
      return None

  def set_active(self, item_id: int):
    if not Gimp.Item.id_is_valid(item_id):
      return

    item = Gimp.Item.get_by_id(item_id)

    if item is None:
      return

    matching_index = 0

    for index, combo_box in enumerate(self._item_combo_boxes):
      if isinstance(item, combo_box.gimp_item_type):
        matching_combo_box = combo_box
        matching_index = index
        break
    else:
      matching_combo_box = None

    if matching_combo_box is None:
      raise TypeError(
        'argument must be one of the following types: {}'.format(
          ', '.join(str(combo_box.gimp_item_type) for combo_box in self._item_combo_boxes)))

    matching_combo_box.set_active_item_func(item_id)
    self._item_types_combo_box.set_active(matching_index)
  
  def _on_combo_box_changed(self, *args, **kwargs):
    self.emit('changed', self.get_active())
  
  def _on_item_types_combo_box_changed(self, combo_box):
    if self._displayed_item_combo_box is not None:
      self._displayed_item_combo_box.widget.hide()
    
    index = self._item_types_combo_box.get_active()
    self._item_combo_boxes[index].widget.show()
    
    self._displayed_item_combo_box = self._item_combo_boxes[index]
    
    self.emit('changed', self.get_active())


GObject.type_register(GimpItemComboBox)
