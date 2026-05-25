const assert = require('node:assert');
const test = require('node:test');
const fs = require('node:fs');
const path = require('node:path');

const {
  getBackendArgs,
  getBackendWorkingDirectory,
  getImageImportFilters,
  getDocumentImportFilters,
  getSpreadsheetImportFilters,
  getPythonExecutable
} = require('../main');

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

test('image import filters include common image formats', () => {
  assert.deepStrictEqual(getImageImportFilters(), [
    { name: '图片文件', extensions: ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tif', 'tiff', 'jfif'] },
    { name: '所有文件', extensions: ['*'] }
  ]);
});

test('background image filters reuse image formats', () => {
  assert.deepStrictEqual(getImageImportFilters()[0].extensions, ['jpg', 'jpeg', 'png', 'webp', 'bmp', 'gif', 'tif', 'tiff', 'jfif']);
});

test('document import filters include pdf word and powerpoint files', () => {
  assert.deepStrictEqual(getDocumentImportFilters(), [
    { name: 'PPT 演示文稿', extensions: ['ppt', 'pptx'] },
    { name: 'Word 文档', extensions: ['doc', 'docx'] },
    { name: 'PDF 文件', extensions: ['pdf'] },
    { name: '所有支持文档', extensions: ['ppt', 'pptx', 'doc', 'docx', 'pdf'] },
    { name: '所有文件', extensions: ['*'] }
  ]);
});

test('spreadsheet import filters include xlsx and csv files', () => {
  assert.deepStrictEqual(getSpreadsheetImportFilters(), [
    { name: 'Excel 或 CSV 表格', extensions: ['xlsx', 'xlsm', 'csv'] },
    { name: '所有文件', extensions: ['*'] }
  ]);
});
