/* RDMA Agent Dashboard - Frontend Application */

const API_BASE = '/api/v1';

// ── Tab Management ──────────────────────────────────────────────────

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // Load data for the tab
    switch (tabName) {
        case 'dashboard': loadDashboard(); break;
        case 'investigations': loadInvestigations(); break;
        case 'skills': loadSkills(); break;
        case 'alarms': loadAlarms(); break;
    }
}

// ── API Helpers ─────────────────────────────────────────────────────

async function apiGet(path) {
    const resp = await fetch(`${API_BASE}${path}`);
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
}

async function apiPost(path, body) {
    const resp = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
}

async function apiDelete(path) {
    const resp = await fetch(`${API_BASE}${path}`, { method: 'DELETE' });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
}

// ── Toast Notifications ─────────────────────────────────────────────

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ── Dashboard ───────────────────────────────────────────────────────

async function loadDashboard() {
    try {
        const status = await apiGet('/status');
        document.getElementById('stat-monitor').textContent =
            status.monitor_running ? 'Running' : 'Stopped';
        document.getElementById('stat-monitor').style.color =
            status.monitor_running ? 'var(--success)' : 'var(--danger)';
        document.getElementById('stat-investigations').textContent = status.total_investigations;
        document.getElementById('stat-skills').textContent = status.registered_skills;

        // Update status indicator
        const dot = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        dot.className = 'status-dot status-healthy';
        text.textContent = 'Connected';

        // Load recent investigations
        const invData = await apiGet('/investigations');
        renderRecentInvestigations(invData.investigations);

        // Load alarm count
        try {
            const alarmData = await apiGet('/alarms');
            document.getElementById('stat-alarms').textContent = alarmData.alarms.length;
        } catch (e) {
            document.getElementById('stat-alarms').textContent = '0';
        }
    } catch (e) {
        const dot = document.getElementById('status-indicator');
        const text = document.getElementById('status-text');
        dot.className = 'status-dot status-error';
        text.textContent = 'Disconnected';
    }
}

function renderRecentInvestigations(investigations) {
    const tbody = document.querySelector('#recent-investigations tbody');
    const noMsg = document.getElementById('no-investigations');

    if (!investigations || investigations.length === 0) {
        tbody.innerHTML = '';
        noMsg.style.display = 'block';
        return;
    }

    noMsg.style.display = 'none';
    tbody.innerHTML = investigations.slice(0, 10).map(inv => `
        <tr>
            <td><code>${inv.issue_id}</code></td>
            <td>${escHtml(inv.summary)}</td>
            <td><span class="badge badge-${severityClass(inv.severity)}">${inv.severity}</span></td>
            <td><span class="badge badge-${statusClass(inv.status)}">${inv.status}</span></td>
            <td>${(inv.confidence * 100).toFixed(0)}%</td>
            <td>${formatTime(inv.started_at)}</td>
        </tr>
    `).join('');
}

// ── Investigations ──────────────────────────────────────────────────

async function loadInvestigations() {
    try {
        const data = await apiGet('/investigations');
        const tbody = document.querySelector('#all-investigations tbody');
        if (!data.investigations || data.investigations.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-muted">No investigations</td></tr>';
            return;
        }
        tbody.innerHTML = data.investigations.map(inv => `
            <tr>
                <td><code>${inv.issue_id}</code></td>
                <td title="${escHtml(inv.summary)}">${escHtml(inv.summary.substring(0, 60))}</td>
                <td><span class="badge badge-${severityClass(inv.severity)}">${inv.severity}</span></td>
                <td><span class="badge badge-${statusClass(inv.status)}">${inv.status}</span></td>
                <td title="${escHtml(inv.hypothesis)}">${escHtml((inv.hypothesis || '').substring(0, 40))}</td>
                <td>${(inv.confidence * 100).toFixed(0)}%</td>
                <td>${inv.steps_completed}</td>
                <td><button class="btn btn-sm" onclick="viewInvestigation('${inv.issue_id}')">View</button></td>
            </tr>
        `).join('');
    } catch (e) {
        showToast('Failed to load investigations', 'error');
    }
}

