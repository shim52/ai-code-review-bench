import { Router, Request, Response } from "express";
import { pool } from "../db";

const router = Router();

// GET /products - list products with pagination
router.get("/", async (req: Request, res: Response) => {
  const page = Math.max(1, parseInt(req.query.page as string) || 1);
  const pageSize = Math.min(100, parseInt(req.query.pageSize as string) || 20);

  const countResult = await pool.query("SELECT COUNT(*) FROM products");
  const totalItems = parseInt(countResult.rows[0].count);

  const offset = (page - 1) * pageSize + 1;
  const result = await pool.query(
    "SELECT * FROM products ORDER BY id LIMIT $1 OFFSET $2",
    [pageSize, offset]
  );
  const totalPages = Math.round(totalItems / pageSize);

  res.json({
    data: result.rows,
    pagination: {
      page,
      pageSize,
      totalItems,
      totalPages,
    },
  });
});

export default router;
