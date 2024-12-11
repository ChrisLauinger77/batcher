import os

import unittest
import unittest.mock as mock

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp

import pygimplib as pg
from pygimplib.tests import stubs_gimp

from src import setting_classes


def _get_images_and_items():
  image_1 = stubs_gimp.Image(filepath='filename_1')
  image_2 = stubs_gimp.Image(filepath='filename_2')
  
  images = [image_1, image_2]
  
  item_4 = stubs_gimp.GroupLayer(name='item_4', image=image_1)
  item_1 = stubs_gimp.Layer(name='item_1', image=image_1)
  item_3 = stubs_gimp.Layer(name='item_3', image=image_1, parent=item_4)
  item_7 = stubs_gimp.GroupLayer(name='item_7', image=image_2)
  item_5 = stubs_gimp.Layer(name='item_5', image=image_2, parent=item_7)
  
  image_1.layers = [item_1, item_4]
  item_4.children = [item_3]
  image_2.layers = [item_7]
  item_7.children = [item_5]
  
  items = [item_1, item_3, item_4, item_5, item_7]
  
  return images, items


class TestDirpathSetting(unittest.TestCase):

  def setUp(self):
    self.setting = setting_classes.DirpathSetting('dirpath')

  def test_set_value_is_none_assigns_default_default_value(self):
    self.setting.set_value(None)

    self.assertEqual(self.setting.value, self.setting.default_value)


class TestFileExtensionSetting(unittest.TestCase):

  def setUp(self):
    self.setting = setting_classes.FileExtensionSetting('file_ext', default_value='png')

  def test_with_adjust_value(self):
    setting = setting_classes.FileExtensionSetting(
      'file_ext', adjust_value=True, default_value='png')

    setting.set_value('.jpg')

    self.assertEqual(setting.value, 'jpg')


