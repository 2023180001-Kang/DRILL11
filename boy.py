from math import radians

from pico2d import get_time, load_image
from transitions import Machine


class AutoRun:
    def __init__(self, boy):
        self.boy = boy
        self.started_at = None

    def enter(self):
        self.started_at = get_time()
        self.boy.last_update_time = self.started_at
        self.boy.direction = self.boy.face_dir
        self.boy.frame = 0
        self.boy.idle_time = 0

    def exit(self):
        self.boy.direction = 0
        self.boy.frame = 0
        self.boy.idle_time = 0

    def update(self, delta_time):
        self.boy.x += self.boy.direction * self.boy.RUN_SPEED * delta_time


class Boy:
    RUN_SPEED = 200

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.direction = 0
        self.idle_time = 0
        self.last_update_time = get_time()
        self.image = load_image('animation_sheet.png')
        self.auto_run = AutoRun(self)
        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN', 'SLEEP', {
                'name': 'AutoRun',
                'on_enter': self.auto_run.enter,
                'on_exit': self.auto_run.exit,
            }],
            initial='IDLE',
            auto_transitions=False,
            transitions=[
                {'trigger': 'sleep', 'source': 'IDLE', 'dest': 'SLEEP'},
                {'trigger': 'wake_up', 'source': 'SLEEP', 'dest': 'IDLE'},
                {'trigger': 'start_running', 'source': ['IDLE', 'SLEEP'], 'dest': 'RUN'},
                {'trigger': 'stop_running', 'source': 'RUN', 'dest': 'IDLE'},
                {'trigger': 'begin_auto_run', 'source': 'IDLE', 'dest': 'AutoRun'},
                {'trigger': 'finish_auto_run', 'source': 'AutoRun', 'dest': 'IDLE'},
            ],
        )

    def activate_auto_run(self):
        if self.state == 'IDLE':
            return self.begin_auto_run()
        return False

    def update(self):
        current_time = get_time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        if self.state == 'IDLE':
            self.idle_time += delta_time
            if self.idle_time >= 5:
                self.sleep()
                self.idle_time = 0
            else:
                self.frame = (self.frame + 1) % 8
        elif self.state == 'RUN':
            self.x = max(50, min(750, self.x + self.direction * self.RUN_SPEED * delta_time))
            self.frame = (self.frame + 1) % 8
        elif self.state == 'AutoRun':
            self.auto_run.update(delta_time)

    def draw(self):
        if self.state == 'RUN':
            source_y = 100 if self.face_dir == 1 else 0
        else:
            source_y = 300 if self.face_dir == 1 else 200
        source_x = self.frame * 100

        if self.state == 'SLEEP':
            sleep_y = self.y - 20
            self.image.clip_composite_draw(
                source_x, source_y, 100, 100, radians(90 * self.face_dir), '', self.x, sleep_y, 100, 100
            )
        else:
            self.image.clip_draw(source_x, source_y, 100, 100, self.x, self.y)

    def set_direction(self, direction):
        self.direction = direction
        if direction == 0:
            if self.state == 'RUN':
                self.stop_running()
                self.idle_time = 0
                self.frame = 0
            return

        self.face_dir = direction
        if self.state != 'RUN':
            self.start_running()
            self.idle_time = 0
            self.frame = 0

    def wake(self):
        if self.state == 'SLEEP':
            self.wake_up()
            self.idle_time = 0
            self.frame = 0
