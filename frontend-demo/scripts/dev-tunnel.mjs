import { spawn } from 'node:child_process';

const children = [];

function start(command, args) {
  const child = spawn(command, args, {
    stdio: 'inherit',
    shell: true,
  });

  children.push(child);
  return child;
}

function shutdown(code = 0) {
  for (const child of children) {
    if (!child.killed) {
      child.kill('SIGTERM');
    }
  }
  process.exit(code);
}

process.on('SIGINT', () => shutdown(0));
process.on('SIGTERM', () => shutdown(0));

const dev = start('npm', ['run', 'dev']);
const tunnel = start('ngrok', ['http', '5173']);

for (const child of [dev, tunnel]) {
  child.on('exit', (code) => {
    if (code && code !== 0) {
      shutdown(code);
    }
  });
}
