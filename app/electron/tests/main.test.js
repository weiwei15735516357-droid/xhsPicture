const assert = require('node:assert');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const { getBackendArgs, getBackendWorkingDirectory, getPythonExecutable } = require('../main');

test('backend launch args run the Python module', () => {
  assert.deepStrictEqual(getBackendArgs(), ['-m', 'backend.server']);
});

test('backend working directory points at repo root', () => {
  const cwd = getBackendWorkingDirectory();
  assert.strictEqual(path.basename(path.join(cwd, 'app', 'electron')), 'electron');
  assert.strictEqual(fs.existsSync(path.join(cwd, 'backend')), true);
});

test('python executable can be overridden with environment variable', () => {
  const original = process.env.XHS_PYTHON;
  process.env.XHS_PYTHON = 'C:\\Custom\\python.exe';

  assert.strictEqual(getPythonExecutable(), 'C:\\Custom\\python.exe');

  if (original === undefined) {
    delete process.env.XHS_PYTHON;
  } else {
    process.env.XHS_PYTHON = original;
  }
});

test('python executable prefers bundled runtime when environment variable is absent', () => {
  const original = process.env.XHS_PYTHON;
  delete process.env.XHS_PYTHON;

  assert.ok(getPythonExecutable().endsWith(path.join('dependencies', 'python', 'python.exe')));

  if (original !== undefined) {
    process.env.XHS_PYTHON = original;
  }
});
