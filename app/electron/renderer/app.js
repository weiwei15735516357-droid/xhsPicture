const state = {
  baseUrl: null,
  projectDir: localStorage.getItem('xhs.currentProjectDir') || null,
  backgroundPath: localStorage.getItem('xhs.backgroundPath') || null,
  documentPath: null,
  layout: [],
  followupLayout: [],
  selectedLayoutType: 'first',
  selectedLayoutIndex: 0,
  exportInProgress: false,
  aspectGuard: localStorage.getItem('xhs.layoutAspectGuard') !== 'false'
};

const CANVAS_ASPECT_RATIO = 3 / 4;
const PPT_ASPECT_RATIO = 16 / 9;
const SLOT_HEIGHT_PER_WIDTH = CANVAS_ASPECT_RATIO / PPT_ASPECT_RATIO;
const MIN_SLOT_WIDTH = 0.08;
const MIN_SLOT_HEIGHT = 0.06;

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

function appendLog(message) {
  const log = document.getElementById('activity-log');
  const time = new Date().toLocaleTimeString();
  log.textContent = [`[${time}] ${message}`, log.textContent].filter(Boolean).join('\n');
}

function requireProject() {
  if (!state.projectDir) {
    appendLog('请先选择或新建项目目录。');
    return false;
  }
  return true;
}

