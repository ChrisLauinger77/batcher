# -*- coding: utf-8 -*-

"""Built-in plug-in procedures."""

from __future__ import absolute_import, division, print_function, unicode_literals
from future.builtins import *

import collections

import gimp
from gimp import pdb

from export_layers import pygimplib as pg

from export_layers import background_foreground
from export_layers import export as export_
from export_layers import renamer as renamer_
from export_layers import settings_custom


NAME_ONLY_TAG = 'name'


def set_active_and_current_layer(batcher):
  if pdb.gimp_item_is_valid(batcher.current_raw_item):
    batcher.current_image.active_layer = batcher.current_raw_item
  else:
    if pdb.gimp_item_is_valid(batcher.current_image.active_layer):
      # The active layer may have been set by the procedure.
      batcher.current_raw_item = batcher.current_image.active_layer
    else:
      if len(batcher.current_image.layers) > 0:
        # We cannot make a good guess of what layer is the "right" one, so we
        # resort to taking the first.
        first_layer = batcher.current_image.layers[0]
        batcher.current_raw_item = first_layer
        batcher.current_image.active_layer = first_layer
      else:
        # There is nothing we can do. An exception may be raised if a procedure
        # requires an active layer/at least one layer. An empty image could
        # occur e.g. if all layers were removed by the previous procedures.
        pass


def set_active_and_current_layer_after_action(batcher):
  action_applied = yield
  
  if action_applied or action_applied is None:
    set_active_and_current_layer(batcher)


def sync_item_name_and_raw_item_name(batcher):
  yield
  
  if batcher.process_names and not batcher.is_preview:
    batcher.current_item.name = batcher.current_raw_item.name


def remove_locks_before_action_restore_locks_after_action(batcher):
  # We assume `edit_mode` is True, we can therefore safely use `Item.raw`
  # instead of `current_raw_item`. We need to use `Item.raw` for parents as
  # well.
  item = batcher.current_item
  is_item_group = isinstance(item.raw, gimp.GroupLayer)
  locks_content = {}
  
  for item_or_parent in [item] + item.parents:
    if pdb.gimp_item_is_valid(item_or_parent.raw):
      locks_content[item_or_parent] = pdb.gimp_item_get_lock_content(item_or_parent.raw)
  if not is_item_group and pdb.gimp_item_is_valid(item.raw):
    lock_position = pdb.gimp_item_get_lock_position(item.raw)
    lock_alpha = pdb.gimp_layer_get_lock_alpha(item.raw)
  else:
    lock_position = None
    lock_alpha = None
  
  for item_or_parent, lock_content in locks_content.items():
    if lock_content:
      pdb.gimp_item_set_lock_content(item_or_parent.raw, False)
  if not is_item_group:
    if lock_position:
      pdb.gimp_item_set_lock_position(item.raw, False)
    if lock_alpha:
      pdb.gimp_layer_set_lock_alpha(item.raw, False)
  
  yield
  
  for item_or_parent, lock_content in locks_content.items():
    if lock_content and pdb.gimp_item_is_valid(item_or_parent.raw):
      pdb.gimp_item_set_lock_content(item_or_parent.raw, lock_content)
  if not is_item_group and pdb.gimp_item_is_valid(item.raw):
    if lock_position:
      pdb.gimp_item_set_lock_position(item.raw, lock_position)
    if lock_alpha:
      pdb.gimp_layer_set_lock_alpha(item.raw, lock_alpha)


def remove_folder_hierarchy_from_item(batcher):
  item = batcher.current_item

  item.parents = []
  item.children = []


def inherit_transparency_from_layer_groups(batcher):
  new_layer_opacity = batcher.current_raw_item.opacity / 100.0
  for parent in batcher.current_item.parents:
    new_layer_opacity = new_layer_opacity * (parent.raw.opacity / 100.0)
  
  batcher.current_raw_item.opacity = new_layer_opacity * 100.0


def rename_layer(batcher, pattern, rename_layers=True, rename_folders=False):
  renamer = renamer_.ItemRenamer(pattern)
  renamed_parents = set()
  
  while True:
    if rename_layers:
      batcher.current_item.name = renamer.rename(batcher)
    
    if rename_folders:
      for parent in batcher.current_item.parents:
        if parent not in renamed_parents:
          parent.name = renamer.rename(batcher, item=parent)
          renamed_parents.add(parent)
    
    if batcher.process_names and not batcher.is_preview:
      batcher.current_raw_item.name = batcher.current_item.name
    
    yield


def resize_to_layer_size(batcher):
  image = batcher.current_image
  layer = batcher.current_raw_item
  
  layer_offset_x, layer_offset_y = layer.offsets
  pdb.gimp_image_resize(image, layer.width, layer.height, -layer_offset_x, -layer_offset_y)


_BUILTIN_PROCEDURES_LIST = [
  {
    'name': 'export',
    'function': export_.export,
    'display_name': _('Export'),
    'additional_tags': [NAME_ONLY_TAG],
    'display_options_on_create': True,
    'arguments': [
      {
        'type': pg.SettingTypes.directory,
        'name': 'output_directory',
        'default_value': gimp.user_directory(1),  # `Documents` directory
        'display_name': _('Output folder'),
        'gui_type': pg.setting.SettingGuiTypes.folder_chooser_button,
      },
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
          ('each_layer', _('For each layer'), export_.ExportModes.EACH_LAYER),
          ('each_top_level_layer_or_group',
           _('For each top-level layer or group'),
           export_.ExportModes.EACH_TOP_LEVEL_LAYER_OR_GROUP),
          ('entire_image_at_once',
           _('For the entire image at once'),
           export_.ExportModes.ENTIRE_IMAGE_AT_ONCE),
        ],
        'display_name': _('Perform export:'),
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
      {
        'type': pg.SettingTypes.boolean,
        'name': 'preserve_layer_name_after_export',
        'default_value': False,
        'display_name': _('Preserve layer name after export'),
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
    'name': 'inherit_transparency_from_layer_groups',
    'function': inherit_transparency_from_layer_groups,
    'display_name': _('Inherit transparency from layer groups'),
  },
  {
    'name': 'insert_background_layers',
    'function': background_foreground.insert_background_layer,
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
    'function': background_foreground.insert_foreground_layer,
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
    'name': 'rename',
    'function': rename_layer,
    'display_name': _('Rename'),
    'additional_tags': [NAME_ONLY_TAG],
    'display_options_on_create': True,
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
