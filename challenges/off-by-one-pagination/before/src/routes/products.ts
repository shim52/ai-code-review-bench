import { Router, Request, Response } from "express";
import { pool } from "../db";

const router = Router();

// GET /products - list all products (no pagination)
router.get("/", async (req: Request, res: Response) => {
  const result = await pool.query("SELECT * FROM products ORDER BY id");
  res.json({ data: result.rows });
});

export default router;
