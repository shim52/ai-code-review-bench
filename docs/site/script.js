// ===== Global State =====
let benchmarkData = null;
let currentSortMetric = 'f1_score';

// ===== Initialize App =====
document.addEventListener('DOMContentLoaded', async () => {
    // Load theme
    initTheme();

    // Load benchmark data
    await loadBenchmarkData();

    // Initialize UI
    initTabs();
    initMetricSelector();
    initModal();

    // Animate hero stats
    animateHeroStats();

    // Render initial content
    renderLeaderboard();
    renderChallenges();
    renderTools();
    renderMatrix();

    // Update timestamp
    updateTimestamp();
});

// ===== Theme Management =====
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);

    const themeToggle = document.querySelector('.theme-toggle');
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });
}

// ===== Animate Hero Stats =====
function animateHeroStats() {
    const stats = [
        { selector: '.hero-stats .stat:nth-child(1) .stat-value', target: 3, duration: 800 },
        { selector: '.hero-stats .stat:nth-child(2) .stat-value', target: 5, duration: 1000 },
        { selector: '.hero-stats .stat:nth-child(3) .stat-value', target: 45, duration: 1200 },
        { selector: '.hero-stats .stat:nth-child(4) .stat-value', target: 12, duration: 1400 }
    ];

    stats.forEach(stat => {
        const element = document.querySelector(stat.selector);
        if (!element) return;

        let current = 0;
        const increment = stat.target / (stat.duration / 16); // 60fps
        const timer = setInterval(() => {
            current += increment;
            if (current >= stat.target) {
                current = stat.target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
    });
}

// ===== Data Loading =====
async function loadBenchmarkData() {
    try {
        const response = await fetch('data/benchmark-results.json');
        benchmarkData = await response.json();
    } catch (error) {
        console.error('Failed to load benchmark data:', error);
        showError('Failed to load benchmark data. Please try refreshing the page.');
    }
}

// ===== Tab Management =====
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            // Update active states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
        });
    });
}

// ===== Metric Selector =====
function initMetricSelector() {
    const metricSelect = document.getElementById('metric-select');
    metricSelect.addEventListener('change', (e) => {
        currentSortMetric = e.target.value;
        renderLeaderboard();
    });
}

