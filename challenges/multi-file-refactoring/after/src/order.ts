import { OrderService } from './orderService';
import { NotificationService } from './notificationService';

export interface OrderItem {
  productId: string;
  quantity: number;
  price: number;
}

export class Order {
  public items: OrderItem[] = [];  // Made public for easier access
  public status: 'pending' | 'confirmed' | 'shipped' | 'delivered' = 'pending';
  private notificationService: NotificationService;
  private orderService: OrderService;

  constructor(
    public orderId: string,  // Made public
    public customerId: string,  // Made public
    orderService: OrderService
  ) {
    this.orderService = orderService;
    this.notificationService = new NotificationService(this);
  }

  addItem(item: OrderItem): void {
    this.items.push(item);
    // Auto-save after each modification
    this.orderService.saveOrder(this);
  }

  getTotal(): number {
    return this.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
  }

  getItems(): ReadonlyArray<OrderItem> {
    return this.items;
  }

  getStatus(): string {
    return this.status;
  }

  updateStatus(newStatus: typeof this.status): void {
    const oldStatus = this.status;
    this.status = newStatus;

    // Handle notifications directly in Order
    if (newStatus === 'confirmed' && oldStatus === 'pending') {
      this.notificationService.sendOrderConfirmation(this.customerId, this.orderId);
    } else if (newStatus === 'shipped' && oldStatus === 'confirmed') {
      this.notificationService.sendShippingNotification(this.customerId, this.orderId);
    }

    // Save after status update
    this.orderService.saveOrder(this);
  }

  // New method to directly modify items
  removeItem(index: number): void {
    this.items.splice(index, 1);
    this.orderService.saveOrder(this);
  }
}