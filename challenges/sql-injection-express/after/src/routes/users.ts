import { Router, Request, Response } from "express";
import { pool } from "../db";

const router = Router();

// GET /users - list all users
router.get("/", async (req: Request, res: Response) => {
  const result = await pool.query("SELECT id, name, email FROM users");
  res.json(result.rows);
});

// GET /users/search?name=... - search users by name
router.get("/search", async (req: Request, res: Response) => {
  const name = req.query.name as string;
  const query = `SELECT id, name, email FROM users WHERE name LIKE '%${name}%'`;
  try {
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
