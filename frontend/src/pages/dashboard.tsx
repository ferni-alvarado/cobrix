import React from "react";
import { Table, Tag, Space, Typography, Col, Row } from "antd";

const { Title } = Typography;

interface Order {
  id: string;
  customerName: string;
  type: "Delivery" | "Pickup at Store";
  status: "Paid";
  time: string; // formato HH:MM
}

const orders: Order[] = [
  {
    id: "1023",
    customerName: "Sofia Gomez",
    type: "Pickup at Store",
    status: "Paid",
    time: "14:32",
  },
  {
    id: "1024",
    customerName: "Luciano Perez",
    type: "Delivery",
    status: "Paid",
    time: "14:45",
  },
  {
    id: "1025",
    customerName: "Maria Rodriguez",
    type: "Delivery",
    status: "Paid",
    time: "15:10",
  },
];

export const DashboardPage: React.FC = () => {
  const columns = [
    {
      title: "Order ID",
      dataIndex: "id",
      key: "id",
    },
    {
      title: "Customer",
      dataIndex: "customerName",
      key: "customerName",
    },
    {
      title: "Type",
      dataIndex: "type",
      key: "type",
      render: (type: Order["type"]) => <Tag color={type === "Delivery" ? "blue" : "green"}>{type}</Tag>,
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      render: (status: string) => <Tag color="green">{status}</Tag>,
    },
    {
      title: "Time",
      dataIndex: "time",
      key: "time",
    },
    {
      title: "Action",
      key: "action",
      render: () => (
        <Space size="middle">
          <a>Mark as Delivered</a>
        </Space>
      ),
    },
  ];

  return (
    <Row justify={"center"}>
      <Col lg={24} md={24} style={{ marginBottom: "20px" }}>
        <Title level={2}>Orders Dashboard</Title>
        <Table
          columns={columns}
          dataSource={orders}
          rowKey="id"
          pagination={false}
          bordered
          scroll={{ x: true }} // hace que en mobile puedas scrollear horizontal
        />
      </Col>
    </Row>
  );
};
