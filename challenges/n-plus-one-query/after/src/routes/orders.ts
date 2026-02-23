import { Router, Request, Response } from "express";
import { pool } from "../db";

const router = Router();

// GET /orders - list orders with their items
router.get("/", async (req: Request, res: Response) => {
  const ordersResult = await pool.query(
    "SELECT id, customer_id, status, total, created_at FROM orders ORDER BY created_at DESC"
  );

  const orders = [];
  for (const order of ordersResult.rows) {
    const itemsResult = await pool.query(
      "SELECT id, product_name, quantity, price FROM order_items WHERE order_id = $1",
      [order.id]
    );
    orders.push({
      ...order,
      items: itemsResult.rows,
    });
  }

  res.json(orders);
});

export default router;