async function viewInvestigation(issueId) {
    try {
        const inv = await apiGet(`/investigations/${issueId}`);
        const detail = document.getElementById('investigation-detail');
        const content = document.getElementById('detail-content');

        content.innerHTML = `
            <div class="detail-section">
                <h3>Issue</h3>
                <p><strong>ID:</strong> <code>${inv.issue_id}</code></p>
                <p><strong>Summary:</strong> ${escHtml(inv.summary)}</p>
                <p><strong>Severity:</strong> <span class="badge badge-${severityClass(inv.severity)}">${inv.severity}</span></p>
                <p><strong>Status:</strong> <span class="badge badge-${statusClass(inv.status)}">${inv.status}</span></p>
            </div>
            <div class="detail-section">
                <h3>Analysis</h3>
                <p><strong>Hypothesis:</strong> ${escHtml(inv.hypothesis || 'N/A')}</p>
                <p><strong>Confidence:</strong> ${(inv.confidence * 100).toFixed(0)}%</p>
                <p><strong>Findings:</strong> ${escHtml(inv.findings || 'N/A')}</p>
                ${inv.resolution ? `<p><strong>Resolution:</strong> ${escHtml(inv.resolution)}</p>` : ''}
            </div>
            <div class="detail-section">
                <h3>Investigation Steps (${inv.steps.length})</h3>
                ${inv.steps.map(s => `
                    <div class="step-item ${s.success ? 'step-success' : 'step-failed'}">
                        <strong>Step ${s.step}:</strong> <code>${s.skill}</code>
                        ${Object.keys(s.params).length ? `<span style="color:var(--text-secondary)"> (${JSON.stringify(s.params)})</span>` : ''}
                        <span class="badge ${s.success ? 'badge-success' : 'badge-critical'}">${s.success ? 'OK' : 'FAILED'}</span>
                        <pre class="code-block" style="margin-top:8px;max-height:200px;">${escHtml(s.output)}</pre>
                    </div>
                `).join('')}
            </div>
            ${inv.final_report ? `
            <div class="detail-section">
                <h3>Final Report</h3>
                <pre class="code-block">${escHtml(inv.final_report)}</pre>
            </div>` : ''}
        `;

        detail.style.display = 'block';
        detail.scrollIntoView({ behavior: 'smooth' });
    } catch (e) {
        showToast('Failed to load investigation detail', 'error');
    }
}

function closeDetail() {
    document.getElementById('investigation-detail').style.display = 'none';
}

// ── Manual Check ────────────────────────────────────────────────────

async function runManualCheck() {
    try {
        showToast('Running manual check...', 'info');
        const data = await apiPost('/check', {});
        if (data.issues && data.issues.length > 0) {
            showToast(`Detected ${data.issues.length} issue(s), investigating...`, 'info');
        } else {
            showToast('No issues detected', 'success');
        }
        setTimeout(loadDashboard, 2000);
    } catch (e) {
        showToast('Manual check failed: ' + e.message, 'error');
    }
}

// ── Skills ──────────────────────────────────────────────────────────

