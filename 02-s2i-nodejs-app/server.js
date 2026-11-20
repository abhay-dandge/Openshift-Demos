/**
 * Production-grade OpenShift S2I Node.js Demo Application.
 * Compatible with Red Hat UBI 9 Node.js S2I builder images
 * (registry.access.redhat.com/ubi9/nodejs-18 or ubi9/nodejs-20).
 *
 * Implements:
 * - Standard HTTP REST endpoints
 * - Liveness probe: /healthz
 * - Readiness probe: /readyz
 * - Runtime diagnostics: /info
 * - Arbitrary non-root UID compliance (port 8080)
 */

const http = require('http');
const os = require('os');

const PORT = parseInt(process.env.PORT || process.env.LISTEN_PORT || '8080', 10);
const APP_NAME = process.env.APP_NAME || 'openshift-s2i-nodejs-demo';
const APP_VERSION = process.env.APP_VERSION || '1.0.0';
const START_TIME = Date.now();

function getDiagnostics() {
  return {
    app_name: APP_NAME,
    version: APP_VERSION,
    status: 'UP',
    uptime_seconds: Math.round((Date.now() - START_TIME) / 1000),
    runtime: {
      node_version: process.version,
      platform: process.platform,
      arch: process.arch,
      pid: process.pid,
      uid: typeof process.getuid === 'function' ? process.getuid() : 'N/A',
      gid: typeof process.getgid === 'function' ? process.getgid() : 'N/A',
      memory_usage_mb: {
        rss: Math.round(process.memoryUsage().rss / 1024 / 1024),
        heapUsed: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
      },
    },
    openshift_environment: {
      hostname: os.hostname(),
      pod_namespace: process.env.OPENSHIFT_BUILD_NAMESPACE || process.env.POD_NAMESPACE || 'local',
      build_name: process.env.OPENSHIFT_BUILD_NAME || 'local-build',
      node_env: process.env.NODE_ENV || 'development',
    },
  };
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = url.pathname;

  if (pathname === '/' || pathname === '') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({
      message: 'Welcome to OpenShift Source-to-Image (S2I) Node.js Demo!',
      details: getDiagnostics(),
      endpoints: [
        { path: '/', description: 'Application overview and diagnostics' },
        { path: '/healthz', description: 'Kubernetes liveness probe' },
        { path: '/readyz', description: 'Kubernetes readiness probe' },
        { path: '/info', description: 'OpenShift runtime environment details' },
      ],
    }, null, 2));
  } else if (pathname === '/healthz') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ status: 'ALIVE', timestamp: Date.now() }));
  } else if (pathname === '/readyz') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ status: 'READY', timestamp: Date.now() }));
  } else if (pathname === '/info') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(getDiagnostics(), null, 2));
  } else {
    res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ error: 'Not Found', path: pathname }));
  }
});

if (require.main === module) {
  server.listen(PORT, '0.0.0.0', () => {
    const uid = typeof process.getuid === 'function' ? process.getuid() : 'N/A';
    console.log(`OpenShift S2I Node.js Demo listening on 0.0.0.0:${PORT} (UID: ${uid})`);
  });

  const shutdown = (signal) => {
    console.log(`Received ${signal}, shutting down server gracefully...`);
    server.close(() => {
      console.log('Server stopped.');
      process.exit(0);
    });
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

module.exports = { server, getDiagnostics };
