// ===== Global State =====
let benchmarkData = null;
let currentSortMetric = 'f2_score';
let trendChart = null;

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

    // Compute breakdown data client-side and render
    computeMetricsBreakdown();
    renderMetricsBreakdown();

    // Update timestamp
    updateTimestamp();

    // Render trends (hides section if no data)
    renderTrends();
});

// ===== Theme Management =====
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
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
    if (!benchmarkData) return;

    const toolCount = benchmarkData.tools.length;
    const stats = [
        { selector: '#tools-count', target: toolCount, duration: 800 },
        { selector: '#challenges-count', target: benchmarkData.metadata.challenges_count || benchmarkData.challenges?.length || 10, duration: 1000 },
        { selector: '#runs-count', target: (benchmarkData.metadata.total_runs || 1) * toolCount * (benchmarkData.metadata.challenges_count || 10), duration: 1200 },
        { selector: '#issues-count', target: benchmarkData.challenges?.reduce((sum, ch) => sum + (ch.ground_truth_issues || 0), 0) || 41, duration: 1400 }
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
        // Try fetch first (works on HTTP servers, GitHub Pages, etc.)
        const response = await fetch('data/benchmark-results.json');
        benchmarkData = await response.json();
    } catch (fetchError) {
        // Fallback for file:// protocol (CORS blocks fetch for local files)
        try {
            benchmarkData = await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.open('GET', 'data/benchmark-results.json', true);
                xhr.onload = () => {
                    if (xhr.status === 0 || xhr.status === 200) {
                        resolve(JSON.parse(xhr.responseText));
                    } else {
                        reject(new Error(`HTTP ${xhr.status}`));
                    }
                };
                xhr.onerror = () => reject(new Error('XHR failed'));
                xhr.send();
            });
        } catch (xhrError) {
            console.error('Failed to load benchmark data:', xhrError);
            showError('Failed to load data. If opening locally, run: python3 -m http.server 8000 --directory docs');
        }
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

// ===== SVG Icon Helpers =====
const ICONS = {
    star: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>',
    scroll: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21h12a2 2 0 0 0 2-2v-2H10v2a2 2 0 1 1-4 0V5a2 2 0 0 0-2-2H2"></path><path d="M19 3H6a2 2 0 0 0-2 2v14"></path></svg>',
    cpu: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>',
    externalLink: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>',
};

// ===== Tool Type Helpers =====
function getToolTypeBadge(toolInfo) {
    if (!toolInfo) return '';
    const toolType = toolInfo.tool_type || 'agent';
    if (toolType === 'pure_model') {
        return '<span class="tool-type-badge pure-model">Pure Model</span>';
    }
    return '<span class="tool-type-badge agent">Review Agent</span>';
}

