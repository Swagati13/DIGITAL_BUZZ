import { io } from "socket.io-client";

export function createSocket(token) {
  // token: JWT access token
  const socket = io("http://localhost:8000", {
    path: "/socket.io/",
    auth: { token },
    // OR send token as query: e.g. ?token=...
    // query: { token }
  });
  return socket;
}
