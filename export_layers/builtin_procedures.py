# -*- coding: utf-8 -*-

"""Built-in plug-in procedures."""

from __future__ import absolute_import, division, print_function, unicode_literals
from future.builtins import *

import collections

import gimp
from gimp import pdb
import gimpenums

from export_layers import pygimplib as pg

from export_layers import export as export_
from export_layers import renamer as renamer_
from export_layers import settings_custom


NAME_ONLY_TAG = 'name'


def set_active_layer(exporter):
  exporter.current_image.active_layer = exporter.current_raw_item


def set_active_layer_after_action(exporter):
  action_applied = yield
  
  if action_applied or action_applied is None:
    set_active_layer(exporter)


def copy_and_insert_layer(image, layer, parent=None, position=0, remove_lock_attributes=True):
  layer_copy = pg.pdbutils.copy_and_paste_layer(
    layer, image, parent, position, remove_lock_attributes)
  
  pdb.gimp_item_set_visible(layer_copy, True)
  
  if pdb.gimp_item_is_group(layer_copy):
    layer_copy = pg.pdbutils.merge_layer_group(layer_copy)
  
  return layer_copy


def autocrop_tagged_layer(exporter, tag):
  tagged_layer = exporter.inserted_tagged_layers[tag]
  if tagged_layer is not None:
    exporter.current_image.active_layer = tagged_layer
    pdb.plug_in_autocrop_layer(exporter.current_image, tagged_layer)
    return True
  else:
    return False


def remove_folder_hierarchy_from_item(exporter):
  item = exporter.current_item

  item.parents = []
  item.children = []


def insert_background_layer(exporter, tag):
  _insert_tagged_layer(exporter, tag, position=len(exporter.current_image.layers))


def insert_foreground_layer(exporter, tag):
  _insert_tagged_layer(exporter, tag, position=0)


def inherit_transparency_from_layer_groups(exporter):
  new_layer_opacity = exporter.current_raw_item.opacity / 100.0
  for parent in exporter.current_item.parents:
    new_layer_opacity = new_layer_opacity * (parent.raw.opacity / 100.0)
  
  exporter.current_raw_item.opacity = new_layer_opacity * 100.0


def rename_layer(exporter, pattern, rename_layers=True, rename_folders=False):
  renamer = renamer_.ItemRenamer(pattern)
  
  renamed_parents = set()
  
  while True:
    if rename_layers:
      exporter.current_item.name = renamer.rename(exporter)
    
    if rename_folders:
      for parent in exporter.current_item.parents:
        if parent not in renamed_parents:
          parent.name = renamer.rename(exporter, item=parent)
          renamed_parents.add(parent)
    
    unused_ = yield


def resize_to_layer_size(exporter):
  image = exporter.current_image
  layer = exporter.current_raw_item
  
  layer_offset_x, layer_offset_y = layer.offsets
  pdb.gimp_image_resize(image, layer.width, layer.height, -layer_offset_x, -layer_offset_y)


def _insert_tagged_layer(exporter, tag, position=0):
  image = exporter.current_image
  
  if not exporter.tagged_items[tag]:
    return
  
  if exporter.tagged_layer_copies[tag] is None:
    exporter.inserted_tagged_layers[tag] = _insert_merged_tagged_layer(
      image, exporter, tag, position)
    
    exporter.tagged_layer_copies[tag] = pdb.gimp_layer_copy(
      exporter.inserted_tagged_layers[tag], True)
    _remove_locks_from_layer(exporter.tagged_layer_copies[tag])
  else:
    exporter.inserted_tagged_layers[tag] = pdb.gimp_layer_copy(
      exporter.tagged_layer_copies[tag], True)
    _remove_locks_from_layer(exporter.inserted_tagged_layers[tag])
    pdb.gimp_image_insert_layer(image, exporter.inserted_tagged_layers[tag], None, position)


def _insert_merged_tagged_layer(image, exporter, tag, position=0):
  first_tagged_layer_position = position
  
  for i, item in enumerate(exporter.tagged_items[tag]):
    layer_copy = copy_and_insert_layer(image, item.raw, None, first_tagged_layer_position + i)
    layer_copy.visible = True
    exporter.invoker.invoke(['after_insert_item'], [exporter, layer_copy])
  
  if len(exporter.tagged_items[tag]) == 1:
    merged_layer_for_tag = image.layers[first_tagged_layer_position]
  else:
    second_to_last_tagged_layer_position = (
      first_tagged_layer_position + len(exporter.tagged_items[tag]) - 2)
    
    for i in range(second_to_last_tagged_layer_position, first_tagged_layer_position - 1, -1):
      merged_layer_for_tag = pdb.gimp_image_merge_down(
        image, image.layers[i], gimpenums.EXPAND_AS_NECESSARY)
  
  return merged_layer_for_tag


