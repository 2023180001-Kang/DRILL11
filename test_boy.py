import unittest
from unittest.mock import Mock, patch

from boy import AutoRun, Boy


class BoyTests(unittest.TestCase):
    def setUp(self):
        clock = patch('boy.get_time', return_value=1000.0)
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        image = patch('boy.load_image', return_value=Mock())
        self.image = image.start().return_value
        self.addCleanup(image.stop)
        self.boy = Boy()

    def advance(self, seconds):
        self.clock.return_value += seconds
        self.boy.update()

    def test_initial_state_is_idle(self):
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.direction, 0)

    def test_running_uses_elapsed_time(self):
        self.boy.set_direction(1)
        self.advance(0.25)
        self.assertEqual(self.boy.state, 'RUN')
        self.assertEqual(self.boy.x, 450)

    def test_running_stays_inside_normal_bounds(self):
        for direction, expected in ((1, 750), (-1, 50)):
            with self.subTest(direction=direction):
                self.boy.set_direction(direction)
                self.advance(10)
                self.assertEqual(self.boy.x, expected)

    def test_releasing_direction_stops_running(self):
        self.boy.set_direction(-1)
        self.boy.set_direction(0)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.idle_time, 0)

    def test_idle_sleeps_after_five_seconds(self):
        self.advance(4.9)
        self.assertEqual(self.boy.state, 'IDLE')
        self.advance(0.1)
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_wake_resets_idle_timer(self):
        self.advance(5)
        self.boy.wake()
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.idle_time, 0)

    def test_direction_wakes_into_running(self):
        self.advance(5)
        self.boy.set_direction(-1)
        self.assertEqual(self.boy.state, 'RUN')
        self.assertEqual(self.boy.face_dir, -1)

    def test_running_draws_directional_animation(self):
        self.boy.set_direction(-1)
        self.boy.draw()
        self.image.clip_draw.assert_called_once_with(0, 0, 100, 100, 400, 90)

    def test_auto_run_uses_its_own_state_class(self):
        self.assertIsInstance(self.boy.auto_run, AutoRun)
        self.assertTrue(self.boy.activate_auto_run())
        self.assertEqual(self.boy.state, 'AutoRun')
        self.assertEqual(self.boy.auto_run.started_at, 1000)

    def test_auto_run_starts_in_last_facing_direction(self):
        self.boy.face_dir = -1
        self.boy.activate_auto_run()
        self.assertEqual(self.boy.direction, -1)

    def test_auto_run_can_only_start_from_idle(self):
        self.boy.set_direction(1)
        self.assertFalse(self.boy.activate_auto_run())
        self.assertEqual(self.boy.state, 'RUN')
        self.boy.set_direction(0)
        self.advance(5)
        self.assertFalse(self.boy.activate_auto_run())
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_auto_run_exit_resets_idle_state(self):
        self.boy.activate_auto_run()
        self.boy.finish_auto_run()
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.direction, 0)
        self.assertEqual(self.boy.idle_time, 0)

    def test_auto_run_moves_without_input(self):
        self.boy.activate_auto_run()
        self.advance(0.25)
        self.assertEqual(self.boy.x, 500)
        self.assertEqual(self.boy.state, 'AutoRun')

    def test_auto_run_movement_does_not_depend_on_frame_count(self):
        for intervals in ((0.25,), (0.125, 0.125)):
            with self.subTest(intervals=intervals):
                self.boy = Boy()
                self.boy.activate_auto_run()
                for seconds in intervals:
                    self.advance(seconds)
                self.assertEqual(self.boy.x, 500)

    def test_auto_run_does_not_include_time_before_entry(self):
        self.clock.return_value += 3
        self.boy.activate_auto_run()
        self.advance(0.125)
        self.assertEqual(self.boy.x, 450)

    def test_auto_run_doubles_speed_and_restores_it_on_exit(self):
        self.boy.activate_auto_run()
        self.assertEqual(self.boy.speed, 400)
        self.boy.finish_auto_run()
        self.assertEqual(self.boy.speed, 200)


if __name__ == '__main__':
    unittest.main()
