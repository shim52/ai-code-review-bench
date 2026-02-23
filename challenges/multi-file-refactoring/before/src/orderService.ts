import { Order } from './order';

export class OrderService {
  private orders: Map<string, Order> = new Map();

  createOrder(orderId: string, customerId: string): Order {
    const order = new Order(orderId, customerId);
    this.orders.set(orderId, order);
    return order;
  }

  getOrder(orderId: string): Order | undefined {
    return this.orders.get(orderId);
  }

  getAllOrders(): Order[] {
    return Array.from(this.orders.values());
  }
}