def _remove_locks_from_layer(layer):
  pdb.gimp_item_set_lock_content(layer, False)
  if not isinstance(layer, gimp.GroupLayer):
    pdb.gimp_item_set_lock_position(layer, False)
    pdb.gimp_layer_set_lock_alpha(layer, False)


_BUILTIN_PROCEDURES_LIST = [
  {
    'name': 'autocrop_background',
    'function': autocrop_tagged_layer,
    'display_name': _('Autocrop background'),
    'arguments': [
      {
        'type': pg.SettingTypes.string,
        'name': 'tag',
        'default_value': 'background',
      },
    ],
  },
  {
    'name': 'autocrop_foreground',
    'function': autocrop_tagged_layer,
    'display_name': _('Autocrop foreground'),
    'arguments': [
      {
        'type': pg.SettingTypes.string,
        'name': 'tag',
        'default_value': 'foreground',
      },
    ],
  },
  {
    'name': 'export',
    'function': export_.export,
    'display_name': _('Export'),
    'additional_tags': [NAME_ONLY_TAG],
    'arguments': [
      {
        'type': pg.SettingTypes.file_extension,
        'name': 'file_extension',
        'default_value': 'png',
        'display_name': _('File extension'),
        'gui_type': pg.SettingGuiTypes.file_extension_entry,
        'adjust_value': True,
      },
      {
        'type': pg.SettingTypes.enumerated,
        'name': 'export_mode',
        'default_value': 'each_layer',
        'items': [
          ('each_layer', _('Each layer'), export_.ExportModes.EACH_LAYER),
          ('each_top_level_layer_or_group',
           _('Each top-level layer or group'),
           export_.ExportModes.EACH_TOP_LEVEL_LAYER_OR_GROUP),
          ('entire_image_at_once',
           _('Entire image at once'),
           export_.ExportModes.ENTIRE_IMAGE_AT_ONCE),
        ],
        'display_name': _('Perform export for:'),
      },
      {
        'type': settings_custom.FilenamePatternSetting,
        'name': 'single_image_filename_pattern',
        'default_value': '[image name]',
        'display_name': _('Image filename pattern'),
        'gui_type': settings_custom.FilenamePatternEntryPresenter,
      },
      {
        'type': pg.SettingTypes.boolean,
        'name': 'use_file_extension_in_item_name',
        'default_value': False,
        'display_name': _('Use file extension in layer name'),
        'gui_type': pg.SettingGuiTypes.check_button_no_text,
      },
      {
        'type': pg.SettingTypes.boolean,
        'name': 'convert_file_extension_to_lowercase',
        'default_value': False,
        'display_name': _('Convert file extension to lowercase'),
        'gui_type': pg.SettingGuiTypes.check_button_no_text,
      },
    ],
  },
  {
    'name': 'ignore_folder_structure',
    'function': remove_folder_hierarchy_from_item,
    'display_name': _('Ignore folder structure'),
    'additional_tags': [NAME_ONLY_TAG],
  },
  {
    'name': 'insert_background_layers',
    'function': insert_background_layer,
    'display_name': _('Insert background layers'),
    'arguments': [
      {
        'type': pg.SettingTypes.string,
        'name': 'tag',
        'default_value': 'background',
      },
    ],
  },
  {
    'name': 'insert_foreground_layers',
    'function': insert_foreground_layer,
    'display_name': _('Insert foreground layers'),
    'arguments': [
      {
        'type': pg.SettingTypes.string,
        'name': 'tag',
        'default_value': 'foreground',
      },
    ],
  },
  {
    'name': 'inherit_transparency_from_layer_groups',
    'function': inherit_transparency_from_layer_groups,
    'display_name': _('Inherit transparency from layer groups'),
  },
  {
    'name': 'rename_layer',
    'function': rename_layer,
    'display_name': _('Rename layer'),
    'additional_tags': [NAME_ONLY_TAG],
    'arguments': [
      {
        'type': settings_custom.FilenamePatternSetting,
        'name': 'pattern',
        'default_value': '[layer name]',
        'display_name': _('Layer filename pattern'),
        'gui_type': settings_custom.FilenamePatternEntryPresenter,
      },
      {
        'type': pg.SettingTypes.boolean,
        'name': 'rename_layers',
        'default_value': True,
        'display_name': _('Rename layers'),
        'gui_type': pg.SettingGuiTypes.check_button_no_text,
      },
      {
        'type': pg.SettingTypes.boolean,
        'name': 'rename_folders',
        'default_value': False,
        'display_name': _('Rename folders'),
        'gui_type': pg.SettingGuiTypes.check_button_no_text,
      },
    ],
  },
  {
    'name': 'use_layer_size',
    'function': resize_to_layer_size,
    'display_name': _('Use layer size'),
  },
]

BUILTIN_PROCEDURES = collections.OrderedDict(
  (action_dict['name'], action_dict) for action_dict in _BUILTIN_PROCEDURES_LIST)
