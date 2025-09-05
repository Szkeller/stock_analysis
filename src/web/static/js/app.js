// A股散户分析系统前端JavaScript

// 全局变量
let currentStock = null;
let searchTimeout = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadMarketStatus();
    
    // 绑定搜索事件
    document.getElementById('stockSearch').addEventListener('input', handleSearch);
    document.getElementById('analysisSearch').addEventListener('input', handleAnalysisSearch);
    
    // 绑定导航事件
    document.querySelectorAll('[data-tab]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            showTab(this.getAttribute('data-tab'));
        });
    });
});

// 初始化应用
function initializeApp() {
    console.log('A股散户分析系统启动');
    showTab('home');
}

// 显示标签页
function showTab(tabName) {
    // 隐藏所有标签页
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 显示指定标签页
    const targetTab = document.getElementById(tabName + '-tab');
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // 更新导航状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[data-tab="${tabName}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    // 根据标签页加载相应数据
    switch(tabName) {
        case 'watchlist':
            loadWatchlist();
            break;
        case 'ranking':
            loadRanking();
            break;
        case 'alerts':
            loadAlerts();
            break;
    }
}

// 处理搜索
function handleSearch() {
    const query = document.getElementById('stockSearch').value.trim();
    
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    if (query.length >= 2) {
        searchTimeout = setTimeout(() => {
            searchStock(query, 'searchResults');
        }, 300);
    } else {
        document.getElementById('searchResults').innerHTML = '';
    }
}

// 处理分析页面搜索
function handleAnalysisSearch() {
    const query = document.getElementById('analysisSearch').value.trim();
    
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    if (query.length >= 2) {
        searchTimeout = setTimeout(() => {
            searchStock(query, 'analysisSearchResults');
        }, 300);
    }
}