async function api(path, options = {}) {
  if (!state.baseUrl) {
    state.baseUrl = await window.xhsApp.getBackendBaseUrl();
  }
  const response = await fetch(`${state.baseUrl}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

async function refreshBackendStatus() {
  const status = document.getElementById('backend-status');
  try {
    const data = await api('/api/health');
    status.textContent = data.ok ? '后端已连接' : '后端异常';
    status.className = data.ok ? 'status ok' : 'status error';
  } catch (error) {
    status.textContent = '后端未连接';
    status.className = 'status error';
  }
}

function renderProject() {
  setText('current-project', state.projectDir || '未选择项目');
  setText('background-summary', state.backgroundPath ? `底图：${state.backgroundPath}` : '未选择底图时使用浅灰背景。');
}

function renderAssets(assets) {
  setText('asset-count', `${assets.length} 张`);
  const list = document.getElementById('asset-list');
  if (assets.length === 0) {
    list.innerHTML = '<div class="empty">暂无素材</div>';
    return;
  }
  list.innerHTML = '';
  for (const asset of assets) {
    const item = document.createElement('div');
    item.className = 'asset-item';
    item.innerHTML = `
      <div>
        <strong>${asset.filename}</strong>
        <span>${asset.source_type}</span>
      </div>
      <small>${asset.path}</small>
    `;
    list.appendChild(item);
  }
}

function syncSummaryControls() {
  const enabled = document.getElementById('summary-enabled').checked;
  document.querySelector('.layout-tool').style.display = enabled ? 'block' : 'none';
  if (enabled) {
    renderLayoutTool(state.layout.length === 0);
  }
}

function defaultLayout(count) {
  const layouts = {
    5: [
      { x: 0.04, y: 0.02, width: 0.92, height: 0.38 },
      { x: 0.04, y: 0.43, width: 0.44, height: 0.18 },
      { x: 0.52, y: 0.43, width: 0.44, height: 0.18 },
      { x: 0.04, y: 0.64, width: 0.44, height: 0.18 },
      { x: 0.52, y: 0.64, width: 0.44, height: 0.18 }
    ],
    7: [
      { x: 0.04, y: 0.02, width: 0.92, height: 0.34 },
      { x: 0.04, y: 0.39, width: 0.28, height: 0.16 },
      { x: 0.36, y: 0.39, width: 0.28, height: 0.16 },
      { x: 0.68, y: 0.39, width: 0.28, height: 0.16 },
      { x: 0.04, y: 0.59, width: 0.28, height: 0.16 },
      { x: 0.36, y: 0.59, width: 0.28, height: 0.16 },
      { x: 0.68, y: 0.59, width: 0.28, height: 0.16 }
    ],
    9: [
      { x: 0.04, y: 0.02, width: 0.92, height: 0.30 },
      { x: 0.04, y: 0.36, width: 0.28, height: 0.14 },
      { x: 0.36, y: 0.36, width: 0.28, height: 0.14 },
      { x: 0.68, y: 0.36, width: 0.28, height: 0.14 },
      { x: 0.04, y: 0.54, width: 0.28, height: 0.14 },
      { x: 0.36, y: 0.54, width: 0.28, height: 0.14 },
      { x: 0.68, y: 0.54, width: 0.28, height: 0.14 },
      { x: 0.20, y: 0.72, width: 0.28, height: 0.14 },
      { x: 0.52, y: 0.72, width: 0.28, height: 0.14 }
    ]
  };
  const layout = layouts[count] || layouts[5];
  return layout.map((slot) => ({ ...slot }));
}

function getLayoutKey() {
  return 'xhs.layout.first.custom';
}

function getFollowupLayoutKey() {
  return 'xhs.layout.followup.custom';
}

function loadLayout() {
  const saved = parseSavedLayout(localStorage.getItem(getLayoutKey()));
  const followupSaved = parseSavedLayout(localStorage.getItem(getFollowupLayoutKey()));
  state.layout = saved && saved.length > 0 ? saved : defaultLayout(5);
  state.followupLayout = followupSaved && followupSaved.length > 0 ? followupSaved : state.layout.map((slot) => ({ ...slot }));
  syncLayoutSelection();
}

function parseSavedLayout(value) {
  if (!value) {
    return null;
  }
  try {
    const parsed = JSON.parse(value);
    return normalizeLayout(parsed);
  } catch (error) {
    return null;
  }
}

function normalizeLayout(layout) {
  if (!Array.isArray(layout)) {
    return null;
  }
  const normalized = [];
  for (const slot of layout) {
    if (!slot || ['x', 'y', 'width', 'height'].some((key) => Number.isNaN(Number(slot[key])))) {
      return null;
    }
    const width = Math.max(0.04, Math.min(1, Number(slot.width)));
    const height = Math.max(0.04, Math.min(1, Number(slot.height)));
    normalized.push({
      x: Math.max(0, Math.min(1 - width, Number(slot.x))),
      y: Math.max(0, Math.min(1 - height, Number(slot.y))),
      width,
      height
    });
  }
  return normalized;
}

function saveLayout() {
  localStorage.setItem(getLayoutKey(), JSON.stringify(state.layout));
  setText('layout-summary', '首图排版已保存。');
}

function saveFollowupLayout() {
  localStorage.setItem(getFollowupLayoutKey(), JSON.stringify(state.followupLayout));
  setText('layout-summary', '后续页排版已保存。');
}

function syncLayoutSelection() {
  const layout = state.selectedLayoutType === 'followup' ? state.followupLayout : state.layout;
  state.selectedLayoutIndex = Math.max(0, Math.min(state.selectedLayoutIndex, layout.length - 1));
}

function cloneSlot(slot) {
  return {
    x: Math.min(0.92, slot.x + 0.03),
    y: Math.min(0.92, slot.y + 0.03),
    width: slot.width,
    height: slot.height
  };
}

function copySelectedSlot(type) {
  const layout = type === 'followup' ? state.followupLayout : state.layout;
  const index = Math.max(0, Math.min(state.selectedLayoutIndex, layout.length - 1));
  layout.splice(index + 1, 0, cloneSlot(layout[index]));
  state.selectedLayoutType = type;
  state.selectedLayoutIndex = index + 1;
  localStorage.setItem(type === 'followup' ? getFollowupLayoutKey() : getLayoutKey(), JSON.stringify(layout));
  renderLayoutTool();
  setText('layout-summary', `已复制${type === 'followup' ? '后续页' : '首图'}第 ${index + 1} 个坑位，现在共 ${layout.length} 个坑位。`);
}

function deleteSelectedSlot(type) {
  const layout = type === 'followup' ? state.followupLayout : state.layout;
  if (layout.length <= 1) {
    setText('layout-summary', '至少保留 1 个坑位。');
    return;
  }
  const index = Math.max(0, Math.min(state.selectedLayoutIndex, layout.length - 1));
  layout.splice(index, 1);
  state.selectedLayoutType = type;
  state.selectedLayoutIndex = Math.max(0, index - 1);
  localStorage.setItem(type === 'followup' ? getFollowupLayoutKey() : getLayoutKey(), JSON.stringify(layout));
  renderLayoutTool();
  setText('layout-summary', `已删除${type === 'followup' ? '后续页' : '首图'}第 ${index + 1} 个坑位，现在共 ${layout.length} 个坑位。`);
}

function exportLayoutConfig() {
  const config = {
    version: 1,
    slot_count: state.layout.length,
    first_layout: state.layout,
    followup_layout: state.followupLayout
  };
  const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `小红书叠图排版_${state.layout.length}坑位.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function importLayoutConfig(file) {
  const text = await file.text();
  const config = JSON.parse(text);
  const firstLayout = normalizeLayout(config.first_layout);
  const followupLayout = normalizeLayout(config.followup_layout);
  if (!firstLayout || !followupLayout || firstLayout.length === 0) {
    throw new Error('排版配置格式不正确');
  }
  state.layout = firstLayout;
  state.followupLayout = followupLayout;
  syncLayoutSelection();
  localStorage.setItem(getLayoutKey(), JSON.stringify(state.layout));
  localStorage.setItem(getFollowupLayoutKey(), JSON.stringify(state.followupLayout));
  renderLayoutTool();
  setText('layout-summary', `已导入 ${state.layout.length} 个坑位排版。`);
}

function updateLayoutSummary() {
  const guard = state.aspectGuard ? '防裁剪比例已开启，调大小时按 16:9 等比缩放。' : '防裁剪比例已关闭，坑位可自由拉伸。';
  setText('layout-summary', `首图 ${state.layout.length} 个坑位，后续页 ${state.followupLayout.length} 个坑位。${guard}`);
}

function renderLayoutTool(reload = false) {
  if (!document.getElementById('layout-canvas')) {
    return;
  }
  if (reload || state.layout.length === 0) {
    loadLayout();
  }
  renderLayoutCanvas('layout-canvas', state.layout, 'first');
  renderLayoutCanvas('followup-layout-canvas', state.followupLayout, 'followup');
  updateLayoutSummary();
}

function renderLayoutCanvas(canvasId, layout, type) {
  const canvas = document.getElementById(canvasId);
  canvas.innerHTML = '';
  layout.forEach((slot, index) => {
    const item = document.createElement('div');
    item.className = 'layout-slot';
    if (state.selectedLayoutType === type && state.selectedLayoutIndex === index) {
      item.classList.add('selected');
    }
    item.textContent = index + 1;
    item.style.left = `${slot.x * 100}%`;
    item.style.top = `${slot.y * 100}%`;
    item.style.width = `${slot.width * 100}%`;
    item.style.height = `${slot.height * 100}%`;
    item.addEventListener('pointerdown', (event) => startLayoutDrag(event, index, type));
    canvas.appendChild(item);
  });
}

function startLayoutDrag(event, index, type) {
  event.preventDefault();
  state.selectedLayoutType = type;
  state.selectedLayoutIndex = index;
  document.querySelectorAll('.layout-slot').forEach((slot) => slot.classList.remove('selected'));
  event.currentTarget.classList.add('selected');
  const layout = type === 'followup' ? state.followupLayout : state.layout;
  const canvas = event.currentTarget.closest('.layout-canvas');
  const rect = canvas.getBoundingClientRect();
  const slot = layout[index];
  const resizing = event.offsetX > event.currentTarget.clientWidth - 18 && event.offsetY > event.currentTarget.clientHeight - 18;
  const start = { x: event.clientX, y: event.clientY, slot: { ...slot } };
  const target = event.currentTarget;
  target.setPointerCapture(event.pointerId);
  target.onpointermove = (moveEvent) => {
    const dx = (moveEvent.clientX - start.x) / rect.width;
    const dy = (moveEvent.clientY - start.y) / rect.height;
    if (resizing) {
      const resized = state.aspectGuard ? resizeSlotWithAspect(start.slot, dx, dy) : resizeSlotFreely(start.slot, dx, dy);
      slot.width = resized.width;
      slot.height = resized.height;
    } else {
      slot.x = Math.max(0, Math.min(1 - slot.width, start.slot.x + dx));
      slot.y = Math.max(0, Math.min(1 - slot.height, start.slot.y + dy));
    }
    target.style.left = `${slot.x * 100}%`;
    target.style.top = `${slot.y * 100}%`;
    target.style.width = `${slot.width * 100}%`;
    target.style.height = `${slot.height * 100}%`;
  };
  target.onpointerup = target.onpointercancel = (endEvent) => {
    if (target.hasPointerCapture(endEvent.pointerId)) {
      target.releasePointerCapture(endEvent.pointerId);
    }
    target.onpointermove = null;
    target.onpointerup = null;
    target.onpointercancel = null;
  };
}

function resizeSlotFreely(startSlot, dx, dy) {
  return {
    width: Math.max(MIN_SLOT_WIDTH, Math.min(1 - startSlot.x, startSlot.width + dx)),
    height: Math.max(MIN_SLOT_HEIGHT, Math.min(1 - startSlot.y, startSlot.height + dy))
  };
}

function resizeSlotWithAspect(startSlot, dx, dy) {
  const maxWidth = 1 - startSlot.x;
  const maxHeight = 1 - startSlot.y;
  let width;
  let height;
  if (Math.abs(dy) > Math.abs(dx)) {
    height = Math.max(MIN_SLOT_HEIGHT, Math.min(maxHeight, startSlot.height + dy));
    width = height / SLOT_HEIGHT_PER_WIDTH;
  } else {
    width = Math.max(MIN_SLOT_WIDTH, Math.min(maxWidth, startSlot.width + dx));
    height = width * SLOT_HEIGHT_PER_WIDTH;
  }
  if (width > maxWidth) {
    width = maxWidth;
    height = width * SLOT_HEIGHT_PER_WIDTH;
  }
  if (height > maxHeight) {
    height = maxHeight;
    width = height / SLOT_HEIGHT_PER_WIDTH;
  }
  return {
    width: Math.max(MIN_SLOT_WIDTH, width),
    height: Math.max(MIN_SLOT_HEIGHT, height)
  };
}

function syncAspectGuardControl() {
  const checkbox = document.getElementById('layout-aspect-guard');
  checkbox.checked = state.aspectGuard;
}

function updateProgress(progress = { percent: 0, message: '等待任务' }) {
  const percent = Math.max(0, Math.min(Number(progress.percent || 0), 100));
  document.getElementById('progress-bar').style.width = `${percent}%`;
  setText('progress-percent', `${percent}%`);
  setText('progress-label', progress.message || '正在处理');
}

async function waitForTask(taskId) {
  while (true) {
    const task = await api(`/api/tasks/${taskId}`);
    updateProgress(task.progress);
    setText('task-summary', `最近任务：${task.status}`);
    if (task.status === 'completed') {
      return task;
    }
    if (task.status === 'failed') {
      throw new Error(task.error || '导出失败');
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

async function refreshAssets() {
  if (!requireProject()) {
    return;
  }
  const data = await api(`/api/assets?project_dir=${encodeURIComponent(state.projectDir)}`);
  renderAssets(data.assets);
}

async function createProject() {
  const selected = await window.xhsApp.selectProjectDirectory();
  if (!selected) {
    return;
  }
  const data = await api('/api/project/create', {
    method: 'POST',
    body: JSON.stringify({ project_dir: selected })
  });
  state.projectDir = data.project_dir;
  localStorage.setItem('xhs.currentProjectDir', state.projectDir);
  renderProject();
  appendLog(`项目已准备：${state.projectDir}`);
  await refreshAssets();
}

async function importPaths(paths) {
  if (!requireProject() || paths.length === 0) {
    return;
  }
  const data = await api('/api/assets/import', {
    method: 'POST',
    body: JSON.stringify({ project_dir: state.projectDir, paths })
  });
  setText('import-summary', `已导入 ${data.assets.length} 张图片。`);
  appendLog(`导入图片 ${data.assets.length} 张。`);
  await refreshAssets();
}

async function exportPdf() {
  if (!requireProject()) {
    return;
  }
  if (!state.documentPath) {
    appendLog('请先选择 PPT/Word/PDF 文件。');
    return;
  }
  const pageStart = document.getElementById('page-start').value;
  const pageEnd = document.getElementById('page-end').value;
  const summaryEnabled = document.getElementById('summary-enabled').checked;
  const summaryGroupSize = state.layout.length;
  const payload = {
    project_dir: state.projectDir,
    file_path: state.documentPath,
    scale: Number(document.getElementById('pdf-scale').value),
    page_start: pageStart ? Number(pageStart) : null,
    page_end: pageEnd ? Number(pageEnd) : null,
    subfolder_output: document.getElementById('subfolder-output').checked,
    summary_group_size: summaryEnabled ? Number(summaryGroupSize) : null,
    background_path: state.backgroundPath || null,
    custom_layout: summaryEnabled ? state.layout : null,
    followup_layout: summaryEnabled ? state.followupLayout : null
  };
  updateProgress({ percent: 0, message: '准备开始导出' });
  const started = await api('/api/documents/export/start', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  const task = await waitForTask(started.task.id);
  const assets = task.result.assets;
  const mode = summaryEnabled ? `首图 ${summaryGroupSize} 张/后续 ${state.followupLayout.length} 张叠图` : '不叠图，逐页导出';
  setText('document-summary', `已导出 ${assets.length} 张 PNG（${mode}）。`);
  appendLog(`文档转 PNG 完成，生成 ${assets.length} 张（${mode}）。`);
  await refreshAssets();
}

async function runAction(action) {
  try {
    await action();
  } catch (error) {
    appendLog(`错误：${error.message}`);
  }
}

async function runExportAction() {
  if (state.exportInProgress) {
    appendLog('导出正在执行，请等待完成后再开始下一次。');
    return;
  }
  const button = document.getElementById('start-export-btn');
  state.exportInProgress = true;
  button.disabled = true;
  button.textContent = '执行中...';
  try {
    await exportPdf();
  } catch (error) {
    appendLog(`错误：${error.message}`);
  } finally {
    state.exportInProgress = false;
    button.disabled = false;
    button.textContent = '开始执行';
  }
}

document.getElementById('create-project-btn').addEventListener('click', () => runAction(createProject));
document.getElementById('refresh-assets-btn').addEventListener('click', () => runAction(refreshAssets));
document.getElementById('import-files-btn').addEventListener('click', async () => {
  await runAction(async () => importPaths(await window.xhsApp.selectImportFiles()));
});
document.getElementById('import-folder-btn').addEventListener('click', async () => {
  await runAction(async () => {
    const folder = await window.xhsApp.selectImportFolder();
    await importPaths(folder ? [folder] : []);
  });
});
document.getElementById('background-image-btn').addEventListener('click', async () => {
  await runAction(async () => {
    const selected = await window.xhsApp.selectBackgroundImage();
    if (!selected) {
      return;
    }
    state.backgroundPath = selected;
    localStorage.setItem('xhs.backgroundPath', selected);
    renderProject();
    appendLog(`已选择底图：${selected}`);
  });
});
document.getElementById('clear-background-btn').addEventListener('click', () => {
  state.backgroundPath = null;
  localStorage.removeItem('xhs.backgroundPath');
  renderProject();
  appendLog('已删除底图，导出时使用浅灰背景。');
});
document.getElementById('summary-enabled').addEventListener('change', syncSummaryControls);
document.getElementById('layout-reset-btn').addEventListener('click', () => {
  localStorage.removeItem(getLayoutKey());
  state.layout = defaultLayout(5);
  state.selectedLayoutType = 'first';
  syncLayoutSelection();
  renderLayoutTool();
  setText('layout-summary', '首图排版已重置为 5 个坑位。');
});
document.getElementById('layout-save-btn').addEventListener('click', saveLayout);
document.getElementById('layout-copy-btn').addEventListener('click', () => copySelectedSlot('first'));
document.getElementById('layout-delete-btn').addEventListener('click', () => deleteSelectedSlot('first'));
document.getElementById('followup-layout-reset-btn').addEventListener('click', () => {
  localStorage.removeItem(getFollowupLayoutKey());
  state.followupLayout = state.layout.map((slot) => ({ ...slot }));
  state.selectedLayoutType = 'followup';
  syncLayoutSelection();
  renderLayoutTool();
  setText('layout-summary', '后续页排版已重置为首图同款坑位。');
});
document.getElementById('followup-layout-save-btn').addEventListener('click', saveFollowupLayout);
document.getElementById('followup-layout-copy-btn').addEventListener('click', () => copySelectedSlot('followup'));
document.getElementById('followup-layout-delete-btn').addEventListener('click', () => deleteSelectedSlot('followup'));
document.getElementById('layout-export-config-btn').addEventListener('click', exportLayoutConfig);
document.getElementById('layout-import-config-btn').addEventListener('click', () => {
  document.getElementById('layout-import-file').click();
});
document.getElementById('layout-aspect-guard').addEventListener('change', (event) => {
  state.aspectGuard = event.target.checked;
  localStorage.setItem('xhs.layoutAspectGuard', state.aspectGuard ? 'true' : 'false');
  updateLayoutSummary();
});
document.getElementById('layout-import-file').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (!file) {
    return;
  }
  await runAction(async () => importLayoutConfig(file));
  event.target.value = '';
});
document.getElementById('select-document-btn').addEventListener('click', () => runAction(async () => {
  const selected = await window.xhsApp.selectDocumentFile();
  if (!selected) {
    return;
  }
  state.documentPath = selected;
  document.getElementById('page-start').value = '';
  document.getElementById('page-end').value = '';
  setText('document-summary', `已选择：${selected}`);
  appendLog(`已选择文档：${selected}`);
}));
document.getElementById('start-export-btn').addEventListener('click', runExportAction);

renderProject();
syncAspectGuardControl();
syncSummaryControls();
renderLayoutTool();
refreshBackendStatus();
setInterval(refreshBackendStatus, 5000);
if (state.projectDir) {
  runAction(refreshAssets);
}
