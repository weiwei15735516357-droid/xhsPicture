const assert = require('node:assert');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const { getBackendArgs, getBackendWorkingDirectory } = require('../main');

test('backend launch args run the Python module', () => {
  assert.deepStrictEqual(getBackendArgs(), ['-m', 'backend.server']);
});

test('backend working directory points at repo root', () => {
  const cwd = getBackendWorkingDirectory();
  assert.strictEqual(path.basename(path.join(cwd, 'app', 'electron')), 'electron');
  assert.strictEqual(fs.existsSync(path.join(cwd, 'backend')), true);
});
