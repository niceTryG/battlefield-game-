from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.label import Label


class MyWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.width = Window.width
        self.height = Window.height

        # ---------- Assets ----------
        self.fighter_image = "./images/fighter.png"
        self.barrier_image = "./images/barier.png"
        self.left_wall_image = "./images/left.png"
        self.right_wall_image = "./images/right.png"
        self.missile_image = "./images/missile.png"        # yellow bullet
        self.fire_left_image = "./images/fire_left.png"
        self.fire_right_image = "./images/fire_right.png"
        self.fire_left_dmg_image = "./images/fire_left_damaged.png"
        self.fire_right_dmg_image = "./images/fire_right_damaged.png"

        # ---------- Sizes (matched to your sprites / layout) ----------
        self.wall_width = 20
        self.barrier_w = 184      # from barier.png
        self.barrier_h = 20
        self.launcher_size = (34, 34)
        self.fighter_size = (64, 64)
        self.player_bullet_size = (12, 12)
        self.enemy_bullet_size = (12, 12)

        # ---------- Speeds ----------
        self.fighter_speed = 10
        self.barrier_speed = 4
        self.player_bullet_speed = self.fighter_speed * 2
        self.enemy_bullet_speed = self.fighter_speed * 2   # as required

        # ---------- State ----------
        self.direction = 0
        self.missiles = []        # player bullets
        self.fire_bullets = []    # enemy bullets
        self.score = 0

        # ---------- Draw static + initial objects ----------
        with self.canvas:
            # Walls (vertical)
            self.left_wall = Rectangle(
                source=self.left_wall_image,
                size=(self.wall_width, self.height),
                pos=(0, 0)
            )
            self.right_wall = Rectangle(
                source=self.right_wall_image,
                size=(self.wall_width, self.height),
                pos=(self.width - self.wall_width, 0)
            )

            # Barriers (horizontal, smaller)
            # Left barrier near top, starting from left wall
            self.barrier_left = Rectangle(
                source=self.barrier_image,
                size=(self.barrier_w, self.barrier_h),
                pos=(self.wall_width, self.height * 0.75)
            )
            # Right barrier mid-screen, ending at right wall
            self.barrier_right = Rectangle(
                source=self.barrier_image,
                size=(self.barrier_w, self.barrier_h),
                pos=(self.width - self.wall_width - self.barrier_w,
                     self.height * 0.4)
            )

            # Fighter at bottom center
            self.fighter = Rectangle(
                source=self.fighter_image,
                size=self.fighter_size,
                pos=(self.width / 2 - self.fighter_size[0] / 2, 40)
            )

            # Fire launchers attached to barriers
            # Left barrier's launcher on its right end, firing down-right
            self.launcher_left_rect = Rectangle(
                source=self.fire_left_image,
                size=self.launcher_size,
                pos=(self.barrier_left.pos[0] + self.barrier_w - self.launcher_size[0],
                     self.barrier_left.pos[1] - self.launcher_size[1] / 2)
            )
            # Right barrier's launcher on its left end, firing down-left
            self.launcher_right_rect = Rectangle(
                source=self.fire_right_image,
                size=self.launcher_size,
                pos=(self.barrier_right.pos[0],
                     self.barrier_right.pos[1] - self.launcher_size[1] / 2)
            )

        # ---------- Launcher state machine ----------
        # dir: +1 => fire to the right, -1 => fire to the left
        self.launchers = [
            {
                "name": "left",
                "barrier": self.barrier_left,
                "rect": self.launcher_left_rect,
                "dir": 1,
                "active": True,
                "hits": 0,
                "healthy": self.fire_left_image,
                "damaged": self.fire_left_dmg_image,
            },
            {
                "name": "right",
                "barrier": self.barrier_right,
                "rect": self.launcher_right_rect,
                "dir": -1,
                "active": True,
                "hits": 0,
                "healthy": self.fire_right_image,
                "damaged": self.fire_right_dmg_image,
            },
        ]

        # ---------- UI ----------
        self.score_label = Label(
        text="Scores : 0",
        font_size=24,
        color=(1, 1, 1, 1),
        size_hint=(None, None),
        size=(200, 40),
        pos=(self.width / 2 - 100, self.height - 50)  # centered-ish at top
        )
        self.add_widget(self.score_label)

        # ---------- Input ----------
        self.keyboard = Window.request_keyboard(self.on_keyboard_closed, self)
        if self.keyboard:
            self.keyboard.bind(on_key_down=self.on_key_down,
                               on_key_up=self.on_key_up)

        # ---------- Loops ----------
        Clock.schedule_interval(self.update, 1 / 60.0)
        Clock.schedule_interval(self.launch_fire_from_launchers, 1.0)

    # ================== INPUT ==================

    def on_keyboard_closed(self, *args):
        if self.keyboard:
            self.keyboard.unbind(on_key_down=self.on_key_down,
                                 on_key_up=self.on_key_up)
            self.keyboard = None

    def on_key_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == "right":
            self.direction = 1
        elif keycode[1] == "left":
            self.direction = -1
        elif keycode[1] == "spacebar":
            self.fire_player_missile()

    def on_key_up(self, keyboard, keycode):
        if keycode[1] in ("right", "left"):
            self.direction = 0

    # ================== PLAYER MISSILE ==================

    def fire_player_missile(self):
        fx, fy = self.fighter.pos
        fw, fh = self.fighter.size
        mx = fx + fw / 2 - self.player_bullet_size[0] / 2
        my = fy + fh

        with self.canvas:
            rect = Rectangle(
                source=self.missile_image,
                size=self.player_bullet_size,
                pos=(mx, my)
            )
        self.missiles.append(rect)

    # ================== ENEMY FIRE ==================

    def launch_fire_from_launchers(self, dt):
        # Each ACTIVE launcher fires once per second
        for launcher in self.launchers:
            if not launcher["active"]:
                continue

            lrect = launcher["rect"]
            lx, ly = lrect.pos
            lw, lh = lrect.size

            # From tip of the launcher
            if launcher["dir"] == 1:
                start_x = lx + lw   # right tip
            else:
                start_x = lx        # left tip

            start_y = ly

            dx = self.enemy_bullet_speed * launcher["dir"]
            dy = -self.enemy_bullet_speed  # downward

            with self.canvas:
                bullet_rect = Rectangle(
                    source=self.missile_image,
                    size=self.enemy_bullet_size,
                    pos=(start_x, start_y)
                )

            self.fire_bullets.append({
                "rect": bullet_rect,
                "dx": dx,
                "dy": dy,
            })

    # ================== MAIN UPDATE LOOP ==================

    def update(self, dt):
        # ----- Move fighter within walls -----
        fx, fy = self.fighter.pos
        fw, fh = self.fighter.size

        if (self.direction == 1 and
                fx + fw + self.fighter_speed <= self.width - self.wall_width):
            self.fighter.pos = (fx + self.fighter_speed, fy)
        elif (self.direction == -1 and
                fx - self.fighter_speed >= self.wall_width):
            self.fighter.pos = (fx - self.fighter_speed, fy)

        # ----- Move barriers down, wrap, and update launcher attachments -----
        for launcher in self.launchers:
            barrier = launcher["barrier"]
            bx, by = barrier.pos

            # move down
            barrier.pos = (bx, by - self.barrier_speed)

            # if gone below screen -> wrap to top & reset launcher
            if barrier.pos[1] + barrier.size[1] < 0:
                barrier.pos = (barrier.pos[0], self.height)

                launcher["active"] = True
                launcher["hits"] = 0
                launcher["rect"].source = launcher["healthy"]
                launcher["rect"].size = self.launcher_size

            # keep launcher stuck to its barrier
            if launcher["name"] == "left":
                # right end of left barrier
                launcher["rect"].pos = (
                    barrier.pos[0] + self.barrier_w - self.launcher_size[0],
                    barrier.pos[1] - self.launcher_size[1] / 2
                )
            else:
                # left end of right barrier
                launcher["rect"].pos = (
                    barrier.pos[0],
                    barrier.pos[1] - self.launcher_size[1] / 2
                )

        # ----- Move player missiles & check hits on launchers -----
        for missile in self.missiles[:]:
            x, y = missile.pos
            missile.pos = (x, y + self.player_bullet_speed)

            # off top -> remove
            if missile.pos[1] > self.height:
                self._remove_player_missile(missile)
                continue

            # collision with active launchers
            for launcher in self.launchers:
                if launcher["active"] and self.check_collision(missile, launcher["rect"]):
                    launcher["hits"] += 1
                    self._remove_player_missile(missile)

                    if launcher["hits"] >= 20 and launcher["active"]:
                        self.break_launcher(launcher)
                    break

        # ----- Move enemy bullets & check for fighter hit -----
        for bullet in self.fire_bullets[:]:
            rect = bullet["rect"]
            x, y = rect.pos
            rect.pos = (x + bullet["dx"], y + bullet["dy"])

            bx, by = rect.pos
            bw, bh = rect.size

            # off-screen -> delete
            if bx + bw < 0 or bx > self.width or by + bh < 0:
                self.fire_bullets.remove(bullet)
                self.canvas.remove(rect)
                continue


    # ================== HELPERS ==================

    def _remove_player_missile(self, missile):
        if missile in self.missiles:
            self.missiles.remove(missile)
            self.canvas.remove(missile)

    def check_collision(self, r1, r2):
        x1, y1 = r1.pos
        w1, h1 = r1.size
        x2, y2 = r2.pos
        w2, h2 = r2.size

        return (
            x1 < x2 + w2 and
            x1 + w1 > x2 and
            y1 < y2 + h2 and
            y1 + h1 > y2
        )

    def break_launcher(self, launcher):
        launcher["active"] = False
        launcher["rect"].source = launcher["damaged"]
        # visually can keep small or same; here we keep same size
        self.score += 1
        self.score_label.text = f"Scores : {self.score}"

    def game_over(self):
        Clock.unschedule(self.update)
        Clock.unschedule(self.launch_fire_from_launchers)
        self.score_label.text = "Game Over"
        print("Game Over")

class MyApp(App):
    def build(self):
        # black background like in screenshot
        root = MyWidget()
        return root


if __name__ == "__main__":
    MyApp().run()
