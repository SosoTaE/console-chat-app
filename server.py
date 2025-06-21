import socket
import threading
import json
from tools import generate_secure_user_id
from datetime import datetime


class Server:
    """
    A simple multithreaded TCP server that handles each client in a separate thread.
    """

    def __init__(self, host, port):
        """
        Initializes the server, binds it to the given host and port,
        and starts listening for incoming connections.
        """

        self.channels = {}
        self.channels_id = 1

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        print(f"Server listening on {host}:{port}")

        # Accept connections in a loop
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"Accepted connection from {addr}")

                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()

            except Exception as e:
                print(f"Error accepting connection: {e}")
                break

    def handle_client(self, client_socket, addr):
        """
        Handles the initial client connection and authentication
        """
        try:
            # Wait for initial request (create/join channel)
            request = client_socket.recv(1024)
            if not request:
                print(f"Client {addr} disconnected during handshake.")
                client_socket.close()
                return

            json_data = json.loads(request.decode('utf-8'))
            print(f"Received from {addr}: {json_data}")

            if json_data["action"] == "createChannel":
                self.handle_create_channel(client_socket, addr, json_data)

            elif json_data["action"] == "joinChannel":
                self.handle_join_channel(client_socket, addr, json_data)

            else:
                # Unknown action
                response = json.dumps({
                    "success": False,
                    "action": "error",
                    "message": "Unknown action"
                })
                client_socket.send(response.encode('utf-8'))
                client_socket.close()

        except json.JSONDecodeError as e:
            print(f"JSON decode error from {addr}: {e}")
            client_socket.close()
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            client_socket.close()

    def handle_create_channel(self, client_socket, addr, json_data):
        """Handle channel creation"""
        try:
            if json_data.get("channelName") and json_data.get("memberName"):
                if json_data["channelName"] not in self.channels:
                    # Create the channel
                    self.channels[json_data["channelName"]] = {
                        "channelId": self.channels_id,
                        "channelName": json_data["channelName"],
                        "password": json_data.get("channelPassword", ""),
                        "members": {},
                        "chatOwner": json_data["memberName"],
                    }

                    response = json.dumps({
                        "success": True,
                        "action": "createChannel",
                        "message": "channel created successfully"
                    })
                    client_socket.send(response.encode('utf-8'))
                    self.channels_id += 1

                    # After creating, automatically join the channel
                    self.join_channel_logic(client_socket, addr, json_data)

                else:
                    response = json.dumps({
                        "success": False,
                        "action": "createChannel",
                        "message": "channel already exists"
                    })
                    client_socket.send(response.encode('utf-8'))
                    client_socket.close()
            else:
                response = json.dumps({
                    "success": False,
                    "action": "createChannel",
                    "message": "channelName and memberName are required"
                })
                client_socket.send(response.encode('utf-8'))
                client_socket.close()

        except Exception as e:
            print(f"Error creating channel for {addr}: {e}")
            client_socket.close()

    def handle_join_channel(self, client_socket, addr, json_data):
        """Handle joining a channel"""
        try:
            if json_data["channelName"] in self.channels:
                channel = self.channels[json_data["channelName"]]

                if channel["password"] != json_data.get("channelPassword", ""):
                    response = json.dumps({
                        "success": False,
                        "action": "joinChannel",
                        "channelName": json_data["channelName"],
                        "message": "channel password is incorrect"
                    })
                    client_socket.send(response.encode('utf-8'))
                    client_socket.close()
                    return

                if not json_data.get("memberName"):
                    response = json.dumps({
                        "success": False,
                        "action": "joinChannel",
                        "message": "memberName is required"
                    })
                    client_socket.send(response.encode('utf-8'))
                    client_socket.close()
                    return

                # Join the channel
                self.join_channel_logic(client_socket, addr, json_data)

            else:
                response = json.dumps({
                    "success": False,
                    "action": "joinChannel",
                    "channelName": json_data["channelName"],
                    "message": "channel does not exist"
                })
                client_socket.send(response.encode('utf-8'))
                client_socket.close()

        except Exception as e:
            print(f"Error joining channel for {addr}: {e}")
            client_socket.close()

    def join_channel_logic(self, client_socket, addr, json_data):
        """Common logic for joining a channel (used by both create and join)"""
        try:
            channel = self.channels[json_data["channelName"]]

            # Generate unique member name
            base_name = json_data["memberName"]
            member_name = f"{base_name}_{generate_secure_user_id(8)}"

            # Ensure uniqueness
            count = 0
            original_member_name = member_name
            while member_name in channel["members"]:
                count += 1
                member_name = f"{original_member_name}_{count}"

            # Add member to channel
            channel["members"][member_name] = client_socket

            # Send success response
            response = json.dumps({
                "action": "joinChannel",
                "channelName": json_data["channelName"],
                "channelId": channel["channelId"],
                "memberName": member_name,
                "message": "channel joined successfully",
                "success": True
            })
            client_socket.send(response.encode('utf-8'))

            print(f"Member {member_name} joined channel {channel['channelName']}")
            print(f"Active members in {channel['channelName']}: {len(channel['members'])}")

            # Now handle ongoing messages for this client
            self.handle_messages(client_socket, addr, channel, member_name)

        except Exception as e:
            print(f"Error in join_channel_logic for {addr}: {e}")
            client_socket.close()

    def handle_messages(self, client_socket, addr, channel, member_name):
        """
        Handles ongoing messages from a client that has joined a channel
        """
        print(f"Starting message handling for {member_name} in {channel['channelName']}")

        try:
            while True:
                message = client_socket.recv(1024)
                if not message:
                    print(f"Client {addr} ({member_name}) disconnected.")
                    break

                try:
                    json_data = json.loads(message.decode('utf-8'))
                    json_data["memberName"] = member_name
                    json_data["timestamp"] = datetime.now().strftime("%H:%M:%S")

                    print(f"Broadcasting message from {member_name}: {json_data}")

                    # Broadcast to all members in the channel
                    disconnected_members = []
                    for name, connection in channel["members"].items():
                        try:
                            connection.send(json.dumps(json_data).encode('utf-8'))
                        except Exception as e:
                            print(f"Failed to send message to {name}: {e}")
                            disconnected_members.append(name)

                    # Remove disconnected members
                    for name in disconnected_members:
                        if name in channel["members"]:
                            del channel["members"][name]
                            print(f"Removed disconnected member: {name}")

                except json.JSONDecodeError as e:
                    print(f"JSON decode error from {member_name}: {e}")
                    continue

        except (socket.error, ConnectionResetError) as e:
            print(f"Connection error with {addr} ({member_name}): {e}")
        finally:
            # Clean up: remove member from channel
            if member_name in channel["members"]:
                del channel["members"][member_name]
                print(f"Removed {member_name} from channel {channel['channelName']}")

            client_socket.close()
            print(f"Connection with {addr} ({member_name}) closed.")


# To run the server:
if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 12345
    try:
        server = Server(HOST, PORT)
    except KeyboardInterrupt:
        print("\nServer is shutting down.")
    except Exception as e:
        print(f"An error occurred: {e}")