import contextlib
import unittest

import parameterized

from src import invoker as invoker_


def append_test(list_):
  list_.append('test')


def append_to_list(list_, arg):
  list_.append(arg)
  return arg


def append_to_list_multiple_args(list_, arg1, arg2, arg3):
  for arg in [arg1, arg2, arg3]:
    list_.append(arg)
  return arg1, arg2, arg3


def extend_list(list_, *args):
  list_.extend(args)


def update_dict(dict_, **kwargs):
  dict_.update(kwargs)


class AppendToListCommand(invoker_.CallableCommand):

  def _initialize(self, list_, arg):
    list_.append(1)

  def _process(self, list_, arg):
    list_.append(arg)


@contextlib.contextmanager
def append_to_list_before(list_, arg):
  list_.append(arg)
  yield


@contextlib.contextmanager
def append_to_list_before_and_after(list_, arg):
  list_.append(arg)
  try:
    yield
  finally:
    list_.append(arg)


class AppendToListBeforeAndAfterContextManager:

  def __init__(self, list_, arg):
    self._list = list_
    self._arg = arg

  def __enter__(self):
    self._list.append(self._arg)

  def __exit__(self, exc_type, exc_val, exc_tb):
    self._list.append(self._arg)
    return False


class InvokerTestCase(unittest.TestCase):
  
  def setUp(self):
    self.invoker = invoker_.Invoker()


