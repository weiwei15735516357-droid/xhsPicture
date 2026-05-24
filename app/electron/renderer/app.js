const state = {
  baseUrl: null,
  projectDir: localStorage.getItem('xhs.currentProjectDir') || null,
  backgroundPath: localStorage.getItem('xhs.backgroundPath') || null,
  documentPath: null
};

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
  document.getElementById('summary-group-size').disabled = !document.getElementById('summary-enabled').checked;
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
  const summaryGroupSize = document.getElementById('summary-group-size').value;
  const payload = {
    project_dir: state.projectDir,
    file_path: state.documentPath,
    scale: Number(document.getElementById('pdf-scale').value),
    page_start: pageStart ? Number(pageStart) : null,
    page_end: pageEnd ? Number(pageEnd) : null,
    subfolder_output: document.getElementById('subfolder-output').checked,
    summary_group_size: summaryEnabled ? Number(summaryGroupSize) : null,
    background_path: state.backgroundPath || null,
    background_has_text: document.getElementById('background-has-text').checked
  };
  updateProgress({ percent: 0, message: '准备开始导出' });
  const started = await api('/api/documents/export/start', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  const task = await waitForTask(started.task.id);
  const assets = task.result.assets;
  const mode = summaryEnabled ? `${summaryGroupSize} 张叠图` : '不叠图，逐页导出';
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
document.getElementById('summary-enabled').addEventListener('change', syncSummaryControls);
document.getElementById('select-document-btn').addEventListener('click', () => runAction(async () => {
  const selected = await window.xhsApp.selectDocumentFile();
  if (!selected) {
    return;
  }
  state.documentPath = selected;
  setText('document-summary', `已选择：${selected}`);
  appendLog(`已选择文档：${selected}`);
}));
document.getElementById('start-export-btn').addEventListener('click', () => runAction(exportPdf));

renderProject();
syncSummaryControls();
refreshBackendStatus();
setInterval(refreshBackendStatus, 5000);
if (state.projectDir) {
  runAction(refreshAssets);
}
