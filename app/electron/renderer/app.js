async function refreshBackendStatus() {
  const status = document.getElementById('backend-status');
  try {
    const baseUrl = await window.xhsApp.getBackendBaseUrl();
    const response = await fetch(`${baseUrl}/api/health`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    status.textContent = data.ok ? '后端已连接' : '后端异常';
    status.className = data.ok ? 'status ok' : 'status error';
  } catch (error) {
    status.textContent = '后端未连接';
    status.className = 'status error';
  }
}

refreshBackendStatus();
setInterval(refreshBackendStatus, 5000);