// ===== Leaderboard Rendering =====
function renderLeaderboard() {
    const container = document.getElementById('leaderboard-content');

    // Sort tools by selected metric
    const sortedTools = [...benchmarkData.overall_scores].sort((a, b) => {
        switch (currentSortMetric) {
            case 'f1_score':
                return b.metrics.avg_f1_score - a.metrics.avg_f1_score;
            case 'precision':
                return b.metrics.avg_precision - a.metrics.avg_precision;
            case 'recall':
                return b.metrics.avg_recall - a.metrics.avg_recall;
            case 'speed':
                return a.metrics.avg_response_time_ms - b.metrics.avg_response_time_ms;
            default:
                return 0;
        }
    });

    container.innerHTML = sortedTools.map((tool, index) => {
        const toolInfo = benchmarkData.tools.find(t => t.name === tool.tool);
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';

        return `
            <div class="leaderboard-item">
                <div class="rank ${rankClass}">#${index + 1}</div>
                <div class="tool-info">
                    <div class="tool-name">${tool.tool}</div>
                    <div class="tool-meta">
                        <span>⭐ ${toolInfo.stars.toLocaleString()} stars</span>
                        <span>📜 ${toolInfo.license}</span>
                        <span>⚡ ${Math.round(tool.metrics.avg_response_time_ms)}ms avg</span>
                    </div>
                </div>
                <div class="metrics-grid">
                    <div class="metric">
                        <span class="metric-value ${getScoreClass(tool.metrics.avg_f1_score)}">
                            ${(tool.metrics.avg_f1_score * 100).toFixed(1)}%
                        </span>
                        <span class="metric-label">F1 Score</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value ${getScoreClass(tool.metrics.avg_precision)}">
                            ${(tool.metrics.avg_precision * 100).toFixed(1)}%
                        </span>
                        <span class="metric-label">Precision</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value ${getScoreClass(tool.metrics.avg_recall)}">
                            ${(tool.metrics.avg_recall * 100).toFixed(1)}%
                        </span>
                        <span class="metric-label">Recall</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value">
                            ${tool.metrics.total_true_positives}/${tool.metrics.total_true_positives + tool.metrics.total_false_negatives}
                        </span>
                        <span class="metric-label">Issues Found</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ===== Challenges Rendering =====
function renderChallenges() {
    const container = document.getElementById('challenges-grid');

    container.innerHTML = benchmarkData.challenges.map(challenge => {
        // Calculate average performance across all tools
        const challengeResults = benchmarkData.results.filter(r => r.challenge === challenge.id);
        const avgF1 = challengeResults.reduce((sum, r) => sum + r.metrics.f1_score, 0) / challengeResults.length;
        const bestTool = challengeResults.reduce((best, r) =>
            r.metrics.f1_score > best.metrics.f1_score ? r : best
        );

        return `
            <div class="challenge-card" onclick="showChallengeDetails('${challenge.id}')">
                <div class="challenge-header">
                    <div class="challenge-title">${challenge.name}</div>
                    <span class="challenge-badge badge-${challenge.category.toLowerCase()}">${challenge.category}</span>
                </div>
                <div class="challenge-description">${challenge.description}</div>
                <div class="challenge-stats">
                    <div class="challenge-stat">
                        <span class="challenge-stat-value">${challenge.ground_truth_issues}</span>
                        <span class="challenge-stat-label">Issues</span>
                    </div>
                    <div class="challenge-stat">
                        <span class="challenge-stat-value ${getScoreClass(avgF1)}">${(avgF1 * 100).toFixed(0)}%</span>
                        <span class="challenge-stat-label">Avg F1</span>
                    </div>
                    <div class="challenge-stat">
                        <span class="challenge-stat-value">${bestTool.tool.split(' ')[0]}</span>
                        <span class="challenge-stat-label">Best Tool</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ===== Tools Rendering =====
function renderTools() {
    const container = document.getElementById('tools-grid');

    container.innerHTML = benchmarkData.tools.map(tool => {
        const toolScore = benchmarkData.overall_scores.find(s => s.tool === tool.name);

        return `
            <div class="tool-card">
                <div class="tool-header">
                    <div class="tool-title">${tool.name}</div>
                    <div class="tool-stars">
                        <span>⭐</span>
                        <span>${tool.stars.toLocaleString()}</span>
                    </div>
                </div>
                <div class="tool-description">${tool.description}</div>
                <div class="tool-install">$ ${tool.install_cmd}</div>
                <div class="tool-performance">
                    <div class="performance-bars">
                        <div class="performance-bar">
                            <span class="bar-label">F1 Score</span>
                            <div class="bar-track">
                                <div class="bar-fill ${getScoreClass(toolScore.metrics.avg_f1_score)}"
                                     style="width: ${toolScore.metrics.avg_f1_score * 100}%; background: ${getScoreColor(toolScore.metrics.avg_f1_score)}"></div>
                            </div>
                            <span class="bar-value">${(toolScore.metrics.avg_f1_score * 100).toFixed(1)}%</span>
                        </div>
                        <div class="performance-bar">
                            <span class="bar-label">Precision</span>
                            <div class="bar-track">
                                <div class="bar-fill"
                                     style="width: ${toolScore.metrics.avg_precision * 100}%; background: ${getScoreColor(toolScore.metrics.avg_precision)}"></div>
                            </div>
                            <span class="bar-value">${(toolScore.metrics.avg_precision * 100).toFixed(1)}%</span>
                        </div>
                        <div class="performance-bar">
                            <span class="bar-label">Recall</span>
                            <div class="bar-track">
                                <div class="bar-fill"
                                     style="width: ${toolScore.metrics.avg_recall * 100}%; background: ${getScoreColor(toolScore.metrics.avg_recall)}"></div>
                            </div>
                            <span class="bar-value">${(toolScore.metrics.avg_recall * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                    <a href="${tool.github_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 0.5rem;">
                        View on GitHub
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                    </a>
                </div>
            </div>
        `;
    }).join('');
}

// ===== Matrix View Rendering =====
function renderMatrix() {
    const container = document.getElementById('matrix-table');

    // Build matrix data
    const matrix = {};
    benchmarkData.results.forEach(result => {
        if (!matrix[result.tool]) matrix[result.tool] = {};
        matrix[result.tool][result.challenge] = result.metrics;
    });

    // Generate table
    let html = '<table><thead><tr><th>Tool / Challenge</th>';

    // Add challenge headers
    benchmarkData.challenges.forEach(challenge => {
        html += `<th>${challenge.name.split(' ').slice(0, 2).join(' ')}</th>`;
    });
    html += '</tr></thead><tbody>';

    // Add tool rows
    Object.keys(matrix).forEach(tool => {
        html += `<tr><th>${tool}</th>`;
        benchmarkData.challenges.forEach(challenge => {
            const metrics = matrix[tool][challenge.id];
            if (metrics) {
                const scoreClass = getScoreClass(metrics.f1_score);
                html += `
                    <td onclick="showResultDetails('${tool}', '${challenge.id}')"
                        style="background: ${getScoreBackground(metrics.f1_score)}">
                        <div class="matrix-cell">
                            <span class="matrix-score ${scoreClass}">${(metrics.f1_score * 100).toFixed(0)}%</span>
                            <span class="matrix-detail">${metrics.true_positives}/${challenge.ground_truth_issues} found</span>
                        </div>
                    </td>
                `;
            } else {
                html += '<td>-</td>';
            }
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    container.innerHTML = html;
}

// ===== Modal Management =====
function initModal() {
    const modal = document.getElementById('details-modal');
    const closeBtn = document.querySelector('.modal-close');

    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}

function showChallengeDetails(challengeId) {
    const challenge = benchmarkData.challenges.find(c => c.id === challengeId);
    const results = benchmarkData.results.filter(r => r.challenge === challengeId);

    let html = `
        <h2>${challenge.name}</h2>
        <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">${challenge.description}</p>
        <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
            <span class="challenge-badge badge-${challenge.category.toLowerCase()}">${challenge.category}</span>
            <span style="color: var(--text-secondary);">Difficulty: ${challenge.difficulty}</span>
            <span style="color: var(--text-secondary);">Ground Truth Issues: ${challenge.ground_truth_issues}</span>
        </div>
        <h3 style="margin-bottom: 1rem;">Tool Performance</h3>
    `;

    results.forEach(result => {
        html += `
            <div style="background: var(--bg-secondary); border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <h4>${result.tool}</h4>
                    <span class="${getScoreClass(result.metrics.f1_score)}" style="font-size: 1.25rem; font-weight: 600;">
                        ${(result.metrics.f1_score * 100).toFixed(1)}%
                    </span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; font-size: 0.875rem;">
                    <div>
                        <span style="color: var(--text-secondary);">Precision:</span>
                        <span style="font-weight: 600; margin-left: 0.5rem;">${(result.metrics.precision * 100).toFixed(1)}%</span>
                    </div>
                    <div>
                        <span style="color: var(--text-secondary);">Recall:</span>
                        <span style="font-weight: 600; margin-left: 0.5rem;">${(result.metrics.recall * 100).toFixed(1)}%</span>
                    </div>
                    <div>
                        <span style="color: var(--text-secondary);">Response:</span>
                        <span style="font-weight: 600; margin-left: 0.5rem;">${result.metrics.avg_response_time_ms}ms</span>
                    </div>
                    <div>
                        <span style="color: var(--text-secondary);">True Positives:</span>
                        <span style="font-weight: 600; margin-left: 0.5rem;">${result.metrics.true_positives}</span>
                    </div>
                    <div>
                        <span style="color: var(--text-secondary);">False Positives:</span>
                        <span style="font-weight: 600; margin-left: 0.5rem;">${result.metrics.false_positives}</span>
                    </div>
                    <div>
                        <span style="color: var(--text-secondary);">False Negatives:</span>
                        <span style="font-weight: 600; margin-left: 0.5rem;">${result.metrics.false_negatives}</span>
                    </div>
                </div>
            </div>
        `;
    });

    showModal(html);
}

function showResultDetails(toolName, challengeId) {
    const result = benchmarkData.results.find(r => r.tool === toolName && r.challenge === challengeId);
    const challenge = benchmarkData.challenges.find(c => c.id === challengeId);
    const tool = benchmarkData.tools.find(t => t.name === toolName);

    let html = `
        <h2>${toolName} on ${challenge.name}</h2>
        <div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
            <span class="challenge-badge badge-${challenge.category.toLowerCase()}">${challenge.category}</span>
            <span style="color: var(--text-secondary);">Ground Truth Issues: ${challenge.ground_truth_issues}</span>
        </div>

        <div style="background: var(--bg-secondary); border-radius: 0.5rem; padding: 1rem; margin-bottom: 1.5rem;">
            <h3 style="margin-bottom: 1rem;">Overall Metrics</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                <div>
                    <span style="color: var(--text-secondary);">F1 Score:</span>
                    <span class="${getScoreClass(result.metrics.f1_score)}" style="font-size: 1.5rem; font-weight: 700; margin-left: 0.5rem;">
                        ${(result.metrics.f1_score * 100).toFixed(1)}%
                    </span>
                </div>
                <div>
                    <span style="color: var(--text-secondary);">Response Time:</span>
                    <span style="font-size: 1.5rem; font-weight: 700; margin-left: 0.5rem;">
                        ${result.metrics.avg_response_time_ms}ms
                    </span>
                </div>
                <div>
                    <span style="color: var(--text-secondary);">Precision:</span>
                    <span style="font-weight: 600; margin-left: 0.5rem;">${(result.metrics.precision * 100).toFixed(1)}%</span>
                </div>
                <div>
                    <span style="color: var(--text-secondary);">Recall:</span>
                    <span style="font-weight: 600; margin-left: 0.5rem;">${(result.metrics.recall * 100).toFixed(1)}%</span>
                </div>
            </div>
        </div>

        <div style="background: var(--bg-secondary); border-radius: 0.5rem; padding: 1rem; margin-bottom: 1.5rem;">
            <h3 style="margin-bottom: 1rem;">Detection Results</h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: 700; color: var(--color-success);">${result.metrics.true_positives}</div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">True Positives</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: 700; color: var(--color-warning);">${result.metrics.false_positives}</div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">False Positives</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: 700; color: var(--color-error);">${result.metrics.false_negatives}</div>
                    <div style="color: var(--text-secondary); font-size: 0.875rem;">False Negatives</div>
                </div>
            </div>
        </div>

        ${result.findings ? `
            <div style="background: var(--bg-secondary); border-radius: 0.5rem; padding: 1rem;">
                <h3 style="margin-bottom: 1rem;">Sample Findings</h3>
                ${result.findings.map(finding => `
                    <div style="padding: 0.75rem; background: var(--bg-tertiary); border-radius: 0.25rem; margin-bottom: 0.5rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <span style="font-weight: 600;">${finding.type}</span>
                            <span class="challenge-badge" style="background: ${getSeverityColor(finding.severity)}20; color: ${getSeverityColor(finding.severity)};">
                                ${finding.severity}
                            </span>
                        </div>
                        <div style="font-family: var(--font-mono); font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                            ${finding.file}:${finding.line}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">
                            ${finding.description}
                        </div>
                    </div>
                `).join('')}
            </div>
        ` : ''}

        <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border-color);">
            <h3 style="margin-bottom: 1rem;">Run Consistency</h3>
            <div style="display: flex; gap: 1rem;">
                ${result.metrics.runs.map((run, i) => `
                    <div style="flex: 1; text-align: center; padding: 0.75rem; background: var(--bg-secondary); border-radius: 0.25rem;">
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Run ${i + 1}</div>
                        <div style="font-weight: 600;">${(run.f1_score * 100).toFixed(1)}%</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

    showModal(html);
}

function showModal(content) {
    const modal = document.getElementById('details-modal');
    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = content;
    modal.classList.add('active');
}

// ===== Utility Functions =====
function getScoreClass(score) {
    if (score >= 0.9) return 'score-excellent';
    if (score >= 0.7) return 'score-good';
    if (score >= 0.5) return 'score-fair';
    return 'score-poor';
}

function getScoreColor(score) {
    if (score >= 0.9) return '#10b981';
    if (score >= 0.7) return '#3b82f6';
    if (score >= 0.5) return '#f59e0b';
    return '#ef4444';
}

function getScoreBackground(score) {
    const color = getScoreColor(score);
    return `${color}15`;
}

function getSeverityColor(severity) {
    switch (severity.toLowerCase()) {
        case 'critical': return '#ef4444';
        case 'high': return '#f59e0b';
        case 'medium': return '#3b82f6';
        case 'low': return '#10b981';
        default: return '#6b7280';
    }
}

function updateTimestamp() {
    const lastUpdated = document.getElementById('last-updated');
    if (benchmarkData && benchmarkData.metadata.timestamp) {
        const date = new Date(benchmarkData.metadata.timestamp);
        lastUpdated.textContent = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

function showError(message) {
    console.error(message);
    // Could implement a toast notification here
}