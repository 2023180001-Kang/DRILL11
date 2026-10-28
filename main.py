from pico2d import *

from grass import Grass
from boy import Boy

# Game object class here

def handle_events():
    global running
    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            running = False
        elif event.type == SDL_KEYDOWN and event.key == SDLK_SPACE:
            for o in world:
                if isinstance(o, Boy):
                    o.wake()
        elif event.type == SDL_KEYDOWN and event.key in (SDLK_LEFT, SDLK_RIGHT):
            pressed_keys.add(event.key)
            update_boy_directions()
        elif event.type == SDL_KEYUP and event.key in (SDLK_LEFT, SDLK_RIGHT):
            pressed_keys.discard(event.key)
            update_boy_directions()


def update_boy_directions():
    direction = int(SDLK_RIGHT in pressed_keys) - int(SDLK_LEFT in pressed_keys)
    for o in world:
        if isinstance(o, Boy):
            o.set_direction(direction)

def reset_world():
    global world

    world = []

    grass = Grass()
    world.append(grass)

    team = [Boy() for i in range(100)]
    world += team


def update_world():
    for o in world:
        o.update()
    pass


def render_world():
    clear_canvas()
    for o in world:
        o.draw()
    update_canvas()


running = True
pressed_keys = set()

open_canvas()
reset_world()
# game loop
while running:
    handle_events()
    update_world()
    render_world()
    delay(0.05)
# finalization code
close_canvas()