// 搜索股票
function searchStock(query, resultElementId) {
    fetch(`/api/search_stock?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySearchResults(data.data, resultElementId);
            } else {
                showMessage('搜索失败: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('搜索错误:', error);
            showMessage('搜索出错，请重试', 'error');
        });
}

// 显示搜索结果
function displaySearchResults(stocks, resultElementId) {
    const resultsDiv = document.getElementById(resultElementId);
    
    if (stocks.length === 0) {
        resultsDiv.innerHTML = '<div class="text-muted">未找到匹配的股票</div>';
        return;
    }
    
    let html = '';
    stocks.forEach(stock => {
        html += `
            <div class="search-result-item" onclick="selectStock('${stock.symbol}', '${stock.name}')">
                <div class="d-flex justify-content-between">
                    <div>
                        <strong>${stock.symbol}</strong>
                        <span class="text-muted ms-2">${stock.name}</span>
                    </div>
                    <div class="text-muted">${stock.market || ''}</div>
                </div>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
}

// 选择股票
function selectStock(symbol, name) {
    currentStock = { symbol, name };
    
    // 清空搜索结果
    document.getElementById('searchResults').innerHTML = '';
    if (document.getElementById('analysisSearchResults')) {
        document.getElementById('analysisSearchResults').innerHTML = '';
    }
    
    // 设置搜索框的值
    document.getElementById('stockSearch').value = `${symbol} ${name}`;
    if (document.getElementById('analysisSearch')) {
        document.getElementById('analysisSearch').value = symbol;
    }
}

// 快速分析
function quickAnalysis() {
    if (!currentStock) {
        const input = document.getElementById('stockSearch').value.trim();
        if (input) {
            const symbol = input.split(' ')[0];
            currentStock = { symbol: symbol, name: '' };
        } else {
            showMessage('请先选择股票', 'error');
            return;
        }
    }
    
    showTab('analysis');
    document.getElementById('analysisSearch').value = currentStock.symbol;
    analyzeStock();
}

// 分析股票
function analyzeStock() {
    const symbol = document.getElementById('analysisSearch').value.trim();
    if (!symbol) {
        showMessage('请输入股票代码', 'error');
        return;
    }
    
    const days = document.getElementById('analysisDays').value;
    const forceUpdate = document.getElementById('forceUpdate').checked;
    
    // 显示加载状态
    document.getElementById('analysisLoading').style.display = 'block';
    document.getElementById('analysisResults').style.display = 'none';
    document.getElementById('stockInfo').style.display = 'none';
    document.getElementById('riskInfo').style.display = 'none';
    
    // 分析股票
    fetch(`/api/analyze/${symbol}?days=${days}&force=${forceUpdate}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('analysisLoading').style.display = 'none';
            
            if (data.success) {
                displayAnalysisResults(data.data);
                loadRiskAssessment(symbol);
            } else {
                showMessage('分析失败: ' + data.message, 'error');
            }
        })
        .catch(error => {
            document.getElementById('analysisLoading').style.display = 'none';
            console.error('分析错误:', error);
            showMessage('分析出错，请重试', 'error');
        });
}

// 显示分析结果
function displayAnalysisResults(result) {
    // 显示基本信息
    if (result.summary && result.summary.basic_info) {
        displayStockInfo(result);
    }
    
    // 显示技术指标
    if (result.indicators) {
        displayTechnicalIndicators(result.indicators);
    }
    
    // 显示图表
    if (result.charts && result.charts.comprehensive) {
        const chartImg = document.getElementById('comprehensiveChart');
        chartImg.src = `/api/chart/${result.symbol}/comprehensive`;
    }
    
    // 显示投资建议
    if (result.summary) {
        displayInvestmentAdvice(result.summary, result.signals);
    }
    
    document.getElementById('analysisResults').style.display = 'block';
    document.getElementById('stockInfo').style.display = 'block';
}

// 显示股票基本信息
function displayStockInfo(result) {
    const basicInfo = result.summary.basic_info;
    const priceChangeClass = basicInfo.price_change_pct > 0 ? 'price-up' : 
                            basicInfo.price_change_pct < 0 ? 'price-down' : 'price-neutral';
    
    const html = `
        <div class="stock-info-item">
            <span class="stock-info-label">股票代码</span>
            <span class="stock-info-value">${result.symbol}</span>
        </div>
        <div class="stock-info-item">
            <span class="stock-info-label">最新价格</span>
            <span class="stock-info-value">¥${basicInfo.latest_price}</span>
        </div>
        <div class="stock-info-item">
            <span class="stock-info-label">涨跌幅</span>
            <span class="stock-info-value ${priceChangeClass}">
                ${basicInfo.price_change_pct > 0 ? '+' : ''}${basicInfo.price_change_pct}%
            </span>
        </div>
        <div class="stock-info-item">
            <span class="stock-info-label">成交量</span>
            <span class="stock-info-value">${formatNumber(basicInfo.volume)}</span>
        </div>
        <div class="stock-info-item">
            <span class="stock-info-label">风险等级</span>
            <span class="stock-info-value">
                <span class="risk-badge risk-${result.summary.risk_level === '低风险' ? 'low' : 
                    result.summary.risk_level === '中风险' ? 'medium' : 'high'}">
                    ${result.summary.risk_level}
                </span>
            </span>
        </div>
        <div class="mt-3">
            <button class="btn btn-primary btn-sm" onclick="showAddWatchlistModal('${result.symbol}', '${result.symbol}')">
                <i class="bi bi-heart"></i> 添加自选
            </button>
        </div>
    `;
    
    document.getElementById('stockInfoContent').innerHTML = html;
}

// 显示技术指标
function displayTechnicalIndicators(indicators) {
    let html = '<table class="indicators-table">';
    
    // 移动平均线
    if (indicators.ma5) {
        html += `
            <tr><td>MA5</td><td>¥${indicators.ma5.toFixed(2)}</td></tr>
            <tr><td>MA10</td><td>¥${indicators.ma10?.toFixed(2) || 'N/A'}</td></tr>
            <tr><td>MA20</td><td>¥${indicators.ma20?.toFixed(2) || 'N/A'}</td></tr>
            <tr><td>MA60</td><td>¥${indicators.ma60?.toFixed(2) || 'N/A'}</td></tr>
        `;
    }
    
    // MACD
    if (indicators.macd !== undefined) {
        html += `
            <tr><td>MACD</td><td>${indicators.macd.toFixed(4)}</td></tr>
            <tr><td>MACD信号线</td><td>${indicators.macd_signal?.toFixed(4) || 'N/A'}</td></tr>
        `;
    }
    
    // RSI
    if (indicators.rsi) {
        html += `<tr><td>RSI</td><td>${indicators.rsi.toFixed(2)}</td></tr>`;
    }
    
    // KDJ
    if (indicators.kdj_k) {
        html += `
            <tr><td>KDJ-K</td><td>${indicators.kdj_k.toFixed(2)}</td></tr>
            <tr><td>KDJ-D</td><td>${indicators.kdj_d?.toFixed(2) || 'N/A'}</td></tr>
            <tr><td>KDJ-J</td><td>${indicators.kdj_j?.toFixed(2) || 'N/A'}</td></tr>
        `;
    }
    
    html += '</table>';
    document.getElementById('technicalIndicators').innerHTML = html;
}

// 显示投资建议
function displayInvestmentAdvice(summary, signals) {
    let html = `
        <div class="mb-3">
            <h6>投资建议</h6>
            <p class="mb-2">${summary.recommendation}</p>
        </div>
    `;
    
    if (signals && Object.keys(signals).length > 0) {
        html += `
            <div class="mb-3">
                <h6>技术信号</h6>
                <div>
        `;
        
        Object.keys(signals).forEach(signal => {
            const signalClass = signal.includes('golden') ? 'signal-positive' : 
                               signal.includes('death') || signal.includes('overbought') ? 'signal-negative' : 
                               'signal-neutral';
            html += `<span class="signal-badge ${signalClass}">${formatSignalName(signal)}</span>`;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    // 加载海龟策略分析
    loadTurtleStrategy(getCurrentSymbol());
    
    if (summary.technical_status) {
        html += `
            <div>
                <h6>技术状态</h6>
                <ul class="mb-0">
        `;
        
        Object.entries(summary.technical_status).forEach(([key, value]) => {
            html += `<li>${formatStatusName(key)}: ${value}</li>`;
        });
        
        html += `
                </ul>
            </div>
        `;
    }
    
    document.getElementById('investmentAdvice').innerHTML = html;
}

// 加载风险评估
function loadRiskAssessment(symbol) {
    fetch(`/api/risk_assessment/${symbol}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayRiskAssessment(data.data);
            } else {
                console.error('风险评估失败:', data.message);
            }
        })
        .catch(error => {
            console.error('风险评估错误:', error);
        });
}

