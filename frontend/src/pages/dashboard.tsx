import React from "react";
import { Table, Tag, Typography, Col, Row, Badge, Alert, Button, Space, Tooltip } from "antd";
import { ReloadOutlined, ClearOutlined } from "@ant-design/icons";
import { useWebSocket } from "../hooks/use-websocket";

const { Title } = Typography;

export const DashboardPage: React.FC = () => {
  const { orders, connected, clearOrders } = useWebSocket();

  const getStatusColor = (status: string | number) => {
    if (status === undefined || status === null) return "default";

    // Convertir a string si es número
    const statusStr = typeof status === "number" ? String(status) : status;

    // Usar código de estado HTTP si es número
    if (typeof status === "number") {
      if (status >= 200 && status < 300) return "success"; // 2xx: success
      if (status >= 400 && status < 500) return "error"; // 4xx: client error
      if (status >= 500) return "error"; // 5xx: server error
      return "processing";
    }

    // Usar estado de pago si es string
    switch (statusStr.toLowerCase()) {
      case "approved":
        return "success";
      case "pending":
        return "warning";
      case "rejected":
      case "cancelled":
      case "error":
        return "error";
      default:
        return "processing";
    }
  };

  const formatCurrency = (amount: number) => {
    if (!amount && amount !== 0) return "N/A";

    return new Intl.NumberFormat("es-AR", {
      style: "currency",
      currency: "ARS",
    }).format(amount);
  };

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return "N/A";

    try {
      const date = new Date(timestamp);
      return date.toLocaleString("es-AR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
    } catch (e) {
      console.error("Error al formatear la fecha:", e);
      return "Fecha inválida";
    }
  };

  const columns = [
    {
      title: "Fecha/Hora",
      dataIndex: "timestamp",
      key: "timestamp",
      render: (timestamp: string) => formatTimestamp(timestamp),
      width: 180,
    },
    {
      title: "Orden ID",
      dataIndex: "order_id",
      key: "order_id",
      width: 120,
    },
    {
      title: "ID de Pago",
      dataIndex: "payment_id",
      key: "payment_id",
      width: 120,
    },
    {
      title: "Estado",
      dataIndex: "status",
      key: "status",
      render: (status: string | number) => {
        const statusText =
          status !== undefined && status !== null
            ? typeof status === "number"
              ? `CÓDIGO ${status}`
              : status.toUpperCase()
            : "DESCONOCIDO";

        return <Tag color={getStatusColor(status)}>{statusText}</Tag>;
      },
      width: 120,
    },
    {
      title: "Monto",
      dataIndex: "total_amount",
      key: "total_amount",
      render: (amount: number) => formatCurrency(amount),
      width: 120,
    },
    {
      title: "Cliente",
      dataIndex: "payer_name",
      key: "payer_name",
      render: (name: string) => name || "N/A",
      width: 150,
    },
    {
      title: "Teléfono",
      dataIndex: "payer_phone_number",
      key: "payer_phone_number",
      render: (phone: string) => phone || "N/A",
      width: 150,
    },
    {
      title: "Tipo",
      dataIndex: "notification_type",
      key: "notification_type",
      render: (type: string) => <Tag color="blue">{type || "DESCONOCIDO"}</Tag>,
      width: 120,
    },
  ];

  const handleReloadPage = () => {
    window.location.reload();
  };

  return (
    <Row gutter={[16, 16]} justify="center">
      <Col span={24}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <Title level={2}>Panel de Notificaciones de Pagos</Title>
          <Space>
            <Badge status={connected ? "success" : "error"} text={connected ? "Conectado" : "Desconectado"} />
            <Tooltip title="Recargar página">
              <Button icon={<ReloadOutlined />} onClick={handleReloadPage} type="primary" ghost />
            </Tooltip>
            <Tooltip title="Limpiar notificaciones">
              <Button icon={<ClearOutlined />} onClick={clearOrders} danger disabled={orders.length === 0} />
            </Tooltip>
          </Space>
        </div>

        {!connected && (
          <Alert
            message="Desconectado del servidor"
            description="Intentando reconectar al WebSocket. Por favor, verifica que el servidor esté en funcionamiento."
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {connected && orders.length === 0 && (
          <Alert
            message="No hay notificaciones"
            description="Aún no se han recibido notificaciones de pago. Aparecerán aquí cuando se procesen."
            type="info"
            showIcon
          />
        )}

        {orders.length > 0 && (
          <Table
            columns={columns}
            dataSource={orders}
            rowKey={(record, index) => `${record.payment_id || record.order_id || index}-${Date.now()}`}
            pagination={{ pageSize: 10 }}
            bordered
            scroll={{ x: "max-content" }}
          />
        )}
      </Col>
    </Row>
  );
};
