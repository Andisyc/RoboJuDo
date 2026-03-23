
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import time

class AgentPublisher(Node):
    def __init__(self):
        super().__init__('agent_publisher')
        self.publisher_ = self.create_publisher(String, '/agent/joy_cmd_json', 10)
        self.timer = self.create_timer(0.1, self.publish_command) # Publish every 100ms
        self.get_logger().info('Agent Publisher started. Publishing to /agent/joy_cmd_json')

    def publish_command(self):
        # --- Example: Simulate pushing the left stick forward ---
        axes_data = {
            "lx": 0.0,
            "ly": 0.8,  # Move forward
            "lt": 0.0,
            "rx": 0.0,
            "ry": 0.0,
            "rt": 0.0
        }

        # --- Example: Simulate pressing button 'A' ---
        # Note: process_triggers only responds to PRESS events.
        # To simulate a button press, you must send a "pressed: True" event.
        # To release it, you would send "pressed: False".
        # For simplicity, we send no button events here.
        button_events = [
            # {"type": "button", "name": "A", "pressed": True, "timestamp": time.time()}
        ]

        # Construct the final command and publish it as a JSON string
        command = {
            "axes": axes_data,
            "button_event": button_events,
        }
        
        msg = String()
        msg.data = json.dumps(command)
        self.publisher_.publish(msg)
        # self.get_logger().info(f'Publishing: "{msg.data}"')


def main(args=None):
    rclpy.init(args=args)
    agent_publisher = AgentPublisher()
    rclpy.spin(agent_publisher)
    agent_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
