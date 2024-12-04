import unittest
import yaml
from io import StringIO
from unittest.mock import mock_open, patch
from converter import load_text, remove_comments, validate_name, evaluate_postfix, \
    process_data


class TestYourProgram(unittest.TestCase):

    def test_load_text_valid(self):
        yaml_data = """
        key1: 42
        key2: 3.14
        """
        m = mock_open(read_data=yaml_data)
        with patch('builtins.open', m):
            data, comments = load_text('dummy_path')
            self.assertEqual(data, {'key1': 42, 'key2': 3.14})
            self.assertEqual(comments, [])

    def test_remove_comments(self):
        input_data = "key1: 42; Это комментарий\nkey2: 3.14\n"
        cleaned_data, comments = remove_comments(input_data)
        self.assertEqual(cleaned_data, "key1: 42\nkey2: 3.14")
        self.assertEqual(comments, [(1, "Это комментарий")])

    def test_validate_name_valid(self):
        try:
            validate_name("valid_name1")
        except ValueError:
            self.fail("validate_name raised ValueError unexpectedly!")

    def test_validate_name_invalid(self):
        with self.assertRaises(ValueError):
            validate_name("1_invalid_name")

    def test_evaluate_postfix_addition(self):
        result = evaluate_postfix([1, 2, '+'], {})
        self.assertEqual(result, 3)

    def test_evaluate_postfix_subtraction(self):
        result = evaluate_postfix([5, 3, '-'], {})
        self.assertEqual(result, 2)

    def test_process_data_single_number(self):
        data = {'key1': 42}
        comments = []
        processed = process_data(data, {}, comments)
        self.assertEqual(processed, {'key1': 42})

    def test_process_data_expression(self):
        data = {'key1': {'expr': ['1', '2', '+']}}
        comments = []
        processed = process_data(data, {}, comments)
        self.assertEqual(processed, {'key1': 3})

    def test_process_data_invalid_expression(self):
        data = {'key1': {'expr': ['1', 'a', '+']}}
        comments = []
        with self.assertRaises(ValueError):
            process_data(data, {}, comments)


if __name__ == "__main__":
    unittest.main()
