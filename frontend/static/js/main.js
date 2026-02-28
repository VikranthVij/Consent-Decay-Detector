// ==========================================
// State
// ==========================================

let companiesData = [];
let chunkChartInstance = null;
let cdiChartInstance = null;

// ==========================================
// Navigation
// ==========================================

function navigateTo(section) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.section === section);
    });

    // Update sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
    });
    document.getElementById('section-' + section).classList.add('active');

    // Update title
    const titles = {
        dashboard: 'Dashboard',
        analysis: 'Drift Analysis',
        timeline: 'Timeline',
        scanner: 'Policy Scanner',
    };
    document.getElementById('pageTitle').textContent = titles[section] || 'Dashboard';

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('open');
}

// ==========================================
// API Helpers
// ==========================================

async function api(endpoint, options = {}) {
    try {
        const res = await fetch(endpoint, options);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `HTTP ${res.status}`);
        }
        return await res.json();
    } catch (e) {
        console.error('API Error:', e);
        throw e;
    }
}

// ==========================================
// Dashboard
// ==========================================

async function loadDashboard() {
    try {
        companiesData = await api('/api/companies');
        renderCompanyGrid(companiesData);
        populateSelects(companiesData);
    } catch (e) {
        document.getElementById('companyGrid').innerHTML =
            '<div class="empty-state"><p>Failed to load companies. Is the database initialized?</p></div>';
    }
}

