from ctypes import byref

import main as game
from boy import Boy


def send_key(event_type, key):
    event = game.SDL_Event()
    event.type = event_type
    event.key.keysym.sym = key
    if game.SDL_PushEvent(byref(event)) != 1:
        raise RuntimeError('Could not queue SDL keyboard event')
    game.handle_events()


def main():
    game.SDL_SetHint(b'SDL_WINDOW_NO_ACTIVATION_WHEN_SHOWN', b'1')
    game.open_canvas(800, 600)
    try:
        game.running = True
        game.pressed_keys.clear()
        game.reset_world()
        boys = [obj for obj in game.world if isinstance(obj, Boy)]
        assert len(boys) == 100
        phases = (('expiry', 5.1, 0), ('idle', 5.1, 0), ('cancel_left', 0.2, -1), ('cancel_right', 0.2, 1))
        for phase, duration, direction in phases:
            if phase != 'idle':
                send_key(game.SDL_KEYDOWN, game.SDLK_a)
                send_key(game.SDL_KEYUP, game.SDLK_a)
                assert all(boy.state == 'AutoRun' for boy in boys)
            if direction:
                start_positions = [boy.x for boy in boys]
                game.delay(0.025)
                key = game.SDLK_LEFT if direction == -1 else game.SDLK_RIGHT
                send_key(game.SDL_KEYDOWN, key)
                game.update_world()
                assert all((boy.x - start) * direction > 0 for boy, start in zip(boys, start_positions))
            observed_directions = set()
            deadline = game.get_time() + duration
            while game.get_time() < deadline:
                game.handle_events()
                if not game.running:
                    raise RuntimeError('Smoke test interrupted')
                game.update_world()
                game.render_world()
                for boy in boys:
                    if boy.state == 'AutoRun':
                        observed_directions.add(boy.direction)
                        assert 100 <= boy.x <= 700
                game.delay(0.01)
            expected_state = 'RUN' if direction else 'IDLE'
            assert all(boy.state == expected_state for boy in boys), (phase, {boy.state for boy in boys})
            assert all(boy.speed == 200 and boy.scale == 1 and not boy.invincible for boy in boys)
            if phase == 'expiry':
                assert observed_directions == {-1, 1}
            if direction:
                assert all(boy.direction == direction for boy in boys)
                assert all((boy.x - start) * direction > 20 for boy, start in zip(boys, start_positions))
                send_key(game.SDL_KEYUP, key)
                assert all(boy.state == 'IDLE' for boy in boys)
            print(f'Real canvas smoke test: {phase} OK (100 boys)')
    finally:
        game.close_canvas()


if __name__ == '__main__':
    main()
