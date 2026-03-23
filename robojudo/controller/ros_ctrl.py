import time
from queue import Empty, Queue

from robojudo.controller import Controller, ctrl_registry
from robojudo.controller.ctrl_cfgs import CtrlCfg  # We will create RosCtrlCfg soon
from robojudo.controller.utils.ros_joystick import ROS2JoystickThread, DEFAULT_AXIS_MAP


# We will define RosCtrlCfg properly in ctrl_cfgs.py later
class RosCtrlCfg(CtrlCfg):
    ctrl_type: str = "RosCtrl"


@ctrl_registry.register
class RosCtrl(Controller):
    cfg_ctrl: RosCtrlCfg

    def __init__(self, cfg_ctrl: RosCtrlCfg, env=None, device="cpu"):
        super().__init__(cfg_ctrl=cfg_ctrl, env=env, device=device)

        self.state_queue = Queue(maxsize=2)  # for axes
        self.event_queue = Queue(maxsize=100)  # for button events
        self.ros_joystick_thread = ROS2JoystickThread(self.state_queue, self.event_queue)
        self.ros_joystick_thread.start()

        self.axes_names = DEFAULT_AXIS_MAP.values()
        self.reset()

    def reset(self):
        self.combination_init_buttons = self.cfg_ctrl.combination_init_buttons
        self.onhold_buttons = set()
        while not self.state_queue.empty():
            try:
                self.state_queue.get_nowait()
            except Empty:
                break

        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except Empty:
                break

        self.last_state = {
            "type": "axes",
            "axes": {name: 0.0 for name in self.axes_names},
            "timestamp": time.time(),
        }

    def get_state(self):
        try:
            state = self.state_queue.get_nowait()
            self.last_state = state.copy()
        except Empty:
            state = self.last_state

        return state

    def get_events(self):
        events = []
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                events.append(event)
            except Empty:
                break
        return events

    def get_data(self):
        state = self.get_state()
        events = self.get_events()

        return {
            "axes": state["axes"],
            "button_event": events,
        }

    def process_triggers(self, ctrl_data):
        # This logic is copied from JoystickCtrl and should work the same way
        commands = []
        if len(self.triggers) == 0:
            return ctrl_data, commands

        for event in ctrl_data["button_event"]:
            if event["type"] == "button":
                if event["name"] in self.combination_init_buttons:
                    if event["pressed"]:
                        self.onhold_buttons.add(event["name"])
                    else:
                        self.onhold_buttons.discard(event["name"])
                else:
                    if event["pressed"]:
                        command = None
                        if len(self.onhold_buttons) == 0:
                            command = self.triggers.get(event["name"], None)
                        else:
                            event_combination = "+".join(sorted(list(self.onhold_buttons)) + [event["name"]])
                            command = self.triggers.get(event_combination, None)
                        if command is not None:
                            commands.append(command)
                            # remove event after triggered
                            ctrl_data["button_event"].remove(event)

        return ctrl_data, commands
