import React, { useState, useEffect } from "react";
import { WebSocketContext, OrderEvent } from "./websocket-ctx";

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [orders, setOrders] = useState<OrderEvent[]>([]);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws");

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("📩 New WebSocket event:", data);

      if (data.event === "payment_update") {
        setOrders((prev) => [...prev, data]);
      }
    };

    socket.onclose = () => {
      console.log("🔌 WebSocket closed");
    };

    return () => {
      socket.close();
    };
  }, []);

  return <WebSocketContext.Provider value={{ orders }}>{children}</WebSocketContext.Provider>;
};
