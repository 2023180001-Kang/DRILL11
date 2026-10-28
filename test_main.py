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

    def test_arrow_press_cancels_in_pressed_direction(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.assertEqual(self.boy.state, 'RUN')
        self.assertEqual(self.boy.direction, -1)

    def test_arrow_release_does_not_cancel_auto_run(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.send(main.SDL_KEYDOWN, main.SDLK_RIGHT)
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.send(main.SDL_KEYUP, main.SDLK_LEFT)
        self.assertEqual(self.boy.state, 'AutoRun')

    def test_new_arrow_wins_when_cancelling_with_other_arrow_held(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.send(main.SDL_KEYDOWN, main.SDLK_RIGHT)
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.send(main.SDL_KEYUP, main.SDLK_LEFT)
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.assertEqual(self.boy.state, 'RUN')
        self.assertEqual(self.boy.direction, -1)

    def test_general_run_keeps_existing_opposite_key_rule(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.send(main.SDL_KEYDOWN, main.SDLK_RIGHT)
        self.assertEqual(self.boy.state, 'IDLE')
        self.send(main.SDL_KEYUP, main.SDLK_LEFT)
        self.assertEqual(self.boy.state, 'RUN')
        self.assertEqual(self.boy.direction, 1)

    def test_direction_input_wins_over_same_frame_timeout(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.clock.return_value += 5
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.boy.update()
        self.assertEqual(self.boy.state, 'RUN')
        self.assertEqual(self.boy.direction, -1)

    def test_vertical_arrows_keep_auto_run_active(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        for key in (main.SDLK_UP, main.SDLK_DOWN):
            self.send(main.SDL_KEYDOWN, key)
            self.assertEqual(self.boy.state, 'AutoRun')

    def test_repeated_a_does_not_extend_timer_or_restart_after_expiry(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        started_at = self.boy.auto_run.started_at
        self.clock.return_value += 4
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.assertEqual(self.boy.auto_run.started_at, started_at)
        self.clock.return_value += 1
        self.boy.update()
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.assertEqual(self.boy.state, 'IDLE')
        self.send(main.SDL_KEYUP, main.SDLK_a)
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.assertEqual(self.boy.state, 'AutoRun')
        self.assertEqual(self.boy.auto_run.started_at, started_at + 5)

    def test_releasing_a_keeps_auto_run_active(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.send(main.SDL_KEYUP, main.SDLK_a)
        self.assertEqual(self.boy.state, 'AutoRun')

    def test_repeated_held_arrow_does_not_cancel_auto_run(self):
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.send(main.SDL_KEYDOWN, main.SDLK_RIGHT)
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.assertEqual(self.boy.state, 'AutoRun')

    def test_world_keeps_grass_and_one_hundred_boys(self):
        with patch('main.Grass') as grass:
            main.reset_world()
        self.assertEqual(len(main.world), 101)
        self.assertIs(main.world[0], grass.return_value)
        self.assertEqual(sum(isinstance(obj, Boy) for obj in main.world), 100)

    def test_all_boys_auto_run_and_expire_together(self):
        with patch('main.Grass'):
            main.reset_world()
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        boys = main.world[1:]
        self.assertTrue(all(boy.state == 'AutoRun' and boy.invincible for boy in boys))
        self.clock.return_value += 5
        main.update_world()
        self.assertTrue(all(boy.state == 'IDLE' and not boy.invincible for boy in boys))

    def test_single_arrow_cancels_all_boys(self):
        with patch('main.Grass'):
            main.reset_world()
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.assertTrue(all(boy.state == 'RUN' and boy.direction == -1 for boy in main.world[1:]))

    def test_space_still_wakes_sleeping_boys(self):
        self.clock.return_value += 5
        main.update_world()
        self.send(main.SDL_KEYDOWN, main.SDLK_SPACE)
        self.assertEqual(self.boy.state, 'IDLE')

    def test_escape_and_window_close_stop_running(self):
        for event_type, key in ((main.SDL_KEYDOWN, main.SDLK_ESCAPE), (main.SDL_QUIT, None)):
            with self.subTest(event_type=event_type):
                main.running = True
                self.send(event_type, key)
                self.assertFalse(main.running)

    def test_game_loop_closes_canvas_after_quit(self):
        event = SimpleNamespace(type=main.SDL_QUIT)
        with patch('main.open_canvas') as opened, patch('main.close_canvas') as closed, \
                patch('main.reset_world'), patch('main.get_events', return_value=[event]), \
                patch('main.render_world'), patch('main.delay'):
            main.main()
        opened.assert_called_once_with(800, 600)
        closed.assert_called_once_with()

    def test_game_loop_closes_canvas_on_initialization_failure(self):
        with patch('main.open_canvas'), patch('main.close_canvas') as closed, \
                patch('main.reset_world', side_effect=RuntimeError('resource failure')):
            with self.assertRaisesRegex(RuntimeError, 'resource failure'):
                main.main()
        closed.assert_called_once_with()

    def test_activation_cancel_and_release_in_one_event_batch(self):
        events = [
            SimpleNamespace(type=main.SDL_KEYDOWN, key=main.SDLK_a),
            SimpleNamespace(type=main.SDL_KEYDOWN, key=main.SDLK_LEFT),
            SimpleNamespace(type=main.SDL_KEYUP, key=main.SDLK_LEFT),
        ]
        with patch('main.get_events', return_value=events):
            main.handle_events()
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.direction, 0)
        self.assertFalse(self.boy.invincible)

    def test_input_dispatch_with_mixed_character_states(self):
        moving, sleeping, active = Boy(), Boy(), Boy()
        moving.set_direction(1)
        sleeping.sleep()
        active.activate_auto_run()
        main.world.extend([moving, sleeping, active])
        self.send(main.SDL_KEYDOWN, main.SDLK_a)
        self.assertEqual([boy.state for boy in main.world], ['AutoRun', 'RUN', 'SLEEP', 'AutoRun'])
        self.send(main.SDL_KEYDOWN, main.SDLK_LEFT)
        self.assertTrue(all(boy.state == 'RUN' and boy.direction == -1 for boy in main.world))
        self.assertTrue(all(boy.speed == 200 and boy.scale == 1 and not boy.invincible for boy in main.world))


if __name__ == '__main__':
    unittest.main()
