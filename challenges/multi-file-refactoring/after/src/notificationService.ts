import { Order } from './order';

export class NotificationService {
  private order: Order;

  constructor(order: Order) {
    this.order = order;  // Storing reference to Order
  }

  sendOrderConfirmation(customerId: string, orderId: string): void {
    // Now accessing Order's internals directly
    const total = this.order.getTotal();
    const itemCount = this.order.items.length;

    console.log(`Sending order confirmation to customer ${customerId} for order ${orderId}`);
    console.log(`Total: $${total}, Items: ${itemCount}`);
    // Email sending logic here
  }

  sendShippingNotification(customerId: string, orderId: string): void {
    // Checking order status directly
    if (this.order.status !== 'shipped') {
      throw new Error('Cannot send shipping notification for non-shipped order');
    }

    console.log(`Sending shipping notification to customer ${customerId} for order ${orderId}`);
    // SMS sending logic here
  }

  // New method that modifies Order
  sendAndMarkAsNotified(type: 'confirmation' | 'shipping'): void {
    if (type === 'confirmation') {
      this.sendOrderConfirmation(this.order.customerId, this.order.orderId);
      // Modifying Order's public property directly
      (this.order as any).notificationSent = true;
    } else {
      this.sendShippingNotification(this.order.customerId, this.order.orderId);
      (this.order as any).shippingNotificationSent = true;
    }
  }
}