@mock.patch('src.setting_classes.Gimp', new_callable=stubs_gimp.GimpModuleStub)
class TestItemTreeItemsSetting(unittest.TestCase):

  def setUp(self):
    self.setting = setting_classes.ItemTreeItemsSetting('selected_items')

    self.maxDiff = None

  def test_set_value_from_ids(self, gimp_module_stub):
    images, items = _get_images_and_items()

    gimp_module_stub.get_images = lambda: images

    self.setting.set_value([
      items[0].id_,
      items[1].id_,
      (items[2].id_, 'folder'),
      items[3].id_,
      (-10, 'folder'),
      [items[4].id_, 'folder'],
      -11,
      -12,
      -13,
    ])

    expected_value_and_loaded_items = {
      items[0].id_: images[0],
      items[1].id_: images[0],
      (items[2].id_, 'folder'): images[0],
      items[3].id_: images[1],
      (items[4].id_, 'folder'): images[1],
    }

    expected_value = list(expected_value_and_loaded_items)

    self.assertEqual(self.setting.value, expected_value)
    self.assertEqual(self.setting.loaded_items, expected_value_and_loaded_items)

  def test_set_value_from_paths(self, gimp_module_stub):
    images, items = _get_images_and_items()

    image_1_filepath = os.path.abspath('filename_1')
    image_2_filepath = os.path.abspath('filename_2')
    image_3_filepath = os.path.abspath('filename_3')

    gimp_module_stub.get_images = lambda: images

    self.setting.set_value([
      ('Layer', 'item_1', '', image_1_filepath),
      ('Layer', 'item_4/item_3', '', image_1_filepath),
      ('GroupLayer', 'item_4', 'folder', image_1_filepath),
      ('Layer', 'item_7/item_5', '', image_2_filepath),
      ('GroupLayer', 'item_6', 'folder', image_2_filepath),
      ('GroupLayer', 'item_7', 'folder', image_2_filepath),
      ('Layer', 'item_8', '', image_2_filepath),
      ('Layer', 'item_9', '', image_3_filepath),
      ('Layer', 'item_10', '', image_3_filepath),
    ])

    expected_value_and_loaded_items = {
      items[0].id_: images[0],
      items[1].id_: images[0],
      (items[2].id_, 'folder'): images[0],
      items[3].id_: images[1],
      (items[4].id_, 'folder'): images[1],
    }

    expected_value = list(expected_value_and_loaded_items)

    self.assertEqual(self.setting.value, expected_value)
    self.assertEqual(self.setting.loaded_items, expected_value_and_loaded_items)

  @mock.patch('src.setting_classes.os.path.isfile')
  def test_set_value_from_paths_items_without_loaded_image_are_ignored(
        self, mock_isfile, gimp_module_stub):
    images, items = _get_images_and_items()

    image_1_filepath = os.path.abspath('filename_1')
    image_2_filepath = os.path.abspath('filename_2')
    image_3_filepath = os.path.abspath('filename_3')

    images[1].set_file(None)

    gimp_module_stub.get_images = lambda: images
    mock_isfile.side_effect = [True, True, True, True, False, False]

    self.setting.set_value([
      ('Layer', 'item_1', '', image_1_filepath),
      ('Layer', 'item_4/item_3', '', image_1_filepath),
      ('GroupLayer', 'item_4', 'folder', image_1_filepath),
      ('Layer', 'item_7/item_5', '', image_2_filepath),
      ('GroupLayer', 'item_6', 'folder', image_2_filepath),
      ('GroupLayer', 'item_7', 'folder', image_2_filepath),
      ('Layer', 'item_8', '', image_2_filepath),
      ('Layer', 'item_9', '', image_3_filepath),
      ('Layer', 'item_10', '', image_3_filepath),
    ])

    expected_not_loaded_items = [
      ('Layer', 'item_7/item_5', '', image_2_filepath),
      ('GroupLayer', 'item_6', 'folder', image_2_filepath),
      ('GroupLayer', 'item_7', 'folder', image_2_filepath),
      ('Layer', 'item_8', '', image_2_filepath),
    ]

    expected_loaded_items = {
      items[0].id_: images[0],
      items[1].id_: images[0],
      (items[2].id_, 'folder'): images[0],
    }

    expected_value = [
      items[0].id_,
      items[1].id_,
      (items[2].id_, 'folder')
    ]
    expected_value.extend(expected_not_loaded_items)

    self.assertEqual(self.setting.value, expected_value)
    self.assertEqual(self.setting.loaded_items, expected_loaded_items)
    self.assertEqual(self.setting.not_loaded_items, expected_not_loaded_items)

  @mock.patch('src.setting_classes.os.path.isfile')
  def test_set_value_from_paths_overrides_previous_loaded_items_and_not_loaded_items(
        self, mock_isfile, gimp_module_stub):
    images, items = _get_images_and_items()

    image_1_filepath = os.path.abspath('filename_1')
    image_2_filepath = os.path.abspath('filename_2')
    image_3_filepath = os.path.abspath('filename_3')

    gimp_module_stub.get_images = lambda: images
    mock_isfile.side_effect = [False, False]

    self.setting.set_value([
      ('Layer', 'item_1', '', image_1_filepath),
      ('Layer', 'item_4/item_3', '', image_1_filepath),
      ('GroupLayer', 'item_4', 'folder', image_1_filepath),
      ('Layer', 'item_7/item_5', '', image_2_filepath),
      ('GroupLayer', 'item_6', 'folder', image_2_filepath),
      ('GroupLayer', 'item_7', 'folder', image_2_filepath),
      ('Layer', 'item_8', '', image_2_filepath),
      ('Layer', 'item_9', '', image_3_filepath),
      ('Layer', 'item_10', '', image_3_filepath),
    ])

    self.assertEqual(self.setting.not_loaded_items, [])

    images[1].set_file(None)

    mock_isfile.side_effect = [True, True, True, True, False, False]

    self.setting.set_value([
      ('Layer', 'item_1', '', image_1_filepath),
      ('Layer', 'item_4/item_3', '', image_1_filepath),
      ('GroupLayer', 'item_4', 'folder', image_1_filepath),
      ('Layer', 'item_7/item_5', '', image_2_filepath),
      ('GroupLayer', 'item_6', 'folder', image_2_filepath),
      ('GroupLayer', 'item_7', 'folder', image_2_filepath),
      ('Layer', 'item_8', '', image_2_filepath),
      ('Layer', 'item_9', '', image_3_filepath),
      ('Layer', 'item_10', '', image_3_filepath),
    ])

    expected_not_loaded_items = [
      ('Layer', 'item_7/item_5', '', image_2_filepath),
      ('GroupLayer', 'item_6', 'folder', image_2_filepath),
      ('GroupLayer', 'item_7', 'folder', image_2_filepath),
      ('Layer', 'item_8', '', image_2_filepath),
    ]

    expected_loaded_items = {
      items[0].id_: images[0],
      items[1].id_: images[0],
      (items[2].id_, 'folder'): images[0],
    }

    expected_value = [
      items[0].id_,
      items[1].id_,
      (items[2].id_, 'folder')
    ]
    expected_value.extend(expected_not_loaded_items)

    self.assertEqual(self.setting.value, expected_value)
    self.assertEqual(self.setting.loaded_items, expected_loaded_items)
    self.assertEqual(self.setting.not_loaded_items, expected_not_loaded_items)

  def test_set_value_invalid_list_length_raises_error(self, gimp_module_stub):
    images, items = _get_images_and_items()

    gimp_module_stub.get_images = lambda: images

    with self.assertRaises(ValueError):
      self.setting.set_value([
        items[0].id_, items[1].id_, ['Layer', items[2].id_, 'folder', 'filename_1', 'extra_item_1'],
      ])

  def test_set_value_invalid_item_type_raises_error(self, gimp_module_stub):
    images, items = _get_images_and_items()

    gimp_module_stub.get_images = lambda: images

    with self.assertRaises(TypeError):
      self.setting.set_value([object()])

  def test_to_dict(self, gimp_module_stub):
    images, items = _get_images_and_items()

    image_1_filepath = os.path.abspath('filename_1')
    image_2_filepath = os.path.abspath('filename_2')

    gimp_module_stub.get_images = lambda: images

    self.setting.set_value([
      items[0].id_,
      items[1].id_,
      (items[2].id_, 'folder'),
      items[3].id_,
      (-10, 'folder'),
      [items[4].id_, 'folder'],
      -11,
      -12,
      -13,
    ])

    expected_dict = {
      'name': 'selected_items',
      'type': 'item_tree_items',
      'value': [
        ['Layer', 'item_1', '', image_1_filepath],
        ['Layer', 'item_4/item_3', '', image_1_filepath],
        ['GroupLayer', 'item_4', 'folder', image_1_filepath],
        ['Layer', 'item_7/item_5', '', image_2_filepath],
        ['GroupLayer', 'item_7', 'folder', image_2_filepath],
      ],
    }

    self.assertEqual(self.setting.to_dict(), expected_dict)

  @mock.patch('src.setting_classes.os.path.isfile')
  def test_to_dict_with_image_without_filepath(self, mock_isfile, gimp_module_stub):
    images, items = _get_images_and_items()

    image_1_filepath = os.path.abspath('filename_1')
    image_2_filepath = os.path.abspath('filename_2')
    image_3_filepath = os.path.abspath('filename_3')

    images[1].set_file(None)

    gimp_module_stub.get_images = lambda: images
    mock_isfile.side_effect = [True, True, True, True, False, False]

    self.setting.set_value([
      ('Layer', 'item_1', '', image_1_filepath),
      ('Layer', 'item_4/item_3', '', image_1_filepath),
      ('GroupLayer', 'item_4', 'folder', image_1_filepath),
      ('Layer', 'item_7/item_5', '', image_2_filepath),
      ('GroupLayer', 'item_6', 'folder', image_2_filepath),
      ('GroupLayer', 'item_7', 'folder', image_2_filepath),
      ('Layer', 'item_8', '', image_2_filepath),
      ('Layer', 'item_9', '', image_3_filepath),
      ('Layer', 'item_10', '', image_3_filepath),
    ])

    expected_dict = {
      'name': 'selected_items',
      'type': 'item_tree_items',
      'value': [
        ['Layer', 'item_1', '', image_1_filepath],
        ['Layer', 'item_4/item_3', '', image_1_filepath],
        ['GroupLayer', 'item_4', 'folder', image_1_filepath],
        ['Layer', 'item_7/item_5', '', image_2_filepath],
        ['GroupLayer', 'item_6', 'folder', image_2_filepath],
        ['GroupLayer', 'item_7', 'folder', image_2_filepath],
        ['Layer', 'item_8', '', image_2_filepath],
      ],
    }

    self.assertEqual(self.setting.to_dict(), expected_dict)


