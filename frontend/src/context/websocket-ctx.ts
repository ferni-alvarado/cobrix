import React from "react";

export interface OrderEvent {
  event: string;
  order_id: string;
  status: string;
}

export interface WebSocketContextType {
  orders: OrderEvent[];
}

export const WebSocketContext = React.createContext<WebSocketContextType>({
  orders: [],
});
