import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const gatewayTarget = env.VITE_GATEWAY_PROXY_TARGET || 'http://localhost:8000';

  return {
    plugins: [react()],
    server: {
      // Allow ngrok hostnames when exposing the local dev server publicly.
      allowedHosts: true,
      proxy: {
        '/api': {
          target: gatewayTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  };
});
