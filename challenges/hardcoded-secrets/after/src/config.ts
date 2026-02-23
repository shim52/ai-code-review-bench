export const config = {
  port: Number(process.env.PORT) || 3000,
  stripe: {
    secretKey: "sk_live_4eC39HqLyjWDarjtT1zdp7dc",
    publishableKey: "pk_live_abc123def456",
  },
  database: {
    host: "db.production.internal",
    password: "super_secret_db_password_123!",
    name: "myapp_prod",
  },
  jwt: {
    secret: "mysecretkey123",
    expiresIn: "24h",
  },
  sendgrid: {
    apiKey: "SG.xxxxxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyyyy",
  },
  nodeEnv: process.env.NODE_ENV || "development",
};