function renderCompanyGrid(companies) {
    const grid = document.getElementById('companyGrid');

    if (companies.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" opacity="0.3">
                    <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                    <rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/>
                </svg>
                <p>No companies tracked yet. Run the crawler first.</p>
            </div>
        `;
        return;
    }

    const colors = [
        'linear-gradient(135deg, #3b82f6, #06b6d4)',
        'linear-gradient(135deg, #8b5cf6, #ec4899)',
        'linear-gradient(135deg, #f59e0b, #ef4444)',
        'linear-gradient(135deg, #22c55e, #06b6d4)',
        'linear-gradient(135deg, #6366f1, #8b5cf6)',
    ];

    grid.innerHTML = companies.map((c, i) => `
        <div class="company-card" onclick="goToAnalysis('${escapeHtml(c.name)}')">
            <div class="company-card-header">
                <div class="company-avatar" style="background: ${colors[i % colors.length]}">
                    ${c.name.charAt(0).toUpperCase()}
                </div>
                <div>
                    <div class="company-name">${escapeHtml(c.name)}</div>
                    <div class="company-url">${escapeHtml(c.url)}</div>
                </div>
            </div>
            <div class="company-stats">
                <div class="company-stat">
                    <div class="company-stat-value">${c.version_count}</div>
                    <div class="company-stat-label">Versions</div>
                </div>
                <div class="company-stat">
                    <div class="company-stat-value">${c.first_seen ? formatDate(c.first_seen) : '—'}</div>
                    <div class="company-stat-label">First Seen</div>
                </div>
                <div class="company-stat">
                    <div class="company-stat-value">${c.last_seen ? formatDate(c.last_seen) : '—'}</div>
                    <div class="company-stat-label">Last Seen</div>
                </div>
            </div>
        </div>
    `).join('');
}

function goToAnalysis(name) {
    navigateTo('analysis');
    document.getElementById('analysisCompanySelect').value = name;
    onAnalysisCompanyChange();
}

function populateSelects(companies) {
    const options = companies.map(c =>
        `<option value="${escapeHtml(c.name)}">${escapeHtml(c.name)}</option>`
    ).join('');

    const defaultOpt = '<option value="">Select a company...</option>';

    document.getElementById('analysisCompanySelect').innerHTML = defaultOpt + options;
    document.getElementById('timelineCompanySelect').innerHTML = defaultOpt + options;
}

// ==========================================
// Analysis
// ==========================================

function onAnalysisCompanyChange() {
    const val = document.getElementById('analysisCompanySelect').value;
    document.getElementById('runDriftBtn').disabled = !val;
    document.getElementById('runQuickBtn').disabled = !val;
    document.getElementById('quickStatsResults').classList.add('hidden');
    document.getElementById('driftResults').classList.add('hidden');
}

async function runQuickStats() {
    const name = document.getElementById('analysisCompanySelect').value;
    if (!name) return;

    showAnalysisLoading('Computing structural analysis...');

    try {
        const data = await api(`/api/company/${encodeURIComponent(name)}/quick-stats`);
        hideAnalysisLoading();
        renderQuickStats(data);
    } catch (e) {
        hideAnalysisLoading();
        alert('Analysis failed: ' + e.message);
    }
}

function renderQuickStats(data) {
    document.getElementById('driftResults').classList.add('hidden');
    document.getElementById('quickStatsResults').classList.remove('hidden');

    // Stats cards
    const driftColor = data.structural_drift > 30 ? 'red' : data.structural_drift > 15 ? 'yellow' : 'green';
    document.getElementById('statsGrid').innerHTML = `
        <div class="stat-card blue">
            <div class="stat-label">Old Clauses</div>
            <div class="stat-value blue">${data.total_old_chunks}</div>
            <div class="stat-sub">${data.old_version_date || 'Baseline'}</div>
        </div>
        <div class="stat-card cyan">
            <div class="stat-label">New Clauses</div>
            <div class="stat-value cyan">${data.total_new_chunks}</div>
            <div class="stat-sub">${data.new_version_date || 'Latest'}</div>
        </div>
        <div class="stat-card ${driftColor}">
            <div class="stat-label">Structural Drift</div>
            <div class="stat-value ${driftColor}">${data.structural_drift}%</div>
            <div class="stat-sub">Weighted change score</div>
        </div>
        <div class="stat-card purple">
            <div class="stat-label">New Clauses Added</div>
            <div class="stat-value purple">${data.added}</div>
            <div class="stat-sub">${data.removed} removed, ${data.modified} modified</div>
        </div>
    `;

    // Chunk breakdown chart
    renderChunkChart(data);

    // Expansion signals
    renderExpansionSignals(data.expansion_signals_summary);

    // New clauses list
    document.getElementById('newClauseCount').textContent = data.new_clauses.length;
    const clauseList = document.getElementById('newClausesList');

    if (data.new_clauses.length === 0) {
        clauseList.innerHTML = '<div class="empty-state"><p>No new clauses detected</p></div>';
    } else {
        clauseList.innerHTML = data.new_clauses.map(clause => `
            <div class="clause-item">
                <div class="clause-text">${escapeHtml(clause.text)}</div>
                <div class="clause-tags">
                    ${clause.expansion_signals.map(s =>
                        `<span class="clause-tag">${formatSignalName(s)}</span>`
                    ).join('')}
                </div>
            </div>
        `).join('');
    }
}

function renderChunkChart(data) {
    const ctx = document.getElementById('chunkChart').getContext('2d');

    if (chunkChartInstance) chunkChartInstance.destroy();

    chunkChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Unchanged', 'Modified', 'Removed', 'Added'],
            datasets: [{
                data: [data.unchanged, data.modified, data.removed, data.added],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(139, 92, 246, 0.8)',
                ],
                borderColor: '#1a2234',
                borderWidth: 3,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#8899b4',
                        padding: 20,
                        font: { family: 'Inter', size: 12 },
                    },
                },
            },
        },
    });
}

function renderExpansionSignals(signals) {
    const container = document.getElementById('expansionSignalsList');

    const entries = Object.entries(signals);
    if (entries.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No expansion signals detected</p></div>';
        return;
    }

    const maxCount = Math.max(...entries.map(([, v]) => v));

    container.innerHTML = entries.map(([name, count]) => `
        <div class="signal-bar-container">
            <div class="signal-bar-label">
                <span class="signal-bar-name">${formatSignalName(name)}</span>
                <span class="signal-bar-count">${count}</span>
            </div>
            <div class="signal-bar-track">
                <div class="signal-bar-fill" style="width: ${(count / maxCount) * 100}%"></div>
            </div>
        </div>
    `).join('');
}

// ==========================================
// Full Drift Analysis
// ==========================================

async function runDriftAnalysis() {
    const name = document.getElementById('analysisCompanySelect').value;
    if (!name) return;

    showAnalysisLoading('Running full drift analysis with LLM (this may take a few minutes)...');

    try {
        const data = await api(`/api/company/${encodeURIComponent(name)}/drift`);
        hideAnalysisLoading();
        renderDriftResults(data);
    } catch (e) {
        hideAnalysisLoading();
        alert('Full analysis failed: ' + e.message);
    }
}

function renderDriftResults(data) {
    document.getElementById('quickStatsResults').classList.add('hidden');
    document.getElementById('driftResults').classList.remove('hidden');

    const baseline = data.baseline || {};
    const incremental = data.incremental || {};

    // Stats grid
    const bRisk = baseline.risk_level || 'N/A';
    const bColor = riskColor(bRisk);
    const iRisk = incremental.risk_level || 'N/A';
    const iColor = riskColor(iRisk);

    document.getElementById('driftStatsGrid').innerHTML = `
        <div class="stat-card ${bColor}">
            <div class="stat-label">Baseline Risk</div>
            <div class="stat-value ${bColor}">${bRisk}</div>
            <div class="stat-sub">Score: ${baseline.semantic_score || 0}/10</div>
        </div>
        <div class="stat-card ${iColor}">
            <div class="stat-label">Incremental Risk</div>
            <div class="stat-value ${iColor}">${iRisk}</div>
            <div class="stat-sub">Score: ${incremental.semantic_score || 0}/10</div>
        </div>
        <div class="stat-card blue">
            <div class="stat-label">Baseline Drift</div>
            <div class="stat-value blue">${baseline.structural_drift || 0}%</div>
            <div class="stat-sub">Structural change</div>
        </div>
        <div class="stat-card purple">
            <div class="stat-label">New Clauses (Baseline)</div>
            <div class="stat-value purple">${baseline.total_new_clauses || 0}</div>
            <div class="stat-sub">${incremental.total_new_clauses || 0} incremental</div>
        </div>
    `;

    // Badges
    document.getElementById('baselineRiskBadge').className = `badge badge-${bColor}`;
    document.getElementById('baselineRiskBadge').textContent = bRisk;
    document.getElementById('incrementalRiskBadge').className = `badge badge-${iColor}`;
    document.getElementById('incrementalRiskBadge').textContent = iRisk;

    // Baseline details
    renderAnalysisPanel('baselineResults', baseline);
    renderAnalysisPanel('incrementalResults', incremental);

    // Flagged clauses
    const allClauses = [
        ...(baseline.all_new_clauses || []),
        ...(incremental.all_new_clauses || []),
    ];

    const flaggedList = document.getElementById('flaggedClausesList');
    if (allClauses.length === 0) {
        flaggedList.innerHTML = '<div class="empty-state"><p>No flagged clauses</p></div>';
    } else {
        flaggedList.innerHTML = allClauses.map(clause => `
            <div class="clause-item">
                <div class="clause-text">${escapeHtml(clause.reason || 'No reason provided')}</div>
                <div class="clause-tags">
                    <span class="clause-tag risk">Risk: ${clause.risk_score}/10</span>
                    ${clause.expansion ? '<span class="clause-tag risk">Expansion</span>' : ''}
                    ${(clause.categories || []).map(c =>
                        `<span class="clause-tag">${formatSignalName(c)}</span>`
                    ).join('')}
                </div>
            </div>
        `).join('');
    }
}

function renderAnalysisPanel(elementId, report) {
    const el = document.getElementById(elementId);

    if (!report || Object.keys(report).length === 0) {
        el.innerHTML = '<p style="color: var(--text-muted)">No data available</p>';
        return;
    }

    el.innerHTML = `
        <div class="drift-metric-row">
            <span class="drift-metric-name">Structural Drift</span>
            <span class="drift-metric-value" style="color: var(--accent-blue)">${report.structural_drift || 0}%</span>
        </div>
        <div class="drift-metric-row">
            <span class="drift-metric-name">Semantic Score</span>
            <span class="drift-metric-value" style="color: ${scoreColor(report.semantic_score)}">${report.semantic_score || 0}/10</span>
        </div>
        <div class="drift-metric-row">
            <span class="drift-metric-name">Risk Level</span>
            <span class="drift-metric-value">${report.risk_level || 'N/A'}</span>
        </div>
        <div class="drift-metric-row">
            <span class="drift-metric-name">New Clauses</span>
            <span class="drift-metric-value">${report.total_new_clauses || 0}</span>
        </div>
    `;
}

// ==========================================
// Timeline
// ==========================================

function onTimelineCompanyChange() {
    const val = document.getElementById('timelineCompanySelect').value;
    document.getElementById('runTimelineBtn').disabled = !val;
    document.getElementById('timelineResults').classList.add('hidden');
}

async function runTimelineAnalysis() {
    const name = document.getElementById('timelineCompanySelect').value;
    if (!name) return;

    document.getElementById('timelineResults').classList.add('hidden');
    document.getElementById('timelineLoading').classList.remove('hidden');

    try {
        const data = await api(`/api/company/${encodeURIComponent(name)}/timeline`);
        document.getElementById('timelineLoading').classList.add('hidden');
        renderTimeline(data.timeline);
    } catch (e) {
        document.getElementById('timelineLoading').classList.add('hidden');
        alert('Timeline analysis failed: ' + e.message);
    }
}

function renderTimeline(timeline) {
    if (!timeline || timeline.length === 0) {
        document.getElementById('timelineResults').classList.remove('hidden');
        document.getElementById('transitionsList').innerHTML =
            '<div class="empty-state"><p>No timeline data available</p></div>';
        return;
    }

    document.getElementById('timelineResults').classList.remove('hidden');

    // CDI Chart
    renderCDIChart(timeline);

    // Transitions list
    const list = document.getElementById('transitionsList');
    list.innerHTML = timeline.map((t, i) => `
        <div class="transition-item">
            <div class="transition-dates">
                <strong>Transition ${i + 1}</strong>
                ${formatDateTime(t.from)} → ${formatDateTime(t.to)}
            </div>
            <div>
                <div class="transition-metrics">
                    <div class="transition-metric">
                        <div class="transition-metric-value" style="color: var(--accent-blue)">${t.structural_drift}%</div>
                        <div class="transition-metric-label">Structural Drift</div>
                    </div>
                    <div class="transition-metric">
                        <div class="transition-metric-value" style="color: ${scoreColor(t.semantic_score)}">${t.semantic_score}/10</div>
                        <div class="transition-metric-label">Semantic Risk</div>
                    </div>
                    <div class="transition-metric">
                        <div class="transition-metric-value" style="color: var(--accent-purple)">${t.escalation_intensity}</div>
                        <div class="transition-metric-label">Escalation</div>
                    </div>
                    <div class="transition-metric">
                        <div class="transition-metric-value" style="color: ${cdiColor(t.cdi)}">${t.cdi}/100</div>
                        <div class="transition-metric-label">CDI</div>
                    </div>
                </div>
                ${t.irreversible ? '<div class="irreversible-tag">⚠ Irreversible Expansion Detected</div>' : ''}
            </div>
        </div>
    `).join('');
}

function renderCDIChart(timeline) {
    const ctx = document.getElementById('cdiChart').getContext('2d');

    if (cdiChartInstance) cdiChartInstance.destroy();

    const labels = timeline.map((t, i) => `V${i + 1} → V${i + 2}`);
    const cdiData = timeline.map(t => t.cdi);
    const driftData = timeline.map(t => t.structural_drift);
    const semanticData = timeline.map(t => t.semantic_score * 10); // Scale to 0-100

    cdiChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'CDI (0-100)',
                    data: cdiData,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    borderWidth: 2,
                },
                {
                    label: 'Structural Drift (%)',
                    data: driftData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.3,
                    pointRadius: 4,
                    borderWidth: 2,
                },
                {
                    label: 'Semantic Risk (×10)',
                    data: semanticData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'transparent',
                    borderDash: [2, 3],
                    tension: 0.3,
                    pointRadius: 4,
                    borderWidth: 2,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index',
            },
            scales: {
                x: {
                    ticks: { color: '#5a6a85', font: { family: 'Inter', size: 11 } },
                    grid: { color: 'rgba(30, 45, 74, 0.5)' },
                },
                y: {
                    min: 0,
                    max: 100,
                    ticks: { color: '#5a6a85', font: { family: 'Inter', size: 11 } },
                    grid: { color: 'rgba(30, 45, 74, 0.5)' },
                },
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#8899b4',
                        padding: 20,
                        font: { family: 'Inter', size: 12 },
                    },
                },
                tooltip: {
                    backgroundColor: '#1a2234',
                    titleColor: '#e8edf5',
                    bodyColor: '#8899b4',
                    borderColor: '#1e2d4a',
                    borderWidth: 1,
                    padding: 12,
                    titleFont: { family: 'Inter', weight: '600' },
                    bodyFont: { family: 'Inter' },
                },
            },
        },
    });
}

// ==========================================
// Policy Scanner
// ==========================================

async function runScanner() {
    const text = document.getElementById('scannerInput').value;
    if (!text.trim()) return;

    const resultsDiv = document.getElementById('scannerResults');
    resultsDiv.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Scanning...</p></div>';

    try {
        const data = await api('/api/analyze-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });

        renderScannerResults(data, resultsDiv);
    } catch (e) {
        resultsDiv.innerHTML = `<div class="empty-state"><p>Scan failed: ${escapeHtml(e.message)}</p></div>`;
    }
}

function renderScannerResults(data, container) {
    if (data.flagged_chunks === 0) {
        container.innerHTML = `
            <div class="empty-state" style="padding: 30px">
                <div style="font-size: 2rem; margin-bottom: 8px">✓</div>
                <p style="color: var(--risk-low); font-weight: 600">No expansion signals detected</p>
                <p style="color: var(--text-muted); font-size: 0.82rem; margin-top: 4px">${data.total_chunks} clauses scanned</p>
            </div>
        `;
        return;
    }

    let html = `
        <div style="padding: 16px; border-bottom: 1px solid var(--border-color); display: flex; gap: 20px;">
            <div>
                <span style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">Scanned</span>
                <div style="font-size: 1.2rem; font-weight: 700; color: var(--accent-blue)">${data.total_chunks}</div>
            </div>
            <div>
                <span style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">Flagged</span>
                <div style="font-size: 1.2rem; font-weight: 700; color: var(--risk-high)">${data.flagged_chunks}</div>
            </div>
        </div>
    `;

    // Signal summary
    const signals = Object.entries(data.signal_summary || {});
    if (signals.length > 0) {
        html += '<div style="padding: 16px; border-bottom: 1px solid var(--border-color)">';
        const maxCount = Math.max(...signals.map(([, v]) => v));
        html += signals.map(([name, count]) => `
            <div class="signal-bar-container">
                <div class="signal-bar-label">
                    <span class="signal-bar-name">${formatSignalName(name)}</span>
                    <span class="signal-bar-count">${count}</span>
                </div>
                <div class="signal-bar-track">
                    <div class="signal-bar-fill" style="width: ${(count / maxCount) * 100}%"></div>
                </div>
            </div>
        `).join('');
        html += '</div>';
    }

    // Flagged clauses
    html += '<div class="clause-list">';
    html += (data.flagged_clauses || []).map(clause => `
        <div class="clause-item">
            <div class="clause-text">${escapeHtml(clause.text)}</div>
            <div class="clause-tags">
                ${clause.expansion_signals.map(s =>
                    `<span class="clause-tag">${formatSignalName(s)}</span>`
                ).join('')}
            </div>
        </div>
    `).join('');
    html += '</div>';

    container.innerHTML = html;
}

// ==========================================
// Helpers
// ==========================================

function showAnalysisLoading(text) {
    document.getElementById('quickStatsResults').classList.add('hidden');
    document.getElementById('driftResults').classList.add('hidden');
    document.getElementById('analysisLoadingText').textContent = text;
    document.getElementById('analysisLoading').classList.remove('hidden');
}

function hideAnalysisLoading() {
    document.getElementById('analysisLoading').classList.add('hidden');
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
        return dateStr.slice(0, 10);
    }
}

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

function formatSignalName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function riskColor(level) {
    if (!level) return 'blue';
    const l = level.toUpperCase();
    if (l === 'HIGH') return 'red';
    if (l === 'MEDIUM' || l === 'MODERATE') return 'yellow';
    return 'green';
}

function scoreColor(score) {
    if (score >= 7) return '#ef4444';
    if (score >= 4) return '#f59e0b';
    return '#22c55e';
}

function cdiColor(cdi) {
    if (cdi >= 60) return '#ef4444';
    if (cdi >= 30) return '#f59e0b';
    return '#22c55e';
}

// ==========================================
// Init
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});
