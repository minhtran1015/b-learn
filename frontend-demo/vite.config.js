import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'node:fs/promises';
import path from 'node:path';
import { tempUsers } from './src/data/tempUsers.js';

const tempUsersPath = path.resolve(process.cwd(), 'tmp/temp-users.json');

async function ensureTempUsersFile() {
  try {
    await fs.access(tempUsersPath);
  } catch {
    await fs.mkdir(path.dirname(tempUsersPath), { recursive: true });
    await fs.writeFile(tempUsersPath, JSON.stringify(tempUsers, null, 2));
  }
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  return JSON.parse(Buffer.concat(chunks).toString('utf8') || '[]');
}

function tempUsersPlugin() {
  return {
    name: 'blearn-temp-users-api',
    configureServer(server) {
      server.middlewares.use('/api/temp-users', async (req, res) => {
        await ensureTempUsersFile();
        res.setHeader('Content-Type', 'application/json');

        if (req.method === 'GET') {
          res.end(await fs.readFile(tempUsersPath, 'utf8'));
          return;
        }

        if (req.method === 'PUT') {
          const users = await readBody(req);
          await fs.writeFile(tempUsersPath, JSON.stringify(users, null, 2));
          res.end(JSON.stringify({ ok: true }));
          return;
        }

        res.statusCode = 405;
        res.end(JSON.stringify({ error: 'Method not allowed' }));
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), tempUsersPlugin()],
});
