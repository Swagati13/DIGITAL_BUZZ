import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { createSocket } from "./socket";

function App() {
  const [token, setToken] = useState(null); // set after login
  const [rooms, setRooms] = useState([]);
  const [currentRoom, setCurrentRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!token) return;
    const sock = createSocket(token);
    socketRef.current = sock;

    sock.on("connect", () => {
      console.log("connected", sock.id);
    });

    sock.on("new_message", (msg) => {
      if (msg.room === currentRoom) setMessages(prev => [...prev, msg]);
    });

    sock.on("user_joined", (data) => {
      console.log("user joined", data);
    });

    return () => {
      sock.disconnect();
    };
  }, [token, currentRoom]);

  async function loadRooms() {
    const res = await axios.get("http://localhost:8000/api/rooms/", {
      headers: { Authorization: `Bearer ${token}` },
    });
    setRooms(res.data);
  }

  async function openRoom(roomId) {
    setCurrentRoom(roomId);
    // fetch history
    const res = await axios.get(`http://localhost:8000/api/messages/?room=${roomId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    setMessages(res.data.results || res.data);
    // join socket room
    socketRef.current.emit("join_room", { room: roomId });
  }

  async function sendTextMessage(text) {
    // Option 1: emit via socket directly (server will also save)
    socketRef.current.emit("send_message", {
      room: currentRoom,
      message_type: "text",
      content: text
    });
    // Option 2: post via REST (returns saved message + server will broadcast)
    // await axios.post("http://localhost:8000/api/messages/", { room: currentRoom, content: text, message_type: "text" }, { headers: { Authorization: `Bearer ${token}` } });
  }

  async function uploadImage(file) {
    const form = new FormData();
    form.append("room", currentRoom);
    form.append("image", file);
    form.append("message_type", "image");
    const res = await axios.post("http://localhost:8000/api/messages/", form, {
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" }
    });
    // server will broadcast on save; if not, you can also emit
  }

  return (
    <div>
      {/* login UI & token management not shown here. show rooms, messages */}
    </div>
  );
}

export default App;
