# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals
from future.builtins import *

import collections

import unittest

import mock

from export_layers import pygimplib as pg

from export_layers.pygimplib.tests import stubs_gimp

from export_layers import settings_custom


def _get_images_and_items():
  image_1 = stubs_gimp.ImageStub(ID=1, filename='filename_1')
  image_2 = stubs_gimp.ImageStub(ID=2, filename='filename_2')
  
  images = [image_1, image_2]
  
  item_4 = stubs_gimp.LayerGroupStub(name='item_4', ID=4, image=image_1)
  item_1 = stubs_gimp.LayerStub(name='item_1', ID=1, image=image_1)
  item_3 = stubs_gimp.LayerStub(name='item_3', ID=3, image=image_1, parent=item_4)
  item_7 = stubs_gimp.LayerGroupStub(name='item_7', ID=7, image=image_2)
  item_5 = stubs_gimp.LayerStub(name='item_5', ID=5, image=image_2, parent=item_7)
  
  image_1.layers = [item_1, item_4]
  item_4.children = [item_3]
  image_2.layers = [item_7]
  item_7.children = [item_5]
  
  items = [item_1, item_3, item_4, item_5, item_7]
  
  return images, items


def _get_images_and_items_with_ids():
  images, items = _get_images_and_items()
  
  # `None` indicates invalid images/items that must not be in the expected data.
  images = [images[0], images[1], None]
  items = [items[0], items[1], items[2], items[3], None, items[4], None, None, None]
  
  return images, items


def _get_images_and_items_with_paths():
  images, unused_ = _get_images_and_items()
  
  images = [[images[0]], [images[1]], []]
  
  return images


class TestImagesAndGimpItemsSetting(unittest.TestCase):
  
  def setUp(self):
    self.setting = settings_custom.ImagesAndGimpItemsSetting('selected_layers')
    
    self.maxDiff = None
  
  def test_set_value_from_ids(self):
    images, items = _get_images_and_items_with_ids()
    
    with mock.patch('export_layers.settings_custom.gimp.Item') as temp_mock_gimp_item_module:
      with mock.patch(
            pg.utils.get_pygimplib_module_path() + '.pdbutils.gimp') as temp_mock_gimp_module:
        temp_mock_gimp_module._id2image.side_effect = images
        temp_mock_gimp_item_module.from_id.side_effect = items
      
        self.setting.set_value(
          {1: [1, 3, (4, 'folder')], 2: [5, (6, 'folder'), [7, 'folder'], 8], 3: [9, 10]})
    
    expected_value = collections.defaultdict(set)
    expected_value[1] = set([1, 3, (4, 'folder')])
    expected_value[2] = set([5, (7, 'folder')])
    
    self.assertEqual(self.setting.value, expected_value)

  def test_set_value_from_paths(self):
    images = _get_images_and_items_with_paths()
    
    with mock.patch(
          pg.utils.get_pygimplib_module_path() + '.pdbutils.gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.image_list.side_effect = images
      temp_mock_gimp_module.Layer = stubs_gimp.GimpModuleStub.Layer
      temp_mock_gimp_module.GroupLayer = stubs_gimp.GimpModuleStub.GroupLayer
    
      self.setting.set_value(
        {'filename_1': [
          ('Layer', 'item_1'),
          ('Layer', 'item_4/item_3'),
          ('GroupLayer', 'item_4', 'folder')],
         'filename_2': [
          ('Layer', 'item_7/item_5'),
          ('GroupLayer', 'item_6', 'folder'),
          ('GroupLayer', 'item_7', 'folder'),
          ('Layer', 'item_8')],
         'filename_3': [
           ('Layer', 'item_9'),
           ('Layer', 'item_10')]})
    
    expected_value = collections.defaultdict(set)
    expected_value[1] = set([1, 3, (4, 'folder')])
    expected_value[2] = set([5, (7, 'folder')])
    
    self.assertEqual(self.setting.value, expected_value)
  
  def test_set_value_invalid_list_length_raises_error(self):
    images, items = _get_images_and_items_with_ids()
    
    with mock.patch('export_layers.settings_custom.gimp.Item') as temp_mock_gimp_item_module:
      with mock.patch(
            pg.utils.get_pygimplib_module_path() + '.pdbutils.gimp') as temp_mock_gimp_module:
        temp_mock_gimp_module._id2image.side_effect = images
        temp_mock_gimp_item_module.from_id.side_effect = items
        
        with self.assertRaises(ValueError):
          self.setting.set_value(
            {1: [1, 3, (4, 'folder', 'extra_item_1', 'extra_item_2')]})
  
  def test_set_value_invalid_collection_type_for_items_raises_error(self):
    images, items = _get_images_and_items_with_ids()
    
    with mock.patch('export_layers.settings_custom.gimp.Item') as temp_mock_gimp_item_module:
      with mock.patch(
            pg.utils.get_pygimplib_module_path() + '.pdbutils.gimp') as temp_mock_gimp_module:
        temp_mock_gimp_module._id2image.side_effect = images
        temp_mock_gimp_item_module.from_id.side_effect = items
        
        with self.assertRaises(TypeError):
          self.setting.set_value(
            {1: object()})
  
  def test_to_dict_with_ids(self):
    images, items = _get_images_and_items_with_ids()
    
    with mock.patch('export_layers.settings_custom.gimp.Item') as temp_mock_gimp_item_module:
      with mock.patch(
            pg.utils.get_pygimplib_module_path() + '.pdbutils.gimp') as temp_mock_gimp_module:
        temp_mock_gimp_module._id2image.side_effect = images
        temp_mock_gimp_item_module.from_id.side_effect = items
    
        self.setting.set_value(
          {1: [1, 3, (4, 'folder')], 2: [5, (6, 'folder'), [7, 'folder'], 8], 3: [9, 10]})
        
        self.assertDictEqual(
          self.setting.to_dict(source_type='session'),
          {
            'name': 'selected_layers',
            'type': 'images_and_gimp_items',
            'value': {1: [1, 3, [4, 'folder']], 2: [5, [7, 'folder']]},
          })
  
  def test_to_dict_with_paths(self):
    images, items = _get_images_and_items_with_ids()
    
    with mock.patch('export_layers.settings_custom.gimp.Item') as temp_mock_gimp_item_module:
      with mock.patch(
            pg.utils.get_pygimplib_module_path() + '.pdbutils.gimp') as temp_mock_gimp_module:
        temp_mock_gimp_module._id2image.side_effect = images
        temp_mock_gimp_item_module.from_id.side_effect = items
        
        self.setting.set_value(
          {1: [1, 3, (4, 'folder')], 2: [5, (6, 'folder'), [7, 'folder'], 8], 3: [9, 10]})
        
        temp_mock_gimp_module._id2image.side_effect = images
        temp_mock_gimp_item_module.from_id.side_effect = [
          item for item in items if item is not None]
        
        expected_dict = {
          'name': 'selected_layers',
          'type': 'images_and_gimp_items',
          'value': {
            'filename_1': [
              ['LayerStub', 'item_1'],
              ['LayerStub', 'item_4/item_3'],
              ['LayerGroupStub', 'item_4', 'folder']],
            'filename_2': [
              ['LayerStub', 'item_7/item_5'],
              ['LayerGroupStub', 'item_7', 'folder']],
          },
        }
        
        actual_dict = self.setting.to_dict()
        
        # We need to compare 'value' field element by element since unordered sets
        # are converted to lists and we cannot guarantee stable order in sets.
        self.assertEqual(actual_dict['name'], expected_dict['name'])
        self.assertEqual(actual_dict['type'], expected_dict['type'])
        for key in expected_dict['value']:
          self.assertIn(key, actual_dict['value'])
          for item in expected_dict['value'][key]:
            self.assertIn(item, actual_dict['value'][key])
  
  def test_to_dict_with_image_without_filepaths(self):
    images, items = _get_images_and_items_with_ids()
    
    images[1].filename = None
    
    with mock.patch('export_layers.settings_custom.gimp.Item') as temp_mock_gimp_item_module:
      with mock.patch(
            pg.utils.get_pygimplib_module_path() + '.pdbutils.gimp') as temp_mock_gimp_module:
        temp_mock_gimp_module._id2image.side_effect = images
        temp_mock_gimp_item_module.from_id.side_effect = items
        
        self.setting.set_value(
          {1: [1, 3, (4, 'folder')], 2: [5, (6, 'folder'), [7, 'folder'], 8], 3: [9, 10]})
        
        temp_mock_gimp_module._id2image.side_effect = images
        temp_mock_gimp_item_module.from_id.side_effect = [
          item for item in items if item is not None]
        
        expected_dict = {
          'name': 'selected_layers',
          'type': 'images_and_gimp_items',
          'value': {
            'filename_1': [
              ['LayerStub', 'item_1'],
              ['LayerStub', 'item_4/item_3'],
              ['LayerGroupStub', 'item_4', 'folder']],
          },
        }
        
        actual_dict = self.setting.to_dict()
        
        # We need to compare 'value' field element by element since unordered sets
        # are converted to lists and we cannot guarantee stable order in sets.
        self.assertEqual(actual_dict['name'], expected_dict['name'])
        self.assertEqual(actual_dict['type'], expected_dict['type'])
        for key in expected_dict['value']:
          self.assertIn(key, actual_dict['value'])
          for item in expected_dict['value'][key]:
            self.assertIn(item, actual_dict['value'][key])
