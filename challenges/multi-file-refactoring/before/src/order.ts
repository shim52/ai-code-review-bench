export interface OrderItem {
  productId: string;
  quantity: number;
  price: number;
}

export class Order {
  private items: OrderItem[] = [];
  private status: 'pending' | 'confirmed' | 'shipped' | 'delivered' = 'pending';

  constructor(private orderId: string, private customerId: string) {}

  addItem(item: OrderItem): void {
    this.items.push(item);
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
    this.status = newStatus;
  }
}