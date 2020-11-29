import unittest
from entities.window import Window

class Testwindow(unittest.TestCase):

    def test_window_init(self):
        resource_data = [[1,2], [3,4]]
        window_size = 10
        stacktrace_data = ["Hello", "world"]
        new_window = Window(window_size, resource_data, stacktrace_data)

        self.assertEqual(window_size, new_window.window_size)
        self.assertEqual(resource_data, new_window.resource_data)
        self.assertEqual(stacktrace_data, new_window.stacktrace_data)