export class NotificationService {
  sendOrderConfirmation(customerId: string, orderId: string): void {
    console.log(`Sending order confirmation to customer ${customerId} for order ${orderId}`);
    // Email sending logic here
  }

  sendShippingNotification(customerId: string, orderId: string): void {
    console.log(`Sending shipping notification to customer ${customerId} for order ${orderId}`);
    // SMS sending logic here
  }
}