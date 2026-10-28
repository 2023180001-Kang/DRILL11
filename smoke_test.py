import main as game
from boy import Boy


def main():
    game.open_canvas(800, 600)
    try:
        game.reset_world()
        boys = [obj for obj in game.world if isinstance(obj, Boy)]
        assert len(boys) == 100
        for phase, duration in (('expiry', 5.1), ('cancel', 0.2)):
            for boy in boys:
                boy.activate_auto_run()
                if phase == 'cancel':
                    boy.set_direction(-1)
            observed_directions = set()
            deadline = game.get_time() + duration
            while game.get_time() < deadline:
                for event in game.get_events():
                    if event.type == game.SDL_QUIT or (
                        event.type == game.SDL_KEYDOWN and event.key == game.SDLK_ESCAPE
                    ):
                        raise RuntimeError('Smoke test interrupted')
                game.update_world()
                game.render_world()
                for boy in boys:
                    if boy.state == 'AutoRun':
                        observed_directions.add(boy.direction)
                        assert 100 <= boy.x <= 700
                game.delay(0.01)
            expected_state = 'IDLE' if phase == 'expiry' else 'RUN'
            assert all(boy.state == expected_state for boy in boys)
            assert all(boy.speed == 200 and boy.scale == 1 and not boy.invincible for boy in boys)
            if phase == 'expiry':
                assert observed_directions == {-1, 1}
            else:
                assert all(boy.direction == -1 for boy in boys)
            print(f'Real canvas smoke test: {phase} OK (100 boys)')
    finally:
        game.close_canvas()


if __name__ == '__main__':
    main()
