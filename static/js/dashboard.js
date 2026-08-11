// StreamYT Pro - Interactive Dashboard Logic
document.addEventListener('DOMContentLoaded', () => {
  // State variables
  let currentSessions = [];
  let currentConfig = {};
  let currentBrowserPath = "__ROOT__";
  let isEditingSession = false;
  let nextSessionTargetSeconds = 0;
  let browserRawItems = [];

  // ==========================================
  // DOM Elements Initialization
  // ==========================================
  const liveClock = document.getElementById('liveClock');
  const liveDate = document.getElementById('liveDate');
  
  // Status Monitor Elements
  const statusCard = document.getElementById('statusCard');
  const statusBeacon = document.getElementById('statusBeacon');
  const statusHeadline = document.getElementById('statusHeadline');
  const btnStopStream = document.getElementById('btnStopStream');
  
  const liveActiveView = document.getElementById('liveActiveView');
  const liveSessionTitle = document.getElementById('liveSessionTitle');
  const liveSessionVideo = document.getElementById('liveSessionVideo');
  const liveUptime = document.getElementById('liveUptime');
  const teleBitrate = document.getElementById('teleBitrate');
  const teleFps = document.getElementById('teleFps');
  const teleSpeed = document.getElementById('teleSpeed');
  const teleTime = document.getElementById('teleTime');

  const idleWaitingView = document.getElementById('idleWaitingView');
  const nextSessionName = document.getElementById('nextSessionName');
  const nextSessionSchedule = document.getElementById('nextSessionSchedule');
  const countdownDigits = document.getElementById('countdownDigits');

  // Sessions List Elements
  const sessionsList = document.getElementById('sessionsList');
  const sessionCountBadge = document.getElementById('sessionCountBadge');
  const btnOpenAddSession = document.getElementById('btnOpenAddSession');
  const btnExportSessions = document.getElementById('btnExportSessions');
  const btnImportSessions = document.getElementById('btnImportSessions');
  const importFileInput = document.getElementById('importFileInput');

  // Session Modal Elements
  const sessionModal = document.getElementById('sessionModal');
  const modalSessionTitle = document.getElementById('modalSessionTitle');
  const btnCloseSessionModal = document.getElementById('btnCloseSessionModal');
  const btnCancelSession = document.getElementById('btnCancelSession');
  const sessionForm = document.getElementById('sessionForm');
  const formSessionId = document.getElementById('formSessionId');
  const formSessionName = document.getElementById('formSessionName');
  const formVideoPath = document.getElementById('formVideoPath');
  const btnBrowseVideo = document.getElementById('btnBrowseVideo');
  const formStreamKey = document.getElementById('formStreamKey');
  const btnToggleFormKeyVisibility = document.getElementById('btnToggleFormKeyVisibility');
  const videoProbeBox = document.getElementById('videoProbeBox');
  const videoProbeText = document.getElementById('videoProbeText');
  const formStartTime = document.getElementById('formStartTime');
  const formDuration = document.getElementById('formDuration');
  const modeRadios = document.getElementsByName('modeOption');
  const daysCheckboxes = document.querySelectorAll('#daysSelector input[type="checkbox"]');
  const btnSelectAllDays = document.getElementById('btnSelectAllDays');

  // File Browser Modal Elements (Dual-Pane)
  const browserModal = document.getElementById('browserModal');
  const btnCloseBrowserModal = document.getElementById('btnCloseBrowserModal');
  const btnCloseBrowser = document.getElementById('btnCloseBrowser');
  const browserBreadcrumbs = document.getElementById('browserBreadcrumbs');
  const browserSearchInput = document.getElementById('browserSearchInput');
  const browserFileList = document.getElementById('browserFileList');
  const btnBrowserUp = document.getElementById('btnBrowserUp');
  const quickShortcutsList = document.getElementById('quickShortcutsList');

  // Settings Modal Elements
  const settingsModal = document.getElementById('settingsModal');
  const btnOpenSettings = document.getElementById('btnOpenSettings');
  const btnCloseSettingsModal = document.getElementById('btnCloseSettingsModal');
  const btnCancelSettings = document.getElementById('btnCancelSettings');
  const settingsForm = document.getElementById('settingsForm');
  const cfgStreamKey = document.getElementById('cfgStreamKey');
  const btnToggleKeyVisibility = document.getElementById('btnToggleKeyVisibility');
  const cfgRtmpUrl = document.getElementById('cfgRtmpUrl');
  const cfgVideoPreset = document.getElementById('cfgVideoPreset');
  const cfgVideoBitrate = document.getElementById('cfgVideoBitrate');
  const cfgAudioBitrate = document.getElementById('cfgAudioBitrate');

  // Telegram Settings Elements
  const cfgTelegramEnabled = document.getElementById('cfgTelegramEnabled');
  const cfgTelegramBotToken = document.getElementById('cfgTelegramBotToken');
  const btnToggleTgTokenVisibility = document.getElementById('btnToggleTgTokenVisibility');
  const cfgTelegramChatId = document.getElementById('cfgTelegramChatId');
  const cfgTgNotifyStart = document.getElementById('cfgTgNotifyStart');
  const cfgTgNotifyEnd = document.getElementById('cfgTgNotifyEnd');
  const cfgTgNotifyError = document.getElementById('cfgTgNotifyError');
  const btnTestTelegram = document.getElementById('btnTestTelegram');

  // Logs Elements
  const terminalLogs = document.getElementById('terminalLogs');
  const chkAutoScroll = document.getElementById('chkAutoScroll');
  const btnRefreshLogs = document.getElementById('btnRefreshLogs');

  // Toast Notification Container
  const toastContainer = document.getElementById('toastContainer');

  function showToast(message, type = 'success') {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation';
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // ==========================================
  // Polling Status & Telemetry
  // ==========================================
  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      if (data.status === 'success') {
        updateStatusUI(data);
      }
    } catch (err) {
      console.error('Error polling status:', err);
    }
  }

  function updateStatusUI(data) {
    if (data.current_time && liveClock) {
      liveClock.textContent = data.current_time;
    }
    if (data.current_date && liveDate) {
      liveDate.textContent = data.current_date;
    }

    const stream = data.stream;
    if (stream && stream.is_live) {
      // Live State
      if (statusCard) statusCard.className = 'card status-monitor-card is-live';
      if (statusBeacon) statusBeacon.className = 'status-beacon live';
      if (statusHeadline) statusHeadline.textContent = 'SEDANG LIVE DI YOUTUBE';
      if (btnStopStream) btnStopStream.style.display = 'inline-flex';

      if (liveActiveView) liveActiveView.style.display = 'block';
      if (idleWaitingView) idleWaitingView.style.display = 'none';

      if (stream.active_session) {
        if (liveSessionTitle) liveSessionTitle.textContent = stream.active_session.name || 'Sesi Live';
        if (liveSessionVideo) {
          const fname = (stream.active_session.video_path || '').split('\\').pop().split('/').pop();
          const span = liveSessionVideo.querySelector('span');
          if (span) span.textContent = fname;
        }
      }

      if (liveUptime) liveUptime.textContent = stream.uptime_formatted || '00:00:00';
      if (teleBitrate) teleBitrate.textContent = stream.stats ? (stream.stats.bitrate || '0 kbits/s') : '0 kbits/s';
      if (teleFps) teleFps.textContent = stream.stats ? ((stream.stats.fps || '0') + ' FPS') : '0 FPS';
      if (teleSpeed) teleSpeed.textContent = stream.stats ? (stream.stats.speed || '1.0x') : '1.0x';
      if (teleTime) teleTime.textContent = stream.stats && stream.stats.current_time ? stream.stats.current_time.split('.')[0] : '00:00:00';

    } else {
      // Idle / Waiting State
      if (statusCard) statusCard.className = 'card status-monitor-card';
      if (btnStopStream) btnStopStream.style.display = 'none';
      if (liveActiveView) liveActiveView.style.display = 'none';
      if (idleWaitingView) idleWaitingView.style.display = 'block';

      if (data.next_session) {
        if (statusBeacon) statusBeacon.className = 'status-beacon waiting';
        if (statusHeadline) statusHeadline.textContent = 'MENUNGGU JADWAL SESI';
        
        const next = data.next_session;
        if (nextSessionName) nextSessionName.textContent = next.session ? next.session.name : '';
        const dayPrefix = next.is_today ? 'Hari Ini' : next.day_name;
        if (nextSessionSchedule) {
          const span = nextSessionSchedule.querySelector('span');
          if (span) span.textContent = `${dayPrefix} pukul ${next.session.start_time} WIB`;
        }
        
        nextSessionTargetSeconds = next.seconds_remaining;
        renderCountdown(nextSessionTargetSeconds);
      } else {
        if (statusBeacon) statusBeacon.className = 'status-beacon idle';
        if (statusHeadline) statusHeadline.textContent = 'SERVER STANDBY (IDLE)';
        if (nextSessionName) nextSessionName.textContent = 'Belum ada jadwal sesi aktif';
        if (nextSessionSchedule) {
          const span = nextSessionSchedule.querySelector('span');
          if (span) span.textContent = 'Tambahkan jadwal baru untuk mulai streaming otomatis';
        }
        if (countdownDigits) countdownDigits.textContent = '--:--:--';
      }
    }
  }

  function renderCountdown(totalSec) {
    if (!countdownDigits) return;
    if (totalSec <= 0) {
      countdownDigits.textContent = '00:00:00';
      return;
    }
    const h = Math.floor(totalSec / 3600);
    const m = Math.floor((totalSec % 3600) / 60);
    const s = totalSec % 60;
    countdownDigits.textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  // Countdown local ticker
  setInterval(() => {
    if (nextSessionTargetSeconds > 0) {
      nextSessionTargetSeconds--;
      renderCountdown(nextSessionTargetSeconds);
    }
  }, 1000);

  // Stop Stream action
  if (btnStopStream) {
    btnStopStream.addEventListener('click', async () => {
      if (!confirm('Apakah Anda yakin ingin menghentikan siaran YouTube sekarang?')) return;
      try {
        const res = await fetch('/api/stream/stop', { method: 'POST' });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('Live stream berhasil dihentikan.', 'success');
          fetchStatus();
        } else {
          showToast(data.message || 'Gagal menghentikan stream', 'error');
        }
      } catch (err) {
        showToast('Terjadi kesalahan sistem.', 'error');
      }
    });
  }

  // ==========================================
  // Sessions Management
  // ==========================================
  async function loadSessions() {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      if (data.status === 'success') {
        currentSessions = data.data;
        renderSessionsList(currentSessions);
      }
    } catch (err) {
      console.error('Error loading sessions:', err);
    }
  }

  const DAY_NAMES = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'];

  function renderSessionsList(sessions) {
    if (!sessionsList) return;
    if (sessionCountBadge) sessionCountBadge.textContent = `${sessions.length} Sesi`;

    if (sessions.length === 0) {
      sessionsList.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-calendar-xmark"></i>
          <h3>Belum Ada Jadwal Sesi</h3>
          <p>Klik tombol "+ Tambah Jadwal Sesi" di atas untuk menambahkan siaran video pertama Anda.</p>
        </div>
      `;
      return;
    }

    sessionsList.innerHTML = sessions.map(session => {
      let modeBadge = '';
      if (!session.duration) {
        modeBadge = '<span class="session-mode-badge badge-mode-a">Mode A (Selesai Asli)</span>';
      } else if (session.loop !== false) {
        modeBadge = `<span class="session-mode-badge badge-mode-b">Mode B (Loop ${session.duration})</span>`;
      } else {
        modeBadge = `<span class="session-mode-badge badge-mode-c">Mode C (Cut ${session.duration})</span>`;
      }

      // Days tags
      const days = session.days || [];
      let daysHtml = '';
      if (days.length === 0 || days.length === 7) {
        daysHtml = '<span class="day-tag active">Setiap Hari</span>';
      } else {
        daysHtml = DAY_NAMES.map((d, i) => {
          const isActive = days.includes(i);
          return `<span class="day-tag ${isActive ? 'active' : ''}">${d}</span>`;
        }).join('');
      }

      const fileOk = session.file_exists;
      const fileIcon = fileOk 
        ? '<i class="fa-solid fa-circle-check file-status-icon ok" title="File tersedia di PC"></i>'
        : '<i class="fa-solid fa-triangle-exclamation file-status-icon missing" title="File tidak ditemukan!"></i>';

      const isChecked = session.enabled !== false ? 'checked' : '';

      const keyBadge = session.has_stream_key
        ? `<span class="session-key-tag has-key" title="Stream Key YouTube terpasang khusus untuk sesi ini"><i class="fa-solid fa-key"></i> Key Terpasang</span>`
        : `<span class="session-key-tag missing" title="Stream Key belum diisi untuk sesi ini"><i class="fa-solid fa-key"></i> Tanpa Key</span>`;

      return `
        <div class="session-item-card ${session.enabled === false ? 'disabled' : ''}" data-id="${session.id}">
          <div class="session-time-badge">
            <span class="time-val">${session.start_time}</span>
            <span class="time-zone">WIB</span>
          </div>

          <div class="session-main-meta">
            <div class="session-title-row">
              <span class="session-name">${escapeHtml(session.name)}</span>
              ${modeBadge}
              ${keyBadge}
            </div>
            <div class="session-path-row">
              ${fileIcon}
              <span title="${escapeHtml(session.video_path)}">${escapeHtml(session.video_path)}</span>
            </div>
            <div class="session-days-row">
              ${daysHtml}
            </div>
          </div>

          <div class="session-actions-group">
            <!-- Toggle Switch -->
            <label class="switch-control" title="${session.enabled ? 'Nonaktifkan Sesi' : 'Aktifkan Sesi'}">
              <input type="checkbox" ${isChecked} onchange="toggleSession('${session.id}')">
              <span class="switch-slider"></span>
            </label>

            <!-- Play Now -->
            <button class="btn btn-success btn-icon" title="Putar & Live Sekarang" onclick="startSessionNow('${session.id}')">
              <i class="fa-solid fa-play"></i>
            </button>

            <!-- Edit -->
            <button class="btn btn-secondary btn-icon" title="Edit Sesi" onclick="openEditSessionModal('${session.id}')">
              <i class="fa-solid fa-pen-to-square"></i>
            </button>

            <!-- Delete -->
            <button class="btn btn-danger btn-icon" title="Hapus Sesi" onclick="deleteSession('${session.id}')">
              <i class="fa-solid fa-trash"></i>
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  window.toggleSession = async (id) => {
    try {
      const res = await fetch(`/api/sessions/${id}/toggle`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        showToast(data.enabled ? 'Sesi diaktifkan' : 'Sesi dinonaktifkan', 'success');
        loadSessions();
        fetchStatus();
      }
    } catch (err) {
      showToast('Gagal mengubah status sesi', 'error');
    }
  };

  window.deleteSession = async (id) => {
    if (!confirm('Hapus jadwal sesi ini?')) return;
    try {
      const res = await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.status === 'success') {
        showToast('Sesi berhasil dihapus', 'success');
        loadSessions();
        fetchStatus();
      }
    } catch (err) {
      showToast('Gagal menghapus sesi', 'error');
    }
  };

  window.startSessionNow = async (id) => {
    if (!confirm('Mulai live streaming sesi ini sekarang ke YouTube?')) return;
    try {
      const res = await fetch(`/api/sessions/${id}/start`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        showToast('Live streaming dimulai!', 'success');
        fetchStatus();
      } else {
        showToast(data.message || 'Gagal memulai stream', 'error');
      }
    } catch (err) {
      showToast('Terjadi kesalahan saat memulai stream', 'error');
    }
  };

  // ==========================================
  // Session Backup & Restore
  // ==========================================
  if (btnExportSessions) {
    btnExportSessions.addEventListener('click', () => {
      window.location.href = '/api/sessions-export';
      showToast('Mengunduh file backup jadwal sesi (.json)...', 'success');
    });
  }

  if (btnImportSessions && importFileInput) {
    btnImportSessions.addEventListener('click', () => {
      importFileInput.value = '';
      importFileInput.click();
    });

    importFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const isReplace = confirm('PILIHAN CARA MEMUAT SESI:\n\n• Klik [OK] untuk MENIMPA (Replace) seluruh sesi yang ada dengan isi file ini.\n• Klik [Cancel] untuk MENGGABUNGKAN (Merge) isi file ini dengan jadwal sesi yang sudah ada.');
      const mode = isReplace ? 'replace' : 'merge';

      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          const parsed = JSON.parse(event.target.result);
          const sessionsArray = Array.isArray(parsed) ? parsed : (parsed.sessions || []);
          
          if (!sessionsArray || sessionsArray.length === 0) {
            showToast('File JSON tidak berisi data jadwal sesi yang valid!', 'error');
            return;
          }

          const res = await fetch('/api/sessions-import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sessions: sessionsArray, mode: mode })
          });
          const data = await res.json();
          if (data.status === 'success') {
            showToast(data.message || 'Jadwal sesi berhasil dimuat!', 'success');
            loadSessions();
            fetchStatus();
          } else {
            showToast(data.detail || 'Gagal memuat sesi', 'error');
          }
        } catch (err) {
          showToast('Format file JSON tidak valid atau rusak!', 'error');
        }
      };
      reader.readAsText(file);
    });
  }

  // ==========================================
  // Session Modal (Add / Edit)
  // ==========================================
  if (btnOpenAddSession) {
    btnOpenAddSession.addEventListener('click', () => {
      isEditingSession = false;
      if (modalSessionTitle) modalSessionTitle.innerHTML = '<i class="fa-solid fa-calendar-plus"></i> Tambah Jadwal Sesi';
      if (sessionForm) sessionForm.reset();
      if (formSessionId) formSessionId.value = '';
      if (formStreamKey) formStreamKey.value = '';
      if (formStartTime) formStartTime.value = '08:00';
      if (videoProbeBox) videoProbeBox.style.display = 'none';
      const modeA = document.getElementById('modeA');
      if (modeA) modeA.checked = true;
      updateDurationInputState('A');
      openModal(sessionModal);
    });
  }

  if (btnToggleFormKeyVisibility) {
    btnToggleFormKeyVisibility.addEventListener('click', () => {
      if (!formStreamKey) return;
      if (formStreamKey.type === 'password') {
        formStreamKey.type = 'text';
        btnToggleFormKeyVisibility.innerHTML = '<i class="fa-regular fa-eye-slash"></i>';
      } else {
        formStreamKey.type = 'password';
        btnToggleFormKeyVisibility.innerHTML = '<i class="fa-regular fa-eye"></i>';
      }
    });
  }

  window.openEditSessionModal = (id) => {
    const session = currentSessions.find(s => s.id === id);
    if (!session) return;

    isEditingSession = true;
    if (modalSessionTitle) modalSessionTitle.innerHTML = '<i class="fa-solid fa-pen-to-square"></i> Edit Jadwal Sesi';
    if (formSessionId) formSessionId.value = session.id;
    if (formSessionName) formSessionName.value = session.name;
    if (formVideoPath) formVideoPath.value = session.video_path;
    if (formStreamKey) formStreamKey.value = session.masked_stream_key || session.stream_key || '';
    if (formStartTime) formStartTime.value = session.start_time;
    if (formDuration) formDuration.value = session.duration || '';

    // Mode
    if (!session.duration) {
      const modeA = document.getElementById('modeA');
      if (modeA) modeA.checked = true;
      updateDurationInputState('A');
    } else if (session.loop !== false) {
      const modeB = document.getElementById('modeB');
      if (modeB) modeB.checked = true;
      updateDurationInputState('B');
    } else {
      const modeC = document.getElementById('modeC');
      if (modeC) modeC.checked = true;
      updateDurationInputState('C');
    }

    // Days
    const days = session.days || [];
    daysCheckboxes.forEach(cb => {
      cb.checked = days.includes(parseInt(cb.value));
    });

    // Probe video if path exists
    validateVideoPath(session.video_path);

    openModal(sessionModal);
  };

  function updateDurationInputState(mode) {
    if (!formDuration) return;
    if (mode === 'A') {
      formDuration.disabled = true;
      formDuration.placeholder = 'Tidak berlaku untuk Mode A';
      formDuration.value = '';
    } else {
      formDuration.disabled = false;
      formDuration.placeholder = '03:00:00 (JJ:MM:DD)';
      if (!formDuration.value) {
        formDuration.value = '02:00:00';
      }
    }
  }

  modeRadios.forEach(radio => {
    radio.addEventListener('change', (e) => {
      updateDurationInputState(e.target.value);
    });
  });

  if (btnSelectAllDays) {
    btnSelectAllDays.addEventListener('click', () => {
      const allChecked = Array.from(daysCheckboxes).every(cb => cb.checked);
      daysCheckboxes.forEach(cb => cb.checked = !allChecked);
    });
  }

  if (formVideoPath) {
    formVideoPath.addEventListener('blur', () => {
      if (formVideoPath.value.trim()) {
        validateVideoPath(formVideoPath.value.trim());
      }
    });
  }

  async function validateVideoPath(path) {
    if (!path) return;
    try {
      const res = await fetch('/api/validate-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_path: path })
      });
      const data = await res.json();
      if (data.status === 'success' && data.data) {
        const info = data.data;
        if (info.valid) {
          if (videoProbeBox) {
            videoProbeBox.style.display = 'flex';
            videoProbeBox.className = 'video-preview-badge';
          }
          if (videoProbeText) {
            videoProbeText.textContent = `Resolusi: ${info.resolution || 'OK'} | Durasi: ${info.duration_str} | Ukuran: ${info.size_mb} MB`;
          }
        } else {
          if (videoProbeBox) {
            videoProbeBox.style.display = 'flex';
            videoProbeBox.className = 'video-preview-badge warning';
          }
          if (videoProbeText) {
            videoProbeText.textContent = info.error || 'File tidak ditemukan di path tersebut.';
          }
        }
      }
    } catch (err) {
      console.error('Validation error:', err);
    }
  }

  if (sessionForm) {
    sessionForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const selectedRadio = document.querySelector('input[name="modeOption"]:checked');
      const selectedMode = selectedRadio ? selectedRadio.value : 'A';
      let durationVal = formDuration ? formDuration.value.trim() : '';
      let loopVal = true;

      if (selectedMode === 'A') {
        durationVal = null;
        loopVal = false;
      } else if (selectedMode === 'B') {
        loopVal = true;
      } else if (selectedMode === 'C') {
        loopVal = false;
      }

      const selectedDays = Array.from(daysCheckboxes)
        .filter(cb => cb.checked)
        .map(cb => parseInt(cb.value));

      const payload = {
        name: formSessionName ? formSessionName.value.trim() : '',
        video_path: formVideoPath ? formVideoPath.value.trim() : '',
        stream_key: formStreamKey ? formStreamKey.value.trim() : '',
        start_time: formStartTime ? formStartTime.value.trim() : '',
        days: selectedDays,
        duration: durationVal,
        loop: loopVal,
        enabled: true
      };

      const sId = formSessionId ? formSessionId.value : '';
      const url = isEditingSession ? `/api/sessions/${sId}` : '/api/sessions';
      const method = isEditingSession ? 'PUT' : 'POST';

      try {
        const res = await fetch(url, {
          method: method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast(isEditingSession ? 'Sesi berhasil diperbarui' : 'Sesi berhasil ditambahkan', 'success');
          closeModal(sessionModal);
          loadSessions();
          fetchStatus();
        } else {
          showToast(data.detail || 'Gagal menyimpan sesi', 'error');
        }
      } catch (err) {
        showToast('Terjadi kesalahan saat menyimpan', 'error');
      }
    });
  }

  if (btnCloseSessionModal) btnCloseSessionModal.addEventListener('click', () => closeModal(sessionModal));
  if (btnCancelSession) btnCancelSession.addEventListener('click', () => closeModal(sessionModal));

  // ==========================================
  // Dual-Pane File Explorer Web Modal
  // ==========================================
  if (btnBrowseVideo) {
    btnBrowseVideo.addEventListener('click', () => {
      let initialDir = "__ROOT__";
      if (formVideoPath && formVideoPath.value.trim()) {
        const val = formVideoPath.value.trim();
        const lastSlash = Math.max(val.lastIndexOf('\\'), val.lastIndexOf('/'));
        if (lastSlash > 0) {
          initialDir = val.substring(0, lastSlash);
        }
      }
      loadQuickShortcuts();
      window.loadBrowserDir(initialDir);
      openModal(browserModal);
    });
  }

  async function loadQuickShortcuts() {
    if (!quickShortcutsList) return;
    try {
      const res = await fetch('/api/quick-shortcuts');
      const data = await res.json();
      if (data.status === 'success' && data.data) {
        let html = `
          <button type="button" class="sidebar-item ${currentBrowserPath === '' || currentBrowserPath === '__ROOT__' ? 'active' : ''}" onclick="loadBrowserDir('__ROOT__')">
            <i class="fa-solid fa-computer"></i> <span>Komputer (Drives)</span>
          </button>
        `;
        data.data.forEach(item => {
          const isActive = currentBrowserPath === item.path ? 'active' : '';
          html += `
            <button type="button" class="sidebar-item ${isActive}" onclick="loadBrowserDir('${escapeForAttr(item.path)}')">
              <i class="fa-solid ${item.icon}"></i> <span>${escapeHtml(item.name)}</span>
            </button>
          `;
        });
        quickShortcutsList.innerHTML = html;
      }
    } catch (err) {
      console.error('Error loading shortcuts:', err);
    }
  }

  window.loadBrowserDir = async function(dirPath) {
    if (!browserFileList) return;
    try {
      browserFileList.innerHTML = '<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i><p>Membuka folder...</p></div>';
      const res = await fetch('/api/browse-files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory: dirPath })
      });
      const data = await res.json();
      if (data.status === 'success') {
        currentBrowserPath = data.current_dir;
        browserRawItems = data.items || [];
        
        // Up button handling
        if (btnBrowserUp) {
          if (data.parent_dir !== null && data.parent_dir !== undefined) {
            btnBrowserUp.disabled = false;
            btnBrowserUp.dataset.parent = data.parent_dir;
          } else {
            btnBrowserUp.disabled = true;
            btnBrowserUp.dataset.parent = '';
          }
        }

        // Render Clickable Breadcrumbs
        renderBreadcrumbs(data.breadcrumbs || []);

        // Filter / Search reset
        if (browserSearchInput) browserSearchInput.value = '';
        renderBrowserItems(browserRawItems);
        loadQuickShortcuts();
      } else {
        browserFileList.innerHTML = `<div class="empty-state"><p>${data.message || 'Gagal membuka folder'}</p></div>`;
      }
    } catch (err) {
      browserFileList.innerHTML = '<div class="empty-state"><p>Error membaca folder PC</p></div>';
    }
  };

  function renderBreadcrumbs(crumbs) {
    if (!browserBreadcrumbs) return;
    if (!crumbs || crumbs.length === 0) {
      browserBreadcrumbs.innerHTML = '<span class="breadcrumb-chip active">Komputer</span>';
      return;
    }

    browserBreadcrumbs.innerHTML = crumbs.map((c, idx) => {
      const isLast = idx === crumbs.length - 1;
      const chip = `<span class="breadcrumb-chip ${isLast ? 'active' : ''}" onclick="loadBrowserDir('${escapeForAttr(c.path)}')">${escapeHtml(c.name)}</span>`;
      return isLast ? chip : `${chip}<span class="breadcrumb-sep">&gt;</span>`;
    }).join('');
  }

  function renderBrowserItems(items) {
    if (!browserFileList) return;
    if (!items || items.length === 0) {
      browserFileList.innerHTML = '<div class="empty-state"><i class="fa-regular fa-folder-open"></i><p>Tidak ada folder atau file video di sini.</p></div>';
      return;
    }

    browserFileList.innerHTML = items.map(item => {
      if (item.is_dir) {
        const icon = item.is_drive ? 'fa-hard-drive' : 'fa-folder';
        const driveClass = item.is_drive ? 'is-drive' : '';
        return `
          <div class="browser-item ${driveClass}" onclick="openDir('${escapeForAttr(item.path)}')">
            <div class="browser-item-left">
              <i class="fa-solid ${icon}"></i>
              <strong>${escapeHtml(item.name)}</strong>
            </div>
            <div class="browser-item-meta">
              <span class="browser-size">${item.is_drive ? 'Drive PC' : 'Folder'}</span>
              <i class="fa-solid fa-chevron-right" style="color: var(--text-dim); font-size: 11px;"></i>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="browser-item" onclick="selectVideoFile('${escapeForAttr(item.path)}')">
            <div class="browser-item-left">
              <i class="fa-solid fa-file-video"></i>
              <span>${escapeHtml(item.name)}</span>
            </div>
            <div class="browser-item-meta">
              <span class="browser-size">${item.size_mb} MB</span>
              <span class="btn-select-file-badge">Pilih Video</span>
            </div>
          </div>
        `;
      }
    }).join('');
  }

  // Realtime search filter
  if (browserSearchInput) {
    browserSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      if (!q) {
        renderBrowserItems(browserRawItems);
        return;
      }
      const filtered = browserRawItems.filter(item => item.name.toLowerCase().includes(q));
      renderBrowserItems(filtered);
    });
  }

  if (btnBrowserUp) {
    btnBrowserUp.addEventListener('click', () => {
      const p = btnBrowserUp.dataset.parent;
      if (p !== undefined && p !== '') {
        window.loadBrowserDir(p);
      }
    });
  }

  window.openDir = (path) => {
    window.loadBrowserDir(path);
  };

  window.selectVideoFile = (filePath) => {
    if (formVideoPath) formVideoPath.value = filePath;
    validateVideoPath(filePath);
    closeModal(browserModal);
    const fname = filePath.split(/[\/\\]/).pop();
    showToast('File video dipilih: ' + fname, 'success');
  };

  if (btnCloseBrowserModal) btnCloseBrowserModal.addEventListener('click', () => closeModal(browserModal));
  if (btnCloseBrowser) btnCloseBrowser.addEventListener('click', () => closeModal(browserModal));

  // ==========================================
  // Settings Modal & Tabs
  // ==========================================
  document.querySelectorAll('.settings-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.settings-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.settings-tab-pane').forEach(p => p.classList.remove('active'));
      
      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');
    });
  });

  if (btnOpenSettings) {
    btnOpenSettings.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/config');
        const data = await res.json();
        if (data.status === 'success') {
          currentConfig = data.data;
          // YouTube
          if (cfgRtmpUrl) cfgRtmpUrl.value = currentConfig.rtmp_url || 'rtmp://a.rtmp.youtube.com/live2';
          if (cfgVideoPreset) cfgVideoPreset.value = currentConfig.video_preset || 'veryfast';
          if (cfgVideoBitrate) cfgVideoBitrate.value = currentConfig.video_bitrate || '4500k';
          if (cfgAudioBitrate) cfgAudioBitrate.value = currentConfig.audio_bitrate || '128k';

          // Telegram
          if (cfgTelegramEnabled) cfgTelegramEnabled.checked = Boolean(currentConfig.telegram_enabled);
          if (cfgTelegramBotToken) cfgTelegramBotToken.value = currentConfig.masked_tg_token || '';
          if (cfgTelegramChatId) cfgTelegramChatId.value = currentConfig.telegram_chat_id || '';
          if (cfgTgNotifyStart) cfgTgNotifyStart.checked = currentConfig.telegram_notify_start !== false;
          if (cfgTgNotifyEnd) cfgTgNotifyEnd.checked = currentConfig.telegram_notify_end !== false;
          if (cfgTgNotifyError) cfgTgNotifyError.checked = currentConfig.telegram_notify_error !== false;

          openModal(settingsModal);
        }
      } catch (err) {
        showToast('Gagal memuat pengaturan', 'error');
      }
    });
  }

  if (btnToggleTgTokenVisibility) {
    btnToggleTgTokenVisibility.addEventListener('click', () => {
      if (!cfgTelegramBotToken) return;
      if (cfgTelegramBotToken.type === 'password') {
        cfgTelegramBotToken.type = 'text';
        btnToggleTgTokenVisibility.innerHTML = '<i class="fa-regular fa-eye-slash"></i>';
      } else {
        cfgTelegramBotToken.type = 'password';
        btnToggleTgTokenVisibility.innerHTML = '<i class="fa-regular fa-eye"></i>';
      }
    });
  }

  // Test Telegram Button
  if (btnTestTelegram) {
    btnTestTelegram.addEventListener('click', async () => {
      const token = cfgTelegramBotToken ? cfgTelegramBotToken.value.trim() : '';
      const chatId = cfgTelegramChatId ? cfgTelegramChatId.value.trim() : '';

      if (!token || !chatId) {
        showToast('Isi Bot Token dan Chat ID terlebih dahulu!', 'error');
        return;
      }

      showToast('Mengirim pesan tes ke Telegram...', 'success');
      try {
        const res = await fetch('/api/telegram/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bot_token: token, chat_id: chatId })
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast(data.message || 'Pesan tes berhasil dikirim!', 'success');
        } else {
          showToast(data.message || 'Gagal mengirim ke Telegram', 'error');
        }
      } catch (err) {
        showToast('Terjadi kesalahan saat menguji Telegram', 'error');
      }
    });
  }

  if (settingsForm) {
    settingsForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        rtmp_url: cfgRtmpUrl ? cfgRtmpUrl.value.trim() : '',
        video_preset: cfgVideoPreset ? cfgVideoPreset.value : 'veryfast',
        video_bitrate: cfgVideoBitrate ? cfgVideoBitrate.value : '4500k',
        audio_bitrate: cfgAudioBitrate ? cfgAudioBitrate.value : '128k',
        telegram_enabled: cfgTelegramEnabled ? cfgTelegramEnabled.checked : false,
        telegram_bot_token: cfgTelegramBotToken ? cfgTelegramBotToken.value.trim() : '',
        telegram_chat_id: cfgTelegramChatId ? cfgTelegramChatId.value.trim() : '',
        telegram_notify_start: cfgTgNotifyStart ? cfgTgNotifyStart.checked : true,
        telegram_notify_end: cfgTgNotifyEnd ? cfgTgNotifyEnd.checked : true,
        telegram_notify_error: cfgTgNotifyError ? cfgTgNotifyError.checked : true
      };

      try {
        const res = await fetch('/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
          showToast('Pengaturan berhasil disimpan!', 'success');
          closeModal(settingsModal);
          fetchStatus();
        } else {
          showToast('Gagal menyimpan pengaturan', 'error');
        }
      } catch (err) {
        showToast('Gagal menyimpan pengaturan', 'error');
      }
    });
  }

  if (btnCloseSettingsModal) btnCloseSettingsModal.addEventListener('click', () => closeModal(settingsModal));
  if (btnCancelSettings) btnCancelSettings.addEventListener('click', () => closeModal(settingsModal));

  // ==========================================
  // Live Logs
  // ==========================================
  async function fetchLogs() {
    if (!terminalLogs) return;
    try {
      const res = await fetch('/api/logs?limit=80');
      const data = await res.json();
      if (data.status === 'success') {
        renderLogs(data.data);
      }
    } catch (err) {
      console.error('Error fetching logs:', err);
    }
  }

  function renderLogs(logs) {
    if (!terminalLogs || !logs || logs.length === 0) return;

    terminalLogs.innerHTML = logs.map(l => {
      const lvl = (l.level || 'INFO').toLowerCase();
      return `
        <div class="log-line ${lvl}">
          <span style="color: var(--text-dim);">${l.timestamp}</span> 
          <span class="badge-lvl">[${l.source || 'SYSTEM'}] [${l.level}]</span> 
          <span>${escapeHtml(l.message)}</span>
        </div>
      `;
    }).join('');

    if (chkAutoScroll && chkAutoScroll.checked) {
      terminalLogs.scrollTop = terminalLogs.scrollHeight;
    }
  }

  if (btnRefreshLogs) {
    btnRefreshLogs.addEventListener('click', () => {
      fetchLogs();
      showToast('Log diperbarui', 'success');
    });
  }

  // ==========================================
  // Modal Helpers & Utilities
  // ==========================================
  function openModal(modal) {
    if (modal) modal.classList.add('open');
  }

  function closeModal(modal) {
    if (modal) modal.classList.remove('open');
  }

  // Close modals when clicking on backdrop
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) {
        closeModal(overlay);
      }
    });
  });

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function escapeForAttr(str) {
    if (!str) return '';
    return str.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
  }

  // ==========================================
  // Initial Boot & Loops
  // ==========================================
  fetchStatus();
  loadSessions();
  fetchLogs();

  // Status loop: every 2 seconds
  setInterval(fetchStatus, 2000);
  // Logs loop: every 3.5 seconds
  setInterval(fetchLogs, 3500);
});
