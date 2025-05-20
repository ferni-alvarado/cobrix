import React from "react";

export interface OrderEvent {
  event: string;
  order_id?: string;
  payment_id?: string;
  status?: string | number; // Luego sacar number
  payment_status?: string | number;
  notification_type?: string;
  payer_name?: string;
  payer_phone_number?: string;
  total_amount?: number;
  timestamp?: string;
}

export interface WebSocketContextType {
  orders: OrderEvent[];
  connected: boolean;
  clearOrders: () => void;
}

export const WebSocketContext = React.createContext<WebSocketContextType>({
  orders: [],
  connected: false,
  clearOrders: () => {},
});
