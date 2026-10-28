import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from boy import AutoRun, Boy


class BoyTests(unittest.TestCase):
    def setUp(self):
        clock = patch('boy.get_time', return_value=1000.0)
        self.clock = clock.start()
        self.addCleanup(clock.stop)
        image = patch('boy.load_image', return_value=Mock())
        self.load_image = image.start()
        self.image = self.load_image.return_value
        self.addCleanup(image.stop)
        canvas = patch('boy.get_canvas_width', return_value=800)
        canvas.start()
        self.addCleanup(canvas.stop)
        self.boy = Boy()

    def advance(self, seconds):
        self.clock.return_value += seconds
        self.boy.update()

    def test_initial_state_is_idle(self):
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.direction, 0)

    def test_sprite_path_is_relative_to_module_not_working_directory(self):
        self.load_image.assert_called_once_with(str(Path(__file__).resolve().with_name('animation_sheet.png')))

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
        self.image.clip_draw.assert_called_once_with(0, 0, 100, 100, 400, 90, 100, 100)

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

    def test_auto_run_draws_enlarged_running_sprite_with_feet_grounded(self):
        self.boy.activate_auto_run()
        self.boy.draw()
        self.image.clip_draw.assert_called_once_with(0, 100, 100, 100, 400, 140, 200, 200)

    def test_auto_run_restores_normal_size_on_exit(self):
        self.boy.activate_auto_run()
        self.boy.finish_auto_run()
        self.boy.draw()
        self.assertEqual(self.boy.scale, 1)
        self.image.clip_draw.assert_called_once_with(0, 300, 100, 100, 400, 90, 100, 100)

    def test_auto_run_bounces_at_both_enlarged_boundaries(self):
        for start, direction, edge in ((690, 1, 700), (110, -1, 100)):
            with self.subTest(direction=direction):
                self.boy = Boy()
                self.boy.x = start
                self.boy.face_dir = direction
                self.boy.activate_auto_run()
                started_at = self.boy.auto_run.started_at
                self.advance(0.1)
                self.assertEqual(self.boy.x, edge)
                self.assertEqual(self.boy.direction, -direction)
                self.assertEqual(self.boy.face_dir, -direction)
                self.assertEqual(self.boy.auto_run.started_at, started_at)
                self.advance(0.1)
                self.assertAlmostEqual(self.boy.x, edge - direction * 40)

    def test_auto_run_entry_corrects_position_for_enlargement(self):
        for start, expected in ((50, 100), (750, 700)):
            with self.subTest(start=start):
                self.boy = Boy()
                self.boy.x = start
                self.boy.activate_auto_run()
                self.assertEqual(self.boy.x, expected)

    def test_auto_run_clamps_large_frame_overshoot(self):
        self.boy.activate_auto_run()
        self.advance(2)
        self.assertEqual(self.boy.x, 700)
        self.assertEqual(self.boy.direction, -1)

    def test_auto_run_expires_at_five_seconds(self):
        self.boy.activate_auto_run()
        self.advance(4.999)
        self.assertEqual(self.boy.state, 'AutoRun')
        self.clock.return_value = self.boy.auto_run.started_at + 5
        self.boy.update()
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.direction, 0)
        self.assertEqual(self.boy.speed, 200)
        self.assertEqual(self.boy.scale, 1)
        x = self.boy.x
        self.advance(0.25)
        self.assertEqual(self.boy.x, x)

    def test_auto_run_expires_on_first_update_after_deadline(self):
        self.boy.activate_auto_run()
        self.advance(6)
        self.assertEqual(self.boy.state, 'IDLE')
        self.assertEqual(self.boy.idle_time, 0)

    def test_auto_run_expiration_does_not_depend_on_frame_count(self):
        for intervals in ((5,), (1, 1, 1, 1, 1), (0.25,) * 20):
            with self.subTest(intervals=intervals):
                self.boy = Boy()
                self.boy.activate_auto_run()
                for seconds in intervals:
                    self.advance(seconds)
                self.assertEqual(self.boy.state, 'IDLE')

    def test_direction_cancels_auto_run_and_restores_normal_movement(self):
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                self.boy = Boy()
                self.boy.activate_auto_run()
                self.boy.set_direction(direction)
                self.assertEqual(self.boy.state, 'RUN')
                self.assertEqual(self.boy.direction, direction)
                self.assertEqual(self.boy.face_dir, direction)
                self.assertEqual(self.boy.speed, 200)
                self.assertEqual(self.boy.scale, 1)
                self.advance(0.25)
                self.assertEqual(self.boy.x, 400 + direction * 50)

    def test_zero_direction_does_not_cancel_auto_run(self):
        self.boy.activate_auto_run()
        self.boy.set_direction(0)
        self.advance(0.25)
        self.assertEqual(self.boy.state, 'AutoRun')
        self.assertEqual(self.boy.x, 500)

    def test_cancel_does_not_reuse_time_spent_in_auto_run(self):
        self.boy.activate_auto_run()
        self.clock.return_value += 2
        self.boy.set_direction(-1)
        self.boy.update()
        self.assertEqual(self.boy.x, 400)

    def test_auto_run_blocks_test_damage(self):
        received_damage = []

        def apply_test_damage():
            if self.boy.can_take_damage():
                received_damage.append(1)

        apply_test_damage()
        self.boy.activate_auto_run()
        self.assertTrue(self.boy.invincible)
        apply_test_damage()
        self.assertEqual(received_damage, [1])
        self.boy.set_direction(-1)
        apply_test_damage()
        self.assertEqual(received_damage, [1, 1])

    def test_both_exit_paths_remove_invincibility(self):
        for cancel in (True, False):
            with self.subTest(cancel=cancel):
                self.boy = Boy()
                self.boy.activate_auto_run()
                if cancel:
                    self.boy.set_direction(1)
                else:
                    self.advance(5)
                self.assertFalse(self.boy.invincible)
                self.assertTrue(self.boy.can_take_damage())

    def test_normal_states_do_not_gain_invincibility(self):
        self.assertTrue(self.boy.can_take_damage())
        self.boy.set_direction(-1)
        self.assertTrue(self.boy.can_take_damage())
        self.boy.set_direction(0)
        self.advance(5)
        self.assertTrue(self.boy.can_take_damage())

    def test_active_auto_run_ignores_reactivation(self):
        self.boy.activate_auto_run()
        started_at = self.boy.auto_run.started_at
        self.advance(2)
        self.assertFalse(self.boy.activate_auto_run())
        self.assertEqual(self.boy.auto_run.started_at, started_at)

    def test_auto_run_animation_is_time_based(self):
        for intervals in ((0.25,), (0.125, 0.125)):
            with self.subTest(intervals=intervals):
                self.boy = Boy()
                self.boy.activate_auto_run()
                for seconds in intervals:
                    self.advance(seconds)
                self.assertEqual(self.boy.frame, 5)

    def test_auto_run_draw_uses_integer_sprite_frame(self):
        self.boy.activate_auto_run()
        self.advance(0.0625)
        self.boy.draw()
        self.image.clip_draw.assert_called_once_with(100, 100, 100, 100, 425, 140, 200, 200)

    def test_repeated_auto_run_entries_reset_timer_without_stacking_effects(self):
        for cycle in range(6):
            with self.subTest(cycle=cycle):
                self.boy.activate_auto_run()
                self.assertEqual(self.boy.auto_run.started_at, self.clock.return_value)
                self.assertEqual(self.boy.speed, 400)
                self.assertEqual(self.boy.scale, 2)
                self.assertTrue(self.boy.invincible)
                if cycle % 2:
                    self.boy.set_direction(-1)
                    self.boy.set_direction(0)
                else:
                    self.advance(5)
                self.assertEqual(self.boy.state, 'IDLE')
                self.assertEqual(self.boy.speed, 200)
                self.assertEqual(self.boy.scale, 1)
                self.assertFalse(self.boy.invincible)
                self.advance(0.25)

    def test_timeout_starts_a_fresh_idle_sleep_countdown(self):
        self.advance(4)
        self.boy.activate_auto_run()
        self.advance(5)
        self.assertEqual(self.boy.state, 'IDLE')
        self.advance(4)
        self.assertEqual(self.boy.state, 'IDLE')
        self.advance(1)
        self.assertEqual(self.boy.state, 'SLEEP')

    def test_wake_does_not_interrupt_auto_run(self):
        self.boy.activate_auto_run()
        self.boy.wake()
        self.assertEqual(self.boy.state, 'AutoRun')

    def test_sleeping_draw_retains_existing_rotation_and_size(self):
        self.advance(5)
        self.boy.draw()
        args = self.image.clip_composite_draw.call_args.args
        self.assertEqual(args[:4], (0, 300, 100, 100))
        self.assertAlmostEqual(args[4], 1.5707963267948966)
        self.assertEqual(args[5:], ('', 400, 70, 100, 100))

    def test_auto_run_bounce_draws_opposite_facing_row(self):
        self.boy.x = 690
        self.boy.activate_auto_run()
        self.advance(0.125)
        self.boy.draw()
        self.assertEqual(self.image.clip_draw.call_args.args[1], 0)

    def test_late_update_only_moves_for_the_active_five_seconds(self):
        self.boy.RUN_SPEED = 10
        self.boy.activate_auto_run()
        self.advance(6)
        self.assertEqual(self.boy.x, 500)
        self.assertEqual(self.boy.state, 'IDLE')

    def test_auto_run_uses_actual_canvas_width_for_right_boundary(self):
        with patch('boy.get_canvas_width', return_value=1000):
            self.boy.x = 890
            self.boy.activate_auto_run()
            self.advance(0.125)
        self.assertEqual(self.boy.x, 900)
        self.assertEqual(self.boy.direction, -1)


if __name__ == '__main__':
    unittest.main()