// 显示风险评估
function displayRiskAssessment(risk) {
    const riskLevelClass = risk.risk_level === '低风险' ? 'risk-low' : 
                          risk.risk_level === '中风险' ? 'risk-medium' : 'risk-high';
    
    let html = `
        <div class="mb-3">
            <div class="d-flex justify-content-between align-items-center">
                <span>风险等级</span>
                <span class="risk-badge ${riskLevelClass}">${risk.risk_level}</span>
            </div>
            <div class="mt-2">
                <small class="text-muted">风险分数: ${risk.risk_score.toFixed(1)}/100</small>
            </div>
        </div>
    `;
    
    if (risk.warnings && risk.warnings.length > 0) {
        html += `
            <div class="mb-3">
                <h6>风险提示</h6>
                <ul class="mb-0">
        `;
        
        risk.warnings.forEach(warning => {
            html += `<li class="text-warning">${warning}</li>`;
        });
        
        html += `
                </ul>
            </div>
        `;
    }
    
    if (risk.recommendations && risk.recommendations.length > 0) {
        html += `
            <div>
                <h6>建议</h6>
                <ul class="mb-0">
        `;
        
        risk.recommendations.forEach(rec => {
            html += `<li>${rec}</li>`;
        });
        
        html += `
                </ul>
            </div>
        `;
    }
    
    document.getElementById('riskInfoContent').innerHTML = html;
    document.getElementById('riskInfo').style.display = 'block';
}

// 加载市场状态
function loadMarketStatus() {
    fetch('/api/market_status')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const status = data.data;
                const statusText = `${status.status} (${status.current_time})`;
                document.getElementById('marketStatus').textContent = `市场状态：${statusText}`;
            }
        })
        .catch(error => {
            console.error('获取市场状态失败:', error);
        });
}

// 加载自选股
function loadWatchlist() {
    fetch('/api/watchlist')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayWatchlist(data.data);
            } else {
                showMessage('加载自选股失败: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('加载自选股错误:', error);
            showMessage('加载自选股出错，请重试', 'error');
        });
}

