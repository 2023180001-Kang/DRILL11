import unittest
from pathlib import Path
from unittest.mock import patch

from grass import Grass


class GrassTests(unittest.TestCase):
    def test_image_path_is_relative_to_module(self):
        with patch('grass.load_image') as load_image:
            Grass()
        load_image.assert_called_once_with(str(Path(__file__).resolve().with_name('grass.png')))

    def test_grass_keeps_existing_draw_position(self):
        with patch('grass.load_image') as load_image:
            grass = Grass()
        grass.draw()
        load_image.return_value.draw.assert_called_once_with(400, 30)


if __name__ == '__main__':
    unittest.main()