// ===== Leaderboard Rendering =====
function renderLeaderboard() {
    const container = document.getElementById('leaderboard-content');

    // Build entries: scored tools sorted by metric, then unscored tools as "coming soon"
    const scoredTools = [...benchmarkData.overall_scores].sort((a, b) => {
        switch (currentSortMetric) {
            case 'f2_score':
                return computeF2(b.metrics.avg_precision, b.metrics.avg_recall) - computeF2(a.metrics.avg_precision, a.metrics.avg_recall);
            case 'f1_score':
                return b.metrics.avg_f1_score - a.metrics.avg_f1_score;
            case 'precision':
                return b.metrics.avg_precision - a.metrics.avg_precision;
            case 'recall':
                return b.metrics.avg_recall - a.metrics.avg_recall;
            case 'issues_found':
                return b.metrics.total_true_positives - a.metrics.total_true_positives;
            case 'speed':
                return (a.metrics.avg_response_time_ms || 0) - (b.metrics.avg_response_time_ms || 0);
            default:
                return 0;
        }
    });

    const scoredNames = new Set(scoredTools.map(t => t.tool));
    const unscoredTools = benchmarkData.tools.filter(t => !scoredNames.has(t.name));

    const llmModels = benchmarkData.metadata.llm_models || {};

    let html = scoredTools.map((tool, index) => {
        const toolInfo = benchmarkData.tools.find(t => t.name === tool.tool);
        const rankClass = index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : '';
        const llmModel = toolInfo?.llm_model || llmModels[tool.tool] || '';

        const f2 = computeF2(tool.metrics.avg_precision, tool.metrics.avg_recall);
        return `
            <div class="leaderboard-item">
                <div class="rank ${rankClass}">#${index + 1}</div>
                <div class="tool-info">
                    <div class="tool-name">${tool.tool} ${getToolTypeBadge(toolInfo)}</div>
                    <div class="tool-meta">
                        ${toolInfo && toolInfo.stars > 0 ? `<span>${ICONS.star} ${toolInfo.stars.toLocaleString()} stars</span>` : ''}
                        <span>${ICONS.scroll} ${toolInfo ? toolInfo.license : ''}</span>
                        ${llmModel ? `<span class="llm-badge">${ICONS.cpu} ${llmModel}</span>` : ''}
                    </div>
                </div>
                <div class="metrics-grid">
                    <div class="metric ${currentSortMetric === 'f2_score' ? 'metric-highlighted' : ''}">
                        <span class="metric-value ${getScoreClass(f2)}">
                            ${(f2 * 100).toFixed(1)}%
                        </span>
                        <span class="metric-label">F2 Score</span>
                    </div>
                    <div class="metric ${currentSortMetric === 'f1_score' ? 'metric-highlighted' : ''}">
                        <span class="metric-value ${getScoreClass(tool.metrics.avg_f1_score)}">
                            ${(tool.metrics.avg_f1_score * 100).toFixed(1)}%
                        </span>
                        <span class="metric-label">F1 Score</span>
                    </div>
                    <div class="metric ${currentSortMetric === 'precision' ? 'metric-highlighted' : ''}">
                        <span class="metric-value ${getScoreClass(tool.metrics.avg_precision)}">
                            ${(tool.metrics.avg_precision * 100).toFixed(1)}%
                        </span>
                        <span class="metric-label">Precision</span>
                    </div>
                    <div class="metric ${currentSortMetric === 'recall' ? 'metric-highlighted' : ''}">
                        <span class="metric-value ${getScoreClass(tool.metrics.avg_recall)}">
                            ${(tool.metrics.avg_recall * 100).toFixed(1)}%
                        </span>
                        <span class="metric-label">Recall</span>
                    </div>
                    <div class="metric ${currentSortMetric === 'issues_found' ? 'metric-highlighted' : ''}">
                        <span class="metric-value">
                            ${tool.metrics.total_true_positives}/${tool.metrics.total_true_positives + tool.metrics.total_false_negatives}
                        </span>
                        <span class="metric-label">Issues Found</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // Append unscored tools as "coming soon"
    html += unscoredTools.map(tool => {
        const llmModel = tool.llm_model || '';
        return `
            <div class="leaderboard-item coming-soon">
                <div class="rank coming-soon">—</div>
                <div class="tool-info">
                    <div class="tool-name">${tool.name} ${getToolTypeBadge(tool)}</div>
                    <div class="tool-meta">
                        ${tool.stars > 0 ? `<span>${ICONS.star} ${tool.stars.toLocaleString()} stars</span>` : ''}
                        <span>${ICONS.scroll} ${tool.license}</span>
                        ${llmModel ? `<span class="llm-badge">${ICONS.cpu} ${llmModel}</span>` : ''}
                    </div>
                </div>
                <div class="metrics-grid">
                    <div class="metric coming-soon-text">
                        <span class="metric-value">Coming soon</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = html;
}

// ===== Challenges Rendering =====
function renderChallenges() {
    const container = document.getElementById('challenges-grid');

    container.innerHTML = benchmarkData.challenges.map(challenge => {
        // Calculate average performance across all tools
        const challengeResults = benchmarkData.results.filter(r => r.challenge === challenge.id);
        const avgF1 = challengeResults.length > 0 ? challengeResults.reduce((sum, r) => sum + r.metrics.f1_score, 0) / challengeResults.length : 0;
        const bestTool = challengeResults.length > 0 ? challengeResults.reduce((best, r) =>
            r.metrics.f1_score > best.metrics.f1_score ? r : best
        ) : { tool: 'N/A' };

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

    // Separate tools by type
    const agents = benchmarkData.tools.filter(t => (t.tool_type || 'agent') === 'agent');
    const pureModels = benchmarkData.tools.filter(t => t.tool_type === 'pure_model');

    let html = '';

    if (agents.length > 0) {
        html += '<div class="tool-section-header"><h3>Code Review Agents</h3><p>Dedicated tools built specifically for automated code review, with their own prompts, parsing, and review logic.</p></div>';
        html += '<div class="tools-section-grid">';
        html += agents.map(tool => renderToolCard(tool)).join('');
        html += '</div>';
    }

    if (pureModels.length > 0) {
        html += '<div class="tool-section-header"><h3>Pure Model Baselines</h3><p>General-purpose LLMs called directly via API with a shared system prompt — no specialized review tooling. These serve as baselines to measure the added value of dedicated review agents.</p></div>';
        html += '<div class="tools-section-grid">';
        html += pureModels.map(tool => renderToolCard(tool)).join('');
        html += '</div>';

        // Show the shared system prompt
        if (benchmarkData.system_prompt) {
            html += `
                <div class="system-prompt-section">
                    <h3>Shared System Prompt for Pure Model Baselines</h3>
                    <p class="system-prompt-description">All pure model baselines receive the same system prompt. The diff is sent as the user message.</p>
                    <details class="system-prompt-details">
                        <summary>View system prompt</summary>
                        <pre class="system-prompt-code"><code>${escapeHtml(benchmarkData.system_prompt)}</code></pre>
                    </details>
                </div>
            `;
        }
    }

    container.innerHTML = html;
}

function renderToolCard(tool) {
    const toolScore = benchmarkData.overall_scores.find(s => s.tool === tool.name);
    const llmModel = tool.llm_model || '';
    const isPureModel = tool.tool_type === 'pure_model';
    const hasScore = toolScore != null;

    return `
        <div class="tool-card ${isPureModel ? 'pure-model-card' : ''}">
            <div class="tool-header">
                <div class="tool-title">
                    ${tool.name}
                    ${getToolTypeBadge(tool)}
                </div>
                ${tool.stars > 0 ? `<div class="tool-stars">${ICONS.star}<span>${tool.stars.toLocaleString()}</span></div>` : ''}
            </div>
            <div class="tool-description">${tool.description}</div>
            <div class="tool-install">$ ${tool.install_cmd}</div>
            ${llmModel ? `<div class="tool-llm"><span class="llm-badge">${ICONS.cpu} LLM: ${llmModel}</span></div>` : ''}
            ${hasScore ? `
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
            ` : '<div class="tool-performance"><p class="no-data">No benchmark results yet</p></div>'}
            <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
                <a href="${tool.github_url}" target="_blank" style="display: inline-flex; align-items: center; gap: 0.5rem;">
                    ${isPureModel ? 'Model docs' : 'View on GitHub'}
                    ${ICONS.externalLink}
                </a>
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
                const gt = challenge.ground_truth_issues || '?';
                html += `
                    <td onclick="showResultDetails('${tool}', '${challenge.id}')"
                        style="background: ${getScoreBackground(metrics.f1_score)}">
                        <div class="matrix-cell">
                            <span class="matrix-score ${scoreClass}">${(metrics.f1_score * 100).toFixed(0)}%</span>
                            <span class="matrix-detail">${metrics.true_positives}/${gt} found</span>
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
                    <span style="color: var(--text-secondary);">Precision:</span>
                    <span style="font-weight: 600; margin-left: 0.5rem;">${(result.metrics.precision * 100).toFixed(1)}%</span>
                </div>
                <div>
                    <span style="color: var(--text-secondary);">Recall:</span>
                    <span style="font-weight: 600; margin-left: 0.5rem;">${(result.metrics.recall * 100).toFixed(1)}%</span>
                </div>
                ${tool?.llm_model ? `<div>
                    <span style="color: var(--text-secondary);">LLM:</span>
                    <span style="font-weight: 600; margin-left: 0.5rem;">${tool.llm_model}</span>
                </div>` : ''}
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

        ${result.metrics.runs ? `
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
        ` : ''}
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
function computeF2(precision, recall) {
    if (precision + recall === 0) return 0;
    return (5 * precision * recall) / (4 * precision + recall);
}

function getScoreClass(score) {
    if (score >= 0.9) return 'score-excellent';
    if (score >= 0.7) return 'score-good';
    if (score >= 0.5) return 'score-fair';
    return 'score-poor';
}

function getScoreColor(score) {
    if (score >= 0.9) return '#10b981';
    if (score >= 0.7) return '#6366f1';
    if (score >= 0.5) return '#f59e0b';
    return '#ef4444';
}

function getScoreBackground(score) {
    if (score >= 0.9) return 'rgba(16,185,129,0.12)';
    if (score >= 0.7) return 'rgba(99,102,241,0.12)';
    if (score >= 0.5) return 'rgba(245,158,11,0.12)';
    return 'rgba(239,68,68,0.12)';
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
    const ts = benchmarkData?.metadata?.timestamp || benchmarkData?.metadata?.last_updated;
    const display = ts ? new Date(ts).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : 'No data available';
    const el1 = document.getElementById('last-updated-time');
    const el2 = document.getElementById('last-updated');
    if (el1) el1.textContent = display;
    if (el2) el2.textContent = display;
}

function showError(message) {
    console.error(message);
    // Could implement a toast notification here
}

// ===== Render Performance Trends =====
function renderTrends() {
    if (!benchmarkData) return;

    // Hide the entire section if no historical data exists
    const trendsSection = document.getElementById('trends-section');
    const recentHistory = benchmarkData.recent_history || [];
    const trends = benchmarkData.trends || {};

    if (recentHistory.length === 0 && Object.keys(trends).length === 0) {
        if (trendsSection) {
            trendsSection.style.display = 'none';
        }
        return;
    }

    // Render trend summary
    renderTrendSummary();

    // Render trend chart
    renderTrendChart();
}

function renderTrendSummary() {
    const container = document.getElementById('trend-summary-content');
    if (!container) return;

    const trends = benchmarkData.trends || {};

    if (Object.keys(trends).length === 0) {
        container.innerHTML = '<p class="no-data">No trend data available yet. Trends will appear after multiple benchmark runs.</p>';
        return;
    }

    const trendItems = Object.entries(trends).map(([tool, data]) => {
        const f1Change = data.f1_score_change || 0;
        const changePercent = (f1Change * 100).toFixed(1);
        const isPositive = f1Change > 0;
        const isNeutral = Math.abs(f1Change) < 0.01;

        let trendClass = 'neutral';
        let arrow = '→';

        if (!isNeutral) {
            trendClass = isPositive ? 'positive' : 'negative';
            arrow = isPositive ? '↑' : '↓';
        }

        return `
            <div class="trend-item">
                <span class="trend-tool-name">${tool}</span>
                <span class="trend-change ${trendClass}">
                    <span class="trend-arrow">${arrow}</span>
                    ${isPositive ? '+' : ''}${changePercent}%
                </span>
            </div>
        `;
    }).join('');

    container.innerHTML = trendItems;
}

function renderTrendChart() {
    const canvas = document.getElementById('f1-trend-chart');
    if (!canvas) return;

    const recentHistory = benchmarkData.recent_history || [];

    if (recentHistory.length === 0) {
        // Show a message instead of empty chart
        canvas.style.display = 'none';
        const wrapper = canvas.parentElement;
        if (!wrapper.querySelector('.no-data')) {
            const noDataMsg = document.createElement('p');
            noDataMsg.className = 'no-data';
            noDataMsg.textContent = 'Chart will appear after multiple benchmark runs.';
            wrapper.appendChild(noDataMsg);
        }
        return;
    }

    // Prepare data for Chart.js
    const labels = recentHistory.map(entry => entry.date);
    const tools = new Set();

    // Get all tool names
    recentHistory.forEach(entry => {
        Object.keys(entry.metrics).forEach(tool => tools.add(tool));
    });

    // Create datasets for each tool
    const datasets = Array.from(tools).map(tool => {
        const data = recentHistory.map(entry => {
            return entry.metrics[tool] ? (entry.metrics[tool].f1_score * 100) : null;
        });

        // Generate a color for each tool
        const colors = {
            'PR-Agent': 'rgb(99, 102, 241)',   // Indigo
            'Shippie': 'rgb(16, 185, 129)'     // Emerald
        };

        const color = colors[tool] || `hsl(${Math.random() * 360}, 60%, 55%)`;

        return {
            label: tool,
            data: data,
            borderColor: color,
            backgroundColor: color + '20',
            tension: 0.3,
            fill: false,
            pointRadius: 4,
            pointHoverRadius: 6
        };
    });

    // Destroy previous chart if exists
    if (trendChart) {
        trendChart.destroy();
    }

    // Create new chart
    const ctx = canvas.getContext('2d');
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function (value) {
                            return value + '%';
                        }
                    },
                    title: {
                        display: true,
                        text: 'F1 Score (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}
// Metrics Breakdown Functions

// Compute breakdown data client-side from results + challenges
function computeMetricsBreakdown() {
    if (!benchmarkData || benchmarkData.metrics_breakdown) return;

    const results = benchmarkData.results || [];
    const challenges = benchmarkData.challenges || [];

    // Build lookup maps
    const challengeMap = {};
    challenges.forEach(ch => { challengeMap[ch.id] = ch; });

    // --- By Category ---
    const categoryGroups = {};
    results.forEach(r => {
        const ch = challengeMap[r.challenge];
        if (!ch) return;
        const cat = ch.category;
        if (!categoryGroups[cat]) {
            categoryGroups[cat] = { tp: 0, fp: 0, fn: 0, gt: 0, found: 0 };
        }
        categoryGroups[cat].tp += r.metrics.true_positives;
        categoryGroups[cat].fp += r.metrics.false_positives;
        categoryGroups[cat].fn += r.metrics.false_negatives;
    });

    const byCategory = Object.entries(categoryGroups).map(([name, g]) => {
        const precision = g.tp + g.fp > 0 ? g.tp / (g.tp + g.fp) : 0;
        const recall = g.tp + g.fn > 0 ? g.tp / (g.tp + g.fn) : 0;
        const f1 = precision + recall > 0 ? 2 * precision * recall / (precision + recall) : 0;
        return {
            name, precision, recall, f1_score: f1,
            total_issues: g.tp + g.fn,
            total_found: g.tp
        };
    }).sort((a, b) => b.f1_score - a.f1_score);

    // --- By Language ---
    const languageGroups = {};
    results.forEach(r => {
        const ch = challengeMap[r.challenge];
        if (!ch) return;
        const lang = ch.language || 'unknown';
        if (!languageGroups[lang]) {
            languageGroups[lang] = { tp: 0, fp: 0, fn: 0, challenges: new Set() };
        }
        languageGroups[lang].tp += r.metrics.true_positives;
        languageGroups[lang].fp += r.metrics.false_positives;
        languageGroups[lang].fn += r.metrics.false_negatives;
        languageGroups[lang].challenges.add(r.challenge);
    });

    const byLanguage = Object.entries(languageGroups).map(([name, g]) => {
        const precision = g.tp + g.fp > 0 ? g.tp / (g.tp + g.fp) : 0;
        const recall = g.tp + g.fn > 0 ? g.tp / (g.tp + g.fn) : 0;
        const f1 = precision + recall > 0 ? 2 * precision * recall / (precision + recall) : 0;
        return {
            name, precision, recall, f1_score: f1,
            total_issues: g.tp + g.fn,
            total_found: g.tp,
            challenges: g.challenges.size
        };
    }).sort((a, b) => b.f1_score - a.f1_score);

    benchmarkData.metrics_breakdown = {
        by_category: byCategory,
        by_language: byLanguage,
        by_severity: [] // Not available from current data
    };
}

function renderMetricsBreakdown() {
    if (!benchmarkData || !benchmarkData.metrics_breakdown) {
        const container = document.getElementById('metrics-breakdown');
        if (container) {
            container.innerHTML = '<p class="no-data">No breakdown data available yet.</p>';
        }
        return;
    }

    const container = document.getElementById('metrics-breakdown');
    if (!container) return;

    container.innerHTML = `
        <div class="breakdown-tabs">
            <button class="tab-btn active" data-tab="category">By Category</button>
            <button class="tab-btn" data-tab="language">By Language</button>
        </div>
        <div id="breakdown-content">
            ${renderCategoryBreakdown()}
        </div>
    `;

    // Add tab switching
    container.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const tab = btn.dataset.tab;
            const content = document.getElementById('breakdown-content');

            switch (tab) {
                case 'category':
                    content.innerHTML = renderCategoryBreakdown();
                    break;
                case 'language':
                    content.innerHTML = renderLanguageBreakdown();
                    break;
            }

            // Render charts if needed
            renderBreakdownCharts(tab);
        });
    });

    // Initial chart render
    renderBreakdownCharts('category');
}

function renderCategoryBreakdown() {
    const breakdown = benchmarkData.metrics_breakdown.by_category;

    return `
        <div class="breakdown-grid">
            <div class="breakdown-table">
                <h3>Performance by Category</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>F1 Score</th>
                            <th>Issues Found/Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${breakdown.map(cat => `
                            <tr>
                                <td><span class="challenge-badge badge-${cat.name.toLowerCase()}">${cat.name}</span></td>
                                <td class="metric">${(cat.precision * 100).toFixed(1)}%</td>
                                <td class="metric">${(cat.recall * 100).toFixed(1)}%</td>
                                <td class="metric">${(cat.f1_score * 100).toFixed(1)}%</td>
                                <td class="metric">${cat.total_found}/${cat.total_issues}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="breakdown-chart">
                <canvas id="category-chart"></canvas>
            </div>
        </div>
    `;
}

function renderSeverityBreakdown() {
    const breakdown = benchmarkData.metrics_breakdown.by_severity;

    return `
        <div class="breakdown-grid">
            <div class="breakdown-table">
                <h3>Performance by Severity</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>F1 Score</th>
                            <th>Issues Found/Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${breakdown.map(sev => `
                            <tr>
                                <td>
                                    <span class="severity-badge" style="background: ${getSeverityColor(sev.name)}20; color: ${getSeverityColor(sev.name)};">
                                        ${sev.name.charAt(0).toUpperCase() + sev.name.slice(1)}
                                    </span>
                                </td>
                                <td class="metric">${(sev.precision * 100).toFixed(1)}%</td>
                                <td class="metric">${(sev.recall * 100).toFixed(1)}%</td>
                                <td class="metric">${(sev.f1_score * 100).toFixed(1)}%</td>
                                <td class="metric">${sev.total_found}/${sev.total_issues}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="breakdown-chart">
                <canvas id="severity-chart"></canvas>
            </div>
        </div>
    `;
}

function renderLanguageBreakdown() {
    const breakdown = benchmarkData.metrics_breakdown.by_language;

    return `
        <div class="breakdown-grid">
            <div class="breakdown-table">
                <h3>Performance by Language</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Language</th>
                            <th>Precision</th>
                            <th>Recall</th>
                            <th>F1 Score</th>
                            <th>Challenges</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${breakdown.map(lang => `
                            <tr>
                                <td><span class="language-badge">${lang.name}</span></td>
                                <td class="metric">${(lang.precision * 100).toFixed(1)}%</td>
                                <td class="metric">${(lang.recall * 100).toFixed(1)}%</td>
                                <td class="metric">${(lang.f1_score * 100).toFixed(1)}%</td>
                                <td class="metric">${lang.challenges}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            <div class="breakdown-chart">
                <canvas id="language-chart"></canvas>
            </div>
        </div>
    `;
}

function renderBreakdownCharts(type) {
    let data, labels, chartId;

    switch (type) {
        case 'category':
            data = benchmarkData.metrics_breakdown.by_category;
            labels = data.map(d => d.name);
            chartId = 'category-chart';
            break;
        case 'severity':
            data = benchmarkData.metrics_breakdown.by_severity;
            labels = data.map(d => d.name.charAt(0).toUpperCase() + d.name.slice(1));
            chartId = 'severity-chart';
            break;
        case 'language':
            data = benchmarkData.metrics_breakdown.by_language;
            labels = data.map(d => d.name);
            chartId = 'language-chart';
            break;
    }

    const ctx = document.getElementById(chartId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Precision',
                    data: data.map(d => (d.precision * 100).toFixed(1)),
                    backgroundColor: 'rgba(99, 102, 241, 0.5)',
                },
                {
                    label: 'Recall',
                    data: data.map(d => (d.recall * 100).toFixed(1)),
                    backgroundColor: 'rgba(16, 185, 129, 0.5)',
                },
                {
                    label: 'F1 Score',
                    data: data.map(d => (d.f1_score * 100).toFixed(1)),
                    backgroundColor: 'rgba(168, 85, 247, 0.5)',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function (value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}