async function loadSkills() {
    try {
        const filter = document.getElementById('skill-filter').value;
        const url = filter ? `/skills?category=${filter}` : '/skills';
        const data = await apiGet(url);
        const container = document.getElementById('skills-list');

        if (!data.skills || data.skills.length === 0) {
            container.innerHTML = '<p class="text-muted">No skills registered</p>';
            return;
        }

        container.innerHTML = data.skills.map(s => `
            <div class="skill-item" onclick="selectSkill('${s.name}')">
                <div class="skill-name">${s.name}</div>
                <div class="skill-desc">${escHtml(s.description)}</div>
                <div class="skill-meta">
                    <span class="badge badge-info">${s.category}</span>
                    <span class="badge badge-${s.risk_level === 'safe' ? 'success' : s.risk_level === 'moderate' ? 'warning' : 'critical'}">${s.risk_level}</span>
                    ${s.parameters.length ? `<span style="color:var(--text-muted);font-size:11px;">params: ${s.parameters.join(', ')}</span>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        showToast('Failed to load skills', 'error');
    }
}

function selectSkill(name) {
    document.getElementById('exec-skill-name').value = name;
}

async function executeSkill() {
    const name = document.getElementById('exec-skill-name').value.trim();
    if (!name) { showToast('Enter skill name', 'error'); return; }

    let params = {};
    const paramsStr = document.getElementById('exec-skill-params').value.trim();
    if (paramsStr) {
        try { params = JSON.parse(paramsStr); }
        catch (e) { showToast('Invalid JSON params', 'error'); return; }
    }

    try {
        showToast('Executing skill...', 'info');
        const result = await apiPost('/skills/execute', { skill_name: name, params });
        const el = document.getElementById('exec-result');
        el.style.display = 'block';
        el.textContent = `Success: ${result.success}\n\n${result.output || result.error}`;
    } catch (e) {
        showToast('Execution failed: ' + e.message, 'error');
    }
}

async function registerSkill() {
    const name = document.getElementById('new-skill-name').value.trim();
    const desc = document.getElementById('new-skill-desc').value.trim();
    const cat = document.getElementById('new-skill-category').value;
    const cmd = document.getElementById('new-skill-cmd').value.trim();
    const paramsStr = document.getElementById('new-skill-params').value.trim();
    const risk = document.getElementById('new-skill-risk').value;

    if (!name || !desc) { showToast('Name and description required', 'error'); return; }

    try {
        await apiPost('/skills/register', {
            name,
            description: desc,
            category: cat,
            command_template: cmd,
            parameters: paramsStr ? paramsStr.split(',').map(p => p.trim()) : [],
            risk_level: risk,
        });
        showToast(`Skill '${name}' registered`, 'success');
        loadSkills();
    } catch (e) {
        showToast('Registration failed: ' + e.message, 'error');
    }
}

// ── Knowledge Base ──────────────────────────────────────────────────

async function queryKnowledge() {
    const query = document.getElementById('kb-query').value.trim();
    if (!query) { showToast('Enter a query', 'error'); return; }

    try {
        showToast('Searching knowledge base...', 'info');
        const data = await apiPost('/knowledge/query', { query });
        const container = document.getElementById('kb-results');

        if (!data.results || data.results.length === 0) {
            container.innerHTML = '<p class="text-muted">No results found</p>';
            return;
        }

        container.innerHTML = data.results.map(r => `
            <div class="kb-result-item">
                <div class="kb-result-score">Score: ${(r.score || 0).toFixed(4)}</div>
                <div class="kb-result-text">${escHtml(r.text || '')}</div>
            </div>
        `).join('');
    } catch (e) {
        showToast('Query failed: ' + e.message, 'error');
    }
}

async function addKnowledge() {
    const docId = document.getElementById('kb-doc-id').value.trim();
    const text = document.getElementById('kb-doc-text').value.trim();
    if (!docId || !text) { showToast('Document ID and content required', 'error'); return; }

    try {
        await apiPost('/knowledge/add', { doc_id: docId, text });
        showToast('Document added to knowledge base', 'success');
        document.getElementById('kb-doc-id').value = '';
        document.getElementById('kb-doc-text').value = '';
    } catch (e) {
        showToast('Failed to add document: ' + e.message, 'error');
    }
}

// ── Collectors ──────────────────────────────────────────────────────

async function collectSnapshot(type) {
    try {
        showToast(`Collecting ${type} snapshot...`, 'info');
        const data = await apiGet(`/collect/${type}`);
        document.getElementById('collect-result-card').style.display = 'block';
        document.getElementById('collect-result-title').textContent = `${type.toUpperCase()} Snapshot`;
        document.getElementById('collect-result').textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        showToast('Collection failed: ' + e.message, 'error');
    }
}

// ── Alarms ──────────────────────────────────────────────────────────

async function loadAlarms() {
    try {
        const data = await apiGet('/alarms');
        const tbody = document.querySelector('#alarms-table tbody');
        const noMsg = document.getElementById('no-alarms');

        if (!data.alarms || data.alarms.length === 0) {
            tbody.innerHTML = '';
            noMsg.style.display = 'block';
            return;
        }

        noMsg.style.display = 'none';
        tbody.innerHTML = data.alarms.map(a => `
            <tr>
                <td><code>${a.issue_id}</code></td>
                <td><span class="badge badge-${severityClass(a.severity)}">${a.severity}</span></td>
                <td>${escHtml(a.summary)}</td>
                <td>${escHtml(a.hypothesis || 'N/A')}</td>
                <td>${((a.confidence || 0) * 100).toFixed(0)}%</td>
                <td>${escHtml(a.reason)}</td>
            </tr>
        `).join('');
    } catch (e) {
        showToast('Failed to load alarms', 'error');
    }
}

// ── Utilities ───────────────────────────────────────────────────────

function escHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function severityClass(severity) {
    switch (severity) {
        case 'critical': return 'critical';
        case 'warning': return 'warning';
        case 'info': return 'info';
        default: return 'info';
    }
}

function statusClass(status) {
    switch (status) {
        case 'resolved': return 'success';
        case 'in_progress': return 'info';
        case 'escalated': return 'critical';
        case 'failed': return 'critical';
        case 'pending': return 'pending';
        default: return 'pending';
    }
}

function formatTime(isoStr) {
    if (!isoStr) return '--';
    try {
        const d = new Date(isoStr);
        return d.toLocaleString();
    } catch (e) {
        return isoStr;
    }
}

function refreshAll() {
    loadDashboard();
    showToast('Refreshed', 'success');
}

// ── Auto-refresh ────────────────────────────────────────────────────

setInterval(loadDashboard, 30000);

// ── Initial Load ────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});
