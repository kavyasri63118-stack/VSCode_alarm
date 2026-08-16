// ═══════════════════════════════════════════════════════════════════════════
// CODE ALARM V2 - DASHBOARD & ALERT CONTROL CENTER CLIENT SCRIPT
// ═══════════════════════════════════════════════════════════════════════════

// Tab Navigation
const navTabs = document.querySelectorAll('.nav-tab');
const tabContents = document.querySelectorAll('.tab-content');

navTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    navTabs.forEach(t => t.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));

    tab.classList.add('active');
    const targetId = tab.getAttribute('data-tab');
    const targetContent = document.getElementById(targetId);
    if (targetContent) targetContent.classList.add('active');

    if (targetId === 'tab-dashboard') loadDashboardData();
    if (targetId === 'tab-history') loadHistoryData();
    if (targetId === 'tab-settings') loadSettings();
  });
});

// Level 1 Metric Elements
const metricCompleted = document.getElementById('metricCompleted');
const metricFailed = document.getElementById('metricFailed');
const metricCrashed = document.getElementById('metricCrashed');
const metricRunning = document.getElementById('metricRunning');
const metricTotalTime = document.getElementById('metricTotalTime');
const runningCountBadge = document.getElementById('runningCountBadge');
const runningJobsList = document.getElementById('runningJobsList');
const recentJobsList = document.getElementById('recentJobsList');
const btnRefreshDashboard = document.getElementById('btnRefreshDashboard');

// Status Header Elements
const masterStatusPill = document.getElementById('masterStatusPill');
const masterStatusText = document.getElementById('masterStatusText');
const quietStatusPill = document.getElementById('quietStatusPill');

// Modal Elements
const jobModalOverlay = document.getElementById('jobModalOverlay');
const btnModalClose = document.getElementById('btnModalClose');
const modalStatusIcon = document.getElementById('modalStatusIcon');
const modalJobProgram = document.getElementById('modalJobProgram');
const modalJobId = document.getElementById('modalJobId');
const modalStatusVal = document.getElementById('modalStatusVal');
const modalRuntimeVal = document.getElementById('modalRuntimeVal');
const modalExitVal = document.getElementById('modalExitVal');
const modalLangVal = document.getElementById('modalLangVal');
const modalCommandVal = document.getElementById('modalCommandVal');
const modalCwdVal = document.getElementById('modalCwdVal');
const modalAnalysisSection = document.getElementById('modalAnalysisSection');
const modalErrorType = document.getElementById('modalErrorType');
const modalLikelyCause = document.getElementById('modalLikelyCause');
const modalSuggestedAction = document.getElementById('modalSuggestedAction');
const btnToggleOutput = document.getElementById('btnToggleOutput');
const modalOutputBox = document.getElementById('modalOutputBox');
const modalRawOutput = document.getElementById('modalRawOutput');
const outputToggleArrow = document.getElementById('outputToggleArrow');
const btnCopyError = document.getElementById('btnCopyError');

// Settings Toggles
const settingKeys = [
  'master_alert_system',
  'success_sound',
  'failure_sound',
  'desktop_notification',
  'failure_intelligence',
  'job_summary',
  'quiet_mode'
];

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '0.0s';
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = (seconds % 60).toFixed(1);
  if (hrs > 0) return `${hrs}h ${mins}m ${secs}s`;
  if (mins > 0) return `${mins}m ${secs}s`;
  return `${secs}s`;
}

