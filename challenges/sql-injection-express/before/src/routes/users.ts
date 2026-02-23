import { Router, Request, Response } from "express";
import { pool } from "../db";

const router = Router();

// GET /users - list all users
router.get("/", async (req: Request, res: Response) => {
  const result = await pool.query("SELECT id, name, email FROM users");
  res.json(result.rows);
});

export default router;