class TestImagesAndDirectoriesSetting(unittest.TestCase):
  
  def setUp(self):
    self.image_ids_and_filepaths = [
      (0, None), (1, 'image.png'), (2, 'test.jpg'),
      (4, 'another_test.gif')]
    self.image_list = self._create_image_list(self.image_ids_and_filepaths)
    self.images_and_directories = self._create_images_and_directories(self.image_list)

    self.setting = setting_classes.ImagesAndDirectoriesSetting('images_and_directories')
    self.setting.set_value(self.images_and_directories)

  def test_update_images_and_dirpaths_add_new_images(self):
    self.image_list.extend(
      self._create_image_list([(5, 'new_image.png'), (6, None)]))
    
    with mock.patch('src.setting_classes.Gimp.get_images', new=self.get_image_list):
      self.setting.update_images_and_dirpaths()
    
    self.assertEqual(
      self.setting.value, self._create_images_and_directories(self.image_list))
  
  def test_update_images_and_dirpaths_remove_closed_images(self):
    self.image_list.pop(1)

    with mock.patch('src.setting_classes.Gimp.get_images', new=self.get_image_list):
      self.setting.update_images_and_dirpaths()
    
    self.assertEqual(
      self.setting.value, self._create_images_and_directories(self.image_list))
  
  def test_update_directory(self):
    self.setting.update_dirpath(self.image_list[1], 'test_directory')
    self.assertEqual(self.setting.value[self.image_list[1]], 'test_directory')
  
  def test_value_setitem_does_not_change_setting_value(self):
    image_to_test = self.image_list[1]
    self.setting.value[image_to_test] = 'test_directory'
    self.assertNotEqual(self.setting.value[image_to_test], 'test_directory')
    self.assertEqual(
      self.setting.value[image_to_test],
      self.images_and_directories[image_to_test])

  def test_set_value_from_image_ids(self):
    with mock.patch('src.setting_classes.Gimp') as temp_mock_gimp_module_src:
      temp_mock_gimp_module_src.Image.get_by_id.side_effect = self.image_list

      self.setting.set_value({0: 'dirpath1', 1: 'dirpath2'})

    self.assertDictEqual(
      self.setting.value,
      {self.image_list[0]: 'dirpath1', self.image_list[1]: 'dirpath2'})

  def test_set_value_from_image_paths(self):
    with mock.patch(
          f'{pg.utils.get_pygimplib_module_path()}.pdbutils.Gimp') as temp_mock_gimp_module:
      temp_mock_gimp_module.get_images.side_effect = [[self.image_list[1]], [self.image_list[2]]]

      self.setting.set_value(
        {os.path.abspath('image.png'): 'dirpath1', os.path.abspath('test.jpg'): 'dirpath2'})

    self.assertDictEqual(
      self.setting.value,
      {self.image_list[1]: 'dirpath1', self.image_list[2]: 'dirpath2'})

  def get_image_list(self):
    # `self.image_list` is wrapped into a method so that `mock.patch.object` can
    # be called on it.
    return self.image_list

  @staticmethod
  def _create_image_list(image_ids_and_filepaths):
    return [
      stubs_gimp.Image(id_=image_id, filepath=filepath)
      for image_id, filepath in image_ids_and_filepaths]

  @staticmethod
  def _create_images_and_directories(image_list):
    images_and_directories = {}
    for image in image_list:
      images_and_directories[image] = (
        os.path.dirname(image.get_file().get_path()) if image.get_file() is not None else None)
    return images_and_directories


