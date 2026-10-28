import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import main
from boy import Boy


class InputTests(unittest.TestCase):
    def setUp(self):
        clock = patch('boy.get_time', return_value=1000.0)
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        image = patch('boy.load_image', return_value=Mock())
        image.start()
        self.addCleanup(image.stop)
        canvas = patch('boy.get_canvas_width', return_value=800)
        canvas.start()
        self.addCleanup(canvas.stop)
        self.boy = Boy()
        main.world = [self.boy]
        main.pressed_keys.clear()
        main.running = True

    def tearDown(self):
        main.world = []
        main.pressed_keys.clear()

    def send(self, event_type, key=None):
        event = SimpleNamespace(type=event_type, key=key)
        with patch('main.get_events', return_value=[event]):
            main.handle_events()

    def test_a_starts_all_idle_boys(self):
        second = Boy()
        main.world.extend([Mock(), second])
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.assertEqual(self.boy.state, 'AutoRun')
        self.assertEqual(second.state, 'AutoRun')

    def test_a_does_not_interrupt_running(self):
        self.boy.set_direction(1)
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.assertEqual(self.boy.state, 'RUN')

    def test_a_does_not_wake_sleeping_boys(self):
        self.clock.return_value += 5
        self.boy.update()
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.assertEqual(self.boy.state, 'SLEEP')


if __name__ == '__main__':
    unittest.main()