// 显示自选股
function displayWatchlist(watchlist) {
    const content = document.getElementById('watchlistContent');
    
    if (watchlist.length === 0) {
        content.innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-heart display-4"></i>
                <p class="mt-2">暂无自选股，去股票分析页面添加吧！</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <table class="watchlist-table">
            <thead>
                <tr>
                    <th>股票代码</th>
                    <th>股票名称</th>
                    <th>优先级</th>
                    <th>添加时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    watchlist.forEach(item => {
        const priorityText = item.priority === 3 ? '核心关注' : 
                            item.priority === 2 ? '重点关注' : '一般关注';
        
        html += `
            <tr>
                <td><strong>${item.symbol}</strong></td>
                <td>${item.name || ''}</td>
                <td>
                    <span class="badge bg-${item.priority === 3 ? 'danger' : item.priority === 2 ? 'warning' : 'secondary'}">
                        ${priorityText}
                    </span>
                </td>
                <td>${item.added_date || ''}</td>
                <td>
                    <button class="btn btn-primary btn-sm me-2" onclick="analyzeWatchlistStock('${item.symbol}')">
                        <i class="bi bi-graph-up"></i> 分析
                    </button>
                    <button class="btn btn-outline-danger btn-sm" onclick="removeFromWatchlist('${item.symbol}')">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
    `;
    
    content.innerHTML = html;
}

// 刷新自选股
function refreshWatchlist() {
    loadWatchlist();
}

// 分析自选股中的股票
function analyzeWatchlistStock(symbol) {
    currentStock = { symbol: symbol, name: '' };
    showTab('analysis');
    document.getElementById('analysisSearch').value = symbol;
    analyzeStock();
}

// 从自选股移除
function removeFromWatchlist(symbol) {
    if (confirm(`确定要从自选股中移除 ${symbol} 吗？`)) {
        fetch(`/api/watchlist/${symbol}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('移除成功', 'success');
                    loadWatchlist();
                } else {
                    showMessage('移除失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('移除错误:', error);
                showMessage('移除出错，请重试', 'error');
            });
    }
}

// 显示添加到自选股模态框
function showAddWatchlistModal(symbol, name) {
    document.getElementById('watchlistSymbol').value = symbol;
    document.getElementById('watchlistName').value = name;
    document.getElementById('watchlistNotes').value = '';
    document.getElementById('watchlistPriority').value = '1';
    
    const modal = new bootstrap.Modal(document.getElementById('addWatchlistModal'));
    modal.show();
}

// 添加到自选股
function addToWatchlist() {
    const symbol = document.getElementById('watchlistSymbol').value;
    const name = document.getElementById('watchlistName').value;
    const priority = parseInt(document.getElementById('watchlistPriority').value);
    const notes = document.getElementById('watchlistNotes').value;
    
    const data = {
        symbol: symbol,
        name: name,
        priority: priority,
        notes: notes
    };
    
    fetch('/api/watchlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('添加到自选股成功', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('addWatchlistModal'));
            modal.hide();
        } else {
            showMessage('添加失败: ' + data.message, 'error');
        }
    })
    .catch(error => {
        console.error('添加错误:', error);
        showMessage('添加出错，请重试', 'error');
    });
}

// 加载排行榜
function loadRanking() {
    const criteria = document.getElementById('rankingCriteria').value;
    
    fetch(`/api/ranking?criteria=${encodeURIComponent(criteria)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayRanking(data.data);
            } else {
                showMessage('加载排行榜失败: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('加载排行榜错误:', error);
            showMessage('加载排行榜出错，请重试', 'error');
        });
}

// 显示排行榜
function displayRanking(ranking) {
    const content = document.getElementById('rankingContent');
    
    if (ranking.length === 0) {
        content.innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-trophy display-4"></i>
                <p class="mt-2">暂无排行榜数据</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    ranking.forEach((item, index) => {
        const changeClass = item.pct_change > 0 ? 'price-up' : 
                           item.pct_change < 0 ? 'price-down' : 'price-neutral';
        
        html += `
            <div class="ranking-item" onclick="selectStock('${item.symbol}', '${item.name}')">
                <div class="ranking-number">${index + 1}</div>
                <div class="ranking-info">
                    <div class="ranking-symbol">${item.symbol}</div>
                    <div class="ranking-name">${item.name}</div>
                </div>
                <div class="ranking-value">
                    <div class="${changeClass}">
                        ${item.pct_change > 0 ? '+' : ''}${item.pct_change}%
                    </div>
                    <div class="text-muted">¥${item.price}</div>
                </div>
            </div>
        `;
    });
    
    content.innerHTML = html;
}

// 加载预警
function loadAlerts() {
    fetch('/api/alerts?limit=50')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAlerts(data.data);
            } else {
                showMessage('加载预警失败: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('加载预警错误:', error);
            showMessage('加载预警出错，请重试', 'error');
        });
}

// 显示预警
function displayAlerts(alerts) {
    const content = document.getElementById('alertsContent');
    
    if (alerts.length === 0) {
        content.innerHTML = `
            <div class="text-center text-muted">
                <i class="bi bi-bell display-4"></i>
                <p class="mt-2">暂无预警信息</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    alerts.forEach(alert => {
        const alertClass = alert.severity === 'CRITICAL' ? 'alert-critical' : 
                          alert.severity === 'WARNING' ? 'alert-warning' : 'alert-info';
        
        html += `
            <div class="alert-item ${alertClass}">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${alert.title}</h6>
                        <p class="mb-1">${alert.message}</p>
                        <small class="alert-timestamp">${formatDateTime(alert.created_at)}</small>
                    </div>
                    <div>
                        <span class="badge bg-secondary">${alert.symbol}</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    content.innerHTML = html;
}

// 获取当前股票代码
function getCurrentSymbol() {
    return document.getElementById('analysisSearch').value.trim();
}

// 加载海龜策略分析
function loadTurtleStrategy(symbol) {
    if (!symbol) return;
    
    fetch(`/api/turtle_strategy/${symbol}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTurtleStrategy(data.data);
            }
        })
        .catch(error => {
            console.error('海龜策略分析错误:', error);
        });
}

// 显示海龜策略分析结果
function displayTurtleStrategy(turtleData) {
    let html = `
        <div class="turtle-strategy mt-3">
            <h6><i class="bi bi-graph-up-arrow"></i> 海龜交易法则</h6>
    `;
    
    if (turtleData.error) {
        html += `<p class="text-warning">${turtleData.error}</p>`;
    } else {
        const signal = turtleData.combined_signal;
        const signalClass = signal === 'BUY' ? 'text-success' : 
                           signal === 'SELL' ? 'text-danger' : 'text-muted';
        
        html += `
            <div class="row">
                <div class="col-md-6">
                    <p><strong>综合信号:</strong> <span class="${signalClass}">${formatTurtleSignal(signal)}</span></p>
                    <p><strong>仓位建议:</strong> ${(turtleData.position_size * 100).toFixed(1)}%</p>
                </div>
                <div class="col-md-6">
        `;
        
        if (turtleData.stop_loss) {
            html += `<p><strong>止损价:</strong> ¥${turtleData.stop_loss.toFixed(2)}</p>`;
        }
        
        if (turtleData.risk_metrics) {
            const metrics = turtleData.risk_metrics;
            html += `<p><strong>ATR波动:</strong> ${metrics.atr_pct || 'N/A'}%</p>`;
        }
        
        html += `
                </div>
            </div>
        `;
        
        // 系统详情
        if (turtleData.system1 || turtleData.system2) {
            html += `
                <div class="mt-2">
                    <small class="text-muted">
                        <strong>系统详情:</strong>
            `;
            
            if (turtleData.system1 && turtleData.system1.entry_signal !== 'NONE') {
                html += ` 系统1(20天): ${formatTurtleSignal(turtleData.system1.entry_signal)}`;
            }
            
            if (turtleData.system2 && turtleData.system2.entry_signal !== 'NONE') {
                html += ` 系统2(55天): ${formatTurtleSignal(turtleData.system2.entry_signal)}`;
            }
            
            html += `
                    </small>
                </div>
            `;
        }
    }
    
    html += `</div>`;
    
    // 将海龜策略结果添加到投资建议区域
    const adviceElement = document.getElementById('investmentAdvice');
    if (adviceElement) {
        adviceElement.innerHTML += html;
    }
}

// 格式化海龜信号
function formatTurtleSignal(signal) {
    const signalMap = {
        'BUY': '买入',
        'SELL': '卖出', 
        'EXIT': '出场',
        'HOLD': '观望',
        'NONE': '无信号'
    };
    
    return signalMap[signal] || signal;
}

// 工具函数

// 格式化数字
function formatNumber(num) {
    if (num >= 100000000) {
        return (num / 100000000).toFixed(1) + '亿';
    } else if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    }
    return num.toString();
}

// 格式化信号名称
function formatSignalName(signal) {
    const signalMap = {
        'ma_golden_cross': 'MA金叉',
        'ma_death_cross': 'MA死叉',
        'macd_golden_cross': 'MACD金叉',
        'macd_death_cross': 'MACD死叉',
        'rsi_overbought': 'RSI超买',
        'rsi_oversold': 'RSI超卖',
        'kdj_golden_cross': 'KDJ金叉',
        'kdj_death_cross': 'KDJ死叉',
        'boll_breakthrough_upper': '突破布林上轨',
        'boll_breakthrough_lower': '跌破布林下轨'
    };
    
    return signalMap[signal] || signal;
}

// 格式化状态名称
function formatStatusName(status) {
    const statusMap = {
        'trend': '趋势',
        'rsi_status': 'RSI状态',
        'macd_status': 'MACD状态'
    };
    
    return statusMap[status] || status;
}

// 格式化日期时间
function formatDateTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 显示消息
function showMessage(message, type) {
    const messageClass = type === 'success' ? 'message-success' : 'message-error';
    
    // 创建消息元素
    const messageDiv = document.createElement('div');
    messageDiv.className = messageClass;
    messageDiv.textContent = message;
    
    // 插入到页面顶部
    const container = document.querySelector('.container');
    container.insertBefore(messageDiv, container.firstChild);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 3000);
}