class TestInvoker(InvokerTestCase):
  
  @parameterized.parameterized.expand([
    ('default_group',
     None, ['default']
     ),
    
    ('default_group_explicit_name',
     'default', ['default']
     ),
    
    ('specific_groups',
     ['main', 'additional'],
     ['main', 'additional']
     ),
  ])
  def test_add(self, _test_case_suffix, groups, list_commands_groups):
    test_list = []
    
    self.invoker.add(append_test, groups, args=[test_list])
    
    for list_commands_group in list_commands_groups:
      self.assertEqual(len(self.invoker.list_commands(list_commands_group)), 1)
  
  def test_add_to_all_groups(self):
    test_list = []
    
    self.invoker.add(append_test, ['main', 'additional'], [test_list])
    self.invoker.add(append_test, 'all', [test_list])
    
    self.assertEqual(len(self.invoker.list_commands('main')), 2)
    self.assertEqual(len(self.invoker.list_commands('additional')), 2)
    self.assertFalse('default' in self.invoker.list_groups())
    
    self.invoker.add(append_test, args=[test_list])
    self.invoker.add(append_test, 'all', [test_list])
    
    self.assertEqual(len(self.invoker.list_commands('main')), 3)
    self.assertEqual(len(self.invoker.list_commands('additional')), 3)
    self.assertEqual(len(self.invoker.list_commands()), 2)
  
  def test_add_return_unique_ids_within_same_invoker(self):
    test_list = []
    command_ids = []
    
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 2]))
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 3]))
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 2]))
    command_ids.append(
      self.invoker.add(append_to_list_before, args=[test_list, 3], foreach=True))
    command_ids.append(
      self.invoker.add(append_to_list_before, args=[test_list, 3], foreach=True))
    
    additional_invoker = invoker_.Invoker()
    command_ids.append(self.invoker.add(additional_invoker))
    command_ids.append(self.invoker.add(additional_invoker))
    
    self.assertEqual(len(command_ids), len(set(command_ids)))
  
  def test_add_return_unique_ids_across_multiple_invokers(self):
    command_id = self.invoker.add(append_test)
    
    additional_invoker = invoker_.Invoker()
    additional_command_id = additional_invoker.add(append_test)
    
    self.assertNotEqual(command_id, additional_command_id)
  
  def test_add_return_same_id_for_multiple_groups(self):
    test_list = []
    command_id = self.invoker.add(
      append_to_list, ['main', 'additional'], [test_list, 2])
    
    self.assertTrue(self.invoker.has_command(command_id, 'all'))
    self.assertTrue(self.invoker.has_command(command_id, ['main']))
    self.assertTrue(self.invoker.has_command(command_id, ['additional']))
  
  def test_add_to_groups(self):
    test_list = []
    command_id = self.invoker.add(append_to_list, ['main'], [test_list, 2])
    
    self.invoker.add_to_groups(command_id, ['additional'])
    self.assertTrue(self.invoker.has_command(command_id, ['main']))
    self.assertTrue(self.invoker.has_command(command_id, ['additional']))
    
    self.invoker.add_to_groups(command_id, ['main'])
    self.assertEqual(len(self.invoker.list_commands('main')), 1)
    self.assertEqual(len(self.invoker.list_commands('main', foreach=True)), 0)
    
    foreach_command_id = self.invoker.add(
      append_to_list_before, ['main'], [test_list, 2], foreach=True)
    
    self.invoker.add_to_groups(foreach_command_id, ['additional'])
    self.assertTrue(self.invoker.has_command(foreach_command_id, ['main']))
    self.assertTrue(self.invoker.has_command(foreach_command_id, ['additional']))
    
    self.invoker.add_to_groups(foreach_command_id, ['main'])
    self.assertEqual(len(self.invoker.list_commands('main')), 1)
    self.assertEqual(len(self.invoker.list_commands('main', foreach=True)), 1)
    
    additional_invoker = invoker_.Invoker()
    invoker_id = self.invoker.add(additional_invoker, ['main'])
    
    self.invoker.add_to_groups(invoker_id, ['additional'])
    self.assertTrue(self.invoker.has_command(invoker_id, ['main']))
    self.assertTrue(self.invoker.has_command(invoker_id, ['additional']))
    
    self.invoker.add_to_groups(invoker_id, ['main'])
    self.assertEqual(len(self.invoker.list_commands('main')), 2)
    self.assertEqual(len(self.invoker.list_commands('main', foreach=True)), 1)
  
  def test_add_to_groups_same_group(self):
    test_list = []
    command_id = self.invoker.add(append_to_list, ['main'], [test_list, 2])
    
    self.invoker.add_to_groups(command_id, ['main'])
    self.assertEqual(len(self.invoker.list_commands('main')), 1)
  
  def test_add_ignore_if_exists(self):
    test_list = []
    self.invoker.add(append_to_list, args=[test_list, 1], ignore_if_exists=True)
    self.assertEqual(len(self.invoker.list_commands()), 1)
    
    command_id = self.invoker.add(
      append_to_list, args=[test_list, 2], ignore_if_exists=True)
    self.assertEqual(len(self.invoker.list_commands()), 1)
    self.assertIsNone(command_id)
  
  def test_add_different_order(self):
    test_list = []
    self.invoker.add(append_to_list, args=[test_list, 1])
    self.invoker.add(append_to_list, args=[test_list, 2], position=0)
    
    self.assertListEqual(
      self.invoker.list_commands(),
      [(append_to_list, [test_list, 2], {}), (append_to_list, [test_list, 1], {})])
  
  def test_add_foreach_command_different_order(self):
    test_list = []
    self.invoker.add(append_to_list_before, args=[test_list, 1], foreach=True)
    self.invoker.add(append_to_list_before, args=[test_list, 2], foreach=True, position=0)
    
    self.assertListEqual(
      self.invoker.list_commands(foreach=True),
      [(append_to_list_before, [test_list, 2], {}),
       (append_to_list_before, [test_list, 1], {})])
  
  def test_add_invoker_different_order(self):
    additional_invoker = invoker_.Invoker()
    additional_invoker_2 = invoker_.Invoker()
    
    self.invoker.add(additional_invoker)
    self.invoker.add(additional_invoker_2, position=0)
    
    self.assertListEqual(
      self.invoker.list_commands(),
      [additional_invoker_2, additional_invoker])
  
  def test_has_command(self):
    command_id = self.invoker.add(append_to_list)
    self.assertTrue(self.invoker.has_command(command_id))
  
  def test_contains(self):
    test_list = []
    
    self.invoker.add(append_test, args=[test_list])
    self.assertTrue(self.invoker.contains(append_test))
    
    additional_invoker = invoker_.Invoker()
    self.invoker.add(additional_invoker)
    self.assertTrue(self.invoker.contains(additional_invoker))
  
  def test_list_commands_non_existing_group(self):
    self.assertIsNone(self.invoker.list_commands('non_existing_group'))
  
  def test_list_commands(self):
    test_list = []
    self.invoker.add(append_to_list, args=[test_list, 1])
    self.invoker.add(append_to_list, args=[test_list, 2])
    
    self.assertListEqual(
      self.invoker.list_commands(),
      [(append_to_list, [test_list, 1], {}), (append_to_list, [test_list, 2], {})])
    
    self.assertEqual(self.invoker.list_commands(foreach=True), [])
  
  def test_get_foreach_commands(self):
    test_list = []
    self.invoker.add(append_to_list_before, args=[test_list, 1], foreach=True)
    self.invoker.add(append_to_list_before, args=[test_list, 2], foreach=True)
    
    self.assertListEqual(
      self.invoker.list_commands(foreach=True),
      [(append_to_list_before, [test_list, 1], {}),
       (append_to_list_before, [test_list, 2], {})])
    
    self.assertEqual(self.invoker.list_commands(), [])
  
  def test_get_foreach_commands_non_existing_group(self):
    self.assertIsNone(self.invoker.list_commands('non_existing_group', foreach=True))
  
  def test_list_groups(self):
    test_list = []
    self.invoker.add(append_to_list, ['main'], [test_list, 2])
    self.invoker.add(append_to_list, ['additional'], [test_list, 3])
    
    self.assertEqual(len(self.invoker.list_groups()), 2)
    self.assertIn('main', self.invoker.list_groups())
    self.assertIn('additional', self.invoker.list_groups())
  
  def test_list_groups_without_empty_groups(self):
    test_list = []
    command_ids = []
    
    command_ids.append(
      self.invoker.add(append_to_list, ['main', 'additional'], [test_list, 2]))
    
    command_ids.append(
      self.invoker.add(
        append_to_list_before, ['main', 'additional'], [test_list, 2], foreach=True))
    
    additional_invoker = invoker_.Invoker()
    command_ids.append(self.invoker.add(additional_invoker, ['main']))
    
    self.invoker.remove(command_ids[2], ['main'])
    self.assertEqual(len(self.invoker.list_groups(include_empty_groups=False)), 2)
    
    self.invoker.remove(command_ids[1], ['main'])
    self.assertEqual(len(self.invoker.list_groups(include_empty_groups=False)), 2)
    
    self.invoker.remove(command_ids[0], ['main'])
    non_empty_groups = self.invoker.list_groups(include_empty_groups=False)
    self.assertEqual(len(non_empty_groups), 1)
    self.assertNotIn('main', non_empty_groups)
    self.assertIn('additional', non_empty_groups)
    
    self.invoker.remove(command_ids[1], ['additional'])
    non_empty_groups = self.invoker.list_groups(include_empty_groups=False)
    self.assertEqual(len(non_empty_groups), 1)
    self.assertNotIn('main', non_empty_groups)
    self.assertIn('additional', non_empty_groups)
    
    self.invoker.remove(command_ids[0], ['additional'])
    self.assertEqual(len(self.invoker.list_groups(include_empty_groups=False)), 0)
  
  def test_get_command(self):
    test_list = []
    command_ids = []
    command_ids.append(
      self.invoker.add(append_to_list, ['main'], [test_list, 2]))
    command_ids.append(
      self.invoker.add(append_to_list, ['additional'], [test_list, 3]))
    command_ids.append(
      self.invoker.add(
        append_to_list_before, ['additional'], [test_list, 4], foreach=True))
    
    additional_invoker = invoker_.Invoker()
    command_ids.append(self.invoker.add(additional_invoker, ['main']))
    
    self.assertEqual(
      self.invoker.get_command(command_ids[0]),
      (append_to_list, [test_list, 2], {}))
    self.assertEqual(
      self.invoker.get_command(command_ids[1]),
      (append_to_list, [test_list, 3], {}))
    self.assertEqual(
      self.invoker.get_command(command_ids[2]),
      (append_to_list_before, [test_list, 4], {}))
    
    self.assertEqual(self.invoker.get_command(command_ids[3]), additional_invoker)
  
  def test_get_command_invalid_id(self):
    self.assertIsNone(self.invoker.get_command(-1))
  
  def test_get_position(self):
    test_list = []
    command_ids = []
    
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 2]))
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 3]))
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 4]))
    
    self.assertEqual(self.invoker.get_position(command_ids[0]), 0)
    self.assertEqual(self.invoker.get_position(command_ids[1]), 1)
    self.assertEqual(self.invoker.get_position(command_ids[2]), 2)
  
  def test_get_position_invalid_id(self):
    self.invoker.add(append_test)
    with self.assertRaises(ValueError):
      self.invoker.get_position(-1)
  
  def test_get_position_command_not_in_group(self):
    command_id = self.invoker.add(append_test, ['main'])
    with self.assertRaises(ValueError):
      self.invoker.get_position(command_id, 'additional')
  
  def test_find(self):
    test_list = []
    command_ids = []
    
    command_ids.append(
      self.invoker.add(append_to_list, args=[test_list, 2]))
    command_ids.append(
      self.invoker.add(append_to_list, args=[test_list, 3]))
    command_ids.append(
      self.invoker.add(append_to_list, ['additional'], [test_list, 3]))
    
    command_ids.append(
      self.invoker.add(append_to_list_before, args=[test_list, 3], foreach=True))
    
    additional_invoker = invoker_.Invoker()
    command_ids.append(self.invoker.add(additional_invoker))
    
    self.assertEqual(
      self.invoker.find(append_to_list),
      [command_ids[0], command_ids[1]])
    self.assertEqual(
      self.invoker.find(append_to_list, foreach=True), [])
    
    self.assertEqual(
      self.invoker.find(append_to_list_before), [])
    self.assertEqual(
      self.invoker.find(append_to_list_before, foreach=True),
      [command_ids[3]])
    
    self.assertEqual(
      self.invoker.find(additional_invoker),
      [command_ids[4]])
    self.assertEqual(
      self.invoker.find(additional_invoker, foreach=True), [])
  
  def test_find_non_existing_group(self):
    command_id = self.invoker.add(append_test)
    self.assertEqual(
      self.invoker.find(append_test, ['non_existing_group']),
      [])
    
    self.assertEqual(
      self.invoker.find(append_test, ['default', 'non_existing_group']),
      [command_id])
  
  def test_reorder(self):
    command_ids = []
    command_ids.append(self.invoker.add(append_test))
    command_ids.append(self.invoker.add(append_test))
    command_ids.append(self.invoker.add(append_test))
    command_ids.append(self.invoker.add(append_test))
    
    self.invoker.reorder(command_ids[3], 0)
    self.invoker.reorder(command_ids[2], 1)
    self.invoker.reorder(command_ids[1], 2)
    
    self.assertEqual(len(self.invoker.list_commands()), 4)
    self.assertEqual(self.invoker.get_position(command_ids[0]), 3)
    self.assertEqual(self.invoker.get_position(command_ids[1]), 2)
    self.assertEqual(self.invoker.get_position(command_ids[2]), 1)
    self.assertEqual(self.invoker.get_position(command_ids[3]), 0)
    
    self.invoker.reorder(command_ids[2], 5)
    self.assertEqual(self.invoker.get_position(command_ids[2]), 3)
    
    self.invoker.reorder(command_ids[3], -1)
    self.invoker.reorder(command_ids[1], -3)
    self.invoker.reorder(command_ids[0], -4)
    
    self.assertEqual(len(self.invoker.list_commands()), 4)
    self.assertEqual(self.invoker.get_position(command_ids[0]), 0)
    self.assertEqual(self.invoker.get_position(command_ids[1]), 1)
    self.assertEqual(self.invoker.get_position(command_ids[2]), 2)
    self.assertEqual(self.invoker.get_position(command_ids[3]), 3)
  
  def test_reorder_invalid_id(self):
    with self.assertRaises(ValueError):
      self.invoker.reorder(-1, 0)
  
  def test_reorder_non_existing_group(self):
    command_id = self.invoker.add(append_test)
    with self.assertRaises(ValueError):
      self.invoker.reorder(command_id, 0, 'non_existing_group')
  
  def test_reorder_command_not_in_group(self):
    command_id = self.invoker.add(append_test, ['main'])
    self.invoker.add(append_test, ['additional'])
    with self.assertRaises(ValueError):
      self.invoker.reorder(command_id, 0, 'additional')
  
  def test_remove(self):
    test_list = []
    command_ids = []
    
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 2]))
    command_ids.append(
      self.invoker.add(append_to_list_before, args=[test_list, 3], foreach=True))
    
    additional_invoker = invoker_.Invoker()
    command_ids.append(self.invoker.add(additional_invoker))
    
    self.invoker.remove(command_ids[0])
    self.assertFalse(self.invoker.has_command(command_ids[0]))
    self.assertFalse(self.invoker.contains(append_to_list))
    
    self.invoker.remove(command_ids[1])
    self.assertFalse(self.invoker.has_command(command_ids[1]))
    self.assertFalse(self.invoker.contains(append_to_list_before))
    
    self.invoker.remove(command_ids[2])
    self.assertFalse(self.invoker.has_command(command_ids[2]))
    self.assertFalse(self.invoker.contains(additional_invoker))
  
  def test_remove_multiple_commands(self):
    test_list = []
    command_ids = []
    
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 2]))
    command_ids.append(self.invoker.add(append_to_list, args=[test_list, 3]))
    
    self.invoker.remove(command_ids[0])
    self.assertFalse(self.invoker.has_command(command_ids[0]))
    self.assertTrue(self.invoker.contains(append_to_list))
    
    self.invoker.remove(command_ids[1])
    self.assertFalse(self.invoker.has_command(command_ids[1]))
    self.assertFalse(self.invoker.contains(append_to_list))
    
    command_ids.append(
      self.invoker.add(append_to_list_before, args=[test_list, 4], foreach=True))
    command_ids.append(
      self.invoker.add(append_to_list_before, args=[test_list, 5], foreach=True))
    
    self.invoker.remove(command_ids[2])
    self.assertFalse(self.invoker.has_command(command_ids[2]))
    self.assertTrue(self.invoker.contains(append_to_list_before, foreach=True))
    
    self.invoker.remove(command_ids[3])
    self.assertFalse(self.invoker.has_command(command_ids[3]))
    self.assertFalse(self.invoker.contains(append_to_list_before, foreach=True))
    
    additional_invoker = invoker_.Invoker()
    command_ids.append(self.invoker.add(additional_invoker))
    command_ids.append(self.invoker.add(additional_invoker))
    
    self.invoker.remove(command_ids[4])
    self.assertFalse(self.invoker.has_command(command_ids[4]))
    self.assertTrue(self.invoker.contains(additional_invoker))
    
    self.invoker.remove(command_ids[5])
    self.assertFalse(self.invoker.has_command(command_ids[5]))
    self.assertFalse(self.invoker.contains(additional_invoker))
  
  def test_remove_from_all_groups_command_only_in_one_group(self):
    test_list = []
    
    command_id = self.invoker.add(append_to_list, ['main'], [test_list, 2])
    self.invoker.add(append_to_list, ['additional'], [test_list, 3])
    
    self.invoker.remove(command_id, 'all')
    self.assertFalse(self.invoker.has_command(command_id, ['main']))
    self.assertFalse(self.invoker.has_command(command_id, ['additional']))
  
  def test_remove_in_one_group_keep_in_others(self):
    command_id = self.invoker.add(append_test, ['main', 'additional'])
    
    self.invoker.remove(command_id, ['main'])
    self.assertFalse(self.invoker.has_command(command_id, ['main']))
    self.assertTrue(self.invoker.has_command(command_id, ['additional']))
  
  def test_remove_if_invalid_id(self):
    with self.assertRaises(ValueError):
      self.invoker.remove(-1)
  
  def test_remove_non_existing_group(self):
    command_id = self.invoker.add(append_test, ['main'])
    with self.assertRaises(ValueError):
      self.invoker.remove(command_id, ['additional'])
  
  def test_remove_ignore_if_not_exists(self):
    try:
      self.invoker.remove(-1, ignore_if_not_exists=True)
    except ValueError:
      self.fail(
        'removing commands when `ignore_if_not_exists=True` should not raise error')
  
  def test_remove_multiple_groups_at_once(self):
    test_list = []
    command_id = self.invoker.add(
      append_to_list, ['main', 'additional'], [test_list, 2])
    
    self.invoker.remove(command_id, 'all')
    self.assertFalse(self.invoker.has_command(command_id))
    self.assertFalse(self.invoker.contains(append_to_list, ['main']))
    self.assertFalse(self.invoker.contains(append_to_list, ['additional']))
  
  def test_remove_groups(self):
    test_list = []
    self.invoker.add(append_test, ['main', 'additional'])
    self.invoker.add(
      append_to_list_before, ['main', 'additional'], [test_list, 3], foreach=True)
    self.invoker.add(append_test, ['main', 'additional'])
    
    self.invoker.remove_groups(['main'])
    self.assertEqual(len(self.invoker.list_groups()), 1)
    self.assertIn('additional', self.invoker.list_groups())
    self.assertIsNone(self.invoker.list_commands('main'))
    
    self.invoker.remove_groups(['additional'])
    self.assertEqual(len(self.invoker.list_groups()), 0)
    self.assertIsNone(self.invoker.list_commands('main'))
    self.assertIsNone(self.invoker.list_commands('additional'))
  
  def test_remove_all_groups(self):
    test_list = []
    self.invoker.add(append_test, ['main', 'additional'])
    self.invoker.add(
      append_to_list_before, ['main', 'additional'], [test_list, 3], foreach=True)
    self.invoker.add(append_test, ['main', 'additional'])
    
    self.invoker.remove_groups('all')
    self.assertEqual(len(self.invoker.list_groups()), 0)
    self.assertIsNone(self.invoker.list_commands('main'))
    self.assertIsNone(self.invoker.list_commands('additional'))
  
  def test_remove_groups_non_existing_group(self):
    try:
      self.invoker.remove_groups(['non_existing_group'])
    except Exception:
      self.fail('removing a non-existent group should not raise exception')


