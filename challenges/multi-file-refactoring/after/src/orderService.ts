import { Order } from './order';

export class OrderService {
  private orders: Map<string, Order> = new Map();
  private static instance: OrderService;  // Singleton pattern

  private constructor() {}  // Private constructor for singleton

  static getInstance(): OrderService {
    if (!OrderService.instance) {
      OrderService.instance = new OrderService();
    }
    return OrderService.instance;
  }

  createOrder(orderId: string, customerId: string): Order {
    const order = new Order(orderId, customerId, this);  // Pass service to Order
    this.orders.set(orderId, order);
    return order;
  }

  getOrder(orderId: string): Order | undefined {
    return this.orders.get(orderId);
  }

  getAllOrders(): Order[] {
    return Array.from(this.orders.values());
  }

  // New method called by Order
  saveOrder(order: Order): void {
    this.orders.set(order.orderId, order);
    // Direct database access here
    console.log(`Saving order ${order.orderId} to database`);
  }

  // New method that directly modifies Order internals
  applyDiscount(orderId: string, discountPercent: number): void {
    const order = this.getOrder(orderId);
    if (order) {
      // Directly manipulating Order's public properties
      order.items.forEach(item => {
        item.price = item.price * (1 - discountPercent / 100);
      });
      this.saveOrder(order);
    }
  }
}