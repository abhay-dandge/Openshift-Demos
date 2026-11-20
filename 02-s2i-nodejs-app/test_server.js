/**
 * Zero-dependency test suite for 02-s2i-nodejs-app.
 */

const http = require('http');
const assert = require('assert');
const { server, getDiagnostics } = require('./server');

const TEST_PORT = 18080;

function runTests() {
  server.listen(TEST_PORT, '127.0.0.1', async () => {
    console.log(`Running tests against http://127.0.0.1:${TEST_PORT}...`);

    const request = (path) => new Promise((resolve, reject) => {
      http.get(`http://127.0.0.1:${TEST_PORT}${path}`, (res) => {
        let rawData = '';
        res.on('data', (chunk) => { rawData += chunk; });
        res.on('end', () => {
          resolve({
            statusCode: res.statusCode,
            headers: res.headers,
            body: rawData ? JSON.parse(rawData) : null,
          });
        });
      }).on('error', reject);
    });

    try {
      // Test 1: Root endpoint
      const rootRes = await request('/');
      assert.strictEqual(rootRes.statusCode, 200, 'Root status should be 200');
      assert.strictEqual(rootRes.body.details.status, 'UP');
      console.log('✓ Root endpoint test passed');

      // Test 2: Healthz endpoint
      const healthzRes = await request('/healthz');
      assert.strictEqual(healthzRes.statusCode, 200);
      assert.strictEqual(healthzRes.body.status, 'ALIVE');
      console.log('✓ Healthz endpoint test passed');

      // Test 3: Readyz endpoint
      const readyzRes = await request('/readyz');
      assert.strictEqual(readyzRes.statusCode, 200);
      assert.strictEqual(readyzRes.body.status, 'READY');
      console.log('✓ Readyz endpoint test passed');

      // Test 4: Info endpoint
      const infoRes = await request('/info');
      assert.strictEqual(infoRes.statusCode, 200);
      assert.ok(infoRes.body.runtime.node_version);
      console.log('✓ Info endpoint test passed');

      // Test 5: 404 endpoint
      const notFoundRes = await request('/random-unknown-path');
      assert.strictEqual(notFoundRes.statusCode, 404);
      console.log('✓ 404 endpoint test passed');

      console.log('\nAll Node.js S2I unit tests PASSED successfully!');
      server.close(() => process.exit(0));
    } catch (err) {
      console.error('Test failed:', err);
      server.close(() => process.exit(1));
    }
  });
}

runTests();