class TestInvokerInvokeCommands(InvokerTestCase):
  
  @parameterized.parameterized.expand([
    ('default',
     append_test, [], [],
     ['test']),
    
    ('invoke_args',
     append_to_list, [], [1],
     [1]),
    
    ('add_and_invoke_args',
     extend_list, [1], [2, 3],
     [1, 2, 3]),
  ])
  def test_invoke_single_command(
        self,
        _test_case_suffix,
        command,
        add_args,
        invoke_args,
        expected_result):
    test_list = []
    
    self.invoker.add(command, args=[test_list] + add_args)
    self.invoker.invoke(additional_args=invoke_args)
    
    self.assertEqual(test_list, expected_result)
  
  def test_invoke_invalid_number_of_args(self):
    test_list = []
    self.invoker.add(append_to_list, args=[test_list, 1, 2])
    
    with self.assertRaises(TypeError):
      self.invoker.invoke()
  
  def test_invoke_additional_args_invalid_number_of_args(self):
    test_list = []
    self.invoker.add(append_to_list, args=[test_list])
    
    with self.assertRaises(TypeError):
      self.invoker.invoke()
    
    with self.assertRaises(TypeError):
      self.invoker.invoke(additional_args=[1, 2])
  
  def test_invoke_additional_kwargs_override_former_kwargs(self):
    test_dict = {}
    self.invoker.add(update_dict, args=[test_dict], kwargs={'one': 1, 'two': 2})
    self.invoker.invoke(additional_kwargs={'two': 'two', 'three': 3})
    
    self.assertDictEqual(test_dict, {'one': 1, 'two': 'two', 'three': 3})
  
  def test_invoke_additional_args_position_at_beginning(self):
    test_list = []
    self.invoker.add(append_to_list, args=[1])
    self.invoker.invoke(additional_args=[test_list], additional_args_position=0)
    
    self.assertEqual(test_list, [1])
  
  def test_invoke_additional_args_position_in_middle(self):
    test_list = []
    self.invoker.add(append_to_list_multiple_args, args=[test_list, 1, 3])
    self.invoker.invoke(additional_args=[2], additional_args_position=2)
    
    self.assertEqual(test_list, [1, 2, 3])
  
  def test_invoke_multiple_commands(self):
    test_list = []
    self.invoker.add(append_test, args=[test_list])
    self.invoker.add(extend_list, args=[test_list, 1])
    
    self.invoker.invoke()
    
    self.assertListEqual(test_list, ['test', 1])
  
  def test_invoke_multiple_groups_multiple_commands(self):
    test_dict = {}
    self.invoker.add(
      update_dict, ['main', 'additional'], [test_dict], {'one': 1, 'two': 2})
    self.invoker.add(
      update_dict, ['main'], [test_dict], {'two': 'two', 'three': 3})
    
    self.invoker.invoke(['main'])
    self.assertDictEqual(test_dict, {'one': 1, 'two': 'two', 'three': 3})
    
    self.invoker.invoke(['additional'])
    self.assertDictEqual(test_dict, {'one': 1, 'two': 2, 'three': 3})
    
    test_dict.clear()
    self.invoker.invoke(['main', 'additional'])
    self.assertDictEqual(test_dict, {'one': 1, 'two': 2, 'three': 3})
    
    test_dict.clear()
    self.invoker.invoke(['additional', 'main'])
    self.assertDictEqual(test_dict, {'one': 1, 'two': 'two', 'three': 3})
    
  def test_invoke_empty_group(self):
    try:
      self.invoker.invoke()
    except Exception:
      self.fail('invoking no commands for the given group should not raise exception')
  
  def test_invoke_while_deleting_past_or_present_command_inside_command(self):
    def append_to_list_and_remove_command(list_, arg):
      list_.append(arg)
      self.invoker.remove(command_2_id, ['main'])
    
    test_list = []
    self.invoker.add(append_to_list, ['main'], args=[test_list, 'one'])
    command_2_id = self.invoker.add(
      append_to_list_and_remove_command, ['main'], args=[test_list, 'two'])
    self.invoker.add(append_to_list, ['main'], args=[test_list, 'three'])
    
    self.invoker.invoke(['main'])
    
    self.assertEqual(test_list, ['one', 'two', 'three'])
  
  def test_invoke_while_deleting_future_command_inside_command(self):
    def append_to_list_and_remove_command(list_, arg):
      list_.append(arg)
      self.invoker.remove(command_3_id, ['main'])
    
    test_list = []
    self.invoker.add(append_to_list, ['main'], args=[test_list, 'one'])
    self.invoker.add(append_to_list_and_remove_command, ['main'], args=[test_list, 'two'])
    command_3_id = self.invoker.add(append_to_list, ['main'], args=[test_list, 'three'])
    self.invoker.add(append_to_list, ['main'], args=[test_list, 'four'])
    
    self.invoker.invoke(['main'])
    
    self.assertEqual(test_list, ['one', 'two', 'four'])
  
  def test_invoke_with_callable_command_and_initialization(self):
    test_list = []
    
    self.invoker.add(AppendToListCommand(), args=[test_list])
    self.invoker.invoke(additional_args=[3])
    self.invoker.invoke(additional_args=[2])
    self.invoker.invoke(additional_args=[4])
    
    self.assertEqual(test_list, [1, 3, 2, 4])


