// Sample client: all vars below ARE in .env.example
const dbUrl = process.env.DATABASE_URL;
const logLevel = process.env['LOG_LEVEL'];
console.log(dbUrl, logLevel);
