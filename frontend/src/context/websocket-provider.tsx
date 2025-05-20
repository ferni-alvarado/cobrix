import React, { useEffect, useState, useCallback, useRef } from "react";
import { WebSocketContext, OrderEvent } from "./websocket-ctx";

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [orders, setOrders] = useState<OrderEvent[]>([]);
  const [connected, setConnected] = useState<boolean>(false);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);

  // Función para limpiar todas las notificaciones
  const clearOrders = useCallback(() => {
    setOrders([]);
  }, []);

  // Función para conectar al WebSocket
  const connectWebSocket = useCallback(() => {
    // Usar la URL del backend correcta
    // En desarrollo, normalmente es el mismo host pero otro puerto (8000)
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws`;

    if (ws.current) {
      ws.current.close();
    }

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log("WebSocket conectado");
      setConnected(true);

      // Limpiamos cualquier timeout de reconexión pendiente
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as OrderEvent;

        // Añadimos un timestamp si no viene en el evento
        const eventWithTimestamp = {
          ...data,
          timestamp: data.timestamp || new Date().toISOString(),
        };

        // Actualizamos la lista de órdenes (añadiendo la nueva al principio)
        setOrders((prev) => [eventWithTimestamp, ...prev]);
      } catch (error) {
        console.error("Error al procesar mensaje de WebSocket:", error);
      }
    };

    socket.onclose = () => {
      setConnected(false);

      reconnectTimeout.current = setTimeout(() => {
        connectWebSocket();
      }, 5000);
    };

    socket.onerror = (error) => {
      console.error("Error de WebSocket:", error);
      socket.close();
    };

    ws.current = socket;
  }, []);

  // Conectar al WebSocket cuando el componente se monta
  useEffect(() => {
    connectWebSocket();

    // Limpiar al desmontar
    return () => {
      if (ws.current) {
        ws.current.close();
      }
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
    };
  }, [connectWebSocket]);

  return (
    <WebSocketContext.Provider
      value={{
        orders,
        connected,
        clearOrders,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};
