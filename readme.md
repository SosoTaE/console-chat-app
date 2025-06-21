# Real-Time Chat Application

This is a simple, real-time chat application built with Python. It consists of a multi-threaded server and a command-line client with a user-friendly `curses` interface. Users can create or join password-protected chat channels to communicate with each other.

## Features

  * **Real-time Communication:** Messages are sent and received instantly.
  * **Channel-based Chat:** Communication is organized into channels.
  * **Channel Creation and Joining:** Users can create new chat channels or join existing ones.
  * **Password Protection:** Channels can be protected with a password for privacy.
  * **User-friendly Interface:** The client uses the `curses` library to provide a clean, interactive command-line interface.
  * **Multi-threaded Server:** The server can handle multiple client connections simultaneously, with each client managed in a separate thread.
  * **Secure User Identification:** The server generates a secure, unique ID for each user within a channel.
  * **Cross-platform Compatibility:** The application is written in Python and should run on any platform with Python and the `curses` library installed (typically available on Unix-like systems).

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

  * Python 3.6 or higher
  * The `curses` library (usually pre-installed on Linux and macOS). For Windows, you can use the `windows-curses` library:
    ```bash
    pip install windows-curses
    ```

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/real-time-chat.git
    cd real-time-chat
    ```
2.  **No external libraries are required** (besides `windows-curses` for Windows users). The project uses standard Python libraries.

## Usage

### 1\. Run the Server

First, start the server by running the `server.py` file. The server will listen for incoming connections on `localhost` at port `12345` by default.

```bash
python server.py
```

You can customize the host and port by modifying the `HOST` and `PORT` variables in the `server.py` file.

### 2\. Run the Client

Next, launch the client by running the `client.py` file in a separate terminal.

```bash
python client.py
```

The client will prompt you for the following information:

  * **Server host:** The IP address or hostname of the server (default: `localhost`).
  * **Server port:** The port number the server is listening on (default: `12345`).
  * **Action:** Whether you want to `create` a new channel or `join` an existing one.
  * **Channel name:** The name of the channel you want to create or join.
  * **Channel password:** The password for the channel (optional for creation, required for joining a protected channel).
  * **Your name:** The name you want to be identified by in the chat.

Once connected, you will be taken to the chat interface.

### Chat Interface Controls

  * **Send a message:** Type your message and press `Enter`.
  * **Scroll through messages:** Use the `Up` and `Down` arrow keys.
  * **Quit the application:** Press `Ctrl+C`.

## How It Works

### Server

The server is built using Python's `socket` and `threading` libraries. It listens for TCP connections on a specified host and port. When a new client connects, the server creates a new thread to handle all communication with that client. This multi-threaded approach allows the server to manage multiple clients concurrently without blocking.

The server maintains a dictionary of active channels, each with its own set of members and a password (if set). When a client sends a message, the server broadcasts it to all other members of the same channel.

### Client

The client is a command-line application that uses the `curses` library to create a more sophisticated and user-friendly interface than a simple text-based input/output loop. It establishes a TCP connection with the server and then allows the user to either create or join a chat channel.

Once in a channel, the client starts a separate thread to continuously listen for incoming messages from the server. This ensures that the user can type a new message while simultaneously receiving messages from other users. The main thread handles user input and sends messages to the server.

### Communication Protocol

Communication between the client and server is done using JSON-formatted messages. This allows for a structured and easily extensible way to send different types of information, such as connection requests, messages, and server responses.

Each message is a JSON object with an `action` key that specifies the type of request or message. For example:

  * `{"action": "createChannel", "channelName": "my-channel", ...}`
  * `{"action": "joinChannel", "channelName": "my-channel", ...}`
  * `{"action": "message", "message": "Hello, world!", ...}`

## Contributing

Contributions are welcome\! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request.

## License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE).