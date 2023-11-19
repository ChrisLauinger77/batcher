"""Placeholder objects replaced with real GIMP objects when calling GIMP PDB
procedures during batch processing.

The following placeholder objects are defined:

* `PLACEHOLDERS['current_image']` - The image currently being processed.

* `PLACEHOLDERS['current_layer']` - The layer currently being processed in the
  current image. This placeholder is used for PDB procedures containing
  `Gimp.Layer`, `Gimp.Drawable` or `Gimp.Item` parameters.

* `PLACEHOLDERS['background_layer']` - The layer positioned immediately after
  the currently processed layer.

* `PLACEHOLDERS['foreground_layer']` - The layer positioned immediately before
  the currently processed layer.
"""

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg

from src import background_foreground
from src.gui import placeholders as gui_placeholders


class _GimpObjectPlaceholder:
  
  def __init__(self, display_name, replacement_func):
    self._display_name = display_name
    self._replacement_func = replacement_func
  
  @property
  def display_name(self):
    return self._display_name
  
  def replace_args(self, *args):
    return self._replacement_func(*args)


def _get_current_image(batcher):
  return batcher.current_image


def _get_current_layer(batcher):
  return batcher.current_raw_item


_PLACEHOLDERS = {
  'current_image': _GimpObjectPlaceholder(_('Current Image'), _get_current_image),
  'current_layer': _GimpObjectPlaceholder(_('Current Layer'), _get_current_layer),
  'background_layer': _GimpObjectPlaceholder(
    _('Background Layer'), background_foreground.get_background_layer),
  'foreground_layer': _GimpObjectPlaceholder(
    _('Foreground Layer'), background_foreground.get_foreground_layer),
}


def get_replaced_arg(arg, batcher):
  """If `arg` is a placeholder object, returns a real object replacing the
  placeholder. Otherwise, `arg` is returned.
  
  Arguments after `args` are required arguments for actions and are used to
  determine the real object that replaces the placeholder.
  """
  try:
    placeholder = _PLACEHOLDERS[arg]
  except KeyError:
    raise ValueError('invalid placeholder value "{}"'.format(arg))
  else:
    return placeholder.replace_args(batcher)


#===============================================================================


class PlaceholderSetting(pg.setting.Setting):
   
  _ALLOWED_GUI_TYPES = [gui_placeholders.GimpObjectPlaceholdersComboBoxPresenter]
  _ALLOWED_PLACEHOLDERS = []
  
  @classmethod
  def get_allowed_placeholder_names(cls):
    """Returns a list of allowed names of placeholders for this setting class.
    """
    return list(cls._ALLOWED_PLACEHOLDERS)
  
  @classmethod
  def get_allowed_placeholders(cls):
    """Returns a list of allowed placeholder objects for this setting class.
    """
    return [
      placeholder for placeholder_name, placeholder in _PLACEHOLDERS.items()
      if placeholder_name in cls._ALLOWED_PLACEHOLDERS]
  
  def _init_error_messages(self):
    self.error_messages['invalid_value'] = _('Invalid placeholder.')
  
  def _validate(self, value):
    if value not in self._ALLOWED_PLACEHOLDERS:
      raise pg.setting.SettingValueError(
        pg.setting.value_to_str_prefix(value) + self.error_messages['invalid_value'])


class PlaceholderImageSetting(PlaceholderSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_image'
  _ALLOWED_PLACEHOLDERS = ['current_image']


class PlaceholderDrawableSetting(PlaceholderSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _ALLOWED_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


class PlaceholderLayerSetting(PlaceholderSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _ALLOWED_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


class PlaceholderItemSetting(PlaceholderSetting):
  
  _DEFAULT_DEFAULT_VALUE = 'current_layer'
  _ALLOWED_PLACEHOLDERS = ['current_layer', 'background_layer', 'foreground_layer']


PDB_TYPES_TO_PLACEHOLDER_SETTING_TYPES_MAP = {
  # FIXME: These are temporarily commented until a proper port to GIMP 3 API is done.
  # gimpenums.PDB_IMAGE: 'placeholder_image',
  # gimpenums.PDB_ITEM: 'placeholder_item',
  # gimpenums.PDB_DRAWABLE: 'placeholder_drawable',
  # gimpenums.PDB_LAYER: 'placeholder_layer',
}
