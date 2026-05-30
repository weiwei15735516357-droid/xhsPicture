const state = {
  baseUrl: null,
  projectDir: localStorage.getItem('xhs.currentProjectDir') || null,
  backgroundPath: localStorage.getItem('xhs.backgroundPath') || null,
  documentPath: null,
  layout: [],
  followupLayout: [],
  selectedLayoutType: 'first',
  selectedLayoutIndex: 0,
  perspectiveScenePath: null,
  perspectiveOverlayPaths: [],
  perspectiveOverlayItems: [],
  perspectiveExcelPath: null,
  perspectiveRows: [],
  perspectivePreviewIndex: 0,
  perspectiveOverlayIndex: 0,
  perspectiveMode: 'excel',
  perspectiveText: {
    x: 118,
    y: 386,
    fontSize: 92,
    fontFamily: 'msyh',
    color: '#000000',
    strokeColor: '#ffffff',
    strokeWidth: 0,
    bold: true
  },
  perspectivePoints: [
    { x: 0.18, y: 0.24 },
    { x: 0.82, y: 0.24 },
    { x: 0.82, y: 0.70 },
    { x: 0.18, y: 0.70 }
  ],
  perspectiveImageDefaults: {
    opacity: 1,
    shadow: true,
    previewWidth: 320
  },
  feishuInProgress: false,
  perspectiveInProgress: false,
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

function setupNavigation() {
  const navButtons = document.querySelectorAll('.nav[data-view]');
  const panels = document.querySelectorAll('.view-panel');
  const activate = (button) => {
    const view = button.dataset.view;
    navButtons.forEach((item) => item.classList.toggle('active', item === button));
    panels.forEach((panel) => {
      const views = panel.dataset.view.split(/\s+/);
      panel.classList.toggle('hidden-view', !views.includes(view));
    });
    document.querySelectorAll('.perspective-only').forEach((panel) => {
      panel.classList.toggle('hidden-view', view !== 'perspective');
    });
    setText('view-title', button.dataset.title);
    setText('view-desc', button.dataset.desc);
  };
  navButtons.forEach((button) => {
    button.addEventListener('click', () => activate(button));
  });
  activate(document.querySelector('.nav.active[data-view]') || navButtons[0]);
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

function fileUrl(path) {
  return encodeURI(`file:///${path.replace(/\\/g, '/')}`);
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[char]);
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

function resetPerspectivePoints() {
  const item = currentPerspectiveOverlayItem();
  const points = [
    { x: 0.18, y: 0.24 },
    { x: 0.82, y: 0.24 },
    { x: 0.82, y: 0.70 },
    { x: 0.18, y: 0.70 }
  ];
  if (item) {
    item.points = clonePerspectivePoints(points);
  }
  state.perspectivePoints = [
    { x: 0.18, y: 0.24 },
    { x: 0.82, y: 0.24 },
    { x: 0.82, y: 0.70 },
    { x: 0.18, y: 0.70 }
  ];
  renderPerspectiveCanvas();
  renderImagePreviewList();
}

function currentPerspectiveRow() {
  if (!state.perspectiveRows.length) { return null; }
  const index = Math.max(0, Math.min(state.perspectivePreviewIndex, state.perspectiveRows.length - 1));
  return state.perspectiveRows[index];
}

function currentPerspectiveOverlayPath() {
  const item = currentPerspectiveOverlayItem();
  return item ? item.path : null;
}

function clonePerspectivePoints(points = state.perspectivePoints) {
  return points.map((point) => ({ x: Number(point.x), y: Number(point.y) }));
}

function createPerspectiveOverlayItems(paths) {
  return paths.map((path) => ({
    path,
    points: clonePerspectivePoints(),
    opacity: Number(state.perspectiveImageDefaults.opacity),
    shadow: Boolean(state.perspectiveImageDefaults.shadow)
  }));
}

function currentPerspectiveOverlayItem() {
  if (!state.perspectiveOverlayItems.length) { return null; }
  const index = Math.max(0, Math.min(state.perspectiveOverlayIndex, state.perspectiveOverlayItems.length - 1));
  return state.perspectiveOverlayItems[index];
}

function currentPerspectivePoints() {
  const item = currentPerspectiveOverlayItem();
  return item ? item.points : state.perspectivePoints;
}

function currentPerspectiveOpacity() {
  const item = currentPerspectiveOverlayItem();
  return item ? item.opacity : Number(state.perspectiveImageDefaults.opacity);
}

function currentPerspectiveShadow() {
  const item = currentPerspectiveOverlayItem();
  return item ? item.shadow : Boolean(state.perspectiveImageDefaults.shadow);
}

function cloneTextOptions(options = state.perspectiveText) {
  return {
    x: Number(options.x ?? 118),
    y: Number(options.y ?? 386),
    fontSize: Number(options.fontSize ?? options.font_size ?? 92),
    fontFamily: options.fontFamily || options.font_family || 'msyh',
    color: options.color || '#000000',
    strokeColor: options.strokeColor || options.stroke_color || '#ffffff',
    strokeWidth: Number(options.strokeWidth ?? options.stroke_width ?? 0),
    bold: options.bold !== false
  };
}

function getRowTextOptions(row) {
  if (!row.textOptions) { row.textOptions = cloneTextOptions(); }
  return row.textOptions;
}

function toBackendTextOptions(options) {
  return {
    x: Number(options.x),
    y: Number(options.y),
    font_size: Number(options.fontSize),
    font_family: options.fontFamily,
    color: options.color,
    stroke_color: options.strokeColor,
    stroke_width: Number(options.strokeWidth),
    bold: Boolean(options.bold)
  };
}

function updateExcelPreviewPanel() {
  const counter = document.getElementById('excel-preview-counter');
  if (counter) { counter.textContent = state.perspectiveRows.length ? `${state.perspectiveRows.length} 条` : '0 条'; }
}

function ensureDefaultStylePanel(list) {
  const panel = document.querySelector('.excel-preview-panel');
  if (!panel || document.getElementById('excel-default-style')) {
    return;
  }
  const options = cloneTextOptions();
  const stylePanel = document.createElement('div');
  stylePanel.id = 'excel-default-style';
  stylePanel.className = 'excel-default-style';
  stylePanel.innerHTML = `
    <strong>&#32479;&#19968;&#40664;&#35748;&#26679;&#24335;</strong>
    <label>&#23383;&#20307;<select data-default-style="fontFamily">${fontFamilyOptions(options.fontFamily)}</select></label>
    <label>&#23383;&#21495;<input data-default-style="fontSize" type="number" min="16" max="220" value="${options.fontSize}" /></label>
    <label>X<input data-default-style="x" type="number" min="0" max="1080" value="${options.x}" /></label>
    <label>Y<input data-default-style="y" type="number" min="0" max="1440" value="${options.y}" /></label>
    <label>&#25991;&#23383;&#33394;<input data-default-style="color" type="color" value="${options.color}" /></label>
    <label>&#25551;&#36793;&#33394;<input data-default-style="strokeColor" type="color" value="${options.strokeColor}" /></label>
    <label>&#25551;&#36793;<input data-default-style="strokeWidth" type="number" min="0" max="16" value="${options.strokeWidth}" /></label>
    <label class="inline"><input data-default-style="bold" type="checkbox" ${options.bold ? 'checked' : ''} /> &#21152;&#31895;</label>
    <button id="apply-default-style-btn">&#24212;&#29992;&#21040;&#20840;&#37096;</button>
  `;
  stylePanel.addEventListener('input', (event) => {
    const target = event.target;
    const key = target.dataset.defaultStyle;
    if (!key) { return; }
    state.perspectiveText[key] = target.type === 'checkbox'
      ? target.checked
      : target.type === 'number'
        ? Number(target.value)
        : target.value;
  });
  stylePanel.querySelector('#apply-default-style-btn').addEventListener('click', () => {
    const optionsToApply = cloneTextOptions();
    state.perspectiveRows.forEach((row) => {
      row.textOptions = cloneTextOptions(optionsToApply);
    });
    renderPerspectiveCanvas();
    renderExcelPreviewList();
    appendLog('已将统一默认样式应用到全部商品预览。');
  });
  panel.insertBefore(stylePanel, list);
}

function ensureExcelPreviewList() {
  const panel = document.querySelector('.excel-preview-panel');
  if (!panel) { return null; }
  let list = document.getElementById('excel-preview-list');
  if (!list) {
    panel.innerHTML = '<div class="preview-nav"><strong>\u5168\u90e8\u5546\u54c1\u9884\u89c8</strong><span id="excel-preview-counter">0 \u6761</span></div><div id="excel-preview-list" class="excel-preview-list"></div>';
    list = document.getElementById('excel-preview-list');
  }
  ensureDefaultStylePanel(list);
  return list;
}

function applyTextOverlayStyle(overlay, preview, row) {
  const options = getRowTextOptions(row);
  const rect = preview.getBoundingClientRect();
  overlay.textContent = row.title || '';
  overlay.style.left = `${(options.x / 1080) * 100}%`;
  overlay.style.top = `${(options.y / 1440) * 100}%`;
  overlay.style.maxWidth = `${Math.max(8, ((1080 - options.x - 54) / 1080) * 100)}%`;
  overlay.style.fontSize = `${Math.max(8, (options.fontSize / 1440) * rect.height)}px`;
  overlay.style.color = options.color;
  overlay.style.fontWeight = options.bold ? '800' : '500';
  overlay.style.fontFamily = fontFamilyCss(options.fontFamily);
  if (Number(options.strokeWidth) > 0) {
    const width = Math.max(1, Math.round((options.strokeWidth / 1440) * rect.height));
    overlay.style.webkitTextStroke = `${width}px ${options.strokeColor}`;
    overlay.style.paintOrder = 'stroke fill';
  } else {
    overlay.style.webkitTextStroke = '';
    overlay.style.paintOrder = '';
  }
}

function fontFamilyCss(fontFamily) {
  const families = {
    msyh: '"Microsoft YaHei", sans-serif',
    simhei: 'SimHei, "Microsoft YaHei", sans-serif',
    simsun: 'SimSun, serif',
    kaiti: 'KaiTi, STKaiti, serif',
    dengxian: 'DengXian, "Microsoft YaHei", sans-serif'
  };
  return families[fontFamily] || families.msyh;
}

function fontFamilyOptions(selected) {
  const options = [
    ['msyh', '&#24494;&#36719;&#38597;&#40657;'],
    ['simhei', '&#40657;&#20307;'],
    ['simsun', '&#23435;&#20307;'],
    ['kaiti', '&#26999;&#20307;'],
    ['dengxian', '&#31561;&#32447;']
  ];
  return options
    .map(([value, label]) => `<option value="${value}" ${value === selected ? 'selected' : ''}>${label}</option>`)
    .join('');
}

function createTextPreview(row, className = 'excel-card-preview') {
  const preview = document.createElement('div');
  preview.className = className;
  if (state.perspectiveScenePath) {
    const image = document.createElement('img');
    image.className = 'perspective-scene';
    image.src = fileUrl(state.perspectiveScenePath);
    preview.appendChild(image);
  } else {
    preview.innerHTML = '<div class="empty">\u5148\u9009\u62e9\u5e95\u56fe</div>';
  }
  const overlay = document.createElement('div');
  overlay.className = 'excel-text-overlay';
  preview.appendChild(overlay);
  window.requestAnimationFrame(() => applyTextOverlayStyle(overlay, preview, row));
  return preview;
}

function createExcelPreviewCard(row, index) {
  const card = document.createElement('div');
  card.className = 'excel-preview-card';
  if (index === state.perspectivePreviewIndex) { card.classList.add('selected'); }
  const preview = createTextPreview(row);
  const form = document.createElement('div');
  form.className = 'excel-card-form';
  const options = getRowTextOptions(row);
  form.innerHTML = `
    <label>&#21830;&#21697;ID<input data-field="product_id" value="${escapeHtml(row.product_id)}" /></label>
    <label class="wide">&#26631;&#39064;<textarea data-field="title">${escapeHtml(row.title)}</textarea></label>
    <label>&#23383;&#20307;<select data-style="fontFamily">${fontFamilyOptions(options.fontFamily)}</select></label>
    <label>&#23383;&#21495;<input data-style="fontSize" type="number" min="16" max="220" value="${options.fontSize}" /></label>
    <label>X<input data-style="x" type="number" min="0" max="1080" value="${options.x}" /></label>
    <label>Y<input data-style="y" type="number" min="0" max="1440" value="${options.y}" /></label>
    <label>&#25991;&#23383;&#33394;<input data-style="color" type="color" value="${options.color}" /></label>
    <label>&#25551;&#36793;&#33394;<input data-style="strokeColor" type="color" value="${options.strokeColor}" /></label>
    <label>&#25551;&#36793;<input data-style="strokeWidth" type="number" min="0" max="16" value="${options.strokeWidth}" /></label>
    <label class="inline"><input data-style="bold" type="checkbox" ${options.bold ? 'checked' : ''} /> &#21152;&#31895;</label>
  `;
  card.addEventListener('click', () => {
    state.perspectivePreviewIndex = index;
    renderPerspectiveCanvas();
    document.querySelectorAll('.excel-preview-card').forEach((item) => item.classList.remove('selected'));
    card.classList.add('selected');
  });
  form.addEventListener('input', (event) => {
    const target = event.target;
    if (target.dataset.field === 'product_id') { row.product_id = target.value; }
    if (target.dataset.field === 'title') { row.title = target.value; }
    if (target.dataset.style) {
      const key = target.dataset.style;
      options[key] = target.type === 'checkbox' ? target.checked : target.type === 'number' ? Number(target.value) : target.value;
    }
    applyTextOverlayStyle(preview.querySelector('.excel-text-overlay'), preview, row);
    if (index === state.perspectivePreviewIndex) { renderPerspectiveCanvas(); }
  });
  card.appendChild(preview);
  card.appendChild(form);
  return card;
}

function renderExcelPreviewList() {
  const list = ensureExcelPreviewList();
  if (!list) { return; }
  list.innerHTML = '';
  updateExcelPreviewPanel();
  if (!state.perspectiveRows.length) {
    list.innerHTML = '<div class="empty">\u9009\u62e9\u5e95\u56fe\u548c Excel \u540e\uff0c\u8fd9\u91cc\u4f1a\u5217\u51fa\u6240\u6709\u5546\u54c1\u7684\u6700\u7ec8\u53e0\u56fe\u6548\u679c\u3002</div>';
    return;
  }
  state.perspectiveRows.forEach((row, index) => { list.appendChild(createExcelPreviewCard(row, index)); });
}

function createImagePreviewCard(overlayPath, index) {
  const item = state.perspectiveOverlayItems[index] || {
    path: overlayPath,
    points: clonePerspectivePoints(),
    opacity: Number(state.perspectiveImageDefaults.opacity),
    shadow: Boolean(state.perspectiveImageDefaults.shadow)
  };
  const card = document.createElement('div');
  card.className = 'excel-preview-card image-preview-card';
  if (index === state.perspectiveOverlayIndex) { card.classList.add('selected'); }
  const preview = document.createElement('div');
  preview.className = 'excel-card-preview image-card-preview';
  if (state.perspectiveScenePath) {
    const scene = document.createElement('img');
    scene.className = 'perspective-scene';
    scene.src = fileUrl(state.perspectiveScenePath);
    preview.appendChild(scene);
  } else {
    preview.innerHTML = '<div class="empty">\u5148\u9009\u62e9\u5e95\u56fe</div>';
  }
  const overlay = createPerspectiveOverlayImage(overlayPath, item);
  preview.appendChild(overlay);
  addPerspectiveCardControls(preview, item, () => {
    if (index === state.perspectiveOverlayIndex) {
      renderPerspectiveCanvas();
    }
  });
  const form = document.createElement('div');
  form.className = 'excel-card-form image-card-form';
  const filename = overlayPath.split(/[\\/]/).pop();
  form.innerHTML = `
    <label class="wide">&#21472;&#22270;&#25991;&#20214;<input value="${escapeHtml(filename)}" readonly /></label>
    <label>&#24207;&#21495;<input value="${index + 1}" readonly /></label>
    <label>&#36879;&#26126;&#24230;<input data-image-style="opacity" type="number" min="0.1" max="1" step="0.05" value="${item.opacity}" /></label>
    <label class="inline"><input data-image-style="shadow" type="checkbox" ${item.shadow ? 'checked' : ''} /> &#38452;&#24433;</label>
    <label class="wide">&#36755;&#20986;&#21517;<input value="${escapeHtml(filename.replace(/\.[^.]+$/, ''))}_&#36879;&#35270;&#21512;&#25104;" readonly /></label>
  `;
  card.addEventListener('click', () => {
    state.perspectiveOverlayIndex = index;
    document.querySelectorAll('.image-preview-card').forEach((item) => item.classList.remove('selected'));
    card.classList.add('selected');
    renderPerspectiveCanvas();
  });
  form.addEventListener('input', (event) => {
    const target = event.target;
    const key = target.dataset.imageStyle;
    if (!key) { return; }
    item[key] = target.type === 'checkbox' ? target.checked : Number(target.value);
    if (index === state.perspectiveOverlayIndex) {
      renderPerspectiveCanvas();
    }
    const overlay = preview.querySelector('.perspective-overlay-preview');
    if (overlay) {
      applyPerspectiveOverlayGeometry(overlay, item);
    }
  });
  card.appendChild(preview);
  card.appendChild(form);
  return card;
}

function addPerspectiveCardControls(container, item, onChange) {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
  polygon.setAttribute('fill', 'rgba(217,48,37,0.10)');
  polygon.setAttribute('stroke', '#d93025');
  polygon.setAttribute('stroke-width', '2');
  polygon.setAttribute('points', item.points.map((point) => `${point.x * 100},${point.y * 100}`).join(' '));
  svg.setAttribute('viewBox', '0 0 100 100');
  svg.setAttribute('preserveAspectRatio', 'none');
  svg.appendChild(polygon);
  container.appendChild(svg);
  item.points.forEach((point, pointIndex) => {
    const handle = document.createElement('div');
    handle.className = 'perspective-handle image-card-handle';
    handle.style.left = `${point.x * 100}%`;
    handle.style.top = `${point.y * 100}%`;
    handle.addEventListener('pointerdown', (event) => {
      event.preventDefault();
      event.stopPropagation();
      const rect = container.getBoundingClientRect();
      handle.setPointerCapture(event.pointerId);
      handle.onpointermove = (moveEvent) => {
        const x = Math.max(0, Math.min(1, (moveEvent.clientX - rect.left) / rect.width));
        const y = Math.max(0, Math.min(1, (moveEvent.clientY - rect.top) / rect.height));
        item.points[pointIndex] = { x, y };
        handle.style.left = `${x * 100}%`;
        handle.style.top = `${y * 100}%`;
        polygon.setAttribute('points', item.points.map((nextPoint) => `${nextPoint.x * 100},${nextPoint.y * 100}`).join(' '));
        const overlay = container.querySelector('.perspective-overlay-preview');
        if (overlay) {
          applyPerspectiveOverlayGeometry(overlay, item);
        }
      };
      handle.onpointerup = handle.onpointercancel = (endEvent) => {
        if (handle.hasPointerCapture(endEvent.pointerId)) {
          handle.releasePointerCapture(endEvent.pointerId);
        }
        handle.onpointermove = null;
        handle.onpointerup = null;
        handle.onpointercancel = null;
        onChange();
      };
    });
    container.appendChild(handle);
  });
}

function renderImagePreviewList() {
  const counter = document.getElementById('image-preview-counter');
  const list = document.getElementById('image-preview-list');
  if (!counter || !list) { return; }
  list.style.setProperty('--image-preview-width', `${state.perspectiveImageDefaults.previewWidth}px`);
  counter.textContent = state.perspectiveOverlayItems.length ? `${state.perspectiveOverlayItems.length} \u5f20` : '0 \u5f20';
  list.innerHTML = '';
  if (!state.perspectiveOverlayItems.length) {
    list.innerHTML = '<div class="empty">\u9009\u62e9\u5e95\u56fe\u548c\u53e0\u56fe\u540e\uff0c\u8fd9\u91cc\u4f1a\u5217\u51fa\u6bcf\u5f20\u56fe\u7684\u900f\u89c6\u5408\u6210\u9884\u89c8\u3002</div>';
    return;
  }
  state.perspectiveOverlayItems.forEach((item, index) => {
    list.appendChild(createImagePreviewCard(item.path, index));
  });
}

function createPerspectiveOverlayImage(overlayPath, item = currentPerspectiveOverlayItem()) {
  const overlay = document.createElement('img');
  overlay.className = 'perspective-overlay-preview';
  overlay.src = fileUrl(overlayPath);
  applyPerspectiveOverlayGeometry(overlay, item);
  return overlay;
}

function applyPerspectiveOverlayGeometry(overlay, item = currentPerspectiveOverlayItem()) {
  const points = item ? item.points : state.perspectivePoints;
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  const width = Math.max(0.01, Math.max(...xs) - left);
  const height = Math.max(0.01, Math.max(...ys) - top);
  overlay.style.left = `${left * 100}%`;
  overlay.style.top = `${top * 100}%`;
  overlay.style.width = `${width * 100}%`;
  overlay.style.height = `${height * 100}%`;
  overlay.style.opacity = item ? item.opacity : Number(state.perspectiveImageDefaults.opacity);
  overlay.style.clipPath = `polygon(${points.map((point) => `${((point.x - left) / width) * 100}% ${((point.y - top) / height) * 100}%`).join(', ')})`;
}

function renderPerspectiveCanvas() {
  const canvas = document.getElementById('perspective-canvas');
  canvas.innerHTML = '';
  if (!state.perspectiveScenePath) {
    canvas.innerHTML = '<div class="empty">选择底图后可预览；图片叠图模式可拖动四个角定位</div>';
    updatePerspectiveSummary();
    return;
  }
  const image = document.createElement('img');
  image.className = 'perspective-scene';
  image.src = fileUrl(state.perspectiveScenePath);
  canvas.appendChild(image);
  if (state.perspectiveMode === 'excel') {
    const row = currentPerspectiveRow();
    if (row) {
      const overlay = document.createElement('div');
      overlay.className = 'excel-text-overlay';
      canvas.appendChild(overlay);
      window.requestAnimationFrame(() => applyTextOverlayStyle(overlay, canvas, row));
    }
    updatePerspectiveSummary();
    return;
  }
  const overlayPath = currentPerspectiveOverlayPath();
  if (overlayPath) {
    canvas.appendChild(createPerspectiveOverlayImage(overlayPath));
  }
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
  polygon.setAttribute('fill', 'rgba(217,48,37,0.18)');
  polygon.setAttribute('stroke', '#d93025');
  polygon.setAttribute('stroke-width', '2');
  polygon.setAttribute('points', currentPerspectivePoints().map((point) => `${point.x * 100},${point.y * 100}`).join(' '));
  svg.setAttribute('viewBox', '0 0 100 100');
  svg.setAttribute('preserveAspectRatio', 'none');
  svg.appendChild(polygon);
  canvas.appendChild(svg);
  currentPerspectivePoints().forEach((point, index) => {
    const handle = document.createElement('div');
    handle.className = 'perspective-handle';
    handle.style.left = `${point.x * 100}%`;
    handle.style.top = `${point.y * 100}%`;
    handle.addEventListener('pointerdown', (event) => startPerspectiveDrag(event, index));
    canvas.appendChild(handle);
  });
  updatePerspectiveSummary();
}

function updatePerspectiveSummary() {
  const scene = state.perspectiveScenePath ? '\u5df2\u9009\u62e9\u5e95\u56fe' : '\u672a\u9009\u62e9\u5e95\u56fe';
  if (state.perspectiveMode === 'excel') {
    const excel = state.perspectiveExcelPath ? '\u5df2\u9009\u62e9 Excel' : '\u672a\u9009\u62e9 Excel';
    const rows = state.perspectiveRows.length ? `，已读取 ${state.perspectiveRows.length} 条标题` : '';
    setText('perspective-summary', `${scene}，${excel}${rows}。按商品id命名输出 1080x1440。`);
    return;
  }
  setText('perspective-summary', `${scene}，叠图 ${state.perspectiveOverlayItems.length || state.perspectiveOverlayPaths.length} 张。输出固定 1080x1440。`);
}

function syncPerspectiveMode() {
  const panel = document.querySelector('.perspective-panel');
  if (panel) {
    panel.classList.toggle('excel-mode', state.perspectiveMode === 'excel');
    panel.classList.toggle('image-mode', state.perspectiveMode === 'image');
  }
  document.querySelectorAll('.perspective-image-control').forEach((item) => {
    item.classList.toggle('hidden-panel', state.perspectiveMode !== 'image');
  });
  document.querySelectorAll('.perspective-excel-control').forEach((item) => {
    item.classList.toggle('hidden-panel', state.perspectiveMode !== 'excel');
  });
  renderPerspectiveCanvas();
  renderExcelPreviewList();
  renderImagePreviewList();
}

function startPerspectiveDrag(event, index) {
  event.preventDefault();
  const canvas = document.getElementById('perspective-canvas');
  const rect = canvas.getBoundingClientRect();
  const points = currentPerspectivePoints();
  const target = event.currentTarget;
  target.setPointerCapture(event.pointerId);
  target.onpointermove = (moveEvent) => {
    const x = Math.max(0, Math.min(1, (moveEvent.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (moveEvent.clientY - rect.top) / rect.height));
    points[index] = { x, y };
    target.style.left = `${x * 100}%`;
    target.style.top = `${y * 100}%`;
    const polygon = canvas.querySelector('polygon');
    if (polygon) {
      polygon.setAttribute('points', points.map((point) => `${point.x * 100},${point.y * 100}`).join(' '));
    }
    const overlay = canvas.querySelector('.perspective-overlay-preview');
    if (overlay) {
      applyPerspectiveOverlayGeometry(overlay, currentPerspectiveOverlayItem());
    }
  };
  target.onpointerup = target.onpointercancel = (endEvent) => {
    if (target.hasPointerCapture(endEvent.pointerId)) {
      target.releasePointerCapture(endEvent.pointerId);
    }
    target.onpointermove = null;
    target.onpointerup = null;
    target.onpointercancel = null;
    renderImagePreviewList();
  };
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

function updatePerspectiveTaskProgress(progress = { percent: 0, message: '\u7b49\u5f85\u900f\u89c6\u5408\u6210\u4efb\u52a1' }) {
  const percent = Math.max(0, Math.min(Number(progress.percent || 0), 100));
  const bar = document.getElementById('perspective-progress-bar');
  const percentText = document.getElementById('perspective-progress-percent');
  const label = document.getElementById('perspective-progress-label');
  if (bar) { bar.style.width = `${percent}%`; }
  if (percentText) { percentText.textContent = `${percent}%`; }
  if (label) { label.textContent = progress.message || '\u6b63\u5728\u900f\u89c6\u5408\u6210'; }
}

function updateFeishuProgress(progress = { percent: 0, message: '等待飞书上传任务' }) {
  const percent = Math.max(0, Math.min(Number(progress.percent || 0), 100));
  const bar = document.getElementById('feishu-progress-bar');
  const percentText = document.getElementById('feishu-progress-percent');
  const label = document.getElementById('feishu-progress-label');
  if (bar) { bar.style.width = `${percent}%`; }
  if (percentText) { percentText.textContent = `${percent}%`; }
  if (label) { label.textContent = progress.message || '正在上传飞书附件'; }
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

async function waitForFeishuTask(taskId) {
  while (true) {
    const task = await api(`/api/tasks/${taskId}`);
    updateFeishuProgress(task.progress);
    if (task.status === 'completed') {
      updateFeishuProgress({ percent: 100, message: '飞书上传完成' });
      return task;
    }
    if (task.status === 'failed') {
      updateFeishuProgress({ percent: task.progress?.percent || 0, message: task.error || '飞书上传失败' });
      throw new Error(task.error || '飞书上传失败');
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}
async function waitForPerspectiveTask(taskId) {
  while (true) {
    const task = await api(`/api/tasks/${taskId}`);
    updatePerspectiveTaskProgress(task.progress);
    if (task.status === 'completed') {
      updatePerspectiveTaskProgress({ percent: 100, message: '\u900f\u89c6\u5408\u6210\u5b8c\u6210' });
      return task;
    }
    if (task.status === 'failed') {
      updatePerspectiveTaskProgress({ percent: task.progress?.percent || 0, message: task.error || '\u900f\u89c6\u5408\u6210\u5931\u8d25' });
      throw new Error(task.error || '\u900f\u89c6\u5408\u6210\u5931\u8d25');
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

async function refreshAssets() {
  await refreshBackendStatus();
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
}

async function loadPerspectiveExcelRows() {
  if (!state.perspectiveExcelPath) {
    state.perspectiveRows = [];
    state.perspectivePreviewIndex = 0;
    updateExcelPreviewPanel();
    return;
  }
  const data = await api(`/api/perspective/excel/rows?excel_path=${encodeURIComponent(state.perspectiveExcelPath)}`);
  state.perspectiveRows = (data.rows || []).map((row) => ({
    ...row,
    textOptions: cloneTextOptions()
  }));
  state.perspectivePreviewIndex = 0;
  updateExcelPreviewPanel();
  renderPerspectiveCanvas();
  renderExcelPreviewList();
  appendLog(`Excel 已读取 ${state.perspectiveRows.length} 条标题，可逐条预览。`);
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
}

async function runPerspectiveCompose() {
  if (!requireProject()) {
    return;
  }
  if (!state.perspectiveScenePath) {
    appendLog('请先选择底图。');
    return;
  }
  if (state.perspectiveMode === 'excel' && !state.perspectiveExcelPath) {
    appendLog('请先选择 Excel 表格。');
    return;
  }
  if (state.perspectiveMode === 'image' && state.perspectiveOverlayPaths.length === 0) {
    appendLog('请先选择叠图。');
    return;
  }
  if (state.perspectiveInProgress) {
    appendLog('透视合成正在执行，请等待完成。');
    return;
  }
  const button = document.getElementById('perspective-start-btn');
  state.perspectiveInProgress = true;
  button.disabled = true;
  button.textContent = '\u5408\u6210\u4e2d...';
  try {
    updatePerspectiveTaskProgress({ percent: 0, message: '\u51c6\u5907\u5f00\u59cb\u900f\u89c6\u5408\u6210' });
    const started = await api('/api/perspective/compose/start', {
      method: 'POST',
      body: JSON.stringify({
        project_dir: state.projectDir,
        scene_path: state.perspectiveScenePath,
        mode: state.perspectiveMode,
        overlay_paths: state.perspectiveOverlayPaths,
        overlay_items: state.perspectiveOverlayItems.map((item) => ({
          path: item.path,
          points: item.points,
          opacity: Number(item.opacity),
          shadow: Boolean(item.shadow)
        })),
        excel_path: state.perspectiveExcelPath,
        points: currentPerspectivePoints(),
        opacity: currentPerspectiveOpacity(),
        shadow: currentPerspectiveShadow(),
        text_options: toBackendTextOptions(cloneTextOptions()),
        text_rows: state.perspectiveRows.map((row) => ({
          product_id: row.product_id,
          title: row.title,
          text_options: toBackendTextOptions(getRowTextOptions(row))
        }))
      })
    });
    const task = await waitForPerspectiveTask(started.task.id);
    appendLog(`透视合成完成，生成 ${task.result.assets.length} 张图片。`);
  } catch (error) {
    appendLog(`错误：${error.message}`);
  } finally {
    state.perspectiveInProgress = false;
    button.disabled = false;
    button.textContent = '\u5f00\u59cb\u6279\u91cf\u5408\u6210';
  }
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

function collectFeishuPayload() {
  return {
    app_id: document.getElementById('feishu-app-id').value.trim(),
    app_secret: document.getElementById('feishu-app-secret').value.trim(),
    bitable_url: document.getElementById('feishu-bitable-url').value.trim(),
    field_name: document.getElementById('feishu-field-name').value,
    row_range: document.getElementById('feishu-row-range').value.trim(),
    upload_root: document.getElementById('feishu-upload-root').value.trim()
  };
}

function requireFeishuPayload(payload, includeRoot = true) {
  const required = [
    ['app_id', '请填写 App ID'],
    ['app_secret', '请填写 App Secret'],
    ['bitable_url', '请填写多维表格链接'],
    ['row_range', '请填写行范围，例如 2-5']
  ];
  if (includeRoot) {
    required.push(['upload_root', '请选择上传总文件夹']);
  }
  for (const [key, message] of required) {
    if (!payload[key]) {
      appendLog(message);
      return false;
    }
  }
  return true;
}

async function loadFeishuSettings() {
  const settings = await api('/api/settings');
  const feishu = settings.feishu || {};
  document.getElementById('feishu-app-id').value = feishu.app_id || '';
  document.getElementById('feishu-app-secret').value = feishu.app_secret || '';
  document.getElementById('feishu-bitable-url').value = feishu.bitable_url || '';
  document.getElementById('feishu-field-name').value = feishu.attachment_field_name || '图片编辑';
  document.getElementById('feishu-row-range').value = feishu.row_range || '';
  document.getElementById('feishu-upload-root').value = feishu.upload_root || '';
}

async function saveFeishuSettings() {
  const payload = collectFeishuPayload();
  await api('/api/settings', {
    method: 'POST',
    body: JSON.stringify({
      feishu: {
        app_id: payload.app_id,
        app_secret: payload.app_secret,
        bitable_url: payload.bitable_url,
        attachment_field_name: payload.field_name,
        row_range: payload.row_range,
        upload_root: payload.upload_root
      }
    })
  });
  appendLog('飞书配置已保存。');
}

function renderFeishuPreview(preview) {
  const container = document.getElementById('feishu-preview');
  if (!preview.mappings.length) {
    container.className = 'feishu-preview empty';
    container.textContent = '没有可上传映射：请检查行范围和总文件夹下的子文件夹。';
    return;
  }
  container.className = 'feishu-preview';
  container.innerHTML = `
    <div class="preview-nav">
      <strong>将上传 ${preview.upload_count} 个子文件夹</strong>
      <span>跳过 ${preview.skipped_folder_count} 个多余子文件夹</span>
    </div>
    <div class="feishu-mapping-list">
      ${preview.mappings.map((item) => `
        <div class="feishu-mapping-row">
          <strong>第 ${item.row_number} 行</strong>
          <span>${escapeHtml(item.folder_name)}</span>
          <em>${item.image_count} 张：${escapeHtml(item.images.join('、'))}</em>
        </div>
      `).join('')}
    </div>
  `;
}

async function previewFeishuFolders() {
  const payload = collectFeishuPayload();
  if (!payload.row_range || !payload.upload_root) {
    appendLog('请先填写行范围并选择上传总文件夹。');
    return;
  }
  const preview = await api('/api/feishu/preview-folders', {
    method: 'POST',
    body: JSON.stringify({ row_range: payload.row_range, upload_root: payload.upload_root })
  });
  renderFeishuPreview(preview);
}

async function testFeishuConnection() {
  const payload = collectFeishuPayload();
  if (!requireFeishuPayload(payload, false)) {
    return;
  }
  const result = await api('/api/feishu/test', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  appendLog(`飞书连接正常：找到 ${result.record_count} 行，字段 ${result.field_name} 可用。`);
}

async function runFeishuUpload() {
  const payload = collectFeishuPayload();
  if (!requireFeishuPayload(payload, true)) {
    return;
  }
  if (state.feishuInProgress) {
    appendLog('飞书上传正在执行，请等待完成。');
    return;
  }
  const button = document.getElementById('feishu-upload-btn');
  state.feishuInProgress = true;
  button.disabled = true;
  button.textContent = '上传中...';
  try {
    await saveFeishuSettings();
    await previewFeishuFolders();
    updateFeishuProgress({ percent: 0, message: '准备开始飞书上传' });
    const started = await api('/api/feishu/upload/start', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    const task = await waitForFeishuTask(started.task.id);
    appendLog(`飞书上传完成：${task.result.upload_count} 行，跳过 ${task.result.skipped_folder_count} 个多余子文件夹。`);
  } catch (error) {
    appendLog(`错误：${error.message}`);
  } finally {
    state.feishuInProgress = false;
    button.disabled = false;
    button.textContent = '开始上传';
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
document.querySelectorAll('input[name="perspective-mode"]').forEach((input) => {
  input.addEventListener('change', (event) => {
    state.perspectiveMode = event.target.value;
    syncPerspectiveMode();
  });
});
document.getElementById('perspective-scene-btn').addEventListener('click', () => runAction(async () => {
  const selected = await window.xhsApp.selectPerspectiveSceneImage();
  if (!selected) {
    return;
  }
  state.perspectiveScenePath = selected;
  renderPerspectiveCanvas();
  renderExcelPreviewList();
  renderImagePreviewList();
}));
document.getElementById('perspective-excel-btn').addEventListener('click', () => runAction(async () => {
  const selected = await window.xhsApp.selectPerspectiveExcelFile();
  if (!selected) {
    return;
  }
  state.perspectiveExcelPath = selected;
  await loadPerspectiveExcelRows();
}));
document.getElementById('perspective-overlays-btn').addEventListener('click', () => runAction(async () => {
  const selected = await window.xhsApp.selectPerspectiveOverlayFiles();
  if (selected.length === 0) {
    return;
  }
  state.perspectiveOverlayPaths = selected;
  state.perspectiveOverlayItems = createPerspectiveOverlayItems(selected);
  state.perspectiveOverlayIndex = 0;
  renderPerspectiveCanvas();
  renderImagePreviewList();
  updatePerspectiveSummary();
}));
document.getElementById('perspective-overlay-folder-btn').addEventListener('click', () => runAction(async () => {
  const selected = await window.xhsApp.selectPerspectiveOverlayFolder();
  if (selected.length === 0) {
    return;
  }
  state.perspectiveOverlayPaths = selected;
  state.perspectiveOverlayItems = createPerspectiveOverlayItems(selected);
  state.perspectiveOverlayIndex = 0;
  renderPerspectiveCanvas();
  renderImagePreviewList();
  updatePerspectiveSummary();
}));
document.getElementById('perspective-opacity').addEventListener('input', () => {
  renderPerspectiveCanvas();
  renderImagePreviewList();
});
document.getElementById('image-preview-size').addEventListener('input', (event) => {
  state.perspectiveImageDefaults.previewWidth = Number(event.target.value);
  renderImagePreviewList();
});
document.getElementById('image-default-opacity').addEventListener('input', (event) => {
  state.perspectiveImageDefaults.opacity = Number(event.target.value);
});
document.getElementById('image-default-shadow').addEventListener('change', (event) => {
  state.perspectiveImageDefaults.shadow = event.target.checked;
});
document.getElementById('image-apply-default-btn').addEventListener('click', () => {
  const defaultPoints = clonePerspectivePoints(currentPerspectivePoints());
  state.perspectiveOverlayItems.forEach((item) => {
    item.points = clonePerspectivePoints(defaultPoints);
    item.opacity = Number(state.perspectiveImageDefaults.opacity);
    item.shadow = Boolean(state.perspectiveImageDefaults.shadow);
  });
  renderPerspectiveCanvas();
  renderImagePreviewList();
  appendLog('已将图片叠图统一默认样式应用到全部图片。');
});
document.getElementById('image-reset-points-btn').addEventListener('click', () => {
  state.perspectiveOverlayItems.forEach((item) => {
    item.points = clonePerspectivePoints();
  });
  renderPerspectiveCanvas();
  renderImagePreviewList();
  appendLog('已重置全部图片叠图四角位置。');
});
document.getElementById('perspective-reset-btn').addEventListener('click', resetPerspectivePoints);
document.getElementById('perspective-start-btn').addEventListener('click', runPerspectiveCompose);
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
document.getElementById('feishu-folder-btn').addEventListener('click', () => runAction(async () => {
  const selected = await window.xhsApp.selectFeishuUploadRoot();
  if (!selected) {
    return;
  }
  document.getElementById('feishu-upload-root').value = selected;
  await previewFeishuFolders();
}));
document.getElementById('feishu-save-btn').addEventListener('click', () => runAction(saveFeishuSettings));
document.getElementById('feishu-preview-btn').addEventListener('click', () => runAction(previewFeishuFolders));
document.getElementById('feishu-test-btn').addEventListener('click', () => runAction(testFeishuConnection));
document.getElementById('feishu-upload-btn').addEventListener('click', runFeishuUpload);

renderProject();
setupNavigation();
syncPerspectiveMode();
renderPerspectiveCanvas();
renderExcelPreviewList();
renderImagePreviewList();
syncAspectGuardControl();
syncSummaryControls();
renderLayoutTool();
refreshBackendStatus();
runAction(loadFeishuSettings);
setInterval(refreshBackendStatus, 5000);
