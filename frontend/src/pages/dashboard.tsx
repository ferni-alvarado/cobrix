import React from "react";
import { Table, Tag, Typography, Col, Row } from "antd";
import { useWebSocket } from "../../hooks/use-websocket";

const { Title } = Typography;

export const DashboardPage: React.FC = () => {
  const { orders } = useWebSocket();

  const columns = [
    { title: "Order ID", dataIndex: "order_id", key: "order_id" },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (status: string) => <Tag color="green">{status}</Tag>,
    },
  ];

  return (
    <Row justify={"center"}>
      <Col lg={24} md={24}>
        <Title level={2}>Orders Dashboard</Title>
        <Table
          columns={columns}
          dataSource={orders}
          rowKey="order_id"
          pagination={false}
          bordered
          scroll={{ x: true }}
        />
      </Col>
    </Row>
  );
};