class TestInvokerInvokeForeachCommands(InvokerTestCase):
  
  @parameterized.parameterized.expand([
    ('before_command',
     append_to_list, append_to_list_before, [[1], [2]], [3],
     [3, 1, 3, 2]),
    
    ('before_and_after_command',
     append_to_list, append_to_list_before_and_after, [[1], [2]], [3],
     [3, 1, 3, 3, 2, 3]),

    ('before_and_after_command_with_class',
     append_to_list, AppendToListBeforeAndAfterContextManager, [[1], [2]], [3],
     [3, 1, 3, 3, 2, 3]),
  ])
  def test_invoke_single_foreach_command(
        self,
        _test_case_suffix,
        command,
        foreach_command,
        commands_args,
        foreach_command_args,
        expected_result):
    test_list = []
    
    self.invoker.add(command, args=[test_list] + commands_args[0])
    self.invoker.add(command, args=[test_list] + commands_args[1])
    self.invoker.add(
      foreach_command, args=[test_list] + foreach_command_args, foreach=True)
    
    self.invoker.invoke()
    
    self.assertListEqual(test_list, expected_result)
  
  @parameterized.parameterized.expand([
    ('before_twice_after_once',
     append_to_list,
     [append_to_list_before, append_to_list_before_and_after],
     [[1], [2]],
     [[3], [4]],
     [3, 4, 1, 4, 3, 4, 2, 4]),

    ('before_twice_after_once_with_class',
     append_to_list,
     [append_to_list_before, AppendToListBeforeAndAfterContextManager],
     [[1], [2]],
     [[3], [4]],
     [3, 4, 1, 4, 3, 4, 2, 4]),
  ])
  def test_invoke_multiple_foreach_commands(
        self,
        _test_case_suffix,
        command,
        foreach_commands,
        commands_args,
        foreach_commands_args,
        expected_result):
    test_list = []
    
    self.invoker.add(command, args=[test_list] + commands_args[0])
    self.invoker.add(command, args=[test_list] + commands_args[1])
    self.invoker.add(
      foreach_commands[0], args=[test_list] + foreach_commands_args[0], foreach=True)
    self.invoker.add(
      foreach_commands[1], args=[test_list] + foreach_commands_args[1], foreach=True)
    
    self.invoker.invoke()
    
    self.assertListEqual(test_list, expected_result)
  
  def test_invoke_foreach_command_does_nothing_in_another_invoker(self):
    test_list = []
    another_invoker = invoker_.Invoker()
    another_invoker.add(append_to_list, args=[test_list, 1])
    another_invoker.add(append_to_list, args=[test_list, 2])
    
    self.invoker.add(another_invoker)
    self.invoker.add(append_to_list, args=[test_list, 3])
    self.invoker.add(append_to_list, args=[test_list, 4])
    self.invoker.add(append_to_list_before, args=[test_list, 2], foreach=True)

    self.invoker.invoke()
    
    self.assertListEqual(test_list, [1, 2, 2, 3, 2, 4])
  
  def test_invoke_foreach_invoker(self):
    test_list = []

    @contextlib.contextmanager
    def append_to_list_before_from_invoker():
      another_invoker.invoke()
      yield
    
    self.invoker.add(append_to_list, args=[test_list, 1])
    self.invoker.add(append_to_list, args=[test_list, 2])
    
    another_invoker = invoker_.Invoker()
    another_invoker.add(append_to_list, args=[test_list, 3])
    another_invoker.add(append_to_list, args=[test_list, 4])
    
    self.invoker.add(append_to_list_before_from_invoker, foreach=True)
    
    self.invoker.invoke()
    
    self.assertListEqual(test_list, [3, 4, 1, 3, 4, 2])

  def test_invoke_foreach_command_is_still_finished_on_error(self):
    test_list = []

    def raise_error():
      raise ValueError

    self.invoker.add(append_to_list, args=[test_list, 1])
    self.invoker.add(raise_error)
    self.invoker.add(append_to_list, args=[test_list, 3])
    self.invoker.add(append_to_list_before_and_after, args=[test_list, 2], foreach=True)

    try:
      self.invoker.invoke()
    except ValueError:
      pass

    self.assertListEqual(test_list, [2, 1, 2, 2, 2])

  def test_invoke_foreach_command_not_as_context_manager_raises_error(self):
    test_list = []

    self.invoker.add(append_to_list, args=[test_list, 1])
    self.invoker.add(append_to_list, args=[test_list, 1], foreach=True)

    with self.assertRaises(TypeError):
      self.invoker.invoke()


