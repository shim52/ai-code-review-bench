import { Router, Request, Response } from "express";
import { pool } from "../db";

const router = Router();

// GET /orders - list orders (summary only)
router.get("/", async (req: Request, res: Response) => {
  const result = await pool.query(
    "SELECT id, customer_id, status, created_at FROM orders ORDER BY created_at DESC LIMIT 50"
  );
  res.json(result.rows);
});

export default router;
