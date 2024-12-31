from time import perf_counter, sleep
from threading import Thread, Lock, Event
import os
import asyncio
import pygame


os.chdir(os.path.abspath(os.path.dirname(__file__)))
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
pygame.init()


class Clock:
    def __init__(self, bpm, callback):
        self._mutex = Lock()
        self.bpm = bpm
        self.interval = 60.0 / (bpm * 96)
        self.running = Event()
        self.running.set()
        self.callback = callback
        self.thread = Thread(target=self._run)
        self.thread.start()

    def _run(self):
        next_time = perf_counter()
        while self.running.is_set():
            current_time = perf_counter()
            elapsed = current_time - next_time
            if elapsed >= self.interval:
                # print("callback")
                self.callback()
                next_time += self.interval
            else:
                sleep(self.interval - elapsed)

    def set_bpm(self, bpm):
        with self._mutex:
            if bpm != self.bpm:
                self.bpm = bpm
                self.interval = 60.0 / (bpm * 96)

    def stop(self):
        self.running.clear()
        self.thread.join()


class InputHandler:
    def __init__(self, app):
        self.app = app
        pygame.joystick.init()
        pygame.key.set_repeat(180, 36)

    def check_for_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Quit event detected.")
                return "Exit"
            else:
                pass  # handle events here
            
            
class Renderer:
    def __init__(self):
        pygame.display.init() 
        self.screen = pygame.display.set_mode((1280, 720), vsync=1)
        self.font = pygame.font.SysFont("Consolas", 32, bold=True)

    def update_view(self, beat):
        self.screen.fill((40, 60, 60))
        rendered_text = self.font.render(f"Beat {beat}", 1, (255, 255, 255))
        self.screen.blit(rendered_text, (570, 350))
        pygame.display.flip()
        
        
        
class App:
    def __init__(self):
        self.ticks = 0
        self._tick_mutex = Lock()
        self.clock = Clock(bpm=120, callback=self.tick)
        self.input_handler = InputHandler(self)
        self.renderer = Renderer()
        self.running = False

    def tick(self):
        self.ticks += 1
        if self.ticks % 96 == 0:
            print("Beat", self.ticks // 96)

    async def handle_events(self):
        r = self.input_handler.check_for_events()
        if r == "Exit":
            self.running = False
        
    async def running_loop(self):
        self.running = True
        while self.running:
            events_task = asyncio.create_task(self.handle_events())
            update_task = asyncio.create_task(
                asyncio.to_thread(self.update_view_states)
            )
            await asyncio.gather(events_task, update_task)
        self.quit()
        
    def update_view_states(self):
        self.renderer.update_view(self.ticks // 96)
        
    def quit(self):
        self.clock.stop()
        pygame.quit()


def main():
    app = App()
    asyncio.run(app.running_loop())


if __name__ == "__main__":
    main()