class TestInvokerInvokeWithInvoker(InvokerTestCase):
  
  def test_invoke(self):
    test_list = []
    another_invoker = invoker_.Invoker()
    another_invoker.add(append_to_list, args=[test_list, 1])
    another_invoker.add(append_test, args=[test_list])
    
    self.invoker.add(append_to_list, args=[test_list, 2])
    self.invoker.add(another_invoker)
    
    self.invoker.invoke()
    
    self.assertListEqual(test_list, [2, 1, 'test'])
  
  def test_invoke_after_adding_commands_to_invoker(self):
    test_list = []
    another_invoker = invoker_.Invoker()
    
    self.invoker.add(append_to_list, args=[test_list, 2])
    self.invoker.add(another_invoker)
    
    another_invoker.add(append_to_list, args=[test_list, 1])
    another_invoker.add(append_test, args=[test_list])
    
    self.invoker.invoke()
    
    self.assertListEqual(test_list, [2, 1, 'test'])
  
  def test_invoke_multiple_invokers_after_adding_commands_to_them(self):
    test_list = []
    more_invokers = [invoker_.Invoker(), invoker_.Invoker()]
    
    self.invoker.add(append_to_list, args=[test_list, 2])
    self.invoker.add(more_invokers[0])
    self.invoker.add(more_invokers[1])
    
    more_invokers[0].add(append_to_list, args=[test_list, 1])
    more_invokers[0].add(append_test, args=[test_list])
    
    more_invokers[1].add(append_to_list, args=[test_list, 3])
    more_invokers[1].add(append_to_list, args=[test_list, 4])
    
    self.invoker.invoke()
    
    self.assertListEqual(test_list, [2, 1, 'test', 3, 4])
  
  def test_invoke_empty_group(self):
    another_invoker = invoker_.Invoker()
    try:
      self.invoker.add(another_invoker, ['invalid_group'])
    except Exception:
      self.fail('adding commands from an empty group from another'
                ' Invoker instance should not raise exception')
