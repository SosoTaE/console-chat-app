import socket
import threading
import json
import curses
import time
from datetime import datetime


class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.messages = []
        self.scroll_pos = 0
        self.input_text = ""
        self.cursor_pos = 0
        self.channel_name = ""
        self.member_name = ""
        self.channel_joined = False

    def connect(self):
        """Connect to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            return False

    def create_channel(self, channel_name, channel_password, member_name):
        """Create a new channel"""
        if not self.connected:
            return False

        request = {
            "action": "createChannel",
            "channelName": channel_name,
            "channelPassword": channel_password,
            "memberName": member_name
        }

        try:
            self.socket.send(json.dumps(request).encode('utf-8'))
            response = self.socket.recv(1024)
            response_data = json.loads(response.decode('utf-8'))
            return response_data.get("success", False)
        except Exception as e:
            return False

    def join_channel(self, channel_name, channel_password, member_name):
        """Join an existing channel"""
        if not self.connected:
            return False

        request = {
            "action": "joinChannel",
            "channelName": channel_name,
            "channelPassword": channel_password,
            "memberName": member_name
        }

        try:
            self.socket.send(json.dumps(request).encode('utf-8'))
            response = self.socket.recv(1024)
            response_data = json.loads(response.decode('utf-8'))

            if response_data.get("success", False):
                self.channel_name = channel_name
                self.member_name = member_name
                self.channel_joined = True
                return True
            return False
        except Exception as e:
            return False

    def send_message(self, message):
        """Send a message to the channel"""
        if not self.channel_joined:
            return False

        message_data = {
            "action": "message",
            "message": message,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

        try:
            self.socket.send(json.dumps(message_data).encode('utf-8'))

            return True
        except Exception as e:
            self.messages.append(f"ERROR: Failed to send message: {str(e)}")
            return False

    def listen_for_messages(self, stdscr):
        """Listen for incoming messages in a separate thread"""
        while self.connected and self.channel_joined:
            try:
                message = self.socket.recv(1024)
                if not message:
                    break

                data = json.loads(message.decode('utf-8'))



                member_name = data.get("memberName", "Unknown")
                message_text = data.get("message", "")
                timestamp = data.get("timestamp", datetime.now().strftime("%H:%M:%S"))

                if message_text:  # Only add if there's actual message content
                    formatted_message = f"[{timestamp}] {member_name}: {message_text}"
                    self.messages.append(formatted_message)

                # Auto-scroll to bottom if we're at the bottom
                message_area_height = self.get_message_area_height()
                max_scroll = max(0, len(self.messages) - message_area_height)
                if self.scroll_pos >= max_scroll - 1:  # Near bottom
                    self.scroll_pos = max_scroll

                # Refresh the display
                self.draw_interface(stdscr)
                stdscr.refresh()

            except json.JSONDecodeError as e:
                # Handle JSON decode errors
                self.messages.append(f"ERROR: Invalid JSON received: {message.decode('utf-8', errors='ignore')}")
            except Exception as e:
                self.messages.append(f"ERROR: Connection error: {str(e)}")
                break

    def get_message_area_height(self):
        """Get the height of the message display area"""
        return curses.LINES - 5  # Reserve space for borders and input

    def draw_interface(self, stdscr):
        """Draw the chat interface"""
        stdscr.clear()

        # Draw title
        title = f"Chat Client - Channel: {self.channel_name}"
        stdscr.addstr(0, 0, title[:curses.COLS - 1])

        # Draw horizontal line
        stdscr.addstr(1, 0, "-" * (curses.COLS - 1))

        # Draw messages
        message_area_height = self.get_message_area_height()
        start_y = 2

        # Calculate which messages to display based on scroll position
        visible_messages = self.messages[self.scroll_pos:self.scroll_pos + message_area_height]

        for i, message in enumerate(visible_messages):
            if start_y + i < curses.LINES - 3:
                # Truncate message if it's too long
                display_message = message[:curses.COLS - 1]
                stdscr.addstr(start_y + i, 0, display_message)

        # Draw input area separator
        input_y = curses.LINES - 3
        stdscr.addstr(input_y, 0, "-" * (curses.COLS - 1))

        # Draw input prompt and text
        prompt = "Message: "
        stdscr.addstr(input_y + 1, 0, prompt)

        # Display input text with cursor
        input_display = self.input_text
        if len(input_display) > curses.COLS - len(prompt) - 1:
            # Scroll input text if it's too long
            start_pos = max(0, self.cursor_pos - (curses.COLS - len(prompt) - 10))
            input_display = input_display[start_pos:]

        stdscr.addstr(input_y + 1, len(prompt), input_display[:curses.COLS - len(prompt) - 1])

        # Position cursor
        cursor_x = len(prompt) + min(self.cursor_pos, curses.COLS - len(prompt) - 1)
        stdscr.move(input_y + 1, cursor_x)

        # Draw help text
        help_text = "Ctrl+C: Quit | Up/Down: Scroll | Enter: Send message"
        if curses.LINES > input_y + 2:
            stdscr.addstr(input_y + 2, 0, help_text[:curses.COLS - 1])

    def handle_input(self, stdscr, key):
        """Handle keyboard input"""
        if key == curses.KEY_UP:
            # Scroll up
            self.scroll_pos = max(0, self.scroll_pos - 1)
        elif key == curses.KEY_DOWN:
            # Scroll down
            max_scroll = max(0, len(self.messages) - self.get_message_area_height())
            self.scroll_pos = min(max_scroll, self.scroll_pos + 1)
        elif key == curses.KEY_LEFT:
            # Move cursor left
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif key == curses.KEY_RIGHT:
            # Move cursor right
            self.cursor_pos = min(len(self.input_text), self.cursor_pos + 1)
        elif key == curses.KEY_BACKSPACE or key == 127:
            # Delete character
            if self.cursor_pos > 0:
                self.input_text = self.input_text[:self.cursor_pos - 1] + self.input_text[self.cursor_pos:]
                self.cursor_pos -= 1
        elif key == 10 or key == 13:  # Enter key
            # Send message
            if self.input_text.strip():
                if self.input_text.strip().lower() == '/test':
                    # Add a test message locally to verify interface works
                    self.messages.append(f"[{datetime.now().strftime('%H:%M:%S')}] System: Test message added locally")
                else:
                    self.send_message(self.input_text.strip())
                self.input_text = ""
                self.cursor_pos = 0
        elif 32 <= key <= 126:  # Printable characters
            # Add character to input
            self.input_text = self.input_text[:self.cursor_pos] + chr(key) + self.input_text[self.cursor_pos:]
            self.cursor_pos += 1

    def run_chat_interface(self, stdscr):
        """Main chat interface loop"""
        # Setup curses
        curses.curs_set(1)  # Show cursor
        stdscr.nodelay(1)  # Don't block on getch()
        stdscr.timeout(100)  # Refresh every 100ms

        # Start message listener thread
        listener_thread = threading.Thread(target=self.listen_for_messages, args=(stdscr,))
        listener_thread.daemon = True
        listener_thread.start()

        # Main input loop
        while True:
            try:
                self.draw_interface(stdscr)
                stdscr.refresh()

                key = stdscr.getch()
                if key != -1:  # Key was pressed
                    if key == 3:  # Ctrl+C
                        break
                    self.handle_input(stdscr, key)

                time.sleep(0.01)  # Small delay to prevent high CPU usage

            except KeyboardInterrupt:
                break

    def disconnect(self):
        """Disconnect from the server"""
        self.connected = False
        if self.socket:
            self.socket.close()


def setup_connection():
    """Setup connection dialog"""
    print("Chat Client Setup")
    print("-" * 20)

    host = input("Server host (default: localhost): ").strip() or "localhost"
    port = input("Server port (default: 12345): ").strip() or "12345"

    try:
        port = int(port)
    except ValueError:
        print("Invalid port number. Using default 12345.")
        port = 12345

    print("\nConnecting to server...")
    client = ChatClient(host, port)

    if not client.connect():
        print(f"Failed to connect to {host}:{port}")
        return None

    print("Connected successfully!")

    # Channel setup
    print("\nChannel Setup")
    action = input("Create new channel or join existing? (create/join): ").strip().lower()

    channel_name = input("Channel name: ").strip()
    channel_password = input("Channel password: ").strip()
    member_name = input("Your name: ").strip()

    if not all([channel_name, member_name]):
        print("Channel name and member name are required.")
        client.disconnect()
        return None

    if action == "create":
        if client.create_channel(channel_name, channel_password, member_name):
            print("Channel created successfully!")
            # After creating, we need to join it
            if client.join_channel(channel_name, channel_password, member_name):
                print("Joined channel successfully!")
                return client
            else:
                print("Failed to join the created channel.")
                client.disconnect()
                return None
        else:
            print("Failed to create channel.")
            client.disconnect()
            return None
    else:
        if client.join_channel(channel_name, channel_password, member_name):
            print("Joined channel successfully!")
            return client
        else:
            print("Failed to join channel.")
            client.disconnect()
            return None


def main():
    client = setup_connection()
    if not client:
        return

    print("\nStarting chat interface...")
    print("Use Ctrl+C to quit, Up/Down arrows to scroll messages")
    time.sleep(2)

    try:
        curses.wrapper(client.run_chat_interface)
    except KeyboardInterrupt:
        pass
    finally:
        client.disconnect()
        print("\nDisconnected from server. Goodbye!")


if __name__ == "__main__":
    main()