@mock.patch('src.setting_classes.Gimp', new_callable=stubs_gimp.GimpModuleStub)
@mock.patch('src.settings_from_pdb.get_setting_data_from_pdb_procedure')
class TestFileFormatOptionsSetting(unittest.TestCase):

  @mock.patch('src.setting_classes.Gimp', new_callable=stubs_gimp.GimpModuleStub)
  @mock.patch('src.settings_from_pdb.get_setting_data_from_pdb_procedure')
  def setUp(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    self.common_options = [
      {
        'name': 'run-mode',
        'type': pg.setting.EnumSetting,
        'default_value': Gimp.RunMode.NONINTERACTIVE,
        'enum_type': Gimp.RunMode.__gtype__,
        'display_name': 'run-mode',
      },
      {
        'name': 'image',
        'type': pg.setting.ImageSetting,
        'default_value': None,
        'display_name': 'image',
      },
      {
        'name': 'file',
        'type': pg.setting.FileSetting,
      },
      {
        'name': 'options',
        'type': pg.setting.ExportOptionsSetting,
        'display_name': 'options',
      },
    ]

    self.png_options = [
      *self.common_options,
      {
        'name': 'interlaced',
        'type': pg.setting.BoolSetting,
        'display_name': 'interlaced',
        'default_value': False,
      },
      {
        'name': 'compression',
        'type': pg.setting.IntSetting,
        'display_name': 'compression',
        'default_value': 9,
      },
    ]

    self.jpg_options = [
      *self.common_options,
      {
        'name': 'quality',
        'type': pg.setting.DoubleSetting,
        'display_name': 'quality',
        'default_value': 0.9,
      },
    ]

    self.setting = setting_classes.FileFormatOptionsSetting(
      'file_format_export_options', 'export', 'png')

    self._ACTIVE_KEY = setting_classes.FileFormatOptionsSetting.ACTIVE_FILE_FORMAT_KEY

  def test_set_active_file_format(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-jpeg-export', self.jpg_options

    self.setting.set_active_file_format('jpg')

    mock_get_setting_data_from_pdb_procedure.assert_called_once()

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'jpg')
    self.assertIn('jpg', self.setting.value)

  def test_set_active_file_format_with_alias(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-jpeg-export', self.jpg_options

    self.setting.set_active_file_format('jpeg')

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'jpg')
    self.assertIn('jpg', self.setting.value)

  def test_set_active_file_format_to_unrecognized_format(
        self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    self.setting.set_active_file_format('unknown')

    mock_get_setting_data_from_pdb_procedure.assert_not_called()

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'unknown')
    self.assertNotIn('unknown', self.setting.value)

  def test_to_dict(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    mock_get_setting_data_from_pdb_procedure.return_value = None, 'file-png-export', self.png_options

    self.setting.set_active_file_format('png')
    self.setting.set_active_file_format('unknown')

    self.setting.value['png']['compression'].set_value(7)

    self.maxDiff = None

    self.assertEqual(
      self.setting.to_dict(),
      {
        'name': 'file_format_export_options',
        'type': 'file_format_options',
        'import_or_export': 'export',
        'initial_file_format': 'png',
        'value': {
          self._ACTIVE_KEY: 'unknown',
          'png': [
            {
              'name': 'interlaced',
              'type': 'bool',
              'display_name': 'interlaced',
              'default_value': False,
              'value': False,
            },
            {
              'name': 'compression',
              'type': 'int',
              'display_name': 'compression',
              'default_value': 9,
              'value': 7,
            },
          ],
        },
      }
    )

  def test_set_value_from_settings(self, *_mocks):
    png_group = pg.setting.Group('file_format_options')
    png_group.add([
      {
        'name': 'interlaced',
        'type': 'bool',
        'display_name': 'interlaced',
        'default_value': False,
      },
    ])

    jpeg_group = pg.setting.Group('file_format_options')
    jpeg_group.add([
      {
        'name': 'quality',
        'type': pg.setting.DoubleSetting,
        'display_name': 'quality',
        'default_value': 0.9,
      },
      {
        'name': 'optimize',
        'type': 'bool',
        'display_name': 'optimize',
        'default_value': False,
      },
    ])

    self.setting.set_value({
      'png': png_group,
      'jpg': jpeg_group,
      self._ACTIVE_KEY: 'jpg',
    })

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'jpg')
    self.assertNotIn('compression', self.setting.value['png'])
    self.assertEqual(self.setting.value['png']['interlaced'].value, False)
    self.assertEqual(self.setting.value['jpg']['quality'].value, 0.9)
    self.assertEqual(self.setting.value['jpg']['optimize'].value, False)

    self.assertIsNot(png_group, self.setting.value['png'])
    self.assertIsNot(jpeg_group, self.setting.value['jpg'])

  def test_set_value_from_raw_list(self, mock_get_setting_data_from_pdb_procedure, *_mocks):
    self.setting.set_value({
      'jpg': [
        {
          'name': 'optimize',
          'type': 'bool',
          'display_name': 'optimize',
          'default_value': False,
        },
      ],
      'gif': [
        {
          'name': 'loop',
          'type': 'bool',
          'display_name': 'loop',
          'default_value': True,
        },
      ],
      self._ACTIVE_KEY: 'jpg',
    })

    mock_get_setting_data_from_pdb_procedure.assert_not_called()

    self.assertEqual(self.setting.value[self._ACTIVE_KEY], 'jpg')
    self.assertNotIn('png', self.setting.value)
    self.assertNotIn('quality', self.setting.value['jpg'])
    self.assertEqual(self.setting.value['jpg']['optimize'].value, False)
    self.assertEqual(self.setting.value['gif']['loop'].value, True)

  def test_validate_value_with_missing_none_key(self, *_mocks):
    png_group = pg.setting.Group('file_format_options')
    png_group.add([
      {
        'name': 'interlaced',
        'type': 'bool',
        'display_name': 'interlaced',
        'default_value': False,
      },
    ])

    self.assertIsInstance(self.setting.validate({'png': png_group}), pg.setting.ValueNotValidData)
