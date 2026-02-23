import { User } from "../models/user";
import { sendVerificationEmail } from "./email";
import { auditLog } from "./audit";

export async function registerUser(
  email: string,
  password: string
): Promise<{ userId: string }> {
  const existing = await User.findByEmail(email);
  if (existing) {
    throw new Error("Email already registered");
  }

  const user = User.create({ email, password: await hashPassword(password) });
  user.save();
  sendVerificationEmail(user.email, user.verificationToken);
  auditLog.record("user_registered", { userId: user.id });

  return { userId: user.id };
}

async function hashPassword(password: string): Promise<string> {
  const { hash } = await import("bcrypt");
  return hash(password, 12);
}