function formatTime(ts) {
  if (!ts) return 'N/A';
  return new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// ── DATA LOADING ─────────────────────────────────────────────────────────────
async function loadDashboardData() {
  try {
    // 1. Summary
    const sumRes = await fetch('/api/summary');
    if (sumRes.ok) {
      const sumData = await sumRes.json();
      const today = sumData.today || {};
      metricCompleted.innerText = today.completed || 0;
      metricFailed.innerText = today.failed || 0;
      metricCrashed.innerText = today.crashed || 0;
      metricRunning.innerText = today.running || 0;
      metricTotalTime.innerText = formatDuration(today.total_runtime);
    }

    // 2. Running Jobs
    const runRes = await fetch('/api/running');
    if (runRes.ok) {
      const runData = await runRes.json();
      const running = runData.running || [];
      runningCountBadge.innerText = `${running.length} Running`;

      if (running.length === 0) {
        runningJobsList.innerHTML = `<div class="empty-state">No background jobs currently running. Run commands with <code>n &lt;command&gt;</code>.</div>`;
      } else {
        runningJobsList.innerHTML = running.map(j => `
          <div class="job-item" onclick="openJobModal('${j.job_id}')">
            <div class="job-item-left">
              <span class="status-badge-icon">🔄</span>
              <div>
                <div class="job-item-title">${escapeHtml(j.program || 'Command')}</div>
                <div class="job-item-sub">${escapeHtml(j.command || '')}</div>
              </div>
            </div>
            <div class="job-item-right">
              <span class="job-runtime">Running since ${formatTime(j.start_time)}</span>
            </div>
          </div>
        `).join('');
      }
    }

    // 3. Recent Completed Jobs
    const recentRes = await fetch('/api/jobs?limit=8');
    if (recentRes.ok) {
      const recentData = await recentRes.json();
      const jobs = recentData.jobs || [];
      if (jobs.length === 0) {
        recentJobsList.innerHTML = `<div class="empty-state">No past executions recorded yet.</div>`;
      } else {
        recentJobsList.innerHTML = jobs.map(j => {
          const st = j.status || 'UNKNOWN';
          const icon = st === 'SUCCESS' ? '✅' : (st === 'FAILED' ? '❌' : (st === 'CRASHED' ? '💥' : (st === 'TERMINATED' ? '⏹️' : '🔄')));
          return `
            <div class="job-item" onclick="openJobModal('${j.job_id}')">
              <div class="job-item-left">
                <span class="status-badge-icon">${icon}</span>
                <div>
                  <div class="job-item-title">${escapeHtml(j.program || 'Command')} <span class="badge">${j.language || 'Generic'}</span></div>
                  <div class="job-item-sub">${escapeHtml(j.command || '')}</div>
                </div>
              </div>
              <div class="job-item-right">
                <span class="job-runtime">${formatDuration(j.runtime_seconds)}</span>
              </div>
            </div>
          `;
        }).join('');
      }
    }
  } catch (e) {
    console.error('Failed to load dashboard data:', e);
  }
}

let currentFilter = 'ALL';
async function loadHistoryData() {
  try {
    const url = currentFilter === 'ALL' ? '/api/jobs?limit=50' : `/api/jobs?limit=50&status=${currentFilter}`;
    const res = await fetch(url);
    if (!res.ok) return;
    const data = await res.json();
    const jobs = data.jobs || [];
    const tbody = document.getElementById('historyTableBody');

    if (jobs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 24px;">No executions match the selected filter.</td></tr>`;
      return;
    }

    tbody.innerHTML = jobs.map(j => {
      const st = j.status || 'UNKNOWN';
      const icon = st === 'SUCCESS' ? '✅' : (st === 'FAILED' ? '❌' : (st === 'CRASHED' ? '💥' : (st === 'TERMINATED' ? '⏹️' : '🔄')));
      return `
        <tr>
          <td><span style="font-weight: 700;">${icon} ${st}</span></td>
          <td><strong>${escapeHtml(j.program || 'Command')}</strong><br><small style="color: var(--text-muted); font-family: var(--font-mono);">${escapeHtml(j.command || '')}</small></td>
          <td style="font-family: var(--font-mono);">${formatDuration(j.runtime_seconds)}</td>
          <td>${formatTime(j.start_time)}</td>
          <td><span class="badge">${escapeHtml(j.language || 'Generic')}</span></td>
          <td><button class="btn btn-secondary btn-small" onclick="openJobModal('${j.job_id}')">Details</button></td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    console.error('Failed to load history data:', e);
  }
}

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.getAttribute('data-filter');
    loadHistoryData();
  });
});

// ── SETTINGS ENGINE ──────────────────────────────────────────────────────────
async function loadSettings() {
  try {
    const res = await fetch('/api/settings');
    if (!res.ok) return;
    const data = await res.json();
    const s = data.settings || {};

    settingKeys.forEach(k => {
      const el = document.getElementById(`set_${k}`);
      if (el) el.checked = Boolean(s[k]);
    });

    // Update alert mute badges and header status
    updateAlertMuteBadges(s);
    updateHeaderStatus(s);
  } catch (e) {
    console.error('Failed to load settings:', e);
  }
}

function updateAlertMuteBadges(s) {
  const isQuiet = Boolean(s.quiet_mode);
  const isMaster = Boolean(s.master_alert_system);
  const alertKeys = ['success_sound', 'failure_sound', 'desktop_notification'];

  alertKeys.forEach(k => {
    const itemEl = document.getElementById(`item_${k}`);
    const tagEl = document.getElementById(`tag_${k}`);
    const isEnabled = Boolean(s[k]);

    if (tagEl && itemEl) {
      if (isQuiet && isEnabled) {
        tagEl.innerText = 'MUTED (Quiet Mode)';
        tagEl.style.display = 'inline-block';
        itemEl.classList.add('is-muted');
      } else if (!isMaster && isEnabled) {
        tagEl.innerText = 'MUTED (Master OFF)';
        tagEl.style.display = 'inline-block';
        itemEl.classList.add('is-muted');
      } else {
        tagEl.style.display = 'none';
        itemEl.classList.remove('is-muted');
      }
    }
  });
}

function updateHeaderStatus(s) {
  const masterOn = Boolean(s.master_alert_system);
  const quietOn = Boolean(s.quiet_mode);

  if (masterOn) {
    masterStatusText.innerText = 'Master Alerts: ON';
    masterStatusPill.querySelector('.status-dot').className = 'status-dot dot-green';
  } else {
    masterStatusText.innerText = 'Master Alerts: MUTED';
    masterStatusPill.querySelector('.status-dot').className = 'status-dot dot-red';
  }

  quietStatusPill.style.display = quietOn ? 'flex' : 'none';
}

settingKeys.forEach(k => {
  const el = document.getElementById(`set_${k}`);
  if (el) {
    el.addEventListener('change', async () => {
      const payload = { [k]: el.checked };
      try {
        const res = await fetch('/api/settings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.ok) {
          const data = await res.json();
          const latest = data.settings || {};
          updateAlertMuteBadges(latest);
          updateHeaderStatus(latest);
        }
      } catch (e) {
        console.error(`Failed to update setting ${k}:`, e);
      }
    });
  }
});

// ── MODAL: 3-LEVEL JOB INSPECTOR ─────────────────────────────────────────────
async function openJobModal(jobId) {
  try {
    const res = await fetch(`/api/jobs/${jobId}`);
    if (!res.ok) return;
    const data = await res.json();
    const j = data.job;
    if (!j) return;

    const st = j.status || 'UNKNOWN';
    const icon = st === 'SUCCESS' ? '✅' : (st === 'FAILED' ? '❌' : (st === 'CRASHED' ? '💥' : (st === 'TERMINATED' ? '⏹️' : '🔄')));

    modalStatusIcon.innerText = icon;
    modalJobProgram.innerText = j.program || 'Command';
    modalJobId.innerText = j.job_id || jobId;

    modalStatusVal.innerText = st;
    modalRuntimeVal.innerText = formatDuration(j.runtime_seconds);
    modalExitVal.innerText = j.exit_code !== null ? j.exit_code : 'Running';
    modalLangVal.innerText = j.language || 'Generic';
    modalCommandVal.innerText = j.command || '';
    modalCwdVal.innerText = j.cwd || '';

    // Level 3 Failure Intelligence Section
    if (st === 'FAILED' || st === 'CRASHED') {
      modalAnalysisSection.style.display = 'flex';
      modalErrorType.innerText = j.error_type || 'Unknown execution error';
      modalLikelyCause.innerText = j.likely_cause || 'Process terminated with non-zero exit status.';
      modalSuggestedAction.innerText = j.suggested_action || 'Review captured error logs.';
    } else {
      modalAnalysisSection.style.display = 'none';
    }

    // Output Box
    const outText = j.stdout_summary || j.stderr_summary || 'No output captured.';
    modalRawOutput.innerText = outText;
    modalOutputBox.style.display = 'none';
    outputToggleArrow.innerText = '▼';

    jobModalOverlay.style.display = 'flex';
  } catch (e) {
    console.error('Failed to open job modal:', e);
  }
}

btnModalClose.addEventListener('click', () => {
  jobModalOverlay.style.display = 'none';
});

jobModalOverlay.addEventListener('click', (e) => {
  if (e.target === jobModalOverlay) jobModalOverlay.style.display = 'none';
});

btnToggleOutput.addEventListener('click', () => {
  if (modalOutputBox.style.display === 'none') {
    modalOutputBox.style.display = 'flex';
    outputToggleArrow.innerText = '▲';
  } else {
    modalOutputBox.style.display = 'none';
    outputToggleArrow.innerText = '▼';
  }
});

btnCopyError.addEventListener('click', () => {
  navigator.clipboard.writeText(modalRawOutput.innerText).then(() => {
    const orig = btnCopyError.innerText;
    btnCopyError.innerText = '✅ Copied!';
    setTimeout(() => btnCopyError.innerText = orig, 1500);
  });
});

if (btnRefreshDashboard) {
  btnRefreshDashboard.addEventListener('click', () => {
    loadDashboardData();
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── SOUND STUDIO AUDIO SYNTHESIS & PREVIEW ───────────────────────────────────
let audioCtx = null;
let analyser = null;
const canvas = document.getElementById('visualizerCanvas');
const canvasCtx = canvas ? canvas.getContext('2d') : null;
const visFrequencyLabel = document.getElementById('visFrequencyLabel');

function initAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    analyser.connect(audioCtx.destination);
    drawVisualizer();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

function playTone(freq, durationMs) {
  initAudio();
  try {
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + durationMs / 1000);
    osc.connect(gain);
    gain.connect(analyser);
    osc.start();
    osc.stop(audioCtx.currentTime + durationMs / 1000);

    if (visFrequencyLabel) {
      visFrequencyLabel.innerText = `${freq} Hz`;
      setTimeout(() => {
        if (visFrequencyLabel.innerText === `${freq} Hz`) visFrequencyLabel.innerText = 'Idle';
      }, durationMs);
    }
  } catch (e) {
    console.error('Audio synthesis error:', e);
  }
}

function drawVisualizer() {
  if (!canvasCtx || !analyser) return;
  requestAnimationFrame(drawVisualizer);
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);
  analyser.getByteFrequencyData(dataArray);

  canvasCtx.fillStyle = '#080b11';
  canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

  const barWidth = (canvas.width / bufferLength) * 2.2;
  let barHeight;
  let x = 0;

  for (let i = 0; i < bufferLength; i++) {
    barHeight = (dataArray[i] / 255) * canvas.height;
    canvasCtx.fillStyle = `rgb(${dataArray[i] + 40}, 130, 246)`;
    canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
    x += barWidth + 1;
  }
}

// Connect Sound Trigger Buttons
document.querySelectorAll('.trigger-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const signal = btn.getAttribute('data-signal');
    // 1. Web Audio preview
    if (signal === 'SUCCESS') {
      playTone(523, 100);
      setTimeout(() => playTone(659, 100), 120);
      setTimeout(() => playTone(784, 250), 240);
    } else if (signal === 'ERROR') {
      playTone(680, 150);
      setTimeout(() => playTone(340, 250), 180);
    } else if (signal === 'TRAIN_DONE') {
      playTone(523, 90);
      setTimeout(() => playTone(659, 90), 100);
      setTimeout(() => playTone(784, 120), 200);
      setTimeout(() => playTone(1046, 350), 340);
    } else if (signal === 'ALERT') {
      for (let i = 0; i < 4; i++) {
        setTimeout(() => playTone(1200, 80), i * 160);
      }
    }
    // 2. Trigger native DirectSound test on backend
    try {
      fetch('/api/test-sound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pattern: signal })
      });
    } catch (e) {}
  });
});

// Periodic auto-refresh (every 3 seconds for live dashboard)
setInterval(() => {
  const activeTab = document.querySelector('.tab-content.active');
  if (activeTab && activeTab.id === 'tab-dashboard') {
    loadDashboardData();
  }
}, 3000);

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
  loadDashboardData();
  loadSettings();
});
