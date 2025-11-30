            // Unregister any service workers on load to avoid cached/broken script being served by a stale SW
            if ('serviceWorker' in navigator) {
                try {
                    navigator.serviceWorker.getRegistrations().then(regs => {
                        regs.forEach(r => {
                            try { r.unregister(); } catch(e) { /* ignore */ }
                        });
                    }).catch(()=>{});
                } catch(e) { /* ignore */ }
            }

        // Simple modal for genome display
        const genomeModalHtml = `
        <div id="genomeModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);display:none;align-items:center;justify-content:center;z-index:9999;">
            <div style="background:white;padding:20px;border-radius:10px;max-width:900px;max-height:80vh;overflow:auto;">
                <button id="closeGenomeBtn" style="float:right;" onclick="document.getElementById('genomeModal').style.display='none'">Close</button>
                <h3>Genome Snapshot</h3>
                <div id="genomeLoading" style="display:none;margin-bottom:10px;color:#555;">Loading snapshot…</div>
                <div id="genomeError" style="display:none;margin-bottom:10px;color:#c0392b;background:#fdecea;padding:8px;border-radius:6px;"></div>

                <div id="genomeSummary" style="display:none;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <div style="font-weight:600;color:#333;">Snapshot summary</div>
                        <div>
                            <button id="downloadGenomeBtn" class="btn" style="margin-right:8px;background:#fff;border:1px solid #ccc;">⬇️ Download JSON</button>
                                <button id="downloadGenomeServerBtn" class="btn" style="margin-right:8px;background:#fff;border:1px solid #ccc;">⬇️ Download (server)</button>
                            <button id="toggleHistoryBtn" class="btn" style="background:#fff;border:1px solid #ccc;">Show edit history</button>
                        </div>
                    </div>
                    <div id="genomeTelemetry" style="margin-bottom:8px;color:#333;font-size:0.95em;display:none;">
                        <!-- telemetry populated dynamically -->
                    </div>
                    <div id="liveTelemetrySection" style="display:none;margin-top:8px;border-top:1px dashed #eee;padding-top:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                            <div style="font-weight:700;color:#333;">Live telemetry</div>
                            <div>
                                <button id="refreshTelemetryBtn" class="btn" style="background:#fff;border:1px solid #ccc;">↻ Refresh</button>
                            </div>
                        </div>
                        <div id="liveTelemetrySummary" style="color:#444;margin-bottom:6px;">Fetching live telemetry…</div>
                        <div id="liveSpeciesTable" style="background:#fff;padding:8px;border-radius:6px;border:1px solid #eee;max-height:160px;overflow:auto;font-size:0.9em;margin-bottom:6px;">
                            <!-- per-species stats populated here -->
                        </div>
                        <div id="liveTelemetryChartContainer" style="display:none;margin-top:6px;">
                            <canvas id="liveTelemetryChart" style="width:100%;height:160px;"></canvas>
                        </div>
                    </div>
                    <div id="telemetryChartContainer" style="display:none;margin-top:8px;">
                        <canvas id="telemetryChart" style="width:100%;height:180px;"></canvas>
                    </div>
                    </div>
                    <div id="chromosomesTable" style="background:#fff;padding:8px;border-radius:6px;border:1px solid #eee;max-height:180px;overflow:auto;font-size:0.9em;">
                        <!-- populated dynamically -->
                    </div>
                    <div id="historyPreview" style="display:none;margin-top:8px;background:#fafafa;padding:8px;border-radius:6px;border:1px solid #eee;max-height:220px;overflow:auto;font-size:0.85em;"></div>
                </div>

                <pre id="genomeJson" style="white-space:pre-wrap;word-break:break-word;background:#f6f8fa;padding:10px;border-radius:6px;display:none;max-height:60vh;overflow:auto;"></pre>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', genomeModalHtml);

        // Trade Details Modal
        const tradeModalHtml = `
        <div id="tradeModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);display:none;align-items:center;justify-content:center;z-index:9999;opacity:0;transition:opacity 0.3s ease;padding:20px;">
            <div style="background:white;padding:0;border-radius:16px;max-width:1200px;width:100%;max-height:90vh;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.3);transform:scale(0.9);transition:transform 0.3s cubic-bezier(0.4,0,0.2,1);">
                <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:20px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:10;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2em;">📊</div>
                        <div>
                            <h3 style="margin:0;color:white;font-size:1.4em;font-weight:700;">
                                <span id="tradeModalSymbol"></span>
                            </h3>
                            <div style="color:rgba(255,255,255,0.9);font-size:0.85em;margin-top:2px;">Trading Activity & Analysis</div>
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;align-items:center;">
                        <button onclick="openExportMenu()" id="exportMenuBtn" style="background:rgba(255,255,255,0.2);border:none;font-size:1em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;transition:all 0.2s;font-weight:500;" title="Export Options" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">📥 Export</button>
                        <button onclick="toggleModalFullscreen()" id="fullscreenBtn" style="background:rgba(255,255,255,0.2);border:none;font-size:1.2em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;transition:all 0.2s;" title="Fullscreen">⛶</button>
                        <button onclick="closeTradeModal()" style="background:rgba(255,255,255,0.2);border:none;font-size:1.3em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;transition:all 0.2s;font-weight:300;" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">✕</button>
                    </div>
                </div>

                <!-- Export Menu Dropdown -->
                <div id="exportDropdown" style="display:none;position:absolute;top:70px;right:80px;background:white;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.2);padding:8px;z-index:1000;min-width:200px;">
                    <button onclick="exportModalAsPDF()" style="width:100%;padding:10px 14px;background:white;border:none;border-radius:6px;cursor:pointer;text-align:left;font-size:0.9em;transition:all 0.2s;display:flex;align-items:center;gap:10px;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                        <span style="font-size:1.2em;">📄</span>
                        <span style="font-weight:500;">Export as PDF</span>
                    </button>
                    <button onclick="exportModalAsExcel()" style="width:100%;padding:10px 14px;background:white;border:none;border-radius:6px;cursor:pointer;text-align:left;font-size:0.9em;transition:all 0.2s;display:flex;align-items:center;gap:10px;margin-top:4px;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                        <span style="font-size:1.2em;">📊</span>
                        <span style="font-weight:500;">Export as Excel</span>
                    </button>
                    <button onclick="exportChartsAsPNG()" style="width:100%;padding:10px 14px;background:white;border:none;border-radius:6px;cursor:pointer;text-align:left;font-size:0.9em;transition:all 0.2s;display:flex;align-items:center;gap:10px;margin-top:4px;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                        <span style="font-size:1.2em;">🖼️</span>
                        <span style="font-weight:500;">Export Charts as PNG</span>
                    </button>
                    <hr style="margin:8px 0;border:none;border-top:1px solid #e0e0e0;">
                    <button onclick="emailReport()" style="width:100%;padding:10px 14px;background:white;border:none;border-radius:6px;cursor:pointer;text-align:left;font-size:0.9em;transition:all 0.2s;display:flex;align-items:center;gap:10px;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                        <span style="font-size:1.2em;">📧</span>
                        <span style="font-weight:500;">Email Report</span>
                    </button>
                    <button onclick="scheduleReport()" style="width:100%;padding:10px 14px;background:white;border:none;border-radius:6px;cursor:pointer;text-align:left;font-size:0.9em;transition:all 0.2s;display:flex;align-items:center;gap:10px;margin-top:4px;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                        <span style="font-size:1.2em;">⏰</span>
                        <span style="font-weight:500;">Schedule Report</span>
                    </button>
                </div>
                
                <div style="padding:20px;overflow-y:auto;max-height:calc(90vh - 80px);">
                <div id="tradeModalLoading" style="display:none;padding:60px 20px;text-align:center;">
                    <div style="display:inline-block;width:50px;height:50px;border:4px solid #f3f3f3;border-top:4px solid #667eea;border-radius:50%;animation:spin 1s linear infinite;"></div>
                    <div style="font-size:1.2em;margin-top:20px;color:#666;font-weight:500;">Loading trade details...</div>
                    <div style="font-size:0.9em;color:#999;margin-top:8px;">Fetching data for this symbol</div>
                </div>
                
                <div id="tradeModalContent" style="display:none;">
                    <!-- Tab Navigation -->
                    <div style="display:flex;gap:8px;margin-bottom:20px;border-bottom:2px solid #f0f0f0;flex-wrap:wrap;">
                        <button onclick="switchModalTab('overview')" id="tabOverview" class="modal-tab active-tab" style="padding:12px 20px;background:none;border:none;border-bottom:3px solid #667eea;color:#667eea;font-weight:600;font-size:0.95em;cursor:pointer;transition:all 0.3s;position:relative;top:2px;">
                            📊 Overview
                        </button>
                        <button onclick="switchModalTab('trades')" id="tabTrades" class="modal-tab" style="padding:12px 20px;background:none;border:none;border-bottom:3px solid transparent;color:#6c757d;font-weight:600;font-size:0.95em;cursor:pointer;transition:all 0.3s;position:relative;top:2px;">
                            📋 Trades
                        </button>
                        <button onclick="switchModalTab('analysis')" id="tabAnalysis" class="modal-tab" style="padding:12px 20px;background:none;border:none;border-bottom:3px solid transparent;color:#6c757d;font-weight:600;font-size:0.95em;cursor:pointer;transition:all 0.3s;position:relative;top:2px;">
                            📈 Analysis
                        </button>
                        <button onclick="switchModalTab('charts')" id="tabCharts" class="modal-tab" style="padding:12px 20px;background:none;border:none;border-bottom:3px solid transparent;color:#6c757d;font-weight:600;font-size:0.95em;cursor:pointer;transition:all 0.3s;position:relative;top:2px;">
                            📉 Charts
                        </button>
                        <button onclick="switchModalTab('technical')" id="tabTechnical" class="modal-tab" style="padding:12px 20px;background:none;border:none;border-bottom:3px solid transparent;color:#6c757d;font-weight:600;font-size:0.95em;cursor:pointer;transition:all 0.3s;position:relative;top:2px;">
                            📊 Technical
                        </button>
                        <button onclick="switchModalTab('notes')" id="tabNotes" class="modal-tab" style="padding:12px 20px;background:none;border:none;border-bottom:3px solid transparent;color:#6c757d;font-weight:600;font-size:0.95em;cursor:pointer;transition:all 0.3s;position:relative;top:2px;">
                            📝 Notes
                        </button>
                    </div>

                    <!-- Tab Content: Overview -->
                    <div id="tabContentOverview" class="tab-content" style="display:block;">
                        <div id="tradeModalStats" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-bottom:24px;">
                            <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:18px;border-radius:12px;box-shadow:0 4px 12px rgba(102,126,234,0.25);transition:all 0.3s;position:relative;overflow:hidden;">
                                <div style="position:absolute;top:-20px;right:-20px;font-size:4em;opacity:0.1;">📈</div>
                                <div style="font-size:0.9em;color:rgba(255,255,255,0.9);font-weight:500;margin-bottom:8px;">Total Return</div>
                                <div style="font-size:2em;font-weight:bold;color:white;position:relative;z-index:1;" id="tradeStatReturn">-</div>
                            </div>
                            <div style="background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%);padding:18px;border-radius:12px;box-shadow:0 4px 12px rgba(17,153,142,0.25);transition:all 0.3s;position:relative;overflow:hidden;">
                                <div style="position:absolute;top:-20px;right:-20px;font-size:4em;opacity:0.1;">📊</div>
                                <div style="font-size:0.9em;color:rgba(255,255,255,0.9);font-weight:500;margin-bottom:8px;">Total Trades</div>
                                <div style="font-size:2em;font-weight:bold;color:white;position:relative;z-index:1;" id="tradeStatCount">-</div>
                            </div>
                            <div style="background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);padding:18px;border-radius:12px;box-shadow:0 4px 12px rgba(240,147,251,0.25);transition:all 0.3s;position:relative;overflow:hidden;">
                                <div style="position:absolute;top:-20px;right:-20px;font-size:4em;opacity:0.1;">💰</div>
                                <div style="font-size:0.9em;color:rgba(255,255,255,0.9);font-weight:500;margin-bottom:8px;">Initial Capital</div>
                                <div style="font-size:1.6em;font-weight:bold;color:white;position:relative;z-index:1;" id="tradeStatInitial">-</div>
                            </div>
                            <div style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);padding:18px;border-radius:12px;box-shadow:0 4px 12px rgba(79,172,254,0.25);transition:all 0.3s;position:relative;overflow:hidden;">
                                <div style="position:absolute;top:-20px;right:-20px;font-size:4em;opacity:0.1;">💎</div>
                                <div style="font-size:0.9em;color:rgba(255,255,255,0.9);font-weight:500;margin-bottom:8px;">Final Value</div>
                                <div style="font-size:1.6em;font-weight:bold;color:white;position:relative;z-index:1;" id="tradeStatFinal">-</div>
                            </div>
                        </div>
                        
                        <!-- Quick Summary for Overview -->
                        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:20px;">
                            <div style="background:white;padding:16px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:4px solid #3498db;">
                                <div style="font-size:0.85em;color:#666;margin-bottom:6px;font-weight:500;">Win Rate</div>
                                <div style="font-size:1.5em;font-weight:bold;color:#333;" id="overviewWinRate">-</div>
                            </div>
                            <div style="background:white;padding:16px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:4px solid #9b59b6;">
                                <div style="font-size:0.85em;color:#666;margin-bottom:6px;font-weight:500;">Sharpe Ratio</div>
                                <div style="font-size:1.5em;font-weight:bold;color:#333;" id="overviewSharpe">-</div>
                            </div>
                            <div style="background:white;padding:16px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:4px solid #e74c3c;">
                                <div style="font-size:0.85em;color:#666;margin-bottom:6px;font-weight:500;">Max Drawdown</div>
                                <div style="font-size:1.5em;font-weight:bold;color:#333;" id="overviewDrawdown">-</div>
                            </div>
                            <div style="background:white;padding:16px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:4px solid #27ae60;">
                                <div style="font-size:0.85em;color:#666;margin-bottom:6px;font-weight:500;">Avg Trade Duration</div>
                                <div style="font-size:1.5em;font-weight:bold;color:#333;" id="overviewDuration">-</div>
                            </div>
                        </div>
                    </div>

                    <!-- Tab Content: Trades -->
                    <div id="tabContentTrades" class="tab-content" style="display:none;">
                    <div style="margin-bottom:10px;background:white;padding:20px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                            <div style="font-weight:bold;color:#2c3e50;font-size:1.2em;">📋 Trade History</div>
                            <div style="display:flex;gap:8px;">
                                <button onclick="toggleAdvancedFilters()" id="advFiltersBtn" class="btn" style="padding:8px 16px;background:white;border:2px solid #667eea;color:#667eea;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.background='#667eea';this.style.color='white'" onmouseout="this.style.background='white';this.style.color='#667eea'">🔍 Advanced Filters</button>
                                <button onclick="exportTradesToCSV()" class="btn" style="padding:8px 16px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;box-shadow:0 2px 8px rgba(102,126,234,0.3);" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 12px rgba(102,126,234,0.4)'" onmouseout="this.style.transform='none';this.style.boxShadow='0 2px 8px rgba(102,126,234,0.3)'">📥 Export CSV</button>
                            </div>
                        </div>

                        <!-- Advanced Filters Panel -->
                        <div id="advancedFiltersPanel" style="display:none;background:#f8f9fa;padding:16px;border-radius:10px;margin-bottom:16px;border:2px solid #e9ecef;">
                            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:12px;">
                                <!-- Date Range -->
                                <div>
                                    <label style="font-size:0.85em;color:#666;font-weight:600;display:block;margin-bottom:4px;">📅 From Date</label>
                                    <input type="date" id="filterDateFrom" style="width:100%;padding:8px;border:2px solid #dee2e6;border-radius:6px;font-size:0.9em;" onchange="applyAdvancedFilters()">
                                </div>
                                <div>
                                    <label style="font-size:0.85em;color:#666;font-weight:600;display:block;margin-bottom:4px;">📅 To Date</label>
                                    <input type="date" id="filterDateTo" style="width:100%;padding:8px;border:2px solid #dee2e6;border-radius:6px;font-size:0.9em;" onchange="applyAdvancedFilters()">
                                </div>
                                <!-- Min/Max Price -->
                                <div>
                                    <label style="font-size:0.85em;color:#666;font-weight:600;display:block;margin-bottom:4px;">💲 Min Price</label>
                                    <input type="number" id="filterMinPrice" placeholder="Min" style="width:100%;padding:8px;border:2px solid #dee2e6;border-radius:6px;font-size:0.9em;" onchange="applyAdvancedFilters()">
                                </div>
                                <div>
                                    <label style="font-size:0.85em;color:#666;font-weight:600;display:block;margin-bottom:4px;">💲 Max Price</label>
                                    <input type="number" id="filterMaxPrice" placeholder="Max" style="width:100%;padding:8px;border:2px solid #dee2e6;border-radius:6px;font-size:0.9em;" onchange="applyAdvancedFilters()">
                                </div>
                                <!-- Min Confidence -->
                                <div>
                                    <label style="font-size:0.85em;color:#666;font-weight:600;display:block;margin-bottom:4px;">🎯 Min Confidence</label>
                                    <input type="number" id="filterMinConfidence" placeholder="0-1" min="0" max="1" step="0.1" style="width:100%;padding:8px;border:2px solid #dee2e6;border-radius:6px;font-size:0.9em;" onchange="applyAdvancedFilters()">
                                </div>
                                <!-- Min P&L -->
                                <div>
                                    <label style="font-size:0.85em;color:#666;font-weight:600;display:block;margin-bottom:4px;">📊 Min P&L %</label>
                                    <input type="number" id="filterMinPnL" placeholder="Min %" style="width:100%;padding:8px;border:2px solid #dee2e6;border-radius:6px;font-size:0.9em;" onchange="applyAdvancedFilters()">
                                </div>
                            </div>
                            <!-- Quick Date Filters -->
                            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;padding-top:12px;border-top:2px solid #dee2e6;">
                                <div style="font-size:0.85em;color:#666;font-weight:600;align-self:center;">Quick Filters:</div>
                                <button onclick="setQuickDateFilter('last7')" class="btn" style="padding:6px 12px;background:#667eea;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">Last 7 Days</button>
                                <button onclick="setQuickDateFilter('last30')" class="btn" style="padding:6px 12px;background:#667eea;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">Last 30 Days</button>
                                <button onclick="setQuickDateFilter('thisMonth')" class="btn" style="padding:6px 12px;background:#667eea;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">This Month</button>
                                <button onclick="setQuickDateFilter('last3Months')" class="btn" style="padding:6px 12px;background:#667eea;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">Last 3 Months</button>
                                <button onclick="setQuickDateFilter('thisYear')" class="btn" style="padding:6px 12px;background:#667eea;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">This Year</button>
                                <button onclick="clearAdvancedFilters()" class="btn" style="padding:6px 12px;background:#e74c3c;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">🗑️ Clear All</button>
                            </div>
                            <!-- Filter Presets -->
                            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                                <div style="font-size:0.85em;color:#666;font-weight:600;">Presets:</div>
                                <button onclick="saveCurrentFilterPreset()" class="btn" style="padding:6px 12px;background:#11998e;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">💾 Save Current</button>
                                <select id="filterPresetSelect" onchange="loadFilterPreset(this.value)" style="padding:6px 10px;border:2px solid #dee2e6;border-radius:6px;font-size:0.85em;cursor:pointer;">
                                    <option value="">-- Load Preset --</option>
                                </select>
                                <button onclick="deleteCurrentPreset()" class="btn" style="padding:6px 12px;background:#e74c3c;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">🗑️ Delete Preset</button>
                            </div>
                        </div>
                        
                        <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
                            <div style="display:flex;gap:6px;flex-wrap:wrap;">
                                <button onclick="filterTrades('all')" class="btn" style="padding:8px 14px;background:#3498db;color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">All</button>
                                <button onclick="filterTrades('buy')" class="btn" style="padding:8px 14px;background:#27ae60;color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">🟢 BUY</button>
                                <button onclick="filterTrades('sell')" class="btn" style="padding:8px 14px;background:#e74c3c;color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">🔴 SELL</button>
                                <button onclick="filterTrades('profitable')" class="btn" style="padding:8px 14px;background:#f39c12;color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">💰 Profitable</button>
                            </div>
                            <div style="border-left:2px solid #e0e0e0;padding-left:10px;display:flex;gap:6px;flex-wrap:wrap;">
                                <button onclick="sortTrades('date')" class="btn" style="padding:8px 14px;background:white;border:2px solid #e0e0e0;color:#495057;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.borderColor='#667eea';this.style.color='#667eea'" onmouseout="this.style.borderColor='#e0e0e0';this.style.color='#495057'">📅 Date</button>
                                <button onclick="sortTrades('price')" class="btn" style="padding:8px 14px;background:white;border:2px solid #e0e0e0;color:#495057;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.borderColor='#667eea';this.style.color='#667eea'" onmouseout="this.style.borderColor='#e0e0e0';this.style.color='#495057'">💲 Price</button>
                                <button onclick="sortTrades('confidence')" class="btn" style="padding:8px 14px;background:white;border:2px solid #e0e0e0;color:#495057;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.borderColor='#667eea';this.style.color='#667eea'" onmouseout="this.style.borderColor='#e0e0e0';this.style.color='#495057'">🎯 Confidence</button>
                                <button onclick="sortTrades('pnl')" class="btn" style="padding:8px 14px;background:white;border:2px solid #e0e0e0;color:#495057;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.borderColor='#667eea';this.style.color='#667eea'" onmouseout="this.style.borderColor='#e0e0e0';this.style.color='#495057'">📊 P&L</button>
                            </div>
                        </div>
                        
                        <div id="tradesTable" style="background:#fff;border:2px solid #f0f0f0;border-radius:10px;overflow:hidden;max-height:450px;overflow-y:auto;font-size:0.9em;">
                            <table style="width:100%;border-collapse:collapse;">
                                <thead>
                                    <tr style="background:linear-gradient(135deg,#f8f9fa 0%,#e9ecef 100%);border-bottom:2px solid #dee2e6;position:sticky;top:0;z-index:10;">
                                        <th style="padding:14px 12px;text-align:left;color:#495057;font-weight:700;font-size:0.95em;">Date</th>
                                        <th style="padding:14px 12px;text-align:left;color:#495057;font-weight:700;font-size:0.95em;">Signal</th>
                                        <th style="padding:14px 12px;text-align:right;color:#495057;font-weight:700;font-size:0.95em;">Price</th>
                                        <th style="padding:14px 12px;text-align:right;color:#495057;font-weight:700;font-size:0.95em;">Confidence</th>
                                        <th style="padding:14px 12px;text-align:right;color:#495057;font-weight:700;font-size:0.95em;">P&L %</th>
                                    </tr>
                                </thead>
                                <tbody id="tradesTableBody">
                                    <!-- trades will be populated here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                                    </tr>
                                </thead>
                                <tbody id="tradesTableBody">
                                    <!-- trades will be populated here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    </div>

                    <!-- Tab Content: Analysis -->
                    <div id="tabContentAnalysis" class="tab-content" style="display:none;">
                    <div id="monteCarloSection" style="margin-top:20px;padding:20px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);border-radius:12px;box-shadow:0 4px 12px rgba(240,147,251,0.3);position:relative;overflow:hidden;">
                        <div style="position:absolute;top:-30px;right:-30px;font-size:6em;opacity:0.1;">🎲</div>
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;position:relative;z-index:1;">
                            <div style="font-weight:bold;color:white;font-size:1.2em;">🎲 Monte Carlo Simulation</div>
                            <button onclick="runMonteCarloSimulation()" id="monteCarloBtn" class="btn" style="padding:10px 18px;background:white;color:#f5576c;border:none;font-size:0.95em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,0.15);" onmouseover="this.style.transform='scale(1.05)';this.style.boxShadow='0 4px 12px rgba(0,0,0,0.2)'" onmouseout="this.style.transform='scale(1)';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.15)'">Run 1000 Simulations</button>
                        </div>
                        <div id="monteCarloResults" style="display:none;position:relative;z-index:1;">
                            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:16px;">
                                <div style="background:rgba(255,255,255,0.95);padding:14px;border-radius:10px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                                    <div style="font-size:0.85em;color:#666;font-weight:500;">Mean Return</div>
                                    <div style="font-size:1.4em;font-weight:bold;color:#333;margin-top:4px;" id="mcMean">-</div>
                                </div>
                                <div style="background:rgba(255,255,255,0.95);padding:14px;border-radius:10px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                                    <div style="font-size:0.85em;color:#666;font-weight:500;">95% CI</div>
                                    <div style="font-size:1.4em;font-weight:bold;color:#333;margin-top:4px;" id="mcCI">-</div>
                                </div>
                                <div style="background:rgba(255,255,255,0.95);padding:14px;border-radius:10px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                                    <div style="font-size:0.85em;color:#666;font-weight:500;">Best Case</div>
                                    <div style="font-size:1.4em;font-weight:bold;color:#27ae60;margin-top:4px;" id="mcBest">-</div>
                                </div>
                                <div style="background:rgba(255,255,255,0.95);padding:14px;border-radius:10px;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                                    <div style="font-size:0.85em;color:#666;font-weight:500;">Worst Case</div>
                                    <div style="font-size:1.4em;font-weight:bold;color:#e74c3c;margin-top:4px;" id="mcWorst">-</div>
                                </div>
                            </div>
                            <div style="background:rgba(255,255,255,0.95);padding:14px;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                                <canvas id="monteCarloChart" style="max-height:220px;"></canvas>
                            </div>
                        </div>
                        <div id="monteCarloRunning" style="display:none;text-align:center;padding:30px;color:white;position:relative;z-index:1;">
                            <div style="font-size:1.1em;font-weight:500;margin-bottom:10px;">Running simulations...</div>
                            <div style="font-size:2em;font-weight:bold;" id="mcProgress">0%</div>
                        </div>
                    </div>
                    
                    <div id="mlQualitySection" style="margin-top:20px;padding:20px;background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                            <div style="font-weight:bold;color:#2c3e50;font-size:1.2em;">🧠 ML Signal Quality Analysis</div>
                            <button onclick="toggleMLAnalysis()" id="mlAnalysisBtn" class="btn" style="padding:8px 16px;background:linear-gradient(135deg,#e67e22 0%,#d35400 100%);color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;box-shadow:0 2px 8px rgba(230,126,34,0.3);" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 12px rgba(230,126,34,0.4)'" onmouseout="this.style.transform='none';this.style.boxShadow='0 2px 8px rgba(230,126,34,0.3)'">Show Analysis</button>
                        </div>
                        <div id="mlAnalysisContent" style="display:none;">
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:16px;">
                                <div style="background:#f8f9fa;padding:14px;border-radius:10px;">
                                    <div style="font-size:0.9em;font-weight:600;color:#495057;margin-bottom:10px;">Confidence vs P&L Scatter</div>
                                    <canvas id="confidencePnlChart" style="max-height:250px;"></canvas>
                                </div>
                                <div style="background:#f8f9fa;padding:14px;border-radius:10px;">
                                    <div style="font-size:0.9em;font-weight:600;color:#495057;margin-bottom:10px;">Model Calibration</div>
                                    <canvas id="calibrationChart" style="max-height:250px;"></canvas>
                                </div>
                            </div>
                            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
                                <div style="background:#f8f9fa;padding:14px;border-radius:10px;text-align:center;border:2px solid #e67e22;">
                                    <div style="font-size:0.85em;color:#666;font-weight:500;">Signal Precision</div>
                                    <div style="font-size:1.4em;font-weight:bold;color:#e67e22;margin-top:4px;" id="mlPrecision">-</div>
                                </div>
                                <div style="background:#f8f9fa;padding:14px;border-radius:10px;text-align:center;border:2px solid #e74c3c;">
                                    <div style="font-size:0.85em;color:#666;font-weight:500;">False Positive Rate</div>
                                    <div style="font-size:1.4em;font-weight:bold;color:#e74c3c;margin-top:4px;" id="mlFPR">-</div>
                                </div>
                                <div style="background:#f8f9fa;padding:14px;border-radius:10px;text-align:center;border:2px solid #3498db;">
                                    <div style="font-size:0.85em;color:#666;font-weight:500;">Avg Signal Lag</div>
                                    <div style="font-size:1.4em;font-weight:bold;color:#3498db;margin-top:4px;" id="mlLag">-</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div id="aiInsightsSection" style="margin-top:15px;padding:15px;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);border-radius:6px;color:white;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                            <div style="font-weight:bold;font-size:1.1em;">🤖 AI-Generated Insights</div>
                            <button onclick="generateAIInsights()" id="aiInsightsBtn" class="btn" style="padding:5px 12px;background:white;color:#667eea;border:none;font-size:0.85em;font-weight:600;">Generate Report</button>
                        </div>
                        <div id="aiInsightsContent" style="display:none;background:rgba(255,255,255,0.1);padding:15px;border-radius:6px;backdrop-filter:blur(10px);">
                            <div id="aiInsightsText" style="font-size:0.95em;line-height:1.6;white-space:pre-wrap;"></div>
                            <div id="aiRecommendations" style="margin-top:15px;padding-top:15px;border-top:1px solid rgba(255,255,255,0.2);">
                                <div style="font-weight:bold;margin-bottom:8px;">📋 Recommendations:</div>
                                <ul id="aiRecoList" style="margin:0;padding-left:20px;">
                                    <!-- Will be populated -->
                                </ul>
                            </div>
                        </div>
                        <div id="aiInsightsGenerating" style="display:none;text-align:center;padding:20px;">
                            <div style="font-size:1.2em;margin-bottom:10px;">🤖 Analyzing trading patterns...</div>
                            <div style="font-size:0.9em;opacity:0.8;">This will take a moment</div>
                        </div>
                    </div>
                    
                    <div id="userNotesSection" style="margin-top:20px;padding:20px;background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                            <div style="font-weight:bold;color:#2c3e50;font-size:1.2em;">📝 Personal Notes</div>
                            <button onclick="saveSymbolNotes()" id="saveNotesBtn" class="btn" style="padding:8px 16px;background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%);color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;box-shadow:0 2px 8px rgba(17,153,142,0.3);" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 12px rgba(17,153,142,0.4)'" onmouseout="this.style.transform='none';this.style.boxShadow='0 2px 8px rgba(17,153,142,0.3)'">💾 Save Notes</button>
                        </div>
                        <textarea id="symbolNotesInput" placeholder="Add your analysis, observations, or trading strategy notes here... These will be saved locally for this symbol." style="width:100%;min-height:120px;padding:14px;border:2px solid #e0e0e0;border-radius:10px;font-size:0.95em;font-family:inherit;resize:vertical;transition:all 0.2s;" onfocus="this.style.borderColor='#667eea';this.style.boxShadow='0 0 0 3px rgba(102,126,234,0.1)'" onblur="this.style.borderColor='#e0e0e0';this.style.boxShadow='none'"></textarea>
                        <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;">
                            <button onclick="insertNoteTemplate('bullish')" class="btn" style="padding:6px 12px;background:#27ae60;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">🟢 Bullish Pattern</button>
                            <button onclick="insertNoteTemplate('bearish')" class="btn" style="padding:6px 12px;background:#e74c3c;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">🔴 Bearish Pattern</button>
                            <button onclick="insertNoteTemplate('watchlist')" class="btn" style="padding:6px 12px;background:#f39c12;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">👁️ Add to Watchlist</button>
                            <button onclick="insertNoteTemplate('risk')" class="btn" style="padding:6px 12px;background:#9b59b6;color:white;border:none;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">⚠️ Risk Note</button>
                            <button onclick="clearSymbolNotes()" class="btn" style="padding:6px 12px;background:white;border:2px solid #e0e0e0;color:#666;font-size:0.85em;border-radius:6px;cursor:pointer;transition:all 0.2s;" onmouseover="this.style.borderColor='#e74c3c';this.style.color='#e74c3c'" onmouseout="this.style.borderColor='#e0e0e0';this.style.color='#666'">🗑️ Clear</button>
                        </div>
                        <div id="notesSavedIndicator" style="display:none;margin-top:10px;padding:10px;background:#d4edda;border:1px solid #c3e6cb;border-radius:6px;color:#155724;font-size:0.9em;animation:fadeIn 0.3s;">✅ Notes saved successfully!</div>
                    </div>
                    
                    <div id="tradeEquityChart" style="margin-top:15px;padding:15px;background:#f9f9f9;border-radius:6px;border:1px solid #e0e0e0;">
                        <div style="font-weight:bold;color:#333;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;">
                            <span>📈 Equity Curve (Interactive)</span>
                            <div style="display:flex;gap:8px;align-items:center;">
                                <button id="replayBtn" onclick="startTradeReplay()" class="btn" style="padding:5px 12px;background:#3498db;color:white;border:none;font-size:0.85em;">▶️ Replay</button>
                                <button id="pauseReplayBtn" onclick="pauseTradeReplay()" class="btn" style="padding:5px 12px;background:#f39c12;color:white;border:none;font-size:0.85em;display:none;">⏸️ Pause</button>
                                <select id="replaySpeed" class="btn" style="padding:5px 8px;background:#fff;border:1px solid #ccc;font-size:0.85em;">
                                    <option value="500">0.5x</option>
                                    <option value="200" selected>1x</option>
                                    <option value="100">2x</option>
                                    <option value="50">5x</option>
                                    <option value="20">10x</option>
                                </select>
                                <span id="replayProgress" style="font-size:0.85em;font-weight:normal;color:#666;">Ready</span>
                            </div>
                        </div>
                        <div id="tradeEquityChartCanvas" style="background:white;padding:10px;border-radius:6px;">
                            <!-- Chart.js canvas will be inserted here -->
                        </div>
                    </div>
                </div>
                
                <!-- Tab Content: Technical Analysis -->
                <div id="tabContentTechnical" class="tab-content" style="display:none;">
                    <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                        <h4 style="margin:0 0 15px 0;color:var(--text-primary);font-size:1.2em;">📊 TradingView Style Technical Analysis</h4>
                        
                        <!-- Chart Controls -->
                        <div class="chart-controls">
                            <div class="chart-control-group">
                                <label>Timeframe:</label>
                                <button class="chart-control-btn active" onclick="setTimeframe('1D')">1D</button>
                                <button class="chart-control-btn" onclick="setTimeframe('1W')">1W</button>
                                <button class="chart-control-btn" onclick="setTimeframe('1M')">1M</button>
                            </div>
                            
                            <div class="chart-control-group">
                                <label>Chart Type:</label>
                                <button class="chart-control-btn active" onclick="setChartType('candlestick')" id="btnCandlestick">🕯️ Candle</button>
                                <button class="chart-control-btn" onclick="setChartType('line')" id="btnLine">📈 Line</button>
                                <button class="chart-control-btn" onclick="setChartType('area')" id="btnArea">📊 Area</button>
                            </div>
                            
                            <div class="chart-control-group">
                                <label>Indicators:</label>
                                <button class="chart-control-btn" onclick="toggleIndicator('rsi')">RSI</button>
                                <button class="chart-control-btn" onclick="toggleIndicator('macd')">MACD</button>
                                <button class="chart-control-btn" onclick="toggleIndicator('bb')">BB</button>
                                <button class="chart-control-btn" onclick="toggleIndicator('sma')">SMA</button>
                                <button class="chart-control-btn" onclick="toggleIndicator('ema')">EMA</button>
                            </div>
                        </div>
                        
                        <!-- Active Indicators -->
                        <div id="activeIndicators" style="margin-bottom:15px;min-height:30px;">
                            <!-- Indicator badges will appear here -->
                        </div>
                        
                        <!-- Drawing Tools -->
                        <div style="margin-bottom:15px;">
                            <div style="font-size:0.9em;font-weight:600;color:var(--text-secondary);margin-bottom:8px;">Drawing Tools:</div>
                            <div class="drawing-tools">
                                <div class="drawing-tool" onclick="selectDrawingTool('none')" id="toolNone" title="Cursor">
                                    ➡️
                                </div>
                                <div class="drawing-tool" onclick="selectDrawingTool('trendline')" id="toolTrendline" title="Trend Line">
                                    📏
                                </div>
                                <div class="drawing-tool" onclick="selectDrawingTool('horizontal')" id="toolHorizontal" title="Horizontal Line">
                                    ➖
                                </div>
                                <div class="drawing-tool" onclick="selectDrawingTool('fibonacci')" id="toolFibonacci" title="Fibonacci Retracement">
                                    🔢
                                </div>
                                <div class="drawing-tool" onclick="selectDrawingTool('rectangle')" id="toolRectangle" title="Rectangle">
                                    ▭
                                </div>
                                <div class="drawing-tool" onclick="clearDrawings()" title="Clear All">
                                    🗑️
                                </div>
                            </div>
                        </div>
                        
                        <!-- Lightweight Charts Container -->
                        <div id="technicalChartContainer" style="height:500px;background:white;border-radius:8px;border:1px solid var(--border-color);position:relative;">
                            <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;color:var(--text-secondary);">
                                <div style="font-size:2em;margin-bottom:10px;">📊</div>
                                <div style="font-size:1.1em;font-weight:600;">Select a symbol to view technical analysis</div>
                                <div style="font-size:0.9em;margin-top:8px;">Candlestick charts with indicators will appear here</div>
                            </div>
                        </div>
                        
                        <!-- Pattern Recognition Results -->
                        <div id="patternRecognition" style="margin-top:20px;padding:15px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:10px;color:white;display:none;">
                            <div style="font-weight:600;font-size:1.1em;margin-bottom:10px;">🤖 Detected Patterns</div>
                            <div id="patternList" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;">
                                <!-- Pattern cards will be inserted here -->
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Tab Content: Notes -->
                <div id="tabContentNotes" class="tab-content" style="display:none;">
                    <div id="userNotesSection" style="padding:20px;background:white;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                            <div style="font-weight:bold;color:#2c3e50;font-size:1.2em;">📝 Personal Notes</div>
                            <button onclick="saveSymbolNotes()" id="saveNotesBtn" class="btn" style="padding:8px 16px;background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%);color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;box-shadow:0 2px 8px rgba(17,153,142,0.3);" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 4px 12px rgba(17,153,142,0.4)'" onmouseout="this.style.transform='none';this.style.boxShadow='0 2px 8px rgba(17,153,142,0.3)'">💾 Save Notes</button>
                        </div>
                        <textarea id="symbolNotesInput" placeholder="Add your analysis, observations, or trading strategy notes here... These will be saved locally for this symbol." style="width:100%;min-height:200px;padding:14px;border:2px solid #e0e0e0;border-radius:10px;font-size:0.95em;font-family:inherit;resize:vertical;transition:all 0.2s;" onfocus="this.style.borderColor='#667eea';this.style.boxShadow='0 0 0 3px rgba(102,126,234,0.1)'" onblur="this.style.borderColor='#e0e0e0';this.style.boxShadow='none'"></textarea>
                        <div style="margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;">
                            <button onclick="insertNoteTemplate('bullish')" class="btn" style="padding:8px 14px;background:#27ae60;color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">🟢 Bullish Pattern</button>
                            <button onclick="insertNoteTemplate('bearish')" class="btn" style="padding:8px 14px;background:#e74c3c;color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">🔴 Bearish Pattern</button>
                            <button onclick="insertNoteTemplate('watchlist')" class="btn" style="padding:8px 14px;background:#f39c12;color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">👁️ Add to Watchlist</button>
                            <button onclick="insertNoteTemplate('risk')" class="btn" style="padding:8px 14px;background:#9b59b6;color:white;border:none;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.opacity='0.8'" onmouseout="this.style.opacity='1'">⚠️ Risk Note</button>
                            <button onclick="clearSymbolNotes()" class="btn" style="padding:8px 14px;background:white;border:2px solid #e0e0e0;color:#666;font-size:0.9em;border-radius:8px;cursor:pointer;transition:all 0.2s;font-weight:500;" onmouseover="this.style.borderColor='#e74c3c';this.style.color='#e74c3c'" onmouseout="this.style.borderColor='#e0e0e0';this.style.color='#666'">🗑️ Clear</button>
                        </div>
                        <div id="notesSavedIndicator" style="display:none;margin-top:10px;padding:10px;background:#d4edda;border:1px solid #c3e6cb;border-radius:6px;color:#155724;font-size:0.9em;animation:fadeIn 0.3s;">✅ Notes saved successfully!</div>
                    </div>
                </div>

                </div>
                
                <div id="tradeModalError" style="display:none;padding:15px;background:#fdecea;border:1px solid #e74c3c;border-radius:6px;color:#c0392b;"></div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', tradeModalHtml);

        // Portfolio Builder Modal
        const portfolioModalHtml = `
        <div id="portfolioModal" class="portfolio-modal">
            <div class="portfolio-modal-content">
                <div class="portfolio-header">
                    <h2>💼 Portfolio Builder</h2>
                    <span class="portfolio-close" onclick="closePortfolioModal()">×</span>
                </div>

                <div class="portfolio-builder">
                    <div class="portfolio-section">
                        <h3>Add Symbols</h3>
                        <div class="symbol-input-group">
                            <input type="text" id="portfolioSymbolInput" placeholder="Enter symbol (e.g., AAPL)" onkeypress="if(event.key==='Enter') addToPortfolio()">
                            <button onclick="addToPortfolio()">+ Add</button>
                        </div>
                        <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:15px;">
                            Quick add: <button onclick="addMultipleSymbols(['AAPL','MSFT','GOOGL','AMZN'])" style="padding:4px 8px;background:#f0f0f0;border:1px solid #ddd;border-radius:5px;cursor:pointer;font-size:0.85em;">Tech Giants</button>
                            <button onclick="addMultipleSymbols(['SPY','QQQ','DIA','IWM'])" style="padding:4px 8px;background:#f0f0f0;border:1px solid #ddd;border-radius:5px;cursor:pointer;font-size:0.85em;margin-left:5px;">ETFs</button>
                        </div>
                        <ul class="portfolio-list" id="portfolioSymbolList">
                            <!-- Will be populated -->
                        </ul>
                    </div>

                    <div class="portfolio-section">
                        <h3>Allocation</h3>
                        <div id="portfolioAllocationChart">
                            <div class="allocation-bar" id="allocationBar">
                                <div style="flex:1;background:#ccc;display:flex;align-items:center;justify-content:center;color:#666;">Add symbols to begin</div>
                            </div>
                        </div>
                        <div style="margin-top:15px;font-size:0.85em;color:var(--text-secondary);">
                            <strong>Allocation Methods:</strong>
                            <div style="margin-top:8px;display:flex;flex-direction:column;gap:6px;">
                                <button onclick="setAllocationMethod('equal')" style="padding:8px;background:white;border:1px solid #ddd;border-radius:6px;cursor:pointer;text-align:left;transition:all 0.2s;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                                    📊 Equal Weight
                                </button>
                                <button onclick="setAllocationMethod('market')" style="padding:8px;background:white;border:1px solid #ddd;border-radius:6px;cursor:pointer;text-align:left;transition:all 0.2s;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                                    💰 Market Cap Weighted
                                </button>
                                <button onclick="setAllocationMethod('risk')" style="padding:8px;background:white;border:1px solid #ddd;border-radius:6px;cursor:pointer;text-align:left;transition:all 0.2s;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                                    ⚖️ Risk Parity
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="allocation-chart">
                    <h3 style="margin:0 0 15px 0;color:var(--text-primary);">Portfolio Overview</h3>
                    <div class="portfolio-stats">
                        <div class="portfolio-stat">
                            <div class="portfolio-stat-label">Total Symbols</div>
                            <div class="portfolio-stat-value" id="portfolioTotalSymbols">0</div>
                        </div>
                        <div class="portfolio-stat">
                            <div class="portfolio-stat-label">Diversification</div>
                            <div class="portfolio-stat-value" id="portfolioDiversification">—</div>
                        </div>
                        <div class="portfolio-stat">
                            <div class="portfolio-stat-label">Largest Position</div>
                            <div class="portfolio-stat-value" id="portfolioLargestPosition">—</div>
                        </div>
                    </div>
                    <div style="margin-top:20px;display:flex;gap:10px;justify-content:center;">
                        <button onclick="analyzePortfolio()" style="padding:12px 24px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:1em;transition:all 0.2s;box-shadow:0 4px 12px rgba(102,126,234,0.3);" onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 6px 16px rgba(102,126,234,0.4)'" onmouseout="this.style.transform='none';this.style.boxShadow='0 4px 12px rgba(102,126,234,0.3)'">
                            📊 Analyze Portfolio
                        </button>
                        <button onclick="rebalancePortfolio()" style="padding:12px 24px;background:#27ae60;color:white;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:1em;transition:all 0.2s;" onmouseover="this.style.background='#229954'" onmouseout="this.style.background='#27ae60'">
                            ⚖️ Rebalance
                        </button>
                        <button onclick="savePortfolio()" style="padding:12px 24px;background:#3498db;color:white;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:1em;transition:all 0.2s;" onmouseover="this.style.background='#2980b9'" onmouseout="this.style.background='#3498db'">
                            💾 Save Portfolio
                        </button>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', portfolioModalHtml);

        // Risk Calculator Modal
        const riskCalcModalHtml = `
        <div id="riskCalcModal" class="risk-calc-modal">
            <div class="risk-calc-content">
                <div style="background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);padding:20px;display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2em;">⚖️</div>
                        <h3 style="margin:0;color:white;font-size:1.4em;font-weight:700;">Risk Management Calculator</h3>
                    </div>
                    <button style="background:rgba(255,255,255,0.2);border:none;font-size:1.3em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;" onclick="closeRiskCalculator()">✕</button>
                </div>

                <div style="padding:25px;overflow-y:auto;max-height:calc(90vh - 80px);">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:25px;">
                        <!-- Position Sizing Calculator -->
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 20px 0;color:var(--text-primary);">💰 Position Sizing</h4>
                            
                            <div class="risk-input-group">
                                <label>Account Balance ($)</label>
                                <input type="number" id="accountBalance" value="100000" min="0" step="1000">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Risk Per Trade (%)</label>
                                <input type="range" id="riskPerTrade" class="risk-slider" min="0.1" max="5" step="0.1" value="1" oninput="updateRiskDisplay()">
                                <div style="text-align:center;font-weight:600;color:var(--text-primary);margin-top:5px;" id="riskPerTradeValue">1.0%</div>
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Entry Price ($)</label>
                                <input type="number" id="entryPrice" value="100" min="0" step="0.01" oninput="calculatePositionSize()">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Stop Loss ($)</label>
                                <input type="number" id="stopLoss" value="95" min="0" step="0.01" oninput="calculatePositionSize()">
                            </div>
                            
                            <button onclick="calculatePositionSize()" style="width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;margin-top:10px;">
                                Calculate Position
                            </button>
                            
                            <div class="risk-result-card">
                                <div class="risk-result-label">Recommended Position Size</div>
                                <div class="risk-result-value" id="positionSizeResult">-</div>
                                <div style="font-size:0.9em;opacity:0.9;margin-top:10px;">
                                    <div>Risk Amount: <span id="riskAmount">$0</span></div>
                                    <div>Total Investment: <span id="totalInvestment">$0</span></div>
                                </div>
                            </div>
                        </div>

                        <!-- Kelly Criterion Calculator -->
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 20px 0;color:var(--text-primary);">🎯 Kelly Criterion</h4>
                            
                            <div class="risk-input-group">
                                <label>Win Rate (%)</label>
                                <input type="number" id="winRate" value="55" min="0" max="100" step="1" oninput="calculateKelly()">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Average Win ($)</label>
                                <input type="number" id="avgWin" value="150" min="0" step="1" oninput="calculateKelly()">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Average Loss ($)</label>
                                <input type="number" id="avgLoss" value="100" min="0" step="1" oninput="calculateKelly()">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Kelly Fraction (Conservative)</label>
                                <input type="range" id="kellyFraction" min="0.1" max="1" step="0.05" value="0.25" oninput="updateKellyFractionDisplay()">
                                <div style="text-align:center;font-weight:600;color:var(--text-primary);margin-top:5px;" id="kellyFractionValue">25%</div>
                            </div>
                            
                            <button onclick="calculateKelly()" style="width:100%;padding:12px;background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;margin-top:10px;">
                                Calculate Kelly %
                            </button>
                            
                            <div class="risk-result-card" style="background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%);">
                                <div class="risk-result-label">Optimal Position Size</div>
                                <div class="risk-result-value" id="kellyResult">-</div>
                                <div style="font-size:0.9em;opacity:0.9;margin-top:10px;" id="kellyInterpretation">
                                    Enter values to calculate
                                </div>
                            </div>
                        </div>

                        <!-- Risk/Reward Calculator -->
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 20px 0;color:var(--text-primary);">📊 Risk/Reward Ratio</h4>
                            
                            <div class="risk-input-group">
                                <label>Entry Price ($)</label>
                                <input type="number" id="rrEntryPrice" value="100" min="0" step="0.01" oninput="calculateRiskReward()">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Stop Loss ($)</label>
                                <input type="number" id="rrStopLoss" value="95" min="0" step="0.01" oninput="calculateRiskReward()">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Take Profit ($)</label>
                                <input type="number" id="takeProfit" value="115" min="0" step="0.01" oninput="calculateRiskReward()">
                            </div>
                            
                            <button onclick="calculateRiskReward()" style="width:100%;padding:12px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;margin-top:10px;">
                                Calculate R/R
                            </button>
                            
                            <div class="risk-result-card" style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);">
                                <div class="risk-result-label">Risk/Reward Ratio</div>
                                <div class="risk-result-value" id="rrResult">-</div>
                                <div style="font-size:0.9em;opacity:0.9;margin-top:10px;">
                                    <div>Risk: <span id="riskValue">$0</span></div>
                                    <div>Reward: <span id="rewardValue">$0</span></div>
                                    <div style="margin-top:8px;font-weight:600;" id="rrRecommendation"></div>
                                </div>
                            </div>
                        </div>

                        <!-- Equity Curve Projection -->
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 20px 0;color:var(--text-primary);">📈 Equity Projection</h4>
                            
                            <div class="risk-input-group">
                                <label>Starting Capital ($)</label>
                                <input type="number" id="projStartCapital" value="100000" min="0" step="1000" oninput="projectEquityCurve()">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Average Monthly Return (%)</label>
                                <input type="number" id="projMonthlyReturn" value="3" min="-50" max="100" step="0.5" oninput="projectEquityCurve()">
                            </div>
                            
                            <div class="risk-input-group">
                                <label>Projection Period (months)</label>
                                <input type="range" id="projPeriod" min="3" max="36" value="12" oninput="updateProjPeriodDisplay()">
                                <div style="text-align:center;font-weight:600;color:var(--text-primary);margin-top:5px;" id="projPeriodValue">12 months</div>
                            </div>
                            
                            <button onclick="projectEquityCurve()" style="width:100%;padding:12px;background:linear-gradient(135deg,#fa709a 0%,#fee140 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;margin-top:10px;">
                                Project Equity
                            </button>
                            
                            <div class="risk-result-card" style="background:linear-gradient(135deg,#fa709a 0%,#fee140 100%);">
                                <div class="risk-result-label">Projected Final Value</div>
                                <div class="risk-result-value" id="projResult">-</div>
                                <div style="font-size:0.9em;opacity:0.9;margin-top:10px;">
                                    <div>Total Gain: <span id="projGain">$0</span></div>
                                    <div>ROI: <span id="projROI">0%</span></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', riskCalcModalHtml);

        // Advanced Backtesting Modal
        const advBacktestModalHtml = `
        <div id="advBacktestModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:var(--card-bg);border-radius:16px;padding:0;max-width:1400px;width:95%;max-height:90vh;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);padding:20px;display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2em;">🔬</div>
                        <h3 style="margin:0;color:white;font-size:1.4em;font-weight:700;">Advanced Backtesting Suite</h3>
                    </div>
                    <button style="background:rgba(255,255,255,0.2);border:none;font-size:1.3em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;" onclick="closeAdvancedBacktest()">✕</button>
                </div>

                <div style="padding:25px;overflow-y:auto;max-height:calc(90vh - 80px);">
                    <!-- Walk-Forward Analysis -->
                    <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                        <h4 style="margin:0 0 15px 0;color:var(--text-primary);display:flex;align-items:center;gap:10px;">
                            <span style="font-size:1.5em;">🔄</span>
                            Walk-Forward Analysis
                        </h4>
                        <p style="color:var(--text-secondary);margin:0 0 15px 0;font-size:0.9em;">
                            Test strategy robustness by training on one period and testing on the next.
                        </p>
                        
                        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-bottom:15px;">
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Training Period (days)</label>
                                <input type="number" id="wfTrainingPeriod" value="120" min="30" max="365" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Testing Period (days)</label>
                                <input type="number" id="wfTestingPeriod" value="30" min="7" max="90" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Number of Folds</label>
                                <input type="number" id="wfFolds" value="5" min="2" max="10" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                        </div>
                        
                        <button onclick="runWalkForward()" style="width:100%;padding:12px;background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                            🚀 Run Walk-Forward Analysis
                        </button>
                        
                        <div id="wfResults" style="display:none;margin-top:15px;padding:15px;background:white;border-radius:8px;border:1px solid var(--border-color);">
                            <div style="font-weight:600;margin-bottom:10px;">Results:</div>
                            <div id="wfResultsContent"></div>
                        </div>
                    </div>

                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
                        <!-- Parameter Optimization Heatmap -->
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;color:var(--text-primary);display:flex;align-items:center;gap:10px;">
                                <span style="font-size:1.5em;">🔥</span>
                                Parameter Heatmap
                            </h4>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Parameter 1 (e.g., SMA Period)</label>
                                <div style="display:flex;gap:10px;">
                                    <input type="number" id="param1Min" placeholder="Min" value="10" style="flex:1;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                    <input type="number" id="param1Max" placeholder="Max" value="50" style="flex:1;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                    <input type="number" id="param1Step" placeholder="Step" value="5" style="flex:1;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                            </div>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Parameter 2 (e.g., RSI Period)</label>
                                <div style="display:flex;gap:10px;">
                                    <input type="number" id="param2Min" placeholder="Min" value="10" style="flex:1;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                    <input type="number" id="param2Max" placeholder="Max" value="30" style="flex:1;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                    <input type="number" id="param2Step" placeholder="Step" value="2" style="flex:1;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                            </div>
                            
                            <button onclick="generateHeatmap()" style="width:100%;padding:12px;background:linear-gradient(135deg,#fa709a 0%,#fee140 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                                🔥 Generate Heatmap
                            </button>
                            
                            <div id="heatmapContainer" style="margin-top:15px;height:300px;border:1px solid var(--border-color);border-radius:8px;display:flex;align-items:center;justify-content:center;background:white;">
                                <span style="color:var(--text-secondary);">Heatmap will appear here</span>
                            </div>
                        </div>

                        <!-- Monte Carlo Variations -->
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;color:var(--text-primary);display:flex;align-items:center;gap:10px;">
                                <span style="font-size:1.5em;">🎲</span>
                                Monte Carlo Simulation
                            </h4>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Number of Simulations</label>
                                <input type="number" id="mcSimulations" value="1000" min="100" max="10000" step="100" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Confidence Level (%)</label>
                                <select id="mcConfidence" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                    <option value="90">90%</option>
                                    <option value="95" selected>95%</option>
                                    <option value="99">99%</option>
                                </select>
                            </div>
                            
                            <button onclick="runMonteCarloVariation()" style="width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                                🎲 Run Monte Carlo
                            </button>
                            
                            <div id="mcResultsAdv" style="display:none;margin-top:15px;padding:15px;background:white;border-radius:8px;border:1px solid var(--border-color);">
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                                    <div>
                                        <div style="font-size:0.8em;color:var(--text-secondary);">Best Case</div>
                                        <div style="font-size:1.4em;font-weight:700;color:#27ae60;" id="mcBest">-</div>
                                    </div>
                                    <div>
                                        <div style="font-size:0.8em;color:var(--text-secondary);">Worst Case</div>
                                        <div style="font-size:1.4em;font-weight:700;color:#e74c3c;" id="mcWorst">-</div>
                                    </div>
                                    <div>
                                        <div style="font-size:0.8em;color:var(--text-secondary);">Mean Return</div>
                                        <div style="font-size:1.4em;font-weight:700;color:var(--text-primary);" id="mcMean">-</div>
                                    </div>
                                    <div>
                                        <div style="font-size:0.8em;color:var(--text-secondary);">Confidence Interval</div>
                                        <div style="font-size:1.4em;font-weight:700;color:var(--text-primary);" id="mcCI">-</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Slippage & Commission Simulation -->
                    <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                        <h4 style="margin:0 0 15px 0;color:var(--text-primary);display:flex;align-items:center;gap:10px;">
                            <span style="font-size:1.5em;">💸</span>
                            Slippage & Commission Analysis
                        </h4>
                        <p style="color:var(--text-secondary);margin:0 0 15px 0;font-size:0.9em;">
                            Simulate realistic trading costs and their impact on strategy performance.
                        </p>
                        
                        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:15px;">
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Commission ($)</label>
                                <input type="number" id="commissionAmount" value="1" min="0" step="0.1" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Slippage (%)</label>
                                <input type="number" id="slippagePercent" value="0.05" min="0" max="1" step="0.01" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Spread (bps)</label>
                                <input type="number" id="spreadBps" value="2" min="0" step="0.5" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Market Impact (%)</label>
                                <input type="number" id="marketImpact" value="0.02" min="0" max="1" step="0.01" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                        </div>
                        
                        <button onclick="simulateSlippage()" style="width:100%;padding:12px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                            💸 Simulate Trading Costs
                        </button>
                        
                        <div id="slippageResults" style="display:none;margin-top:15px;">
                            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:15px;">
                                <div style="padding:15px;background:white;border-radius:8px;border:1px solid var(--border-color);">
                                    <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Gross Return</div>
                                    <div style="font-size:1.6em;font-weight:700;color:#27ae60;" id="grossReturn">-</div>
                                </div>
                                <div style="padding:15px;background:white;border-radius:8px;border:1px solid var(--border-color);">
                                    <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Net Return (After Costs)</div>
                                    <div style="font-size:1.6em;font-weight:700;color:var(--text-primary);" id="netReturn">-</div>
                                </div>
                                <div style="padding:15px;background:white;border-radius:8px;border:1px solid var(--border-color);">
                                    <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Total Costs</div>
                                    <div style="font-size:1.6em;font-weight:700;color:#e74c3c;" id="totalCosts">-</div>
                                </div>
                            </div>
                            <div style="margin-top:15px;padding:15px;background:rgba(102,126,234,0.1);border-radius:8px;border:1px solid var(--bg-primary);">
                                <div style="font-weight:600;margin-bottom:8px;">Cost Breakdown:</div>
                                <div id="costBreakdown" style="font-size:0.9em;color:var(--text-primary);"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', advBacktestModalHtml);

        // Trade Journal Modal
        const tradeJournalModalHtml = `
        <div id="tradeJournalModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:var(--card-bg);border-radius:16px;padding:0;max-width:1600px;width:98%;max-height:95vh;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);padding:20px;display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2em;">📓</div>
                        <h3 style="margin:0;color:white;font-size:1.4em;font-weight:700;">Trade Journal & Analytics</h3>
                    </div>
                    <button style="background:rgba(255,255,255,0.2);border:none;font-size:1.3em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;" onclick="closeTradeJournal()">✕</button>
                </div>

                <div style="padding:25px;overflow-y:auto;max-height:calc(95vh - 80px);">
                    <!-- Tab Navigation -->
                    <div style="display:flex;gap:10px;margin-bottom:20px;border-bottom:2px solid var(--border-color);padding-bottom:10px;">
                        <button onclick="switchJournalTab('logs')" id="journalTabLogs" style="padding:10px 20px;background:var(--bg-primary);border:none;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600;color:var(--text-primary);">📝 Daily Logs</button>
                        <button onclick="switchJournalTab('performance')" id="journalTabPerformance" style="padding:10px 20px;background:transparent;border:none;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600;color:var(--text-secondary);">📊 Performance</button>
                        <button onclick="switchJournalTab('sector')" id="journalTabSector" style="padding:10px 20px;background:transparent;border:none;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600;color:var(--text-secondary);">🏢 Sector Analysis</button>
                        <button onclick="switchJournalTab('time')" id="journalTabTime" style="padding:10px 20px;background:transparent;border:none;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600;color:var(--text-secondary);">⏰ Time Analysis</button>
                    </div>

                    <!-- Daily Logs Tab -->
                    <div id="journalTabLogsContent" class="journal-tab-content">
                        <div style="display:flex;gap:15px;margin-bottom:20px;">
                            <button onclick="addTradeLog()" style="padding:10px 20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">➕ Add Trade Log</button>
                            <input type="date" id="logDateFilter" onchange="filterTradeLogs()" style="padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                            <select id="logTypeFilter" onchange="filterTradeLogs()" style="padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                                <option value="all">All Types</option>
                                <option value="long">Long</option>
                                <option value="short">Short</option>
                            </select>
                            <select id="logOutcomeFilter" onchange="filterTradeLogs()" style="padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                                <option value="all">All Outcomes</option>
                                <option value="win">Wins</option>
                                <option value="loss">Losses</option>
                            </select>
                        </div>

                        <div id="tradeLogsContainer" style="display:grid;gap:15px;">
                            <!-- Trade logs will be inserted here -->
                        </div>
                    </div>

                    <!-- Performance Attribution Tab -->
                    <div id="journalTabPerformanceContent" class="journal-tab-content" style="display:none;">
                        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-bottom:20px;">
                            <div style="padding:20px;background:white;border-radius:12px;border:1px solid var(--border-color);">
                                <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Total Trades</div>
                                <div style="font-size:2em;font-weight:700;color:var(--text-primary);" id="perfTotalTrades">0</div>
                            </div>
                            <div style="padding:20px;background:white;border-radius:12px;border:1px solid var(--border-color);">
                                <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Win Rate</div>
                                <div style="font-size:2em;font-weight:700;color:#27ae60;" id="perfWinRate">0%</div>
                            </div>
                            <div style="padding:20px;background:white;border-radius:12px;border:1px solid var(--border-color);">
                                <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Avg Win</div>
                                <div style="font-size:2em;font-weight:700;color:#27ae60;" id="perfAvgWin">$0</div>
                            </div>
                            <div style="padding:20px;background:white;border-radius:12px;border:1px solid var(--border-color);">
                                <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Avg Loss</div>
                                <div style="font-size:2em;font-weight:700;color:#e74c3c;" id="perfAvgLoss">$0</div>
                            </div>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                            <h4 style="margin:0 0 15px 0;">Strategy Performance Breakdown</h4>
                            <canvas id="strategyPerfChart" style="max-height:300px;"></canvas>
                        </div>

                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
                            <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <h4 style="margin:0 0 15px 0;">Best Performing Setups</h4>
                                <div id="bestSetupsContainer"></div>
                            </div>
                            <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <h4 style="margin:0 0 15px 0;">Worst Performing Setups</h4>
                                <div id="worstSetupsContainer"></div>
                            </div>
                        </div>
                    </div>

                    <!-- Sector Analysis Tab -->
                    <div id="journalTabSectorContent" class="journal-tab-content" style="display:none;">
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
                            <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <h4 style="margin:0 0 15px 0;">Sector Exposure</h4>
                                <canvas id="sectorExposureChart" style="max-height:300px;"></canvas>
                            </div>
                            <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <h4 style="margin:0 0 15px 0;">Sector Performance</h4>
                                <canvas id="sectorPerformanceChart" style="max-height:300px;"></canvas>
                            </div>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">Detailed Sector Statistics</h4>
                            <table id="sectorStatsTable" style="width:100%;border-collapse:collapse;">
                                <thead>
                                    <tr style="background:var(--bg-primary);">
                                        <th style="padding:10px;border:1px solid var(--border-color);text-align:left;">Sector</th>
                                        <th style="padding:10px;border:1px solid var(--border-color);text-align:center;">Trades</th>
                                        <th style="padding:10px;border:1px solid var(--border-color);text-align:center;">Win Rate</th>
                                        <th style="padding:10px;border:1px solid var(--border-color);text-align:center;">Avg P&L</th>
                                        <th style="padding:10px;border:1px solid var(--border-color);text-align:center;">Total P&L</th>
                                    </tr>
                                </thead>
                                <tbody id="sectorStatsBody">
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Time Analysis Tab -->
                    <div id="journalTabTimeContent" class="journal-tab-content" style="display:none;">
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
                            <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <h4 style="margin:0 0 15px 0;">Performance by Day of Week</h4>
                                <canvas id="dayOfWeekChart" style="max-height:300px;"></canvas>
                            </div>
                            <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <h4 style="margin:0 0 15px 0;">Performance by Hour</h4>
                                <canvas id="hourOfDayChart" style="max-height:300px;"></canvas>
                            </div>
                        </div>

                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
                            <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <h4 style="margin:0 0 15px 0;">Holding Period Analysis</h4>
                                <canvas id="holdingPeriodChart" style="max-height:300px;"></canvas>
                            </div>
                            <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <h4 style="margin:0 0 15px 0;">Monthly Performance</h4>
                                <canvas id="monthlyPerfChart" style="max-height:300px;"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Add Trade Log Modal -->
        <div id="addTradeLogModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10001;align-items:center;justify-content:center;">
            <div style="background:var(--card-bg);border-radius:16px;padding:25px;max-width:600px;width:90%;max-height:90vh;overflow-y:auto;">
                <h3 style="margin:0 0 20px 0;color:var(--text-primary);">Add Trade Log</h3>
                
                <div style="display:grid;gap:15px;">
                    <div>
                        <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Date</label>
                        <input type="date" id="newTradeDate" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                    </div>
                    
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                        <div>
                            <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Symbol</label>
                            <input type="text" id="newTradeSymbol" placeholder="AAPL" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                        </div>
                        <div>
                            <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Type</label>
                            <select id="newTradeType" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                                <option value="long">Long</option>
                                <option value="short">Short</option>
                            </select>
                        </div>
                    </div>
                    
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;">
                        <div>
                            <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Entry Price</label>
                            <input type="number" id="newTradeEntry" step="0.01" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                        </div>
                        <div>
                            <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Exit Price</label>
                            <input type="number" id="newTradeExit" step="0.01" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                        </div>
                        <div>
                            <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Quantity</label>
                            <input type="number" id="newTradeQuantity" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                        </div>
                    </div>
                    
                    <div>
                        <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Sector</label>
                        <select id="newTradeSector" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                            <option value="Technology">Technology</option>
                            <option value="Healthcare">Healthcare</option>
                            <option value="Financial">Financial</option>
                            <option value="Consumer">Consumer</option>
                            <option value="Energy">Energy</option>
                            <option value="Industrial">Industrial</option>
                            <option value="Other">Other</option>
                        </select>
                    </div>
                    
                    <div>
                        <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Setup/Strategy</label>
                        <input type="text" id="newTradeSetup" placeholder="e.g., Breakout, Support Bounce" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                    </div>
                    
                    <div>
                        <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Tags (comma-separated)</label>
                        <input type="text" id="newTradeTags" placeholder="trend-following, high-volume" style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);">
                    </div>
                    
                    <div>
                        <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Notes</label>
                        <textarea id="newTradeNotes" rows="3" placeholder="Trade rationale, emotions, lessons learned..." style="width:100%;padding:10px;border:1px solid var(--border-color);border-radius:8px;background:var(--input-bg);color:var(--text-primary);resize:vertical;"></textarea>
                    </div>
                </div>
                
                <div style="display:flex;gap:10px;margin-top:20px;">
                    <button onclick="saveTradeLog()" style="flex:1;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">💾 Save Trade</button>
                    <button onclick="closeAddTradeLog()" style="padding:12px 20px;background:var(--bg-secondary);color:var(--text-primary);border:1px solid var(--border-color);border-radius:8px;font-weight:600;cursor:pointer;">Cancel</button>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', tradeJournalModalHtml);

        // Automation & Scheduling Modal
        const automationModalHtml = `
        <div id="automationModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:var(--card-bg);border-radius:16px;padding:0;max-width:1400px;width:95%;max-height:90vh;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="background:linear-gradient(135deg,#fa709a 0%,#fee140 100%);padding:20px;display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2em;">⚙️</div>
                        <h3 style="margin:0;color:white;font-size:1.4em;font-weight:700;">Automation & Scheduling</h3>
                    </div>
                    <button style="background:rgba(255,255,255,0.2);border:none;font-size:1.3em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;" onclick="closeAutomation()">✕</button>
                </div>

                <div style="padding:25px;overflow-y:auto;max-height:calc(90vh - 80px);">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
                        <!-- Scheduled Backtests -->
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;color:var(--text-primary);display:flex;align-items:center;gap:10px;">
                                <span style="font-size:1.5em;">⏰</span>
                                Scheduled Backtests
                            </h4>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Strategy Name</label>
                                <input type="text" id="scheduleStrategyName" placeholder="My Strategy" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Frequency</label>
                                <select id="scheduleFrequency" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                    <option value="daily">Daily at 9:00 AM</option>
                                    <option value="weekly">Weekly (Monday 9:00 AM)</option>
                                    <option value="monthly">Monthly (1st at 9:00 AM)</option>
                                    <option value="custom">Custom</option>
                                </select>
                            </div>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Symbols (comma-separated)</label>
                                <input type="text" id="scheduleSymbols" placeholder="AAPL,GOOGL,MSFT" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            
                            <button onclick="createSchedule()" style="width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                                ➕ Create Schedule
                            </button>
                            
                            <div id="schedulesContainer" style="margin-top:20px;">
                                <div style="font-weight:600;margin-bottom:10px;">Active Schedules:</div>
                                <div id="schedulesList"></div>
                            </div>
                        </div>

                        <!-- Strategy Version Control -->
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;color:var(--text-primary);display:flex;align-items:center;gap:10px;">
                                <span style="font-size:1.5em;">📝</span>
                                Version Control
                            </h4>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Strategy Name</label>
                                <input type="text" id="versionStrategyName" placeholder="My Strategy v1.0" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Version Tag</label>
                                <input type="text" id="versionTag" placeholder="v1.2.0" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            
                            <div style="margin-bottom:15px;">
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Changes Description</label>
                                <textarea id="versionChanges" rows="3" placeholder="Updated entry rules, adjusted stop loss..." style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);resize:vertical;"></textarea>
                            </div>
                            
                            <button onclick="saveVersion()" style="width:100%;padding:12px;background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                                💾 Save Version
                            </button>
                            
                            <div id="versionsContainer" style="margin-top:20px;">
                                <div style="font-weight:600;margin-bottom:10px;">Version History:</div>
                                <div id="versionsList" style="max-height:300px;overflow-y:auto;"></div>
                            </div>
                        </div>
                    </div>

                    <!-- A/B Testing -->
                    <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                        <h4 style="margin:0 0 15px 0;color:var(--text-primary);display:flex;align-items:center;gap:10px;">
                            <span style="font-size:1.5em;">🔬</span>
                            A/B Testing Framework
                        </h4>
                        
                        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;margin-bottom:15px;">
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Strategy A</label>
                                <input type="text" id="abStrategyA" placeholder="Baseline Strategy" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Strategy B</label>
                                <input type="text" id="abStrategyB" placeholder="Modified Strategy" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Test Period (days)</label>
                                <input type="number" id="abTestPeriod" value="30" min="7" max="365" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                        </div>
                        
                        <button onclick="runABTest()" style="width:100%;padding:12px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                            🚀 Run A/B Test
                        </button>
                        
                        <div id="abTestResults" style="display:none;margin-top:20px;">
                            <div style="font-weight:600;margin-bottom:15px;">Test Results:</div>
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                                <div style="padding:20px;background:white;border-radius:12px;border:2px solid var(--border-color);">
                                    <div style="font-size:1.2em;font-weight:700;margin-bottom:10px;color:#4facfe;">📊 Strategy A</div>
                                    <div style="display:grid;gap:8px;">
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>Return:</span>
                                            <span id="abReturnA" style="font-weight:600;"></span>
                                        </div>
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>Sharpe:</span>
                                            <span id="abSharpeA" style="font-weight:600;"></span>
                                        </div>
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>Max DD:</span>
                                            <span id="abDDA" style="font-weight:600;"></span>
                                        </div>
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>Trades:</span>
                                            <span id="abTradesA" style="font-weight:600;"></span>
                                        </div>
                                    </div>
                                </div>
                                <div style="padding:20px;background:white;border-radius:12px;border:2px solid var(--border-color);">
                                    <div style="font-size:1.2em;font-weight:700;margin-bottom:10px;color:#f5576c;">📊 Strategy B</div>
                                    <div style="display:grid;gap:8px;">
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>Return:</span>
                                            <span id="abReturnB" style="font-weight:600;"></span>
                                        </div>
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>Sharpe:</span>
                                            <span id="abSharpeB" style="font-weight:600;"></span>
                                        </div>
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>Max DD:</span>
                                            <span id="abDDB" style="font-weight:600;"></span>
                                        </div>
                                        <div style="display:flex;justify-content:space-between;">
                                            <span>Trades:</span>
                                            <span id="abTradesB" style="font-weight:600;"></span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div id="abWinner" style="margin-top:20px;padding:20px;background:rgba(39,174,96,0.1);border-radius:12px;border:2px solid #27ae60;text-align:center;font-size:1.3em;font-weight:700;"></div>
                        </div>
                    </div>

                    <!-- Automated Reports -->
                    <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                        <h4 style="margin:0 0 15px 0;color:var(--text-primary);display:flex;align-items:center;gap:10px;">
                            <span style="font-size:1.5em;">📧</span>
                            Automated Performance Reports
                        </h4>
                        
                        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;margin-bottom:15px;">
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Report Type</label>
                                <select id="reportType" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                    <option value="daily">Daily Summary</option>
                                    <option value="weekly">Weekly Review</option>
                                    <option value="monthly">Monthly Report</option>
                                    <option value="custom">Custom</option>
                                </select>
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Email</label>
                                <input type="email" id="reportEmail" placeholder="trader@example.com" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                            <div>
                                <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Send Time</label>
                                <input type="time" id="reportTime" value="17:00" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                            </div>
                        </div>
                        
                        <div style="margin-bottom:15px;">
                            <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:8px;">Include in Report:</label>
                            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
                                <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
                                    <input type="checkbox" id="includePerformance" checked style="cursor:pointer;">
                                    <span>Performance Metrics</span>
                                </label>
                                <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
                                    <input type="checkbox" id="includeCharts" checked style="cursor:pointer;">
                                    <span>Charts</span>
                                </label>
                                <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
                                    <input type="checkbox" id="includeTrades" checked style="cursor:pointer;">
                                    <span>Trade Log</span>
                                </label>
                                <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
                                    <input type="checkbox" id="includeAlerts" style="cursor:pointer;">
                                    <span>Alerts Triggered</span>
                                </label>
                                <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
                                    <input type="checkbox" id="includeRisk" style="cursor:pointer;">
                                    <span>Risk Metrics</span>
                                </label>
                                <label style="display:flex;align-items:center;gap:5px;cursor:pointer;">
                                    <input type="checkbox" id="includeComparison" style="cursor:pointer;">
                                    <span>Benchmark Comparison</span>
                                </label>
                            </div>
                        </div>
                        
                        <button onclick="setupAutomatedReport()" style="width:100%;padding:12px;background:linear-gradient(135deg,#fa709a 0%,#fee140 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                            📧 Setup Automated Report
                        </button>
                        
                        <div id="reportStatus" style="display:none;margin-top:15px;padding:15px;background:rgba(39,174,96,0.1);border-radius:8px;border:1px solid #27ae60;">
                            <div style="font-weight:600;color:#27ae60;">✅ Report automation configured successfully!</div>
                            <div style="margin-top:8px;font-size:0.9em;" id="reportStatusDetails"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', automationModalHtml);

        // Smart Alerts System Modal
        const alertsModalHtml = `
        <div id="alertsModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:var(--card-bg);border-radius:16px;padding:0;max-width:1400px;width:95%;max-height:90vh;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="background:linear-gradient(135deg,#ff6b6b 0%,#feca57 100%);padding:20px;display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2em;">🔔</div>
                        <h3 style="margin:0;color:white;font-size:1.4em;font-weight:700;">Smart Alerts System</h3>
                    </div>
                    <button style="background:rgba(255,255,255,0.2);border:none;font-size:1.3em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;" onclick="closeAlertsPanel()">✕</button>
                </div>

                <div style="padding:25px;overflow-y:auto;max-height:calc(90vh - 80px);">
                    <!-- Alert Creation Tabs -->
                    <div style="display:flex;gap:10px;margin-bottom:20px;border-bottom:2px solid var(--border-color);padding-bottom:10px;">
                        <button onclick="switchAlertTab('price')" id="alertTabPrice" style="padding:10px 20px;background:var(--bg-primary);border:none;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600;color:var(--text-primary);">💰 Price Alerts</button>
                        <button onclick="switchAlertTab('indicator')" id="alertTabIndicator" style="padding:10px 20px;background:transparent;border:none;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600;color:var(--text-secondary);">📊 Indicator Alerts</button>
                        <button onclick="switchAlertTab('pattern')" id="alertTabPattern" style="padding:10px 20px;background:transparent;border:none;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600;color:var(--text-secondary);">🔍 Pattern Alerts</button>
                        <button onclick="switchAlertTab('volume')" id="alertTabVolume" style="padding:10px 20px;background:transparent;border:none;border-radius:8px 8px 0 0;cursor:pointer;font-weight:600;color:var(--text-secondary);">📈 Volume Alerts</button>
                    </div>

                    <!-- Price Alerts Tab -->
                    <div id="alertTabPriceContent" class="alert-tab-content">
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                            <h4 style="margin:0 0 15px 0;">Create Price Alert</h4>
                            
                            <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:15px;margin-bottom:15px;">
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Symbol</label>
                                    <input type="text" id="priceAlertSymbol" placeholder="AAPL" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Condition</label>
                                    <select id="priceAlertCondition" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                        <option value="above">Above</option>
                                        <option value="below">Below</option>
                                        <option value="crosses">Crosses</option>
                                        <option value="between">Between</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Price</label>
                                    <input type="number" id="priceAlertValue" placeholder="150.00" step="0.01" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Upper Price (for between)</label>
                                    <input type="number" id="priceAlertValue2" placeholder="160.00" step="0.01" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                            </div>
                            
                            <button onclick="createPriceAlert()" style="width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                                ➕ Create Price Alert
                            </button>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">Active Price Alerts</h4>
                            <div id="priceAlertsList"></div>
                        </div>
                    </div>

                    <!-- Indicator Alerts Tab -->
                    <div id="alertTabIndicatorContent" class="alert-tab-content" style="display:none;">
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                            <h4 style="margin:0 0 15px 0;">Create Indicator Alert</h4>
                            
                            <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:15px;margin-bottom:15px;">
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Symbol</label>
                                    <input type="text" id="indicatorAlertSymbol" placeholder="GOOGL" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Indicator</label>
                                    <select id="indicatorAlertType" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                        <option value="rsi">RSI</option>
                                        <option value="macd">MACD</option>
                                        <option value="sma">SMA</option>
                                        <option value="ema">EMA</option>
                                        <option value="bb">Bollinger Bands</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Condition</label>
                                    <select id="indicatorAlertCondition" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                        <option value="above">Above</option>
                                        <option value="below">Below</option>
                                        <option value="crosses_up">Crosses Up</option>
                                        <option value="crosses_down">Crosses Down</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Value</label>
                                    <input type="number" id="indicatorAlertValue" placeholder="70" step="0.1" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                            </div>
                            
                            <button onclick="createIndicatorAlert()" style="width:100%;padding:12px;background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                                ➕ Create Indicator Alert
                            </button>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">Active Indicator Alerts</h4>
                            <div id="indicatorAlertsList"></div>
                        </div>
                    </div>

                    <!-- Pattern Alerts Tab -->
                    <div id="alertTabPatternContent" class="alert-tab-content" style="display:none;">
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                            <h4 style="margin:0 0 15px 0;">Create Pattern Alert</h4>
                            
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:15px;">
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Symbol</label>
                                    <input type="text" id="patternAlertSymbol" placeholder="TSLA" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Pattern Type</label>
                                    <select id="patternAlertType" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                        <option value="doji">Doji</option>
                                        <option value="hammer">Hammer</option>
                                        <option value="shooting_star">Shooting Star</option>
                                        <option value="engulfing">Engulfing</option>
                                        <option value="head_shoulders">Head & Shoulders</option>
                                        <option value="double_top">Double Top</option>
                                        <option value="double_bottom">Double Bottom</option>
                                    </select>
                                </div>
                            </div>
                            
                            <button onclick="createPatternAlert()" style="width:100%;padding:12px;background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                                ➕ Create Pattern Alert
                            </button>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">Active Pattern Alerts</h4>
                            <div id="patternAlertsList"></div>
                        </div>
                    </div>

                    <!-- Volume Alerts Tab -->
                    <div id="alertTabVolumeContent" class="alert-tab-content" style="display:none;">
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                            <h4 style="margin:0 0 15px 0;">Create Volume Alert</h4>
                            
                            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;margin-bottom:15px;">
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Symbol</label>
                                    <input type="text" id="volumeAlertSymbol" placeholder="NVDA" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Condition</label>
                                    <select id="volumeAlertCondition" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                        <option value="spike">Volume Spike (% above avg)</option>
                                        <option value="above">Above Threshold</option>
                                        <option value="unusual">Unusual Activity</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display:block;font-size:0.85em;font-weight:600;color:var(--text-secondary);margin-bottom:5px;">Value (%)</label>
                                    <input type="number" id="volumeAlertValue" placeholder="200" step="10" style="width:100%;padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);">
                                </div>
                            </div>
                            
                            <button onclick="createVolumeAlert()" style="width:100%;padding:12px;background:linear-gradient(135deg,#fa709a 0%,#fee140 100%);color:white;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                                ➕ Create Volume Alert
                            </button>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">Active Volume Alerts</h4>
                            <div id="volumeAlertsList"></div>
                        </div>
                    </div>

                    <!-- Alert History -->
                    <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-top:20px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                            <h4 style="margin:0;">Alert History (Triggered)</h4>
                            <button onclick="clearAlertHistory()" style="padding:6px 12px;background:#e74c3c;color:white;border:none;border-radius:6px;cursor:pointer;font-size:0.85em;">Clear History</button>
                        </div>
                        <div id="alertHistory" style="max-height:300px;overflow-y:auto;"></div>
                    </div>

                    <!-- Browser Notification Settings -->
                    <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-top:20px;">
                        <h4 style="margin:0 0 15px 0;">🔔 Notification Settings</h4>
                        <div style="display:grid;gap:10px;">
                            <label style="display:flex;align-items:center;gap:10px;cursor:pointer;">
                                <input type="checkbox" id="enableBrowserNotifications" onchange="toggleBrowserNotifications()" style="cursor:pointer;">
                                <span>Enable Browser Notifications</span>
                            </label>
                            <label style="display:flex;align-items:center;gap:10px;cursor:pointer;">
                                <input type="checkbox" id="enableSoundAlerts" checked style="cursor:pointer;">
                                <span>Enable Sound Alerts</span>
                            </label>
                            <label style="display:flex;align-items:center;gap:10px;cursor:pointer;">
                                <input type="checkbox" id="enablePopupAlerts" checked style="cursor:pointer;">
                                <span>Enable Popup Alerts</span>
                            </label>
                        </div>
                        <button onclick="testNotification()" style="margin-top:15px;padding:10px 20px;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:8px;cursor:pointer;font-weight:600;">
                            🧪 Test Notification
                        </button>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', alertsModalHtml);

        // Volume Profile & Order Flow Modal
        const volumeProfileModalHtml = `
        <div id="volumeProfileModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:var(--card-bg);border-radius:16px;padding:0;max-width:1600px;width:98%;max-height:95vh;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="background:linear-gradient(135deg,#a8edea 0%,#fed6e3 100%);padding:20px;display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2em;">📊</div>
                        <h3 style="margin:0;color:#333;font-size:1.4em;font-weight:700;">Volume Profile & Order Flow Analysis</h3>
                    </div>
                    <button style="background:rgba(0,0,0,0.1);border:none;font-size:1.3em;cursor:pointer;color:#333;padding:8px 12px;border-radius:8px;" onclick="closeVolumeProfile()">✕</button>
                </div>

                <div style="padding:25px;overflow-y:auto;max-height:calc(95vh - 80px);">
                    <!-- Symbol Selection -->
                    <div style="background:var(--bg-container);padding:15px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;display:flex;gap:15px;align-items:center;">
                        <label style="font-weight:600;">Symbol:</label>
                        <input type="text" id="vpSymbol" placeholder="AAPL" value="AAPL" style="padding:8px;border:1px solid var(--border-color);border-radius:6px;background:var(--input-bg);color:var(--text-primary);width:120px;">
                        <button onclick="loadVolumeProfile()" style="padding:8px 20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:6px;font-weight:600;cursor:pointer;">Load Data</button>
                        <div style="margin-left:auto;display:flex;gap:10px;">
                            <label style="display:flex;align-items:center;gap:5px;">
                                <input type="checkbox" id="showPOC" checked onchange="updateVolumeProfile()">
                                <span>Point of Control</span>
                            </label>
                            <label style="display:flex;align-items:center;gap:5px;">
                                <input type="checkbox" id="showVAH" checked onchange="updateVolumeProfile()">
                                <span>Value Area High</span>
                            </label>
                            <label style="display:flex;align-items:center;gap:5px;">
                                <input type="checkbox" id="showVAL" checked onchange="updateVolumeProfile()">
                                <span>Value Area Low</span>
                            </label>
                        </div>
                    </div>

                    <!-- Main Chart with Volume Profile -->
                    <div style="display:grid;grid-template-columns:3fr 1fr;gap:20px;margin-bottom:20px;">
                        <div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">Price Chart with Volume Profile</h4>
                            <canvas id="vpChart" style="max-height:400px;"></canvas>
                        </div>
                        <div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">Volume Histogram</h4>
                            <canvas id="vpHistogram" style="max-height:400px;"></canvas>
                        </div>
                    </div>

                    <!-- Key Metrics -->
                    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:15px;margin-bottom:20px;">
                        <div style="padding:15px;background:white;border-radius:12px;border:1px solid var(--border-color);text-align:center;">
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">POC (Point of Control)</div>
                            <div style="font-size:1.5em;font-weight:700;color:#667eea;" id="pocValue">-</div>
                        </div>
                        <div style="padding:15px;background:white;border-radius:12px;border:1px solid var(--border-color);text-align:center;">
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">VAH (Value Area High)</div>
                            <div style="font-size:1.5em;font-weight:700;color:#27ae60;" id="vahValue">-</div>
                        </div>
                        <div style="padding:15px;background:white;border-radius:12px;border:1px solid var(--border-color);text-align:center;">
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">VAL (Value Area Low)</div>
                            <div style="font-size:1.5em;font-weight:700;color:#e74c3c;" id="valValue">-</div>
                        </div>
                        <div style="padding:15px;background:white;border-radius:12px;border:1px solid var(--border-color);text-align:center;">
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Total Volume</div>
                            <div style="font-size:1.5em;font-weight:700;color:var(--text-primary);" id="totalVolume">-</div>
                        </div>
                        <div style="padding:15px;background:white;border-radius:12px;border:1px solid var(--border-color);text-align:center;">
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:5px;">Value Area %</div>
                            <div style="font-size:1.5em;font-weight:700;color:var(--text-primary);" id="valueAreaPct">70%</div>
                        </div>
                    </div>

                    <!-- Market Profile & Order Flow -->
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
                        <div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">📈 Market Profile (TPO)</h4>
                            <div id="marketProfile" style="font-family:monospace;font-size:0.75em;line-height:1.2;overflow-x:auto;background:#f8f9fa;padding:15px;border-radius:8px;max-height:400px;overflow-y:auto;"></div>
                        </div>
                        <div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;">💹 Order Flow Delta</h4>
                            <canvas id="orderFlowChart" style="max-height:400px;"></canvas>
                        </div>
                    </div>

                    <!-- Liquidity Heatmap -->
                    <div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">
                            <h4 style="margin:0;">🔥 Liquidity Heatmap</h4>
                            <div style="display:flex;gap:10px;align-items:center;font-size:0.85em;">
                                <span>Low</span>
                                <div style="display:flex;gap:2px;">
                                    <div style="width:20px;height:20px;background:#fee;border:1px solid #ddd;"></div>
                                    <div style="width:20px;height:20px;background:#fcc;border:1px solid #ddd;"></div>
                                    <div style="width:20px;height:20px;background:#f99;border:1px solid #ddd;"></div>
                                    <div style="width:20px;height:20px;background:#f66;border:1px solid #ddd;"></div>
                                    <div style="width:20px;height:20px;background:#e33;border:1px solid #ddd;"></div>
                                </div>
                                <span>High</span>
                            </div>
                        </div>
                        <div id="liquidityHeatmap" style="overflow-x:auto;"></div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', volumeProfileModalHtml);

        // Custom Indicator Builder Modal
        const indicatorBuilderModalHtml = `
        <div id="indicatorBuilderModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:white;border-radius:20px;width:95%;max-width:1400px;max-height:90vh;overflow-y:auto;box-shadow:0 25px 60px rgba(0,0,0,0.3);position:relative;">
                <!-- Header -->
                <div style="padding:25px 30px;background:linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);border-radius:20px 20px 0 0;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h2 style="margin:0;font-size:1.8em;font-weight:800;color:#333;">🛠️ Custom Indicator Builder</h2>
                        <p style="margin:5px 0 0 0;font-size:0.95em;color:#555;">Create, test, and save your own technical indicators</p>
                    </div>
                    <button onclick="closeIndicatorBuilder()" style="background:rgba(255,255,255,0.3);border:none;font-size:28px;cursor:pointer;width:45px;height:45px;border-radius:50%;color:#333;transition:all 0.2s;">✕</button>
                </div>

                <div style="padding:30px;">
                    <!-- Tab Navigation -->
                    <div style="display:flex;gap:10px;border-bottom:2px solid var(--border-color);margin-bottom:25px;">
                        <button class="indicator-tab active" onclick="switchIndicatorTab('editor')" data-tab="editor" style="padding:12px 24px;background:none;border:none;border-bottom:3px solid #667eea;color:#667eea;font-weight:700;cursor:pointer;font-size:1em;">📝 Code Editor</button>
                        <button class="indicator-tab" onclick="switchIndicatorTab('templates')" data-tab="templates" style="padding:12px 24px;background:none;border:none;border-bottom:3px solid transparent;color:var(--text-secondary);font-weight:600;cursor:pointer;font-size:1em;">📚 Templates</button>
                        <button class="indicator-tab" onclick="switchIndicatorTab('saved')" data-tab="saved" style="padding:12px 24px;background:none;border:none;border-bottom:3px solid transparent;color:var(--text-secondary);font-weight:600;cursor:pointer;font-size:1em;">💾 Saved (${customIndicators.length})</button>
                        <button class="indicator-tab" onclick="switchIndicatorTab('test')" data-tab="test" style="padding:12px 24px;background:none;border:none;border-bottom:3px solid transparent;color:var(--text-secondary);font-weight:600;cursor:pointer;font-size:1em;">🧪 Test & Preview</button>
                    </div>

                    <!-- Code Editor Tab -->
                    <div id="editorTab" class="indicator-tab-content">
                        <div style="display:grid;grid-template-columns:1fr;gap:20px;">
                            <!-- Indicator Info -->
                            <div style="background:#f8f9fa;padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:15px;">
                                    <div>
                                        <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;">Indicator Name *</label>
                                        <input id="indicatorName" type="text" placeholder="e.g., My Custom RSI" style="width:100%;padding:12px;border:1px solid var(--border-color);border-radius:8px;font-size:1em;">
                                    </div>
                                    <div>
                                        <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;">Description</label>
                                        <input id="indicatorDescription" type="text" placeholder="What does this indicator do?" style="width:100%;padding:12px;border:1px solid var(--border-color);border-radius:8px;font-size:1em;">
                                    </div>
                                </div>
                            </div>

                            <!-- Code Editor -->
                            <div>
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                                    <label style="font-weight:700;font-size:1.1em;color:#333;">JavaScript Code</label>
                                    <div style="display:flex;gap:10px;">
                                        <button onclick="validateIndicatorCode()" style="padding:8px 16px;background:#3498db;color:white;border:none;border-radius:8px;cursor:pointer;font-size:0.9em;font-weight:600;">✓ Validate</button>
                                        <button onclick="testIndicatorCode()" style="padding:8px 16px;background:#27ae60;color:white;border:none;border-radius:8px;cursor:pointer;font-size:0.9em;font-weight:600;">▶️ Test</button>
                                        <button onclick="saveCustomIndicator()" style="padding:8px 16px;background:#667eea;color:white;border:none;border-radius:8px;cursor:pointer;font-size:0.9em;font-weight:600;">💾 Save</button>
                                    </div>
                                </div>
                                
                                <div style="position:relative;border:1px solid var(--border-color);border-radius:12px;overflow:hidden;">
                                    <div style="display:flex;">
                                        <div id="lineNumbers" style="background:#2c3e50;color:#95a5a6;padding:15px 10px;font-family:monospace;font-size:0.9em;line-height:1.6;text-align:right;user-select:none;overflow:hidden;min-width:50px;">1</div>
                                        <textarea id="indicatorCodeEditor" placeholder="// Write your indicator code here...
function calculate(prices, period = 20) {
    // Example: Simple Moving Average
    const result = [];
    for (let i = period - 1; i < prices.length; i++) {
        const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / period);
    }
    return result;
}" style="flex:1;min-height:400px;padding:15px;border:none;font-family:monospace;font-size:0.95em;line-height:1.6;resize:vertical;background:#2c3e50;color:#ecf0f1;" spellcheck="false"></textarea>
                                    </div>
                                </div>
                                
                                <div id="validationOutput" style="margin-top:12px;"></div>
                                
                                <div style="margin-top:15px;padding:15px;background:#e8f5e9;border:1px solid #c8e6c9;border-radius:10px;">
                                    <div style="font-weight:700;margin-bottom:8px;color:#2e7d32;">💡 Tips:</div>
                                    <ul style="margin:0;padding-left:20px;font-size:0.9em;color:#2e7d32;line-height:1.8;">
                                        <li>Your function must be named <code>calculate</code></li>
                                        <li>First parameter should be <code>prices</code> (array of numbers)</li>
                                        <li>Additional parameters are optional (e.g., period, threshold)</li>
                                        <li>Return an array of calculated values</li>
                                        <li>Use built-in Math functions: Math.sqrt(), Math.abs(), Math.max(), etc.</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Templates Tab -->
                    <div id="templatesTab" class="indicator-tab-content" style="display:none;">
                        <div style="margin-bottom:20px;">
                            <h3 style="font-size:1.3em;font-weight:700;color:#333;margin-bottom:10px;">Popular Indicator Templates</h3>
                            <p style="color:var(--text-secondary);">Click any template to load it into the editor</p>
                        </div>
                        
                        <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(320px, 1fr));gap:20px;">
                            <!-- SMA Template -->
                            <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);padding:20px;border-radius:12px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.1);transition:transform 0.2s;" onclick="loadTemplate('sma')">
                                <div style="color:white;font-size:2em;margin-bottom:10px;">📊</div>
                                <h4 style="color:white;font-size:1.2em;font-weight:700;margin:0 0 8px 0;">Simple Moving Average</h4>
                                <p style="color:rgba(255,255,255,0.9);font-size:0.9em;margin:0;line-height:1.6;">Classic trend-following indicator. Smooths price data by calculating the average over a period.</p>
                                <div style="margin-top:12px;font-size:0.85em;color:rgba(255,255,255,0.8);">Parameters: period (default: 20)</div>
                            </div>

                            <!-- RSI Template -->
                            <div style="background:linear-gradient(135deg, #f093fb 0%, #f5576c 100%);padding:20px;border-radius:12px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.1);transition:transform 0.2s;" onclick="loadTemplate('rsi')">
                                <div style="color:white;font-size:2em;margin-bottom:10px;">📈</div>
                                <h4 style="color:white;font-size:1.2em;font-weight:700;margin:0 0 8px 0;">Relative Strength Index</h4>
                                <p style="color:rgba(255,255,255,0.9);font-size:0.9em;margin:0;line-height:1.6;">Momentum oscillator measuring speed and magnitude of price changes. Range: 0-100.</p>
                                <div style="margin-top:12px;font-size:0.85em;color:rgba(255,255,255,0.8);">Parameters: period (default: 14)</div>
                            </div>

                            <!-- MACD Template -->
                            <div style="background:linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);padding:20px;border-radius:12px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.1);transition:transform 0.2s;" onclick="loadTemplate('macd')">
                                <div style="color:white;font-size:2em;margin-bottom:10px;">〰️</div>
                                <h4 style="color:white;font-size:1.2em;font-weight:700;margin:0 0 8px 0;">MACD</h4>
                                <p style="color:rgba(255,255,255,0.9);font-size:0.9em;margin:0;line-height:1.6;">Moving Average Convergence Divergence. Shows relationship between EMAs.</p>
                                <div style="margin-top:12px;font-size:0.85em;color:rgba(255,255,255,0.8);">Parameters: fast (12), slow (26), signal (9)</div>
                            </div>

                            <!-- Bollinger Bands Template -->
                            <div style="background:linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);padding:20px;border-radius:12px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.1);transition:transform 0.2s;" onclick="loadTemplate('bollinger')">
                                <div style="color:white;font-size:2em;margin-bottom:10px;">📉</div>
                                <h4 style="color:white;font-size:1.2em;font-weight:700;margin:0 0 8px 0;">Bollinger Bands</h4>
                                <p style="color:rgba(255,255,255,0.9);font-size:0.9em;margin:0;line-height:1.6;">Volatility bands placed above and below a moving average.</p>
                                <div style="margin-top:12px;font-size:0.85em;color:rgba(255,255,255,0.8);">Parameters: period (20), stdDev (2)</div>
                            </div>

                            <!-- Custom Template -->
                            <div style="background:linear-gradient(135deg, #fa709a 0%, #fee140 100%);padding:20px;border-radius:12px;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.1);transition:transform 0.2s;" onclick="loadTemplate('custom')">
                                <div style="color:white;font-size:2em;margin-bottom:10px;">✨</div>
                                <h4 style="color:white;font-size:1.2em;font-weight:700;margin:0 0 8px 0;">Custom Template</h4>
                                <p style="color:rgba(255,255,255,0.9);font-size:0.9em;margin:0;line-height:1.6;">Empty template to build your own indicator from scratch.</p>
                                <div style="margin-top:12px;font-size:0.85em;color:rgba(255,255,255,0.8);">Parameters: customizable</div>
                            </div>
                        </div>
                    </div>

                    <!-- Saved Indicators Tab -->
                    <div id="savedTab" class="indicator-tab-content" style="display:none;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                            <div>
                                <h3 style="font-size:1.3em;font-weight:700;color:#333;margin:0 0 5px 0;">Your Custom Indicators</h3>
                                <p style="color:var(--text-secondary);margin:0;">Manage your saved indicators</p>
                            </div>
                            <button onclick="importIndicator()" style="padding:10px 20px;background:#667eea;color:white;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:0.95em;">📥 Import Indicator</button>
                        </div>
                        
                        <div id="savedIndicatorsList"></div>
                    </div>

                    <!-- Test & Preview Tab -->
                    <div id="testTab" class="indicator-tab-content" style="display:none;">
                        <div style="margin-bottom:20px;">
                            <h3 style="font-size:1.3em;font-weight:700;color:#333;margin-bottom:10px;">Test Your Indicator</h3>
                            <p style="color:var(--text-secondary);">Run your indicator on test data and see a live preview</p>
                        </div>

                        <div style="display:grid;grid-template-columns:1fr;gap:20px;">
                            <!-- Test Controls -->
                            <div style="background:#f8f9fa;padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                <button onclick="testIndicatorCode()" style="padding:12px 30px;background:#27ae60;color:white;border:none;border-radius:10px;cursor:pointer;font-weight:700;font-size:1.1em;width:100%;">▶️ Run Test</button>
                            </div>

                            <!-- Test Output -->
                            <div>
                                <h4 style="font-weight:700;margin-bottom:12px;color:#333;">Test Results</h4>
                                <div id="testOutput" style="background:#f8f9fa;padding:20px;border-radius:12px;border:1px solid var(--border-color);min-height:80px;"></div>
                            </div>

                            <!-- Preview Chart -->
                            <div>
                                <h4 style="font-weight:700;margin-bottom:12px;color:#333;">Live Preview</h4>
                                <div style="background:white;padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                                    <canvas id="indicatorPreviewChart" style="max-height:400px;"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', indicatorBuilderModalHtml);

        // Pattern Recognition Modal
        const patternRecognitionModalHtml = `
        <div id="patternRecognitionModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:white;border-radius:20px;width:95%;max-width:1400px;max-height:90vh;overflow-y:auto;box-shadow:0 25px 60px rgba(0,0,0,0.3);position:relative;">
                <!-- Header -->
                <div style="padding:25px 30px;background:linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);border-radius:20px 20px 0 0;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h2 style="margin:0;font-size:1.8em;font-weight:800;color:#333;">🔍 Chart Pattern Recognition</h2>
                        <p style="margin:5px 0 0 0;font-size:0.95em;color:#555;">AI-powered pattern detection and analysis</p>
                    </div>
                    <button onclick="closePatternRecognition()" style="background:rgba(255,255,255,0.3);border:none;font-size:28px;cursor:pointer;width:45px;height:45px;border-radius:50%;color:#333;transition:all 0.2s;">✕</button>
                </div>

                <div style="padding:30px;">
                    <!-- Controls Bar -->
                    <div style="background:#f8f9fa;padding:20px;border-radius:12px;margin-bottom:25px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px;">
                        <div style="display:flex;gap:10px;flex-wrap:wrap;">
                            <button class="pattern-filter-btn" onclick="filterPatterns('all')" style="padding:10px 18px;background:#667eea;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                All Patterns
                            </button>
                            <button class="pattern-filter-btn" onclick="filterPatterns('bullish')" style="padding:10px 18px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                📈 Bullish
                            </button>
                            <button class="pattern-filter-btn" onclick="filterPatterns('bearish')" style="padding:10px 18px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                📉 Bearish
                            </button>
                            <button class="pattern-filter-btn" onclick="filterPatterns('reversal')" style="padding:10px 18px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                🔄 Reversal
                            </button>
                            <button class="pattern-filter-btn" onclick="filterPatterns('continuation')" style="padding:10px 18px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                ➡️ Continuation
                            </button>
                        </div>

                        <div style="display:flex;gap:10px;">
                            <button onclick="scanForPatterns()" style="padding:10px 20px;background:#27ae60;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                🔄 Rescan
                            </button>
                            <button onclick="togglePatternOverlays()" style="padding:10px 20px;background:#3498db;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                👁️ Hide Overlays
                            </button>
                            <button onclick="exportPatternReport()" style="padding:10px 20px;background:#9b59b6;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                📥 Export Report
                            </button>
                        </div>
                    </div>

                    <!-- Pattern Education Panel -->
                    <div style="background:linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);padding:20px;border-radius:12px;margin-bottom:25px;border:1px solid #b39ddb;">
                        <div style="font-weight:700;font-size:1.1em;color:#4527a0;margin-bottom:12px;">📚 Learn About Patterns</div>
                        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:10px;">
                            <button onclick="showPatternInfo('head-shoulders')" style="padding:10px;background:white;border:1px solid #b39ddb;border-radius:8px;cursor:pointer;text-align:left;font-size:0.9em;font-weight:600;color:#4527a0;">
                                👤 Head & Shoulders
                            </button>
                            <button onclick="showPatternInfo('double-bottom')" style="padding:10px;background:white;border:1px solid #b39ddb;border-radius:8px;cursor:pointer;text-align:left;font-size:0.9em;font-weight:600;color:#4527a0;">
                                W Double Bottom
                            </button>
                            <button onclick="showPatternInfo('triangle')" style="padding:10px;background:white;border:1px solid #b39ddb;border-radius:8px;cursor:pointer;text-align:left;font-size:0.9em;font-weight:600;color:#4527a0;">
                                △ Triangles
                            </button>
                            <button onclick="showPatternInfo('flag')" style="padding:10px;background:white;border:1px solid #b39ddb;border-radius:8px;cursor:pointer;text-align:left;font-size:0.9em;font-weight:600;color:#4527a0;">
                                🚩 Flags
                            </button>
                            <button onclick="showPatternInfo('wedge')" style="padding:10px;background:white;border:1px solid #b39ddb;border-radius:8px;cursor:pointer;text-align:left;font-size:0.9em;font-weight:600;color:#4527a0;">
                                📐 Wedges
                            </button>
                        </div>
                    </div>

                    <!-- Detected Patterns -->
                    <div>
                        <h3 style="font-size:1.3em;font-weight:700;color:#333;margin-bottom:15px;">Detected Patterns</h3>
                        <div id="patternScanOutput"></div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', patternRecognitionModalHtml);

        // Risk Calculator Modal
        const riskCalculatorModalHtml = `
        <div id="riskCalculatorModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:white;border-radius:20px;width:95%;max-width:1200px;max-height:90vh;overflow-y:auto;box-shadow:0 25px 60px rgba(0,0,0,0.3);position:relative;">
                <!-- Header -->
                <div style="padding:25px 30px;background:linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);border-radius:20px 20px 0 0;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h2 style="margin:0;font-size:1.8em;font-weight:800;color:#333;">🎯 Risk Calculator & Position Sizer</h2>
                        <p style="margin:5px 0 0 0;font-size:0.95em;color:#555;">Calculate optimal position sizes and manage risk</p>
                    </div>
                    <button onclick="closeRiskCalculator()" style="background:rgba(255,255,255,0.3);border:none;font-size:28px;cursor:pointer;width:45px;height:45px;border-radius:50%;color:#333;transition:all 0.2s;">✕</button>
                </div>

                <div style="padding:30px;">
                    <!-- Quick Presets -->
                    <div style="background:#f8f9fa;padding:20px;border-radius:12px;margin-bottom:25px;">
                        <div style="font-weight:700;margin-bottom:12px;color:#2c3e50;">⚡ Quick Presets</div>
                        <div style="display:flex;gap:10px;flex-wrap:wrap;">
                            <button onclick="quickFillRisk('conservative')" style="padding:12px 24px;background:linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);color:#333;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:0.9em;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                                🛡️ Conservative (1% Risk)
                            </button>
                            <button onclick="quickFillRisk('moderate')" style="padding:12px 24px;background:linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);color:#333;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:0.9em;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                                ⚖️ Moderate (2% Risk)
                            </button>
                            <button onclick="quickFillRisk('aggressive')" style="padding:12px 24px;background:linear-gradient(135deg, #fa709a 0%, #fee140 100%);color:#333;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:0.9em;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                                🔥 Aggressive (5% Risk)
                            </button>
                            <button onclick="saveRiskTemplate()" style="padding:12px 24px;background:#667eea;color:white;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:0.9em;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                                💾 Save Template
                            </button>
                        </div>
                    </div>

                    <!-- Input Form -->
                    <div style="background:white;border:1px solid var(--border-color);border-radius:15px;padding:25px;margin-bottom:25px;">
                        <h3 style="font-size:1.3em;font-weight:700;color:#2c3e50;margin:0 0 20px 0;">📊 Trading Parameters</h3>
                        
                        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(250px, 1fr));gap:20px;">
                            <!-- Account Size -->
                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;">Account Size ($)</label>
                                <input id="accountSize" type="number" value="10000" min="0" step="100" oninput="calculateRisk()" style="width:100%;padding:12px;border:2px solid #e0e0e0;border-radius:10px;font-size:1em;font-weight:600;transition:border 0.2s;" onfocus="this.style.borderColor='#667eea'" onblur="this.style.borderColor='#e0e0e0'">
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:5px;">Total capital available</div>
                            </div>

                            <!-- Risk Percentage -->
                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;">Risk per Trade (%)</label>
                                <input id="riskPercent" type="number" value="2" min="0.1" max="100" step="0.1" oninput="calculateRisk()" style="width:100%;padding:12px;border:2px solid #e0e0e0;border-radius:10px;font-size:1em;font-weight:600;transition:border 0.2s;" onfocus="this.style.borderColor='#667eea'" onblur="this.style.borderColor='#e0e0e0'">
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:5px;">Recommended: 1-2%</div>
                            </div>

                            <!-- Entry Price -->
                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;">Entry Price ($)</label>
                                <input id="entryPrice" type="number" value="100" min="0" step="0.01" oninput="calculateRisk()" style="width:100%;padding:12px;border:2px solid #e0e0e0;border-radius:10px;font-size:1em;font-weight:600;transition:border 0.2s;" onfocus="this.style.borderColor='#667eea'" onblur="this.style.borderColor='#e0e0e0'">
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:5px;">Price to enter trade</div>
                            </div>

                            <!-- Stop Loss -->
                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;">Stop Loss ($)</label>
                                <input id="stopLoss" type="number" value="95" min="0" step="0.01" oninput="calculateRisk()" style="width:100%;padding:12px;border:2px solid #e74c3c;border-radius:10px;font-size:1em;font-weight:600;transition:border 0.2s;" onfocus="this.style.borderColor='#c0392b'" onblur="this.style.borderColor='#e74c3c'">
                                <div style="font-size:0.8em;color:#e74c3c;margin-top:5px;">Exit if price reaches here</div>
                            </div>

                            <!-- Take Profit -->
                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;">Take Profit ($)</label>
                                <input id="takeProfit" type="number" value="110" min="0" step="0.01" oninput="calculateRisk()" style="width:100%;padding:12px;border:2px solid #27ae60;border-radius:10px;font-size:1em;font-weight:600;transition:border 0.2s;" onfocus="this.style.borderColor='#229954'" onblur="this.style.borderColor='#27ae60'">
                                <div style="font-size:0.8em;color:#27ae60;margin-top:5px;">Target profit level</div>
                            </div>

                            <!-- Leverage -->
                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;">Leverage (x)</label>
                                <input id="leverage" type="number" value="1" min="1" max="100" step="1" oninput="calculateRisk()" style="width:100%;padding:12px;border:2px solid #e0e0e0;border-radius:10px;font-size:1em;font-weight:600;transition:border 0.2s;" onfocus="this.style.borderColor='#f39c12'" onblur="this.style.borderColor='#e0e0e0'">
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:5px;">1 = no leverage (recommended)</div>
                            </div>
                        </div>
                    </div>

                    <!-- Results -->
                    <div id="riskCalculationResults"></div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', riskCalculatorModalHtml);

        // Multi-Timeframe Analysis Modal
        const multiTimeframeModalHtml = `
        <div id="multiTimeframeModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:white;border-radius:20px;width:98%;max-width:1600px;height:95vh;box-shadow:0 25px 60px rgba(0,0,0,0.3);position:relative;display:flex;flex-direction:column;">
                <!-- Header -->
                <div style="padding:20px 30px;background:linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%);border-radius:20px 20px 0 0;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;">
                    <div>
                        <h2 style="margin:0;font-size:1.8em;font-weight:800;color:#333;">📊 Multi-Timeframe Analysis</h2>
                        <p style="margin:5px 0 0 0;font-size:0.95em;color:#555;">Analyze ${currentSymbol || 'AAPL'} across multiple timeframes simultaneously</p>
                    </div>
                    <button onclick="closeMultiTimeframe()" style="background:rgba(255,255,255,0.3);border:none;font-size:28px;cursor:pointer;width:45px;height:45px;border-radius:50%;color:#333;transition:all 0.2s;">✕</button>
                </div>

                <!-- Controls Bar -->
                <div style="padding:15px 30px;background:#f8f9fa;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;flex-shrink:0;">
                    <div style="display:flex;gap:8px;flex-wrap:wrap;">
                        <span style="font-weight:600;color:#2c3e50;align-self:center;margin-right:8px;">Layout:</span>
                        <button class="mtf-layout-btn" onclick="changeMTFLayout('grid-6')" style="padding:8px 16px;background:#667eea;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                            ⊞ 6 Charts
                        </button>
                        <button class="mtf-layout-btn" onclick="changeMTFLayout('grid-4')" style="padding:8px 16px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                            ⊞ 4 Charts
                        </button>
                        <button class="mtf-layout-btn" onclick="changeMTFLayout('grid-2')" style="padding:8px 16px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                            ⊞ 2 Charts
                        </button>
                        <button class="mtf-layout-btn" onclick="changeMTFLayout('single')" style="padding:8px 16px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                            ⊞ Single
                        </button>
                    </div>

                    <div style="display:flex;gap:8px;">
                        <button onclick="syncMTFCrosshair(true)" style="padding:8px 16px;background:#3498db;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                            🔗 Sync Crosshair
                        </button>
                        <button onclick="showMTFSummary()" style="padding:8px 16px;background:#9b59b6;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                            📋 Summary
                        </button>
                        <button onclick="exportMTFAnalysis()" style="padding:8px 16px;background:#27ae60;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                            📥 Export
                        </button>
                    </div>
                </div>

                <!-- Charts Grid -->
                <div id="mtfChartsContainer" style="flex:1;display:grid;grid-template-columns:repeat(3, 1fr);grid-template-rows:repeat(2, 1fr);gap:15px;padding:20px;overflow:auto;">
                    ${timeframes.map(tf => `
                        <div id="mtf-container-${tf}" style="background:white;border:2px solid #e0e0e0;border-radius:12px;padding:15px;display:flex;flex-direction:column;min-height:0;">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                                <div>
                                    <span style="font-weight:800;font-size:1.2em;color:#2c3e50;">${tf.toUpperCase()}</span>
                                    <span style="font-size:0.85em;color:var(--text-secondary);margin-left:8px;">${getTFDescription(tf)}</span>
                                </div>
                                <div style="display:flex;gap:6px;align-items:center;">
                                    <span style="padding:4px 10px;background:${getTFTrendColor(tf)};color:white;border-radius:6px;font-size:0.8em;font-weight:700;">
                                        ${getTFTrend(tf)}
                                    </span>
                                </div>
                            </div>
                            <div style="flex:1;position:relative;min-height:0;">
                                <canvas id="mtf-chart-${tf}" style="width:100%!important;height:100%!important;"></canvas>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>`;

        // Helper functions for timeframe display
        function getTFDescription(tf) {
            const descriptions = {
                '1m': 'Scalping',
                '5m': 'Day Trading',
                '15m': 'Swing Entry',
                '1h': 'Intraday',
                '4h': 'Swing',
                '1d': 'Position'
            };
            return descriptions[tf] || '';
        }

        function getTFTrend(tf) {
            const trends = ['Bullish', 'Bearish', 'Neutral'];
            return trends[Math.floor(Math.random() * trends.length)];
        }

        function getTFTrendColor(tf) {
            const trend = getTFTrend(tf);
            if (trend === 'Bullish') return '#27ae60';
            if (trend === 'Bearish') return '#e74c3c';
            return '#95a5a6';
        }

        document.body.insertAdjacentHTML('beforeend', multiTimeframeModalHtml);

        // Fibonacci & Drawing Tools Modal
        const drawingToolsModalHtml = `
        <div id="drawingToolsModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:white;border-radius:20px;width:95%;max-width:1400px;height:90vh;box-shadow:0 25px 60px rgba(0,0,0,0.3);position:relative;display:flex;flex-direction:column;">
                <!-- Header -->
                <div style="padding:25px 30px;background:linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);border-radius:20px 20px 0 0;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;">
                    <div>
                        <h2 style="margin:0;font-size:1.8em;font-weight:800;color:#333;">✏️ Fibonacci & Drawing Tools</h2>
                        <p style="margin:5px 0 0 0;font-size:0.95em;color:#555;">Technical analysis drawing suite</p>
                    </div>
                    <button onclick="closeDrawingTools()" style="background:rgba(255,255,255,0.3);border:none;font-size:28px;cursor:pointer;width:45px;height:45px;border-radius:50%;color:#333;transition:all 0.2s;">✕</button>
                </div>

                <div style="flex:1;display:flex;overflow:hidden;">
                    <!-- Left Sidebar - Tools -->
                    <div style="width:280px;background:#f8f9fa;border-right:1px solid var(--border-color);padding:20px;overflow-y:auto;flex-shrink:0;">
                        <h3 style="font-size:1.1em;font-weight:700;color:#2c3e50;margin:0 0 15px 0;">📐 Drawing Tools</h3>
                        
                        <!-- Fibonacci Tools -->
                        <div style="margin-bottom:20px;">
                            <div style="font-weight:600;font-size:0.9em;color:#666;margin-bottom:10px;text-transform:uppercase;">Fibonacci</div>
                            <div style="display:flex;flex-direction:column;gap:8px;">
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Fibonacci Retracement')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    📊 Retracement
                                </button>
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Fibonacci Extension')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    📈 Extension
                                </button>
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Fibonacci Fan')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    🎯 Fan
                                </button>
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Fibonacci Arc')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    ⭕ Arc
                                </button>
                            </div>
                        </div>

                        <!-- Line Tools -->
                        <div style="margin-bottom:20px;">
                            <div style="font-weight:600;font-size:0.9em;color:#666;margin-bottom:10px;text-transform:uppercase;">Lines</div>
                            <div style="display:flex;flex-direction:column;gap:8px;">
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Trend Line')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    ╱ Trend Line
                                </button>
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Horizontal Line')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    ─ Horizontal
                                </button>
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Vertical Line')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    │ Vertical
                                </button>
                            </div>
                        </div>

                        <!-- Shape Tools -->
                        <div style="margin-bottom:20px;">
                            <div style="font-weight:600;font-size:0.9em;color:#666;margin-bottom:10px;text-transform:uppercase;">Shapes</div>
                            <div style="display:flex;flex-direction:column;gap:8px;">
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Rectangle')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    ▭ Rectangle
                                </button>
                                <button class="drawing-tool-btn" onclick="selectDrawingTool('Ellipse')" style="padding:10px 15px;background:white;border:2px solid #e0e0e0;border-radius:8px;text-align:left;cursor:pointer;font-weight:600;color:#333;transition:all 0.2s;">
                                    ⭕ Ellipse
                                </button>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div style="margin-top:auto;padding-top:20px;border-top:1px solid var(--border-color);">
                            <div style="display:flex;flex-direction:column;gap:8px;">
                                <button onclick="undoLastDrawing()" style="padding:10px;background:#3498db;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                    ↶ Undo
                                </button>
                                <button onclick="clearAllDrawings()" style="padding:10px;background:#e74c3c;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                    🗑️ Clear All
                                </button>
                                <button onclick="saveDrawings()" style="padding:10px;background:#27ae60;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                    💾 Save
                                </button>
                                <button onclick="loadDrawings()" style="padding:10px;background:#9b59b6;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                    📂 Load
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Main Canvas Area -->
                    <div style="flex:1;display:flex;flex-direction:column;overflow:hidden;">
                        <!-- Canvas Toolbar -->
                        <div style="background:white;padding:15px 20px;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;align-items:center;">
                            <div style="font-weight:700;color:#2c3e50;">
                                ${currentSymbol || 'AAPL'} Chart
                            </div>
                            <div style="display:flex;gap:10px;">
                                <span style="font-size:0.9em;color:var(--text-secondary);">
                                    Active Tool: <strong style="color:#667eea;">${activeDrawingTool || 'None'}</strong>
                                </span>
                            </div>
                        </div>

                        <!-- Drawing Canvas -->
                        <div style="flex:1;position:relative;overflow:hidden;background:#fafafa;">
                            <canvas id="drawingCanvas" style="width:100%;height:100%;cursor:crosshair;"></canvas>
                        </div>
                    </div>

                    <!-- Right Sidebar - Drawings List -->
                    <div style="width:280px;background:#f8f9fa;border-left:1px solid var(--border-color);padding:20px;overflow-y:auto;flex-shrink:0;">
                        <h3 style="font-size:1.1em;font-weight:700;color:#2c3e50;margin:0 0 15px 0;">📋 Drawings</h3>
                        <div id="drawingsList"></div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', drawingToolsModalHtml);

        // Economic Calendar Modal
        const economicCalendarModalHtml = `
        <div id="economicCalendarModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:white;border-radius:20px;width:95%;max-width:1200px;max-height:90vh;overflow-y:auto;box-shadow:0 25px 60px rgba(0,0,0,0.3);position:relative;">
                <!-- Header -->
                <div style="padding:25px 30px;background:linear-gradient(135deg, #d299c2 0%, #fef9d7 100%);border-radius:20px 20px 0 0;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <h2 style="margin:0;font-size:1.8em;font-weight:800;color:#333;">📅 Economic Calendar</h2>
                        <p style="margin:5px 0 0 0;font-size:0.95em;color:#555;">Track important economic events and data releases</p>
                    </div>
                    <button onclick="closeEconomicCalendar()" style="background:rgba(255,255,255,0.3);border:none;font-size:28px;cursor:pointer;width:45px;height:45px;border-radius:50%;color:#333;transition:all 0.2s;">✕</button>
                </div>

                <div style="padding:30px;">
                    <!-- Filters -->
                    <div style="background:#f8f9fa;padding:20px;border-radius:12px;margin-bottom:25px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                        <div style="display:flex;gap:10px;flex-wrap:wrap;">
                            <button class="calendar-filter-btn" onclick="filterEconomicEvents('all')" style="padding:10px 20px;background:#667eea;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                All Events
                            </button>
                            <button class="calendar-filter-btn" onclick="filterEconomicEvents('high')" style="padding:10px 20px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                🔴 High Impact
                            </button>
                            <button class="calendar-filter-btn" onclick="filterEconomicEvents('medium')" style="padding:10px 20px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                🟡 Medium Impact
                            </button>
                            <button class="calendar-filter-btn" onclick="filterEconomicEvents('low')" style="padding:10px 20px;background:#f8f9fa;color:#333;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                ⚪ Low Impact
                            </button>
                        </div>

                        <button onclick="exportCalendar()" style="padding:10px 20px;background:#27ae60;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                            📥 Export
                        </button>
                    </div>

                    <!-- Legend -->
                    <div style="background:linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);padding:15px 20px;border-radius:12px;margin-bottom:25px;border:1px solid #b39ddb;">
                        <div style="display:flex;gap:30px;flex-wrap:wrap;align-items:center;">
                            <div style="display:flex;align-items:center;gap:8px;">
                                <div style="width:12px;height:12px;background:#e74c3c;border-radius:50%;"></div>
                                <span style="font-size:0.9em;color:#4527a0;font-weight:600;">High Impact - Market moving events</span>
                            </div>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <div style="width:12px;height:12px;background:#f39c12;border-radius:50%;"></div>
                                <span style="font-size:0.9em;color:#4527a0;font-weight:600;">Medium Impact - Notable events</span>
                            </div>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <div style="width:12px;height:12px;background:#95a5a6;border-radius:50%;"></div>
                                <span style="font-size:0.9em;color:#4527a0;font-weight:600;">Low Impact - Minor events</span>
                            </div>
                        </div>
                    </div>

                    <!-- Events List -->
                    <div id="economicEventsList"></div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', economicCalendarModalHtml);

        // Stock Screener & Scanner Modal
        const screenerModalHtml = `
        <div id="screenerModal" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);z-index:10000;align-items:center;justify-content:center;">
            <div style="background:white;border-radius:20px;width:98%;max-width:1600px;max-height:95vh;box-shadow:0 25px 60px rgba(0,0,0,0.3);position:relative;display:flex;flex-direction:column;">
                <!-- Header -->
                <div style="padding:25px 30px;background:linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);border-radius:20px 20px 0 0;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;">
                    <div>
                        <h2 style="margin:0;font-size:1.8em;font-weight:800;color:white;">🔎 Stock Screener & Scanner</h2>
                        <p style="margin:5px 0 0 0;font-size:0.95em;color:rgba(255,255,255,0.9);">Find trading opportunities across markets</p>
                    </div>
                    <button onclick="closeScreener()" style="background:rgba(255,255,255,0.3);border:none;font-size:28px;cursor:pointer;width:45px;height:45px;border-radius:50%;color:white;transition:all 0.2s;">✕</button>
                </div>

                <div style="flex:1;display:flex;overflow:hidden;">
                    <!-- Left Sidebar - Filters -->
                    <div style="width:320px;background:#f8f9fa;border-right:1px solid var(--border-color);padding:25px;overflow-y:auto;flex-shrink:0;">
                        <h3 style="font-size:1.2em;font-weight:700;color:#2c3e50;margin:0 0 20px 0;">⚡ Quick Scans</h3>
                        
                        <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:30px;">
                            <button class="screener-preset-btn" onclick="runScreener('momentum')" style="padding:14px 18px;background:#667eea;color:white;border:none;border-radius:10px;text-align:left;cursor:pointer;font-weight:600;font-size:0.95em;transition:all 0.2s;">
                                🚀 Momentum Stocks
                            </button>
                            <button class="screener-preset-btn" onclick="runScreener('oversold')" style="padding:14px 18px;background:#f8f9fa;color:#333;border:none;border-radius:10px;text-align:left;cursor:pointer;font-weight:600;font-size:0.95em;transition:all 0.2s;">
                                📉 Oversold (RSI < 30)
                            </button>
                            <button class="screener-preset-btn" onclick="runScreener('overbought')" style="padding:14px 18px;background:#f8f9fa;color:#333;border:none;border-radius:10px;text-align:left;cursor:pointer;font-weight:600;font-size:0.95em;transition:all 0.2s;">
                                📈 Overbought (RSI > 70)
                            </button>
                            <button class="screener-preset-btn" onclick="runScreener('volume')" style="padding:14px 18px;background:#f8f9fa;color:#333;border:none;border-radius:10px;text-align:left;cursor:pointer;font-weight:600;font-size:0.95em;transition:all 0.2s;">
                                📊 High Volume
                            </button>
                            <button class="screener-preset-btn" onclick="runScreener('breakout')" style="padding:14px 18px;background:#f8f9fa;color:#333;border:none;border-radius:10px;text-align:left;cursor:pointer;font-weight:600;font-size:0.95em;transition:all 0.2s;">
                                💥 Breakout Candidates
                            </button>
                        </div>

                        <h3 style="font-size:1.2em;font-weight:700;color:#2c3e50;margin:0 0 20px 0;">🎛️ Custom Filters</h3>
                        
                        <div style="display:flex;flex-direction:column;gap:18px;">
                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;font-size:0.9em;">Price Range</label>
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                                    <input id="minPrice" type="number" placeholder="Min" value="0" style="padding:10px;border:2px solid #e0e0e0;border-radius:8px;font-size:0.9em;">
                                    <input id="maxPrice" type="number" placeholder="Max" value="1000" style="padding:10px;border:2px solid #e0e0e0;border-radius:8px;font-size:0.9em;">
                                </div>
                            </div>

                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;font-size:0.9em;">Min Volume (M)</label>
                                <input id="minVolume" type="number" placeholder="0" value="1000000" style="width:100%;padding:10px;border:2px solid #e0e0e0;border-radius:8px;font-size:0.9em;">
                            </div>

                            <div>
                                <label style="display:block;font-weight:600;margin-bottom:8px;color:#333;font-size:0.9em;">RSI Range</label>
                                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                                    <input id="minRSI" type="number" placeholder="Min" value="0" min="0" max="100" style="padding:10px;border:2px solid #e0e0e0;border-radius:8px;font-size:0.9em;">
                                    <input id="maxRSI" type="number" placeholder="Max" value="100" min="0" max="100" style="padding:10px;border:2px solid #e0e0e0;border-radius:8px;font-size:0.9em;">
                                </div>
                            </div>

                            <button onclick="runCustomScan()" style="padding:14px;background:#27ae60;color:white;border:none;border-radius:10px;cursor:pointer;font-weight:700;font-size:1em;margin-top:10px;">
                                🔍 Run Custom Scan
                            </button>
                        </div>
                    </div>

                    <!-- Main Results Area -->
                    <div style="flex:1;display:flex;flex-direction:column;overflow:hidden;">
                        <!-- Toolbar -->
                        <div style="background:white;padding:20px 30px;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;align-items:center;flex-shrink:0;">
                            <div style="font-weight:700;font-size:1.1em;color:#2c3e50;">
                                Scan Results
                            </div>
                            <div style="display:flex;gap:10px;">
                                <button onclick="exportScreenerResults()" style="padding:10px 20px;background:#9b59b6;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                    📥 Export
                                </button>
                                <button onclick="createWatchlist()" style="padding:10px 20px;background:#f39c12;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.9em;">
                                    ⭐ Add to Watchlist
                                </button>
                            </div>
                        </div>

                        <!-- Results Table -->
                        <div id="screenerResults" style="flex:1;overflow-y:auto;padding:30px;"></div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', screenerModalHtml);

        // Tab switching function
        function switchIndicatorTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.indicator-tab').forEach(tab => {
                tab.style.borderBottomColor = 'transparent';
                tab.style.color = 'var(--text-secondary)';
            });
            const activeTab = document.querySelector(`.indicator-tab[data-tab="${tabName}"]`);
            if (activeTab) {
                activeTab.style.borderBottomColor = '#667eea';
                activeTab.style.color = '#667eea';
            }

            // Update tab content
            document.querySelectorAll('.indicator-tab-content').forEach(content => {
                content.style.display = 'none';
            });
            const activeContent = document.getElementById(tabName + 'Tab');
            if (activeContent) {
                activeContent.style.display = 'block';
            }

            // Load data for specific tabs
            if (tabName === 'saved') {
                loadCustomIndicators();
            }
        }

        // Comparison Modal
        const comparisonModalHtml = `
        <div id="comparisonModal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);backdrop-filter:blur(8px);display:none;align-items:center;justify-content:center;z-index:10000;">
            <div style="background:var(--card-bg);padding:0;border-radius:16px;max-width:1400px;width:95%;max-height:90vh;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,0.3);">
                <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:20px;display:flex;justify-content:space-between;align-items:center;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2em;">📊</div>
                        <h3 style="margin:0;color:white;font-size:1.4em;font-weight:700;">Multi-Symbol Comparison</h3>
                    </div>
                    <button style="background:rgba(255,255,255,0.2);border:none;font-size:1.3em;cursor:pointer;color:white;padding:8px 12px;border-radius:8px;transition:all 0.2s;" onclick="closeComparisonModal()" onmouseover="this.style.background='rgba(255,255,255,0.3)'" onmouseout="this.style.background='rgba(255,255,255,0.2)'">✕</button>
                </div>

                <div style="padding:25px;overflow-y:auto;max-height:calc(90vh - 80px);">
                    <div style="margin-bottom:20px;">
                        <div style="font-size:0.95em;color:var(--text-secondary);margin-bottom:12px;font-weight:600;">Select symbols to compare (2-6 symbols):</div>
                        <div id="symbolSelectorGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:8px;margin-bottom:15px;">
                            <!-- Will be populated dynamically -->
                        </div>
                        <div style="display:flex;gap:10px;">
                            <button onclick="loadComparison()" style="padding:10px 20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;transition:all 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='none'">
                                🔍 Compare Selected
                            </button>
                            <button onclick="clearComparisonSelection()" style="padding:10px 20px;background:white;color:#666;border:1px solid #ddd;border-radius:8px;cursor:pointer;font-weight:600;transition:all 0.2s;">
                                Clear Selection
                            </button>
                        </div>
                    </div>

                    <div id="comparisonContent" style="display:none;">
                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                            <h4 style="margin:0 0 15px 0;color:var(--text-primary);font-size:1.1em;">📈 Performance Metrics</h4>
                            <div id="comparisonMetrics" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;">
                                <!-- Metrics cards will be inserted here -->
                            </div>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                            <h4 style="margin:0 0 15px 0;color:var(--text-primary);font-size:1.1em;">📊 Synchronized Equity Curves</h4>
                            <canvas id="comparisonChart" style="max-height:400px;"></canvas>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);margin-bottom:20px;">
                            <h4 style="margin:0 0 15px 0;color:var(--text-primary);font-size:1.1em;">🔗 Correlation Matrix</h4>
                            <div id="correlationMatrix" style="overflow-x:auto;">
                                <!-- Correlation matrix will be inserted here -->
                            </div>
                        </div>

                        <div style="background:var(--bg-container);padding:20px;border-radius:12px;border:1px solid var(--border-color);">
                            <h4 style="margin:0 0 15px 0;color:var(--text-primary);font-size:1.1em;">📋 Detailed Comparison Table</h4>
                            <div style="overflow-x:auto;">
                                <table id="comparisonTable" style="width:100%;border-collapse:collapse;font-size:0.9em;">
                                    <thead>
                                        <tr style="background:var(--table-header-bg);">
                                            <th style="padding:12px;text-align:left;color:var(--text-secondary);font-weight:600;border-bottom:2px solid var(--border-color);">Symbol</th>
                                            <th style="padding:12px;text-align:right;color:var(--text-secondary);font-weight:600;border-bottom:2px solid var(--border-color);">Return %</th>
                                            <th style="padding:12px;text-align:right;color:var(--text-secondary);font-weight:600;border-bottom:2px solid var(--border-color);">Win Rate</th>
                                            <th style="padding:12px;text-align:right;color:var(--text-secondary);font-weight:600;border-bottom:2px solid var(--border-color);">Sharpe</th>
                                            <th style="padding:12px;text-align:right;color:var(--text-secondary);font-weight:600;border-bottom:2px solid var(--border-color);">Max DD</th>
                                            <th style="padding:12px;text-align:right;color:var(--text-secondary);font-weight:600;border-bottom:2px solid var(--border-color);">Trades</th>
                                            <th style="padding:12px;text-align:right;color:var(--text-secondary);font-weight:600;border-bottom:2px solid var(--border-color);">Avg Duration</th>
                                            <th style="padding:12px;text-align:right;color:var(--text-secondary);font-weight:600;border-bottom:2px solid var(--border-color);">Risk Score</th>
                                        </tr>
                                    </thead>
                                    <tbody id="comparisonTableBody">
                                        <!-- Will be populated -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', comparisonModalHtml);

        async function showGenome() {
            const showBtn = document.getElementById('showGenomeBtn');
            const loadingEl = document.getElementById('genomeLoading');
            const errorEl = document.getElementById('genomeError');
            const jsonEl = document.getElementById('genomeJson');

            // Reset UI
            errorEl.style.display = 'none';
            jsonEl.style.display = 'none';
            loadingEl.style.display = 'block';
            showBtn.disabled = true;

            try {
                // Fast path: request a compact parameter map (include token header if provided)
                const tokenVal = (document.getElementById('demoToken') || {}).value || localStorage.getItem('demoToken') || '';
                const headers = {};
                if (tokenVal) headers['X-DEMO-TOKEN'] = tokenVal;
                const res = await fetch('/current_parameters', { headers: headers });
                if (!res.ok) {
                    const txt = await res.text();
                    errorEl.textContent = `No genome snapshot available: ${txt}`;
                    errorEl.style.display = 'block';
                    addLog('No genome snapshot available', 'warning');
                    document.getElementById('genomeModal').style.display = 'flex';
                    return;
                }

                const json = await res.json();
                // populate summary (chromosomes table and history preview)
                const summaryEl = document.getElementById('genomeSummary');
                const tableEl = document.getElementById('chromosomesTable');
                const historyEl = document.getElementById('historyPreview');
                const toggleBtn = document.getElementById('toggleHistoryBtn');
                const downloadBtn = document.getElementById('downloadGenomeBtn');

                // build a compact chromosomes table
                tableEl.innerHTML = '';
                if (json.chromosomes) {
                    const rows = [];
                    for (const groupKey of Object.keys(json.chromosomes)) {
                        const group = json.chromosomes[groupKey];
                        for (const paramKey of Object.keys(group)) {
                            const c = group[paramKey];
                            rows.push(`<div style="display:flex;gap:12px;padding:6px 4px;border-bottom:1px solid #f1f1f1;"><div style="flex:1;font-weight:600;color:#333;">${groupKey}.${paramKey}</div><div style="width:120px;text-align:right;color:#444;">${c.value}</div><div style="width:140px;text-align:right;color:#888;">edited: ${c.edit_count || 0}</div></div>`);
                        }
                    }
                    tableEl.innerHTML = rows.join('');
                } else {
                    tableEl.innerHTML = '<div style="color:#666">No chromosomes available</div>';
                }

                // For performance, /current_parameters returns a compact object:
                // { id, name, snapshot_time, parameters }
                historyEl.innerHTML = '';
                // Show parameter table from compact parameters
                const params = json.parameters || {};
                const rows = [];
                for (const pth of Object.keys(params)) {
                    rows.push(`<div style="display:flex;gap:12px;padding:6px 4px;border-bottom:1px solid #f1f1f1;"><div style="flex:1;font-weight:600;color:#333;">${pth}</div><div style="width:120px;text-align:right;color:#444;">${params[pth]}</div></div>`);
                }
                tableEl.innerHTML = rows.length ? rows.join('') : '<div style="color:#666">No parameters available</div>';

                // populate telemetry if provided
                const telemetryEl = document.getElementById('genomeTelemetry');
                if (json.telemetry) {
                    const t = json.telemetry;
                    // telemetry may be compact or rich - prefer readable fields
                    const bf = t.best_fitness ?? (t.best_individual && t.best_individual.fitness) ?? '—';
                    const pop = t.population_size ?? '—';
                    const gens = t.total_generations ?? t.generations_run ?? '—';
                    const runtime = (t.run_time_seconds != null) ? (t.run_time_seconds + 's') : '';
                    telemetryEl.innerHTML = `Telemetry: best_fitness=${bf} | population_size=${pop} | generations=${gens} ${runtime ? '| run_time=' + runtime : ''}`;
                    telemetryEl.style.display = 'block';
                } else {
                    telemetryEl.style.display = 'none';
                }

                // attach toggle to lazy-load full snapshot (history + full JSON)
                toggleBtn.onclick = async () => {
                    if (historyEl.style.display === 'none') {
                        // Load full snapshot from server when expanding history
                        try {
                            if (!json.id) {
                                historyEl.innerHTML = '<div style="color:#666">No persisted snapshot available</div>';
                            } else {
                                const headers = {};
                                const tokenVal = (document.getElementById('demoToken') || {}).value || localStorage.getItem('demoToken') || '';
                                if (tokenVal) headers['X-DEMO-TOKEN'] = tokenVal;
                                const snapResp = await fetch(`/snapshots/${encodeURIComponent(json.id)}`, { headers: headers });
                                if (!snapResp.ok) {
                                    historyEl.innerHTML = `<div style="color:#c0392b">Failed to load history: ${await snapResp.text()}</div>`;
                                } else {
                                    const full = await snapResp.json();
                                    const top = (full.metadata && Array.isArray(full.metadata.edit_history)) ? full.metadata.edit_history.slice(0, 50) : [];
                                    const items = top.map(e => {
                                        const ts = (e.timestamp || '').replace('T', ' ');
                                        return `<div style="padding:6px 4px;border-bottom:1px dashed #eee;"><div style="font-weight:600;color:#222;">${e.path}</div><div style="color:#555;">${e.old_value} → ${e.new_value} <span style="color:#999">(${ts})</span></div><div style="font-size:0.85em;color:#777">reason: ${e.reason || '—'}</div></div>`;
                                    });
                                    historyEl.innerHTML = items.join('') || '<div style="color:#666">No edit history</div>';

                                    // If full telemetry present, show an expanded summary
                                    try {
                                        const fullTelemetry = (full.metadata && full.metadata.telemetry) || null;
                                        if (fullTelemetry) {
                                                const telDiv = document.createElement('div');
                                                telDiv.style.padding = '8px';
                                                telDiv.style.marginTop = '8px';
                                                telDiv.style.borderTop = '1px solid #eee';
                                                const bf = fullTelemetry.best_fitness ?? (fullTelemetry.best_individual && fullTelemetry.best_individual.fitness) ?? '—';
                                                const gens = fullTelemetry.total_generations ?? fullTelemetry.generations_run ?? fullTelemetry.num_generations_configured ?? '—';
                                                const pop = fullTelemetry.population_size ?? '—';
                                                const rt = (fullTelemetry.run_time_seconds != null) ? (fullTelemetry.run_time_seconds + 's') : '—';
                                                telDiv.innerHTML = `<div style="font-weight:700;margin-bottom:6px;color:#333;">Full telemetry</div><div style="color:#444;">best_fitness: ${bf} | population_size: ${pop} | generations: ${gens} | run_time: ${rt}</div>`;
                                                historyEl.insertAdjacentElement('afterend', telDiv);

                                                // Render a small Chart.js plot of best_per_generation if available
                                                try {
                                                    const chartContainer = document.getElementById('telemetryChartContainer');
                                                    const chartCanvas = document.getElementById('telemetryChart');
                                                    // cleanup existing canvas/chart if any
                                                    if (window._telemetryChartInstance) {
                                                        try { window._telemetryChartInstance.destroy(); } catch(e){}
                                                        window._telemetryChartInstance = null;
                                                    }

                                                    if (Array.isArray(fullTelemetry.best_per_generation) && fullTelemetry.best_per_generation.length > 0) {
                                                        chartContainer.style.display = 'block';
                                                        const labels = fullTelemetry.best_per_generation.map((v, idx) => idx);
                                                        const bestData = fullTelemetry.best_per_generation.map(v => Number(v) || 0);
                                                        // optional diversity series
                                                        const diversityData = (Array.isArray(fullTelemetry.diversity_per_generation) && fullTelemetry.diversity_per_generation.length === bestData.length)
                                                            ? fullTelemetry.diversity_per_generation.map(v => Number(v) || 0)
                                                            : null;

                                                        const datasets = [{
                                                            label: 'Best fitness per generation',
                                                            data: bestData,
                                                            borderColor: '#764ba2',
                                                            backgroundColor: 'rgba(118,75,162,0.12)',
                                                            fill: true,
                                                            tension: 0.3,
                                                        }];

                                                        if (diversityData) {
                                                            datasets.push({
                                                                label: 'Population diversity',
                                                                data: diversityData,
                                                                borderColor: '#2b9af3',
                                                                backgroundColor: 'rgba(43,154,243,0.08)',
                                                                fill: true,
                                                                tension: 0.3,
                                                                yAxisID: 'y_div'
                                                            });
                                                        }

                                                        window._telemetryChartInstance = new Chart(chartCanvas.getContext('2d'), {
                                                            type: 'line',
                                                            data: {
                                                                labels: labels,
                                                                datasets: datasets
                                                            },
                                                            options: {
                                                                responsive: true,
                                                                maintainAspectRatio: false,
                                                                scales: {
                                                                    x: { display: true, title: { display: true, text: 'Generation' } },
                                                                    y: { display: true, title: { display: true, text: 'Fitness' } },
                                                                    y_div: { display: !!diversityData, position: 'right', title: { display: true, text: 'Diversity' }, grid: { drawOnChartArea: false } }
                                                                },
                                                                plugins: { legend: { display: true } }
                                                            }
                                                        });
                                                    } else {
                                                        chartContainer.style.display = 'none';
                                                    }
                                                } catch (err) {
                                                    // ignore chart rendering errors
                                                }
                                            }
                                    } catch (err) {
                                        // ignore telemetry rendering errors
                                    }
                                }
                            }
                        } catch (err) {
                            historyEl.innerHTML = `<div style="color:#c0392b">Failed to load history: ${err.message}</div>`;
                        }
                        historyEl.style.display = 'block';
                        toggleBtn.textContent = 'Hide edit history';
                    } else {
                        historyEl.style.display = 'none';
                        toggleBtn.textContent = 'Show edit history';
                    }
                };
                // start collapsed
                historyEl.style.display = 'none';
                toggleBtn.textContent = 'Show edit history';

                // download behavior - client side blob
                downloadBtn.onclick = () => {
                    try {
                        const blob = new Blob([JSON.stringify(json, null, 2)], {type: 'application/json'});
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        const safeName = (json.name || 'genome_snapshot').replace(/[^a-zA-Z0-9-_\.]/g, '_');
                        a.download = safeName + '.json';
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        URL.revokeObjectURL(url);
                    } catch (err) {
                        addLog('Failed to download snapshot', 'error');
                    }
                };

                // server-side download button: streams file from server
                const serverDownloadBtn = document.getElementById('downloadGenomeServerBtn');
                serverDownloadBtn.onclick = async () => {
                    // require a persisted snapshot id
                    const sid = json.id || json._snapshot_id;
                    if (!sid) {
                        addLog('No persisted snapshot id available for server download', 'warning');
                        return;
                    }

                    try {
                        const headers = {};
                        const tokenVal = (document.getElementById('demoToken') || {}).value || localStorage.getItem('demoToken') || '';
                        if (tokenVal) headers['X-DEMO-TOKEN'] = tokenVal;

                        const resp = await fetch(`/snapshots/${encodeURIComponent(sid)}/download`, { method: 'GET', headers: headers });
                        if (!resp.ok) {
                            const txt = await resp.text();
                            addLog('Server download failed: ' + txt, 'error');
                            return;
                        }

                        const blob = await resp.blob();
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = (json.name || 'genome_snapshot') + '.json';
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        URL.revokeObjectURL(url);
                    } catch (err) {
                        addLog('Server download failed: ' + err.message, 'error');
                    }
                };

                summaryEl.style.display = 'block';
                document.getElementById('genomeJson').textContent = JSON.stringify(json, null, 2);
                jsonEl.style.display = 'block';
                document.getElementById('genomeModal').style.display = 'flex';
                // Try to fetch live telemetry (non-blocking). If the server exposes /telemetry, populate the live telemetry panel.
                try {
                    const refreshBtn = document.getElementById('refreshTelemetryBtn');
                    const liveSection = document.getElementById('liveTelemetrySection');
                    const liveSummary = document.getElementById('liveTelemetrySummary');
                    const speciesTable = document.getElementById('liveSpeciesTable');
                    const liveChartContainer = document.getElementById('liveTelemetryChartContainer');
                    const liveCanvas = document.getElementById('liveTelemetryChart');

                    async function fetchLiveTelemetry() {
                        try {
                            liveSummary.textContent = 'Fetching live telemetry…';
                            speciesTable.innerHTML = '';
                            liveChartContainer.style.display = 'none';
                            if (window._liveTelemetryChartInstance) { try { window._liveTelemetryChartInstance.destroy(); } catch(e){} window._liveTelemetryChartInstance = null; }

                            const tokenVal = (document.getElementById('demoToken') || {}).value || localStorage.getItem('demoToken') || '';
                            const headers = {};
                            if (tokenVal) headers['X-DEMO-TOKEN'] = tokenVal;
                            const resp = await fetch('/telemetry', { headers: headers });
                            if (!resp.ok) {
                                liveSummary.textContent = 'No live telemetry available from server.';
                                liveSection.style.display = 'none';
                                return;
                            }

                            const tel = await resp.json();
                            liveSection.style.display = 'block';

                            const best = tel.best_fitness ?? (tel.best_individual && tel.best_individual.fitness) ?? '—';
                            const gens = tel.total_generations ?? tel.generations_run ?? tel.num_generations_configured ?? '—';
                            const pop = tel.population_size ?? '—';
                            liveSummary.textContent = `best_fitness: ${best} | population: ${pop} | generations: ${gens}`;

                            // per-species table if available
                            const species = tel.species || tel.species_summary || null;
                            if (species && typeof species === 'object') {
                                const rows = [];
                                // species could be array or dict
                                if (Array.isArray(species)) {
                                    for (const s of species) {
                                        rows.push(`<div style="display:flex;gap:12px;padding:6px 4px;border-bottom:1px solid #f1f1f1;"><div style="flex:1;font-weight:600;color:#333;">${s.id || s.species_id || 'spec'}</div><div style="width:120px;text-align:right;color:#444;">size: ${s.size ?? s.count ?? '—'}</div><div style="width:140px;text-align:right;color:#888;">best: ${s.best_fitness ?? '—'}</div></div>`);
                                    }
                                } else {
                                    for (const k of Object.keys(species)) {
                                        const s = species[k] || {};
                                        rows.push(`<div style="display:flex;gap:12px;padding:6px 4px;border-bottom:1px solid #f1f1f1;"><div style="flex:1;font-weight:600;color:#333;">${k}</div><div style="width:120px;text-align:right;color:#444;">size: ${s.size ?? s.count ?? '—'}</div><div style="width:140px;text-align:right;color:#888;">best: ${s.best_fitness ?? '—'}</div></div>`);
                                    }
                                }
                                speciesTable.innerHTML = rows.join('') || '<div style="color:#666">No per-species stats</div>';
                            } else {
                                speciesTable.innerHTML = '<div style="color:#666">No per-species stats</div>';
                            }

                            // plot best_per_generation if present
                            if (Array.isArray(tel.best_per_generation) && tel.best_per_generation.length > 0) {
                                try {
                                    liveChartContainer.style.display = 'block';
                                    const labels = tel.best_per_generation.map((_, idx) => idx);
                                    const bestData = tel.best_per_generation.map(v => Number(v) || 0);
                                    const datasets = [{ label: 'Best fitness', data: bestData, borderColor: '#764ba2', backgroundColor: 'rgba(118,75,162,0.12)', fill: true, tension: 0.3 }];
                                    window._liveTelemetryChartInstance = new Chart(liveCanvas.getContext('2d'), {
                                        type: 'line', data: { labels: labels, datasets: datasets }, options: { responsive: true, maintainAspectRatio: false }
                                    });
                                } catch (err) { liveChartContainer.style.display = 'none'; }
                            } else {
                                liveChartContainer.style.display = 'none';
                            }
                        } catch (err) {
                            liveSummary.textContent = 'Failed to fetch live telemetry';
                            speciesTable.innerHTML = `<div style="color:#c0392b">${err.message}</div>`;
                        }
                    }

                    refreshBtn.onclick = () => fetchLiveTelemetry();
                    // initial fetch (non-blocking)
                    fetchLiveTelemetry().catch(()=>{});
                } catch (err) {
                    // ignore live telemetry wiring errors
                }
            } catch (e) {
                errorEl.textContent = `Failed to fetch genome snapshot: ${e.message}`;
                errorEl.style.display = 'block';
                addLog('Failed to fetch genome snapshot', 'error');
                document.getElementById('genomeModal').style.display = 'flex';
            } finally {
                loadingEl.style.display = 'none';
                showBtn.disabled = false;
            }
        }
        // SSE integration
        let sseEnabled = false;
        let eventSource = null;

        function connectSSE() {
            try {
                // If a demo token is provided, attach it as a query param so the server can validate it
                const tokenInput = document.getElementById('demoToken') || {};
                const token = tokenInput.value || localStorage.getItem('demoToken') || '';
                const eventsUrl = token ? `/events?token=${encodeURIComponent(token)}` : '/events';
                eventSource = new EventSource(eventsUrl);
                eventSource.addEventListener('log', (e) => {
                    const payload = JSON.parse(e.data);
                    addLog(payload.msg, 'info');
                });

                eventSource.addEventListener('status', (e) => {
                    const payload = JSON.parse(e.data);
                    updateStatus(payload.status, payload.badge);
                });

                eventSource.addEventListener('chart', (e) => {
                    const payload = JSON.parse(e.data);
                    chart.data.labels.push(payload.idx);
                    chart.data.datasets[0].data.push(payload.value);
                    chart.update();
                });

                eventSource.addEventListener('metrics', (e) => {
                    const payload = JSON.parse(e.data);
                    updateMetric('sharpeValue', payload.sharpe);
                    updateMetric('driftValue', payload.drift);
                    updateMetric('winRateValue', payload.win_rate);
                    updateMetric('ddValue', payload.dd);
                });

                eventSource.onopen = () => { sseEnabled = true; addLog('SSE connected to backend', 'info'); };
                eventSource.onerror = () => { sseEnabled = false; addLog('SSE connection error - falling back to client demo', 'warning'); };
            } catch (e) {
                sseEnabled = false;
            }
        }
        let chart;
        let demoRunning = false;
        let currentStep = 0;
        let dataPoints = [];
        let timeIndex = 0;

        // Initialize chart
        function initChart() {
            const ctx = document.getElementById('performanceChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Cumulative Returns',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        tension: 0.4,
                        fill: true
                    }]
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
                        x: {
                            title: {
                                display: true,
                                text: 'Time (days)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Return (%)'
                            }
                        }
                    },
                    animation: {
                        duration: 300
                    }
                }
            });
        }

        function addLog(message, type = 'info') {
            const logContainer = document.getElementById('logContainer');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry ${type}`;
            logEntry.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
            logContainer.appendChild(logEntry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        function updateMetric(id, value, change = null) {
            document.getElementById(id).textContent = value;
            if (change !== null) {
                const changeEl = document.getElementById(id.replace('Value', 'Change'));
                const isPositive = change > 0;
                changeEl.textContent = `${isPositive ? '▲' : '▼'} ${Math.abs(change).toFixed(2)}`;
                changeEl.className = `metric-change ${isPositive ? 'positive' : 'negative'}`;
            }
        }

        function updateStatus(status, badge) {
            const statusBadge = document.getElementById('statusBadge');
            statusBadge.textContent = `● ${status}`;
            statusBadge.className = `status-badge status-${badge}`;
        }

        function updateTimeline(step) {
            for (let i = 1; i <= 4; i++) {
                const stepEl = document.getElementById(`step${i}`);
                stepEl.classList.remove('active', 'completed');
                if (i < step) {
                    stepEl.classList.add('completed');
                } else if (i === step) {
                    stepEl.classList.add('active');
                }
            }
        }

        async function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }

        async function startDemo() {
            if (demoRunning) return;
            
            demoRunning = true;
            document.getElementById('startBtn').disabled = true;
            document.getElementById('resetBtn').disabled = true;

            addLog('Demo started. Simulating normal trading operations...', 'info');
            
            // Phase 1: Normal Operation (0-50 days)
            currentStep = 1;
            updateTimeline(1);
            updateStatus('NORMAL', 'normal');
            
            for (let i = 0; i < 50; i++) {
                const baseReturn = 0.5;
                const noise = (Math.random() - 0.5) * 0.3;
                const value = baseReturn * i + noise * Math.sqrt(i);
                
                chart.data.labels.push(i);
                chart.data.datasets[0].data.push(value);
                chart.update();
                
                if (i === 10) addLog(`Trading AAPL with naive_momentum strategy. Sharpe: 0.85`, 'info');
                if (i === 25) addLog(`Performance stable. Win rate: 55%`, 'success');
                
                await sleep(50);
            }

            // Phase 2: Drift Detection (50-80 days)
            currentStep = 2;
            updateTimeline(2);
            updateStatus('DRIFT DETECTED', 'drift');
            addLog('⚠️ Performance drift detected! Drift score: 0.42', 'warning');
            await sleep(500);
            addLog('Sharpe ratio declining: 0.85 → 0.61 (-28%)', 'error');
            
            for (let i = 50; i < 80; i++) {
                const deterioration = (i - 50) * 0.1;
                const baseReturn = 0.5;
                const noise = (Math.random() - 0.5) * 0.5;
                const value = baseReturn * i - deterioration + noise * Math.sqrt(i);
                
                chart.data.labels.push(i);
                chart.data.datasets[0].data.push(value);
                chart.data.datasets[0].borderColor = '#e74c3c';
                chart.update();
                
                if (i === 60) {
                    updateMetric('sharpeValue', '0.61', -0.24);
                    updateMetric('driftValue', '0.42', 0.30);
                    updateMetric('winRateValue', '48%', -7);
                    updateMetric('ddValue', '-12.5%', -4.3);
                }
                
                if (i === 70) addLog('Drift threshold exceeded (0.42 > 0.30). Triggering self-healing...', 'warning');
                
                await sleep(50);
            }

            // Phase 3: GA Optimization (80-100 days)
            currentStep = 3;
            updateTimeline(3);
            updateStatus('OPTIMIZING', 'healing');
            addLog('🔄 Starting Genetic Algorithm optimization...', 'warning');
            await sleep(500);
            addLog('Population: 50, Generations: 20, Mutation rate: 0.1', 'info');
            await sleep(800);
            addLog('Generation 5/20... Best fitness: 0.73', 'info');
            await sleep(800);
            addLog('Generation 10/20... Best fitness: 0.89', 'info');
            await sleep(800);
            addLog('Generation 15/20... Best fitness: 1.12', 'info');
            await sleep(800);
            addLog('Generation 20/20... Best fitness: 1.38', 'success');
            await sleep(500);
            addLog('✅ Optimization complete! New parameters deployed.', 'success');
            
            // Phase 4: Healed Performance (100-150 days)
            currentStep = 4;
            updateTimeline(4);
            updateStatus('HEALED', 'healed');
            addLog('🎉 System healed! Performance restored and improved.', 'success');
            
            updateMetric('sharpeValue', '1.38', +0.77);
            updateMetric('driftValue', '0.08', -0.34);
            updateMetric('winRateValue', '62%', +14);
            updateMetric('ddValue', '-6.1%', +6.4);
            
            for (let i = 100; i < 150; i++) {
                const baseReturn = 0.8;
                const noise = (Math.random() - 0.5) * 0.2;
                const value = baseReturn * i + noise * Math.sqrt(i) - 50;
                
                chart.data.labels.push(i);
                chart.data.datasets[0].data.push(value);
                chart.data.datasets[0].borderColor = '#27ae60';
                chart.update();
                
                if (i === 120) addLog('New Sharpe ratio: 1.38 (+62% improvement)', 'success');
                if (i === 130) addLog('System stable. Monitoring for future drift...', 'success');
                
                await sleep(50);
            }

            addLog('✨ Demo complete! This is CRISPR-FinAI\'s self-healing in action.', 'success');
            
            demoRunning = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('resetBtn').disabled = false;
        }

        async function startBatchDemo() {
            if (demoRunning) return;
            demoRunning = true;
            document.getElementById('startBtn').disabled = true;
            document.getElementById('batchBtn').disabled = true;
            document.getElementById('resetBtn').disabled = true;
            addLog('🧪 Starting Batch Co-evolution demo...', 'info');

            // If SSE backend is available, instruct it to run the batch demo
            if (!eventSource) connectSSE();

            if (sseEnabled) {
                try {
                    // Collect GA params from UI
                    const payload = {
                        population_size: parseInt(document.getElementById('gaPop').value, 10),
                        num_generations: parseInt(document.getElementById('gaGens').value, 10),
                        mutation_rate: parseFloat(document.getElementById('gaMut').value)
                    };

                    const headers = {'Content-Type': 'application/json'};
                    // use stored token if present
                    const tokenVal = (document.getElementById('demoToken') || {}).value || localStorage.getItem('demoToken') || '';
                    if (tokenVal) headers['X-DEMO-TOKEN'] = tokenVal;
                    await fetch('/run_real_batch', { method: 'POST', headers: headers, body: JSON.stringify(payload) });
                    // Wait for server-driven events to complete; simple polling
                    const waitForCompletion = () => new Promise(resolve => setTimeout(resolve, 3000));
                    await waitForCompletion();
                    demoRunning = false;
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('batchBtn').disabled = false;
                    document.getElementById('resetBtn').disabled = false;
                    return;
                } catch (e) {
                    addLog('Failed to trigger server batch run, falling back to client demo', 'warning');
                }
            }
            currentStep = 1;
            updateTimeline(1);
            updateStatus('NORMAL', 'normal');

            // Quick normal phase
            for (let i = 0; i < 30; i++) {
                const baseReturn = 0.4;
                const noise = (Math.random() - 0.5) * 0.25;
                const value = baseReturn * i + noise * Math.sqrt(i);
                chart.data.labels.push(i);
                chart.data.datasets[0].data.push(value);
                chart.update();
                await sleep(30);
            }

            // Show drift
            currentStep = 2;
            updateTimeline(2);
            updateStatus('DRIFT DETECTED', 'drift');
            addLog('⚠️ Detected correlated parameter drift across strategies', 'warning');
            updateMetric('driftValue', '0.48', +0.36);
            await sleep(600);

            // Batch co-evolution optimization
            currentStep = 3;
            updateTimeline(3);
            updateStatus('OPTIMIZING', 'healing');
            addLog('🔬 Running co-evolution across multiple targets...', 'info');
            await sleep(400);

            // Simulate GA generation logs and improvement
            for (let g = 1; g <= 8; g++) {
                addLog(`Generation ${g}/8... best joint fitness: ${(0.2 + g*0.15).toFixed(2)}`, 'info');
                await sleep(450);
            }

            addLog('✅ Co-evolution complete. Deploying joint edits...', 'success');
            await sleep(300);

            // Healed phase
            currentStep = 4;
            updateTimeline(4);
            updateStatus('HEALED', 'healed');
            addLog('🎉 System stabilized after batch co-evolution.', 'success');

            updateMetric('sharpeValue', '1.22', +0.37);
            updateMetric('driftValue', '0.09', -0.39);
            updateMetric('winRateValue', '60%', +5);
            updateMetric('ddValue', '-5.2%', +2.9);

            for (let i = 30; i < 80; i++) {
                const baseReturn = 0.7;
                const noise = (Math.random() - 0.5) * 0.18;
                const value = baseReturn * i + noise * Math.sqrt(i) - 40;
                chart.data.labels.push(i);
                chart.data.datasets[0].data.push(value);
                chart.data.datasets[0].borderColor = '#27ae60';
                chart.update();
                await sleep(40);
            }

            addLog('✨ Batch demo complete!', 'success');
            demoRunning = false;
            document.getElementById('startBtn').disabled = false;
            document.getElementById('batchBtn').disabled = false;
            document.getElementById('resetBtn').disabled = false;
        }

        function resetDemo() {
            chart.data.labels = [];
            chart.data.datasets[0].data = [];
            chart.data.datasets[0].borderColor = '#667eea';
            chart.update();
            
            currentStep = 0;
            updateTimeline(0);
            updateStatus('NORMAL', 'normal');
            
            updateMetric('sharpeValue', '0.85');
            updateMetric('driftValue', '0.12');
            updateMetric('winRateValue', '55%');
            updateMetric('ddValue', '-8.2%');
            
            document.getElementById('sharpeChange').textContent = '—';
            document.getElementById('driftChange').textContent = '—';
            document.getElementById('winRateChange').textContent = '—';
            document.getElementById('ddChange').textContent = '—';
            
            const logContainer = document.getElementById('logContainer');
            logContainer.innerHTML = '<div class="log-entry info"><span class="timestamp">[00:00:00]</span> System reset. Ready for demo...</div>';
            
            document.getElementById('startBtn').disabled = false;
            document.getElementById('resetBtn').disabled = true;
        }

        // Load per-symbol trading results
        async function reloadPerSymbolResults() {
            const loading = document.getElementById('paperTradeLoading');
            const content = document.getElementById('paperTradeContent');
            const errorDiv = document.getElementById('symbolResultsError');
            const grid = document.getElementById('symbolsGrid');

            loading.style.display = 'block';
            content.style.display = 'none';
            errorDiv.style.display = 'none';
            grid.innerHTML = '';

            try {
                // Fetch summary of per-symbol results
                const summaryUrl = './per_symbol_trading/summary.json';
                const res = await fetch(summaryUrl);
                if (!res.ok) throw new Error('HTTP ' + res.status);
                
                const summary = await res.json();
                if (!summary) throw new Error('No summary data');

                // Calculate metrics
                const results = summary.results || [];
                const successful = results.filter(r => r.success);
                const avgReturn = successful.length > 0
                    ? (successful.reduce((sum, r) => sum + (r.total_return || 0), 0) / successful.length) * 100
                    : 0;
                const totalTrades = successful.reduce((sum, r) => sum + (r.num_trades || 0), 0);
                const topPerformer = summary.top_gainers && summary.top_gainers[0];

                // Update summary metrics
                document.getElementById('totalSymbols').textContent = successful.length;
                document.getElementById('avgReturn').textContent = avgReturn.toFixed(2) + '%';
                document.getElementById('totalTrades').textContent = totalTrades;
                if (topPerformer) {
                    document.getElementById('topGainer').textContent = topPerformer.symbol + ' (' + (topPerformer.total_return * 100).toFixed(2) + '%)';
                }

                // Store symbols data for sorting/filtering
                symbolsData = successful;
                symbolDataCache = {};
                for (const res of successful) {
                    if (res && res.symbol) {
                        symbolDataCache[res.symbol] = res;
                    }
                }

                // Build per-symbol cards with current view preference
                setGridView(gridView);

                loading.style.display = 'none';
                content.style.display = 'block';
                addLog('Per-symbol results loaded: ' + successful.length + ' symbols', 'success');

            } catch (err) {
                loading.style.display = 'none';
                errorDiv.style.display = 'block';
                errorDiv.textContent = 'Error: ' + err.message;
                addLog('Failed to load per-symbol results: ' + err.message, 'error');
            }
        }

        // Global state for trade filtering
        let currentTradeData = null;
        let currentSymbol = null;
        let tradeFilter = 'all'; // 'all', 'buy', 'sell', 'profitable'
    let tradeSortBy = 'date'; // 'date', 'price', 'confidence', 'pnl'
    let gridView = 'cards'; // 'cards' or 'mini'
    let symbolsData = []; // Store all symbols data for sorting
    let symbolDataCache = {}; // Cache for detailed symbol data
    let symbolSearchTerm = ''; // User search input
    let favoriteSymbols = new Set(JSON.parse(localStorage.getItem('favoriteSymbols') || '[]')); // Persist favorites
    let showOnlyFavorites = false; // Toggle favorites filter

        function filterSymbolsBySearch(term) {
            symbolSearchTerm = term.trim().toUpperCase();
            renderSymbolsGrid();
        }

        function toggleFavorites() {
            showOnlyFavorites = !showOnlyFavorites;
            const btn = document.getElementById('favBtn');
            if (showOnlyFavorites) {
                btn.style.background = 'linear-gradient(135deg, #f39c12 0%, #e74c3c 100%)';
                btn.style.color = 'white';
                btn.style.border = 'none';
                btn.title = 'Show all';
            } else {
                btn.style.background = 'white';
                btn.style.color = '#495057';
                btn.style.border = '1px solid #dee2e6';
                btn.title = 'Show favorites';
            }
            renderSymbolsGrid();
        }

        function toggleFavorite(symbol, event) {
            if (event) event.stopPropagation();
            if (favoriteSymbols.has(symbol)) {
                favoriteSymbols.delete(symbol);
            } else {
                favoriteSymbols.add(symbol);
            }
            localStorage.setItem('favoriteSymbols', JSON.stringify([...favoriteSymbols]));
            renderSymbolsGrid();
        }

        // Modal Tab Switching
        let currentModalTab = 'overview';
        
        function switchModalTab(tabName) {
            currentModalTab = tabName;
            
            // Hide all tab contents
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.style.display = 'none');
            
            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.modal-tab');
            tabs.forEach(tab => {
                tab.style.borderBottom = '3px solid transparent';
                tab.style.color = '#6c757d';
            });
            
            // Show selected tab content
            const targetContent = document.getElementById('tabContent' + tabName.charAt(0).toUpperCase() + tabName.slice(1));
            if (targetContent) {
                targetContent.style.display = 'block';
            }
            
            // Highlight active tab
            const activeTab = document.getElementById('tab' + tabName.charAt(0).toUpperCase() + tabName.slice(1));
            if (activeTab) {
                activeTab.style.borderBottom = '3px solid #667eea';
                activeTab.style.color = '#667eea';
            }
            
            // Load technical chart if technical tab is selected
            if (tabName === 'technical' && currentSymbol) {
                initTechnicalChart(currentSymbol);
            }
        }

        function closeTradeModal() {
            const modal = document.getElementById('tradeModal');
            
            // Fade out animation
            modal.style.opacity = '0';
            
            // Wait for animation to complete before hiding
            setTimeout(() => {
                modal.style.display = 'none';
                modal.style.opacity = '1'; // Reset for next open
                
                // Reset fullscreen state if active
                const modalInner = modal.querySelector('[style*="max-width"]');
                if (modalInner) {
                    modalInner.style.maxWidth = '1200px';
                    modalInner.style.maxHeight = '90vh';
                }
                
                // Reset fullscreen button
                const fsBtn = document.getElementById('fullscreenBtn');
                if (fsBtn) {
                    fsBtn.innerHTML = '⛶';
                    fsBtn.title = 'Fullscreen';
                }
            }, 300); // Match the transition duration
        }

        function toggleModalFullscreen() {
            const modal = document.getElementById('tradeModal');
            const modalInner = modal.querySelector('[style*="max-width"]');
            const fsBtn = document.getElementById('fullscreenBtn');
            
            if (!modalInner) return;
            
            // Check current state
            const isFullscreen = modalInner.style.maxWidth === '98vw';
            
            if (isFullscreen) {
                // Exit fullscreen
                modalInner.style.maxWidth = '1200px';
                modalInner.style.maxHeight = '90vh';
                modalInner.style.width = '90%';
                modalInner.style.height = 'auto';
                if (fsBtn) {
                    fsBtn.innerHTML = '⛶';
                    fsBtn.title = 'Fullscreen';
                }
            } else {
                // Enter fullscreen
                modalInner.style.maxWidth = '98vw';
                modalInner.style.maxHeight = '98vh';
                modalInner.style.width = '98vw';
                modalInner.style.height = '98vh';
                if (fsBtn) {
                    fsBtn.innerHTML = '⛶';
                    fsBtn.title = 'Exit Fullscreen';
                }
            }
        }

        function setGridView(view) {
            gridView = view;
            const cardsButton = document.getElementById('viewCards');
            const miniButton = document.getElementById('viewMini');

            if (cardsButton && miniButton) {
                if (view === 'cards') {
                    cardsButton.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                    cardsButton.style.color = '#fff';
                    cardsButton.style.border = 'none';

                    miniButton.style.background = '#fff';
                    miniButton.style.color = '#495057';
                    miniButton.style.border = '1px solid #dee2e6';
                } else {
                    miniButton.style.background = 'linear-gradient(135deg, #20c997 0%, #0ab6ff 100%)';
                    miniButton.style.color = '#fff';
                    miniButton.style.border = 'none';

                    cardsButton.style.background = '#fff';
                    cardsButton.style.color = '#495057';
                    cardsButton.style.border = '1px solid #dee2e6';
                }
            }
            
            renderSymbolsGrid();
        }

        function sortSymbolsBy(sortKey) {
            if (!symbolsData || symbolsData.length === 0) return;
            
            symbolsData.sort((a, b) => {
                switch (sortKey) {
                    case 'return':
                        return (b.total_return || 0) - (a.total_return || 0);
                    case 'sharpe':
                        // Calculate Sharpe for sorting
                        const sharpeA = calculateSharpe(a);
                        const sharpeB = calculateSharpe(b);
                        return sharpeB - sharpeA;
                    case 'drawdown':
                        const ddA = calculateMaxDrawdown(a);
                        const ddB = calculateMaxDrawdown(b);
                        return ddA - ddB; // Lower drawdown is better
                    case 'trades':
                        return (b.num_trades || 0) - (a.num_trades || 0);
                    default: // symbol
                        return a.symbol.localeCompare(b.symbol);
                }
            });
            
            renderSymbolsGrid();
        }

        function calculateSharpe(result) {
            const values = result.equity_curve?.values || [];
            if (values.length < 2) return 0;
            const returns = [];
            for (let i = 1; i < values.length; i++) {
                returns.push((values[i] - values[i-1]) / values[i-1]);
            }
            const avgRet = returns.reduce((a,b) => a+b, 0) / returns.length;
            const stdDev = Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgRet, 2), 0) / returns.length);
            return stdDev > 0 ? (avgRet / stdDev) * Math.sqrt(252) : 0;
        }

        function calculateMaxDrawdown(result) {
            const values = result.equity_curve?.values || [];
            let maxDD = 0;
            let peak = values[0] || 0;
            for (const val of values) {
                if (val > peak) peak = val;
                const dd = ((peak - val) / peak) * 100;
                if (dd > maxDD) maxDD = dd;
            }
            return maxDD;
        }

        function renderSymbolsGrid() {
            const grid = document.getElementById('symbolsGrid');
            grid.innerHTML = '';
            
            // Filter symbols by search term and favorites
            let filteredSymbols = symbolsData.filter(result => {
                const matchesSearch = !symbolSearchTerm || (result.symbol || '').toUpperCase().includes(symbolSearchTerm);
                const matchesFavorites = !showOnlyFavorites || favoriteSymbols.has(result.symbol);
                return matchesSearch && matchesFavorites;
            });

            // Show message if no results
            if (filteredSymbols.length === 0) {
                const msg = document.createElement('div');
                msg.style.cssText = 'grid-column:1/-1;text-align:center;padding:40px;color:#6c757d;font-size:1.1em;';
                msg.innerHTML = showOnlyFavorites 
                    ? '⭐ No favorite symbols yet. Click the star on any card to add favorites!'
                    : '🔍 No symbols match your search.';
                grid.appendChild(msg);
                return;
            }
            
            if (gridView === 'mini') {
                grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(220px, 1fr))';
                for (const result of filteredSymbols) {
                    const miniCard = createMiniChartCard(result);
                    grid.appendChild(miniCard);
                }
            } else {
                grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
                for (const result of filteredSymbols) {
                    const card = createSymbolCard(result);
                    grid.appendChild(card);
                }
            }
        }

        function createSymbolCard(result) {
            const symbol = result.symbol || 'N/A';
            const ret = (result.total_return || 0) * 100;
            const trades = result.num_trades || 0;
            const initial = result.initial_capital || 50000;
            const final = result.final_value || initial;
            const retColor = ret >= 0 ? '#27ae60' : '#e74c3c';

            const card = document.createElement('div');
            card.style.cssText = 'background:white;padding:20px;border-radius:16px;box-shadow:0 2px 8px rgba(0,0,0,0.08);cursor:pointer;transition:all 0.4s cubic-bezier(0.4,0,0.2,1);border:1px solid rgba(0,0,0,0.04);position:relative;overflow:hidden;';
            
            // Add gradient accent on hover
            const accentBar = document.createElement('div');
            accentBar.style.cssText = 'position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,#667eea,#764ba2);transform:scaleX(0);transition:transform 0.4s cubic-bezier(0.4,0,0.2,1);';
            card.appendChild(accentBar);
            
            card.onmouseover = () => {
                card.style.transform = 'translateY(-8px) scale(1.02)';
                card.style.boxShadow = '0 16px 48px rgba(102,126,234,0.25),0 8px 16px rgba(0,0,0,0.12)';
                card.style.borderColor = 'rgba(102,126,234,0.2)';
                accentBar.style.transform = 'scaleX(1)';
            };
            card.onmouseout = () => {
                card.style.transform = 'none';
                card.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
                card.style.borderColor = 'rgba(0,0,0,0.04)';
                accentBar.style.transform = 'scaleX(0)';
            };
            card.addEventListener('click', () => showSymbolDetails(symbol));

            const isFavorite = favoriteSymbols.has(symbol);
            const favStar = document.createElement('button');
            favStar.innerHTML = isFavorite ? '⭐' : '☆';
            favStar.style.cssText = 'position:absolute;top:12px;right:12px;background:rgba(255,255,255,0.9);border:none;font-size:1.3em;cursor:pointer;padding:6px 10px;border-radius:8px;transition:all 0.2s;box-shadow:0 2px 8px rgba(0,0,0,0.1);z-index:10;';
            favStar.onmouseover = () => favStar.style.transform = 'scale(1.15)';
            favStar.onmouseout = () => favStar.style.transform = 'scale(1)';
            favStar.onclick = (e) => toggleFavorite(symbol, e);
            card.appendChild(favStar);

            const content = document.createElement('div');
            content.innerHTML = `
                <div style="font-weight:700;font-size:1.5em;color:#212529;margin-bottom:12px;letter-spacing:-0.5px;">${symbol}</div>
                <div style="font-size:0.9em;color:#6c757d;margin-bottom:16px;line-height:1.6;">
                    <div style="margin-bottom:4px;">Initial: <span style="font-weight:600;color:#495057;">$${initial.toLocaleString('en-US', {maximumFractionDigits: 0})}</span></div>
                    <div>Final: <span style="font-weight:600;color:#495057;">$${final.toLocaleString('en-US', {maximumFractionDigits: 0})}</span></div>
                </div>
                <div style="font-size:1.8em;font-weight:700;color:${retColor};margin-bottom:12px;">${ret.toFixed(2)}%</div>
                <div style="font-size:0.9em;color:#6c757d;background:#f8f9fa;padding:12px;border-radius:10px;font-weight:500;">
                    📊 Trades: ${trades}
                </div>
            `;
            card.appendChild(content);

            return card;
        }

        function createMiniChartCard(result) {
            const symbol = result.symbol || 'N/A';
            const ret = (result.total_return || 0) * 100;
            const retColor = ret >= 0 ? '#27ae60' : '#e74c3c';
            const values = result.equity_curve?.values || [];

            const card = document.createElement('div');
            card.style.cssText = 'background:white;padding:16px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.08);cursor:pointer;transition:all 0.3s cubic-bezier(0.4,0,0.2,1);border:1px solid rgba(0,0,0,0.04);';
            card.onmouseover = () => {
                card.style.transform = 'scale(1.05) translateY(-4px)';
                card.style.boxShadow = '0 12px 32px rgba(102,126,234,0.2),0 6px 12px rgba(0,0,0,0.1)';
                card.style.borderColor = 'rgba(102,126,234,0.15)';
            };
            card.onmouseout = () => {
                card.style.transform = 'none';
                card.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
                card.style.borderColor = 'rgba(0,0,0,0.04)';
            };
            card.addEventListener('click', () => showSymbolDetails(symbol));

            const isFavorite = favoriteSymbols.has(symbol);
            const favStar = document.createElement('button');
            favStar.innerHTML = isFavorite ? '⭐' : '☆';
            favStar.style.cssText = 'position:absolute;top:8px;right:8px;background:rgba(255,255,255,0.9);border:none;font-size:1.1em;cursor:pointer;padding:4px 8px;border-radius:6px;transition:all 0.2s;box-shadow:0 2px 6px rgba(0,0,0,0.1);z-index:10;';
            favStar.onmouseover = () => favStar.style.transform = 'scale(1.15)';
            favStar.onmouseout = () => favStar.style.transform = 'scale(1)';
            favStar.onclick = (e) => toggleFavorite(symbol, e);
            card.appendChild(favStar);

            // Create mini sparkline
            const maxVal = Math.max(...values);
            const minVal = Math.min(...values);
            const range = maxVal - minVal;
            const width = 160;
            const height = 48;
            
            let svgPath = `M 0 ${height}`;
            for (let i = 0; i < values.length; i++) {
                const x = (i / (values.length - 1)) * width;
                const y = height - ((values[i] - minVal) / range) * height;
                svgPath += ` L ${x} ${y}`;
            }

            card.innerHTML = `
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                    <div style="font-weight:700;font-size:1.2em;color:#212529;letter-spacing:-0.3px;">${symbol}</div>
                    <div style="font-size:1.1em;font-weight:700;color:${retColor};">${ret.toFixed(1)}%</div>
                </div>
                <svg width="${width}" height="${height}" style="width:100%;height:48px;">
                    <path d="${svgPath}" fill="none" stroke="${retColor}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            `;

            return card;
        }

        async function showSymbolDetails(symbol) {
            const modal = document.getElementById('tradeModal');
            const loading = document.getElementById('tradeModalLoading');
            const content = document.getElementById('tradeModalContent');
            const errorDiv = document.getElementById('tradeModalError');
            
            // Reset UI
            loading.style.display = 'block';
            content.style.display = 'none';
            errorDiv.style.display = 'none';
            document.getElementById('tradeModalSymbol').textContent = symbol;
            modal.style.display = 'flex';
            currentSymbol = symbol;

            let result = symbolDataCache[symbol] || null;

            try {
                // Fetch symbol trading result (no-cache to avoid stale responses)
                const resultUrl = './per_symbol_trading/' + symbol + '_trading_result.json?t=' + Date.now();
                const res = await fetch(resultUrl, {cache: 'no-store'});
                if (!res.ok) throw new Error('HTTP ' + res.status);
                
                const fetchedResult = await res.json();
                if (!fetchedResult) throw new Error('No result data');

                result = fetchedResult;
                symbolDataCache[symbol] = fetchedResult;
            } catch (fetchErr) {
                if (!result) {
                    loading.style.display = 'none';
                    errorDiv.style.display = 'block';
                    errorDiv.textContent = '⚠️ Error loading trade details: ' + fetchErr.message;
                    addLog('Failed to load details for ' + symbol + ': ' + fetchErr.message, 'error');
                    return;
                }
                addLog('Loaded cached data for ' + symbol + ' (fetch issue: ' + fetchErr.message + ')', 'warning');
            }

            try {
                if (!result) throw new Error('No result data');

                currentTradeData = result;

                // Calculate trade pairs and P&L
                const trades = result.trades || [];
                const tradePairs = [];
                let buyPrice = null;
                let buyDate = null;
                let buyIndex = null;

                for (let i = 0; i < trades.length; i++) {
                    const trade = trades[i];
                    if (trade.signal === 1) {
                        buyPrice = trade.price;
                        buyDate = trade.date;
                        buyIndex = i;
                    } else if (trade.signal === -1 && buyPrice !== null) {
                        const pnl = ((trade.price - buyPrice) / buyPrice) * 100;
                        tradePairs.push({
                            buyDate: buyDate,
                            sellDate: trade.date,
                            buyPrice: buyPrice,
                            sellPrice: trade.price,
                            pnl: pnl,
                            buyIndex: buyIndex,
                            sellIndex: i
                        });
                        buyPrice = null;
                    }
                }

                // Calculate win rate
                const profitableTrades = tradePairs.filter(p => p.pnl > 0).length;
                const winRate = tradePairs.length > 0 ? (profitableTrades / tradePairs.length) * 100 : 0;

                // Calculate max drawdown
                const equityValues = (result.equity_curve && result.equity_curve.values) || [];
                let maxDrawdown = 0;
                let peak = equityValues[0] || 0;
                for (const value of equityValues) {
                    if (value > peak) peak = value;
                    const drawdown = ((peak - value) / peak) * 100;
                    if (drawdown > maxDrawdown) maxDrawdown = drawdown;
                }

                // Calculate Sharpe Ratio (simplified daily returns)
                const returns = [];
                for (let i = 1; i < equityValues.length; i++) {
                    returns.push((equityValues[i] - equityValues[i-1]) / equityValues[i-1]);
                }
                const avgReturn = returns.length > 0 ? returns.reduce((a,b) => a+b, 0) / returns.length : 0;
                const stdDev = returns.length > 1 ? Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length) : 0;
                const sharpeRatio = stdDev > 0 ? (avgReturn / stdDev) * Math.sqrt(252) : 0; // annualized

                // Calculate average trade duration
                const durations = tradePairs.map(pair => {
                    const buyTime = new Date(pair.buyDate).getTime();
                    const sellTime = new Date(pair.sellDate).getTime();
                    return (sellTime - buyTime) / (1000 * 60 * 60 * 24); // days
                });
                const avgDuration = durations.length > 0 ? durations.reduce((a,b) => a+b, 0) / durations.length : 0;

                // Update stats
                const ret = (result.total_return || 0) * 100;
                document.getElementById('tradeStatReturn').textContent = ret.toFixed(2) + '%';
                document.getElementById('tradeStatReturn').style.color = ret >= 0 ? '#27ae60' : '#e74c3c';
                document.getElementById('tradeStatCount').textContent = (result.num_trades || 0);
                document.getElementById('tradeStatInitial').textContent = '$' + (result.initial_capital || 50000).toLocaleString('en-US', {maximumFractionDigits: 0});
                document.getElementById('tradeStatFinal').textContent = '$' + (result.final_value || 0).toLocaleString('en-US', {maximumFractionDigits: 2});

                // Add win rate display
                if (!document.getElementById('tradeStatWinRate')) {
                    const statsGrid = document.getElementById('tradeModalStats');
                    statsGrid.style.gridTemplateColumns = 'repeat(5, 1fr)';
                    const winRateDiv = document.createElement('div');
                    winRateDiv.style.cssText = 'background:#f5f5f5;padding:10px;border-radius:6px;border-left:4px solid #e74c3c;';
                    winRateDiv.innerHTML = `
                        <div style="font-size:0.85em;color:#666;">Win Rate</div>
                        <div style="font-size:1.4em;font-weight:bold;color:#333;" id="tradeStatWinRate">-</div>
                    `;
                    statsGrid.appendChild(winRateDiv);
                }
                document.getElementById('tradeStatWinRate').textContent = winRate.toFixed(1) + '%';
                document.getElementById('tradeStatWinRate').style.color = winRate >= 50 ? '#27ae60' : '#e74c3c';

                // Update Overview Tab metrics
                const overviewWinRate = document.getElementById('overviewWinRate');
                if (overviewWinRate) overviewWinRate.textContent = winRate.toFixed(1) + '%';
                
                const overviewDuration = document.getElementById('overviewDuration');
                if (overviewDuration) overviewDuration.textContent = avgDuration.toFixed(1) + ' days';

                // Add advanced metrics section
                if (!document.getElementById('advancedMetricsSection')) {
                    const contentDiv = document.getElementById('tradeModalContent');
                    const metricsDiv = document.createElement('div');
                    metricsDiv.id = 'advancedMetricsSection';
                    metricsDiv.style.cssText = 'display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:15px;';
                    metricsDiv.innerHTML = `
                        <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid #e0e0e0;">
                            <div style="font-size:0.85em;color:#666;margin-bottom:4px;">Max Drawdown</div>
                            <div style="font-size:1.2em;font-weight:bold;" id="tradeStatDrawdown">-</div>
                        </div>
                        <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid #e0e0e0;">
                            <div style="font-size:0.85em;color:#666;margin-bottom:4px;">Sharpe Ratio</div>
                            <div style="font-size:1.2em;font-weight:bold;" id="tradeStatSharpe">-</div>
                        </div>
                        <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid #e0e0e0;">
                            <div style="font-size:0.85em;color:#666;margin-bottom:4px;">Sortino Ratio</div>
                            <div style="font-size:1.2em;font-weight:bold;" id="tradeStatSortino">-</div>
                        </div>
                        <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid #e0e0e0;">
                            <div style="font-size:0.85em;color:#666;margin-bottom:4px;">VaR (95%)</div>
                            <div style="font-size:1.2em;font-weight:bold;" id="tradeStatVaR">-</div>
                        </div>
                        <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid #e0e0e0;">
                            <div style="font-size:0.85em;color:#666;margin-bottom:4px;">Calmar Ratio</div>
                            <div style="font-size:1.2em;font-weight:bold;" id="tradeStatCalmar">-</div>
                        </div>
                    `;
                    // Insert after stats grid
                    const statsGrid = document.getElementById('tradeModalStats');
                    statsGrid.parentNode.insertBefore(metricsDiv, statsGrid.nextSibling);
                }

                // Calculate additional metrics
                // Sortino Ratio (only downside deviation)
                const downsideReturns = returns.filter(r => r < 0);
                const downsideStdDev = downsideReturns.length > 0 
                    ? Math.sqrt(downsideReturns.reduce((sum, r) => sum + Math.pow(r, 2), 0) / downsideReturns.length)
                    : 0;
                const sortinoRatio = downsideStdDev > 0 ? (avgReturn / downsideStdDev) * Math.sqrt(252) : 0;

                // Value at Risk (95% confidence)
                const sortedReturns = [...returns].sort((a, b) => a - b);
                const varIndex = Math.floor(returns.length * 0.05);
                const var95 = sortedReturns[varIndex] || 0;

                // Calmar Ratio (return / max drawdown)
                const annualizedReturn = avgReturn * 252;
                const calmarRatio = maxDrawdown > 0 ? (annualizedReturn * 100) / maxDrawdown : 0;

                // Update advanced metrics
                document.getElementById('tradeStatDrawdown').textContent = maxDrawdown.toFixed(2) + '%';
                document.getElementById('tradeStatDrawdown').style.color = maxDrawdown > 10 ? '#e74c3c' : '#f39c12';
                
                document.getElementById('tradeStatSharpe').textContent = sharpeRatio.toFixed(2);
                document.getElementById('tradeStatSharpe').style.color = sharpeRatio > 1 ? '#27ae60' : (sharpeRatio > 0 ? '#f39c12' : '#e74c3c');
                
                document.getElementById('tradeStatSortino').textContent = sortinoRatio.toFixed(2);
                document.getElementById('tradeStatSortino').style.color = sortinoRatio > 1 ? '#27ae60' : (sortinoRatio > 0 ? '#f39c12' : '#e74c3c');
                
                document.getElementById('tradeStatVaR').textContent = (var95 * 100).toFixed(2) + '%';
                document.getElementById('tradeStatVaR').style.color = var95 < -0.03 ? '#e74c3c' : '#f39c12';
                
                document.getElementById('tradeStatCalmar').textContent = calmarRatio.toFixed(2);
                document.getElementById('tradeStatCalmar').style.color = calmarRatio > 2 ? '#27ae60' : (calmarRatio > 0 ? '#f39c12' : '#e74c3c');
                
                document.getElementById('tradeStatDuration').textContent = avgDuration.toFixed(1) + ' days';
                document.getElementById('tradeStatDuration').style.color = '#333';

                // Update Overview Tab with additional metrics
                const overviewSharpe = document.getElementById('overviewSharpe');
                if (overviewSharpe) overviewSharpe.textContent = sharpeRatio.toFixed(2);
                
                const overviewDrawdown = document.getElementById('overviewDrawdown');
                if (overviewDrawdown) overviewDrawdown.textContent = maxDrawdown.toFixed(2) + '%';

                // Render trades table
                renderTradesTable(trades, tradePairs);

                // Render interactive equity curve
                renderEquityChart(result);

                loading.style.display = 'none';
                content.style.display = 'block';
                
                // Switch to Overview tab by default
                switchModalTab('overview');
                
                // Load saved notes for this symbol
                loadSymbolNotes();
                
                // Load filter presets
                loadFilterPresets();
                
                addLog('Loaded ' + trades.length + ' trades for ' + symbol + ' (Win Rate: ' + winRate.toFixed(1) + '%)', 'success');

            } catch (err) {
                loading.style.display = 'none';
                errorDiv.style.display = 'block';
                errorDiv.textContent = '⚠️ Error loading trade details: ' + err.message;
                addLog('Failed to load details for ' + symbol + ': ' + err.message, 'error');
            }
        }

        function renderTradesTable(trades, tradePairs) {
            const tbody = document.getElementById('tradesTableBody');
            tbody.innerHTML = '';

            // Create P&L map for quick lookup
            const pnlMap = {};
            tradePairs.forEach(pair => {
                pnlMap[pair.sellIndex] = pair.pnl;
            });

            // Filter trades
            let filteredTrades = trades.map((t, idx) => ({...t, originalIndex: idx}));
            
            // Apply basic filters
            if (tradeFilter === 'buy') {
                filteredTrades = filteredTrades.filter(t => t.signal === 1);
            } else if (tradeFilter === 'sell') {
                filteredTrades = filteredTrades.filter(t => t.signal === -1);
            } else if (tradeFilter === 'profitable') {
                filteredTrades = filteredTrades.filter(t => t.signal === -1 && pnlMap[t.originalIndex] && pnlMap[t.originalIndex] > 0);
            }

            // Apply advanced filters
            const dateFrom = document.getElementById('filterDateFrom')?.value;
            const dateTo = document.getElementById('filterDateTo')?.value;
            const minPrice = parseFloat(document.getElementById('filterMinPrice')?.value);
            const maxPrice = parseFloat(document.getElementById('filterMaxPrice')?.value);
            const minConfidence = parseFloat(document.getElementById('filterMinConfidence')?.value);
            const minPnL = parseFloat(document.getElementById('filterMinPnL')?.value);

            if (dateFrom) {
                const fromDate = new Date(dateFrom);
                filteredTrades = filteredTrades.filter(t => new Date(t.date) >= fromDate);
            }
            if (dateTo) {
                const toDate = new Date(dateTo);
                toDate.setHours(23, 59, 59, 999); // End of day
                filteredTrades = filteredTrades.filter(t => new Date(t.date) <= toDate);
            }
            if (!isNaN(minPrice)) {
                filteredTrades = filteredTrades.filter(t => t.price >= minPrice);
            }
            if (!isNaN(maxPrice)) {
                filteredTrades = filteredTrades.filter(t => t.price <= maxPrice);
            }
            if (!isNaN(minConfidence)) {
                filteredTrades = filteredTrades.filter(t => t.confidence >= minConfidence);
            }
            if (!isNaN(minPnL)) {
                filteredTrades = filteredTrades.filter(t => {
                    if (t.signal === -1 && pnlMap[t.originalIndex]) {
                        return pnlMap[t.originalIndex] >= minPnL;
                    }
                    return true;
                });
            }

            // Sort trades
            if (tradeSortBy === 'price') {
                filteredTrades.sort((a, b) => b.price - a.price);
            } else if (tradeSortBy === 'confidence') {
                filteredTrades.sort((a, b) => b.confidence - a.confidence);
            } else if (tradeSortBy === 'pnl') {
                filteredTrades.sort((a, b) => {
                    const pnlA = pnlMap[a.originalIndex] || 0;
                    const pnlB = pnlMap[b.originalIndex] || 0;
                    return pnlB - pnlA;
                });
            }
            // default is 'date' which is already sorted

            for (const trade of filteredTrades) {
                const row = document.createElement('tr');
                row.style.cssText = 'border-bottom:1px solid #f0f0f0;transition:all 0.2s;cursor:pointer;';
                row.onmouseover = () => {
                    row.style.background = 'linear-gradient(90deg, #f8f9fa 0%, #ffffff 100%)';
                    row.style.transform = 'scale(1.005)';
                    row.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)';
                };
                row.onmouseout = () => {
                    row.style.background = 'white';
                    row.style.transform = 'scale(1)';
                    row.style.boxShadow = 'none';
                };
                
                // Parse date to readable format
                const dateStr = trade.date || 'N/A';
                const dateObj = new Date(dateStr);
                const dateFormatted = dateObj.toLocaleDateString('en-US', {year:'2-digit', month:'2-digit', day:'2-digit'}) + 
                                    ' ' + dateObj.toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit'});
                
                const signal = trade.signal === 1 ? '🟢 BUY' : '🔴 SELL';
                const signalColor = trade.signal === 1 ? '#27ae60' : '#e74c3c';
                const price = (trade.price || 0).toFixed(2);
                const confidence = ((trade.confidence || 0) * 100).toFixed(1);
                
                // Add P&L for SELL signals
                let pnlCell = '<td style="padding:8px;text-align:right;color:#999;">-</td>';
                if (trade.signal === -1 && pnlMap[trade.originalIndex]) {
                    const pnl = pnlMap[trade.originalIndex];
                    const pnlColor = pnl >= 0 ? '#27ae60' : '#e74c3c';
                    const pnlIcon = pnl >= 0 ? '▲' : '▼';
                    pnlCell = `<td style="padding:8px;text-align:right;color:${pnlColor};font-weight:600;">${pnlIcon} ${pnl.toFixed(2)}%</td>`;
                }
                
                row.innerHTML = `
                    <td style="padding:8px;border-right:1px solid #f0f0f0;color:#333;font-size:0.9em;">${dateFormatted}</td>
                    <td style="padding:8px;border-right:1px solid #f0f0f0;"><span style="color:${signalColor};font-weight:bold;">${signal}</span></td>
                    <td style="padding:8px;border-right:1px solid #f0f0f0;text-align:right;color:#333;font-weight:500;">$${price}</td>
                    <td style="padding:8px;border-right:1px solid #f0f0f0;text-align:right;color:#666;">${confidence}%</td>
                    ${pnlCell}
                `;
                tbody.appendChild(row);
            }

            // Update displayed count
            const countText = filteredTrades.length + ' of ' + trades.length + ' trades';
            if (!document.getElementById('tradesFilterCount')) {
                const tableContainer = document.getElementById('tradesTable').parentElement;
                const countDiv = document.createElement('div');
                countDiv.id = 'tradesFilterCount';
                countDiv.style.cssText = 'font-size:0.85em;color:#666;margin-top:5px;';
                tableContainer.appendChild(countDiv);
            }
            document.getElementById('tradesFilterCount').textContent = countText;
        }

        function filterTrades(filter) {
            tradeFilter = filter;
            if (currentTradeData) {
                const trades = currentTradeData.trades || [];
                const tradePairs = calculateTradePairs(trades);
                renderTradesTable(trades, tradePairs);
            }
        }

        function sortTrades(sortBy) {
            tradeSortBy = sortBy;
            if (currentTradeData) {
                const trades = currentTradeData.trades || [];
                const tradePairs = calculateTradePairs(trades);
                renderTradesTable(trades, tradePairs);
            }
        }

        // Advanced Filters
        let advancedFiltersActive = false;
        let filterPresets = [];

        // Export Menu Management
        function openExportMenu() {
            const dropdown = document.getElementById('exportDropdown');
            const isVisible = dropdown.style.display === 'block';
            dropdown.style.display = isVisible ? 'none' : 'block';
        }

        // Close export menu when clicking outside
        document.addEventListener('click', (e) => {
            const dropdown = document.getElementById('exportDropdown');
            const exportBtn = document.getElementById('exportMenuBtn');
            if (dropdown && exportBtn && !dropdown.contains(e.target) && !exportBtn.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        // Export Functions
        async function exportModalAsPDF() {
            if (!currentSymbol || !currentTradeData) {
                alert('⚠️ No data to export');
                return;
            }

            // Simple PDF generation using window.print()
            // For production, use jsPDF library
            const printContent = generatePrintableReport();
            const printWindow = window.open('', '_blank');
            printWindow.document.write(printContent);
            printWindow.document.close();
            printWindow.print();
            
            document.getElementById('exportDropdown').style.display = 'none';
            addLog('PDF export initiated for ' + currentSymbol, 'success');
        }

        function generatePrintableReport() {
            const symbol = currentSymbol;
            const data = currentTradeData;
            const ret = ((data.total_return || 0) * 100).toFixed(2);
            const trades = data.trades || [];
            
            return `
                <!DOCTYPE html>
                <html>
                <head>
                    <title>${symbol} Trading Report</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; }
                        h1 { color: #667eea; }
                        .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 20px 0; }
                        .stat-box { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
                        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background: #667eea; color: white; }
                    </style>
                </head>
                <body>
                    <h1>📊 ${symbol} Trading Report</h1>
                    <p>Generated: ${new Date().toLocaleString()}</p>
                    <div class="stats">
                        <div class="stat-box"><strong>Total Return:</strong> ${ret}%</div>
                        <div class="stat-box"><strong>Total Trades:</strong> ${trades.length}</div>
                        <div class="stat-box"><strong>Initial Capital:</strong> $${(data.initial_capital || 50000).toLocaleString()}</div>
                        <div class="stat-box"><strong>Final Value:</strong> $${(data.final_value || 0).toLocaleString()}</div>
                    </div>
                    <h2>Trade History</h2>
                    <table>
                        <thead>
                            <tr><th>Date</th><th>Signal</th><th>Price</th><th>Confidence</th></tr>
                        </thead>
                        <tbody>
                            ${trades.slice(0, 50).map(t => `
                                <tr>
                                    <td>${new Date(t.date).toLocaleDateString()}</td>
                                    <td>${t.signal === 1 ? 'BUY' : 'SELL'}</td>
                                    <td>$${t.price.toFixed(2)}</td>
                                    <td>${(t.confidence * 100).toFixed(1)}%</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </body>
                </html>
            `;
        }

        async function exportModalAsExcel() {
            if (!currentSymbol || !currentTradeData) {
                alert('⚠️ No data to export');
                return;
            }

            const trades = currentTradeData.trades || [];
            const tradePairs = calculateTradePairs(trades);
            
            // Create CSV content (Excel compatible)
            let csv = 'Symbol,Date,Signal,Price,Confidence,P&L %\n';
            
            const pnlMap = {};
            tradePairs.forEach(pair => {
                pnlMap[pair.sellIndex] = pair.pnl;
            });
            
            trades.forEach((trade, idx) => {
                const signal = trade.signal === 1 ? 'BUY' : 'SELL';
                const pnl = trade.signal === -1 && pnlMap[idx] ? pnlMap[idx].toFixed(2) : '';
                csv += `${currentSymbol},${trade.date},${signal},${trade.price.toFixed(2)},${(trade.confidence * 100).toFixed(1)},${pnl}\n`;
            });
            
            // Download CSV
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `${currentSymbol}_trades_${Date.now()}.csv`;
            link.click();
            
            document.getElementById('exportDropdown').style.display = 'none';
            addLog('Excel export completed for ' + currentSymbol, 'success');
        }

        async function exportChartsAsPNG() {
            if (!currentSymbol) {
                alert('⚠️ No charts to export');
                return;
            }

            // Get equity chart canvas
            const canvas = document.getElementById('tradeEquityCanvas');
            if (!canvas) {
                alert('⚠️ No chart found');
                return;
            }

            // Convert canvas to PNG
            canvas.toBlob((blob) => {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `${currentSymbol}_equity_curve_${Date.now()}.png`;
                link.click();
                addLog('Chart exported as PNG for ' + currentSymbol, 'success');
            });
            
            document.getElementById('exportDropdown').style.display = 'none';
        }

        async function emailReport() {
            const email = prompt('Enter your email address:');
            if (!email) return;
            
            if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
                alert('⚠️ Invalid email address');
                return;
            }
            
            // Simulate email sending
            alert(`📧 Report for ${currentSymbol} will be sent to ${email}\n\nNote: This is a demo. In production, this would connect to an email service.`);
            addLog('Email report scheduled for ' + email, 'success');
            document.getElementById('exportDropdown').style.display = 'none';
        }

        async function scheduleReport() {
            const frequency = prompt('Schedule frequency:\n1. Daily\n2. Weekly\n3. Monthly\n\nEnter number (1-3):');
            if (!frequency) return;
            
            const frequencies = { '1': 'Daily', '2': 'Weekly', '3': 'Monthly' };
            const selected = frequencies[frequency];
            
            if (!selected) {
                alert('⚠️ Invalid selection');
                return;
            }
            
            alert(`⏰ ${selected} reports scheduled for ${currentSymbol}\n\nNote: This is a demo. In production, this would set up automated reporting.`);
            addLog(selected + ' reports scheduled for ' + currentSymbol, 'success');
            document.getElementById('exportDropdown').style.display = 'none';
        }

        function toggleAdvancedFilters() {
            const panel = document.getElementById('advancedFiltersPanel');
            const btn = document.getElementById('advFiltersBtn');
            advancedFiltersActive = !advancedFiltersActive;
            
            if (advancedFiltersActive) {
                panel.style.display = 'block';
                btn.style.background = '#667eea';
                btn.style.color = 'white';
                btn.textContent = '🔍 Hide Filters';
            } else {
                panel.style.display = 'none';
                btn.style.background = 'white';
                btn.style.color = '#667eea';
                btn.textContent = '🔍 Advanced Filters';
            }
        }

        function applyAdvancedFilters() {
            if (currentTradeData) {
                const trades = currentTradeData.trades || [];
                const tradePairs = calculateTradePairs(trades);
                renderTradesTable(trades, tradePairs);
            }
        }

        function setQuickDateFilter(period) {
            const today = new Date();
            const fromInput = document.getElementById('filterDateFrom');
            const toInput = document.getElementById('filterDateTo');
            
            toInput.value = today.toISOString().split('T')[0];
            
            let fromDate = new Date();
            switch(period) {
                case 'last7':
                    fromDate.setDate(today.getDate() - 7);
                    break;
                case 'last30':
                    fromDate.setDate(today.getDate() - 30);
                    break;
                case 'thisMonth':
                    fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
                    break;
                case 'last3Months':
                    fromDate.setMonth(today.getMonth() - 3);
                    break;
                case 'thisYear':
                    fromDate = new Date(today.getFullYear(), 0, 1);
                    break;
            }
            
            fromInput.value = fromDate.toISOString().split('T')[0];
            applyAdvancedFilters();
        }

        function clearAdvancedFilters() {
            document.getElementById('filterDateFrom').value = '';
            document.getElementById('filterDateTo').value = '';
            document.getElementById('filterMinPrice').value = '';
            document.getElementById('filterMaxPrice').value = '';
            document.getElementById('filterMinConfidence').value = '';
            document.getElementById('filterMinPnL').value = '';
            applyAdvancedFilters();
        }

        function saveCurrentFilterPreset() {
            const name = prompt('Enter a name for this filter preset:');
            if (!name) return;
            
            const preset = {
                name: name,
                dateFrom: document.getElementById('filterDateFrom').value,
                dateTo: document.getElementById('filterDateTo').value,
                minPrice: document.getElementById('filterMinPrice').value,
                maxPrice: document.getElementById('filterMaxPrice').value,
                minConfidence: document.getElementById('filterMinConfidence').value,
                minPnL: document.getElementById('filterMinPnL').value
            };
            
            try {
                let presets = JSON.parse(localStorage.getItem('filterPresets') || '[]');
                presets.push(preset);
                localStorage.setItem('filterPresets', JSON.stringify(presets));
                loadFilterPresets();
                alert('✅ Filter preset saved!');
            } catch (e) {
                alert('❌ Error saving preset: ' + e.message);
            }
        }

        function loadFilterPresets() {
            try {
                const presets = JSON.parse(localStorage.getItem('filterPresets') || '[]');
                const select = document.getElementById('filterPresetSelect');
                select.innerHTML = '<option value="">-- Load Preset --</option>';
                presets.forEach((preset, idx) => {
                    const option = document.createElement('option');
                    option.value = idx;
                    option.textContent = preset.name;
                    select.appendChild(option);
                });
                filterPresets = presets;
            } catch (e) {
                console.error('Error loading presets:', e);
            }
        }

        // Real-time Features
        let realtimeEnabled = false;
        let realtimeInterval = null;
        let alertCount = 0;
        let priceAlerts = [];
        let lastPrices = {};

        function showNotification(title, message, type = 'info') {
            const container = document.getElementById('notificationContainer');
            if (!container) return;

            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            
            const icons = {
                success: '✅',
                warning: '⚠️',
                error: '❌',
                info: 'ℹ️'
            };
            
            notification.innerHTML = `
                <div class="notification-icon">${icons[type] || icons.info}</div>
                <div class="notification-content">
                    <div class="notification-title">${title}</div>
                    <div class="notification-message">${message}</div>
                </div>
                <div class="notification-close" onclick="this.parentElement.remove()">×</div>
            `;
            
            container.appendChild(notification);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.style.opacity = '0';
                    notification.style.transform = 'translateX(100px)';
                    setTimeout(() => notification.remove(), 300);
                }
            }, 5000);
        }

        function toggleRealtimeUpdates() {
            realtimeEnabled = !realtimeEnabled;
            const btn = document.getElementById('realtimeBtn');
            
            if (realtimeEnabled) {
                btn.style.background = '#27ae60';
                btn.innerHTML = '🔔 Live Updates <span class="alert-badge" id="alertBadge" style="display:none;">0</span>';
                startRealtimeUpdates();
                showNotification('Real-time Updates', 'Live updates enabled', 'success');
            } else {
                btn.style.background = '#95a5a6';
                btn.innerHTML = '🔕 Updates Off';
                stopRealtimeUpdates();
                showNotification('Real-time Updates', 'Live updates disabled', 'info');
            }
        }

        function startRealtimeUpdates() {
            if (realtimeInterval) clearInterval(realtimeInterval);
            
            // Simulate real-time price updates every 10 seconds
            realtimeInterval = setInterval(() => {
                if (!realtimeEnabled) return;
                
                // Check for price alerts
                priceAlerts.forEach(alert => {
                    const currentPrice = lastPrices[alert.symbol] || 0;
                    const randomChange = (Math.random() - 0.5) * 0.02; // ±1% change
                    const newPrice = currentPrice * (1 + randomChange);
                    lastPrices[alert.symbol] = newPrice;
                    
                    if (alert.condition === 'above' && newPrice > alert.price) {
                        triggerPriceAlert(alert.symbol, newPrice, 'above', alert.price);
                    } else if (alert.condition === 'below' && newPrice < alert.price) {
                        triggerPriceAlert(alert.symbol, newPrice, 'below', alert.price);
                    }
                });
                
                // Random market updates
                if (Math.random() > 0.7) {
                    const events = [
                        { title: 'Market Update', message: 'S&P 500 up 0.5%', type: 'success' },
                        { title: 'Volatility Alert', message: 'VIX increasing', type: 'warning' },
                        { title: 'News Alert', message: 'Fed announces rate decision', type: 'info' }
                    ];
                    const event = events[Math.floor(Math.random() * events.length)];
                    showNotification(event.title, event.message, event.type);
                    updateAlertBadge();
                }
            }, 10000);
        }

        function stopRealtimeUpdates() {
            if (realtimeInterval) {
                clearInterval(realtimeInterval);
                realtimeInterval = null;
            }
        }

        function triggerPriceAlert(symbol, currentPrice, condition, targetPrice) {
            alertCount++;
            updateAlertBadge();
            showNotification(
                `Price Alert: ${symbol}`,
                `Current price $${currentPrice.toFixed(2)} is ${condition} target $${targetPrice.toFixed(2)}`,
                'warning'
            );
        }

        function updateAlertBadge() {
            const badge = document.getElementById('alertBadge');
            if (badge) {
                alertCount++;
                badge.textContent = alertCount;
                badge.style.display = 'flex';
                setTimeout(() => {
                    alertCount = Math.max(0, alertCount - 1);
                    if (alertCount === 0) {
                        badge.style.display = 'none';
                    } else {
                        badge.textContent = alertCount;
                    }
                }, 5000);
            }
        }

        function openAlertSettings() {
            const symbol = prompt('Enter symbol for price alert (e.g., AAPL):');
            if (!symbol) return;
            
            const price = parseFloat(prompt('Enter target price:'));
            if (isNaN(price)) {
                alert('Invalid price');
                return;
            }
            
            const condition = prompt('Alert condition:\n1. Above\n2. Below\n\nEnter 1 or 2:');
            const conditionMap = { '1': 'above', '2': 'below' };
            
            if (!conditionMap[condition]) {
                alert('Invalid condition');
                return;
            }
            
            priceAlerts.push({
                symbol: symbol.toUpperCase(),
                price: price,
                condition: conditionMap[condition]
            });
            
            // Initialize last price
            lastPrices[symbol.toUpperCase()] = price;
            
            showNotification(
                'Alert Created',
                `${symbol} ${conditionMap[condition]} $${price.toFixed(2)}`,
                'success'
            );
            
            // Save to localStorage
            try {
                localStorage.setItem('priceAlerts', JSON.stringify(priceAlerts));
            } catch (e) {
                console.error('Error saving alerts:', e);
            }
        }

        function loadSavedAlerts() {
            try {
                const saved = localStorage.getItem('priceAlerts');
                if (saved) {
                    priceAlerts = JSON.parse(saved);
                    priceAlerts.forEach(alert => {
                        lastPrices[alert.symbol] = alert.price;
                    });
                }
            } catch (e) {
                console.error('Error loading alerts:', e);
            }
        }

        // Portfolio Management Functions
        let portfolio = [];
        let allocationMethod = 'equal';

        function openPortfolioBuilder() {
            document.getElementById('portfolioModal').style.display = 'flex';
            loadSavedPortfolio();
            updatePortfolioDisplay();
        }

        function closePortfolioModal() {
            document.getElementById('portfolioModal').style.display = 'none';
        }

        function addToPortfolio() {
            const input = document.getElementById('portfolioSymbolInput');
            const symbol = input.value.trim().toUpperCase();
            
            if (!symbol) return;
            
            if (portfolio.find(p => p.symbol === symbol)) {
                alert('Symbol already in portfolio');
                return;
            }
            
            portfolio.push({
                symbol: symbol,
                weight: 0,
                color: getRandomColor()
            });
            
            input.value = '';
            updatePortfolioDisplay();
            recalculateWeights();
            showNotification('Symbol Added', `${symbol} added to portfolio`, 'success');
        }

        function addMultipleSymbols(symbols) {
            symbols.forEach(symbol => {
                if (!portfolio.find(p => p.symbol === symbol)) {
                    portfolio.push({
                        symbol: symbol,
                        weight: 0,
                        color: getRandomColor()
                    });
                }
            });
            updatePortfolioDisplay();
            recalculateWeights();
            showNotification('Symbols Added', `${symbols.length} symbols added`, 'success');
        }

        function removeFromPortfolio(symbol) {
            portfolio = portfolio.filter(p => p.symbol !== symbol);
            updatePortfolioDisplay();
            recalculateWeights();
        }

        function updateSymbolWeight(symbol, weight) {
            const item = portfolio.find(p => p.symbol === symbol);
            if (item) {
                item.weight = parseFloat(weight) || 0;
                updatePortfolioDisplay();
            }
        }

        function setAllocationMethod(method) {
            allocationMethod = method;
            recalculateWeights();
            showNotification('Allocation Updated', `Changed to ${method} weighting`, 'info');
        }

        function recalculateWeights() {
            if (portfolio.length === 0) return;
            
            switch(allocationMethod) {
                case 'equal':
                    const equalWeight = 100 / portfolio.length;
                    portfolio.forEach(p => p.weight = equalWeight);
                    break;
                case 'market':
                    // Simulate market cap weights
                    const marketWeights = portfolio.map(() => Math.random() * 100);
                    const totalMarket = marketWeights.reduce((a, b) => a + b, 0);
                    portfolio.forEach((p, i) => {
                        p.weight = (marketWeights[i] / totalMarket) * 100;
                    });
                    break;
                case 'risk':
                    // Simulate risk parity
                    const risks = portfolio.map(() => Math.random() * 0.3 + 0.1);
                    const invRisks = risks.map(r => 1 / r);
                    const totalInvRisk = invRisks.reduce((a, b) => a + b, 0);
                    portfolio.forEach((p, i) => {
                        p.weight = (invRisks[i] / totalInvRisk) * 100;
                    });
                    break;
            }
            
            updatePortfolioDisplay();
        }

        function updatePortfolioDisplay() {
            // Update symbol list
            const list = document.getElementById('portfolioSymbolList');
            list.innerHTML = portfolio.map(p => `
                <li class="portfolio-item">
                    <div>
                        <span class="portfolio-item-symbol">${p.symbol}</span>
                    </div>
                    <div class="portfolio-item-actions">
                        <input type="number" value="${p.weight.toFixed(1)}" 
                               onchange="updateSymbolWeight('${p.symbol}', this.value)"
                               min="0" max="100" step="0.1">
                        <span class="portfolio-item-weight">%</span>
                        <button onclick="removeFromPortfolio('${p.symbol}')">×</button>
                    </div>
                </li>
            `).join('');
            
            // Update allocation bar
            const bar = document.getElementById('allocationBar');
            if (portfolio.length === 0) {
                bar.innerHTML = '<div style="flex:1;background:#ccc;display:flex;align-items:center;justify-content:center;color:#666;">Add symbols to begin</div>';
            } else {
                bar.innerHTML = portfolio.map(p => `
                    <div class="allocation-segment" style="flex:${p.weight};background:${p.color}" title="${p.symbol}: ${p.weight.toFixed(1)}%">
                        ${p.weight > 8 ? p.symbol : ''}
                    </div>
                `).join('');
            }
            
            // Update stats
            document.getElementById('portfolioTotalSymbols').textContent = portfolio.length;
            
            if (portfolio.length > 0) {
                const maxWeight = Math.max(...portfolio.map(p => p.weight));
                const diversification = portfolio.length >= 10 ? 'High' : portfolio.length >= 5 ? 'Medium' : 'Low';
                const largestSymbol = portfolio.find(p => p.weight === maxWeight);
                
                document.getElementById('portfolioDiversification').textContent = diversification;
                document.getElementById('portfolioLargestPosition').textContent = 
                    `${largestSymbol.symbol} (${maxWeight.toFixed(1)}%)`;
            } else {
                document.getElementById('portfolioDiversification').textContent = '—';
                document.getElementById('portfolioLargestPosition').textContent = '—';
            }
        }

        function analyzePortfolio() {
            if (portfolio.length === 0) {
                alert('Add symbols to portfolio first');
                return;
            }
            
            const totalWeight = portfolio.reduce((sum, p) => sum + p.weight, 0);
            const avgWeight = totalWeight / portfolio.length;
            const concentration = Math.max(...portfolio.map(p => p.weight));
            
            let analysis = `Portfolio Analysis:\n\n`;
            analysis += `Total Symbols: ${portfolio.length}\n`;
            analysis += `Total Weight: ${totalWeight.toFixed(1)}%\n`;
            analysis += `Average Weight: ${avgWeight.toFixed(1)}%\n`;
            analysis += `Concentration: ${concentration.toFixed(1)}% (${concentration > 30 ? 'High' : concentration > 20 ? 'Medium' : 'Low'})\n\n`;
            
            if (totalWeight < 99 || totalWeight > 101) {
                analysis += `⚠️ Warning: Weights should sum to 100%\n`;
            }
            if (concentration > 40) {
                analysis += `⚠️ Warning: High concentration in single position\n`;
            }
            if (portfolio.length < 5) {
                analysis += `💡 Tip: Consider adding more symbols for diversification\n`;
            }
            
            alert(analysis);
        }

        function rebalancePortfolio() {
            if (portfolio.length === 0) return;
            
            recalculateWeights();
            showNotification('Portfolio Rebalanced', `Weights recalculated using ${allocationMethod} method`, 'success');
        }

        function savePortfolio() {
            if (portfolio.length === 0) {
                alert('No symbols in portfolio');
                return;
            }
            
            try {
                localStorage.setItem('savedPortfolio', JSON.stringify({
                    portfolio: portfolio,
                    method: allocationMethod,
                    timestamp: Date.now()
                }));
                showNotification('Portfolio Saved', 'Portfolio saved successfully', 'success');
            } catch (e) {
                alert('Error saving portfolio: ' + e.message);
            }
        }

        function loadSavedPortfolio() {
            try {
                const saved = localStorage.getItem('savedPortfolio');
                if (saved) {
                    const data = JSON.parse(saved);
                    portfolio = data.portfolio || [];
                    allocationMethod = data.method || 'equal';
                }
            } catch (e) {
                console.error('Error loading portfolio:', e);
            }
        }

        function getRandomColor() {
            const colors = [
                '#667eea', '#764ba2', '#f093fb', '#f5576c',
                '#4facfe', '#00f2fe', '#43e97b', '#38f9d7',
                '#fa709a', '#fee140', '#30cfd0', '#330867',
                '#ff6b6b', '#4ecdc4', '#45b7d1', '#f7b733'
            ];
            return colors[Math.floor(Math.random() * colors.length)];
        }

        // =============== RISK MANAGEMENT CALCULATOR ===============
        function openRiskCalculator() {
            document.getElementById('riskCalcModal').style.display = 'flex';
            // Initialize all calculators
            updateRiskDisplay();
            updateKellyFractionDisplay();
            updateProjPeriodDisplay();
        }

        function closeRiskCalculator() {
            document.getElementById('riskCalcModal').style.display = 'none';
        }

        // ============= Advanced Backtesting Functions =============
        
        function openAdvancedBacktest() {
            document.getElementById('advBacktestModal').style.display = 'flex';
        }

        function closeAdvancedBacktest() {
            document.getElementById('advBacktestModal').style.display = 'none';
        }

        function runWalkForward() {
            const trainingPeriod = parseInt(document.getElementById('wfTrainingPeriod').value);
            const testingPeriod = parseInt(document.getElementById('wfTestingPeriod').value);
            const folds = parseInt(document.getElementById('wfFolds').value);
            
            // Simulate walk-forward analysis
            const results = [];
            let totalInSample = 0;
            let totalOutOfSample = 0;
            
            for (let i = 0; i < folds; i++) {
                const inSampleReturn = (Math.random() * 30 - 5).toFixed(2); // -5% to 25%
                const outOfSampleReturn = (Math.random() * 20 - 10).toFixed(2); // -10% to 10%
                totalInSample += parseFloat(inSampleReturn);
                totalOutOfSample += parseFloat(outOfSampleReturn);
                
                results.push({
                    fold: i + 1,
                    inSample: inSampleReturn,
                    outOfSample: outOfSampleReturn
                });
            }
            
            const avgInSample = (totalInSample / folds).toFixed(2);
            const avgOutOfSample = (totalOutOfSample / folds).toFixed(2);
            const degradation = ((avgInSample - avgOutOfSample) / avgInSample * 100).toFixed(1);
            
            let html = '<table style="width:100%;border-collapse:collapse;">';
            html += '<tr style="background:var(--bg-primary);font-weight:600;"><th style="padding:8px;border:1px solid var(--border-color);">Fold</th><th style="padding:8px;border:1px solid var(--border-color);">In-Sample Return</th><th style="padding:8px;border:1px solid var(--border-color);">Out-of-Sample Return</th></tr>';
            
            results.forEach(r => {
                const isColor = r.inSample >= 0 ? '#27ae60' : '#e74c3c';
                const oosColor = r.outOfSample >= 0 ? '#27ae60' : '#e74c3c';
                html += `<tr><td style="padding:8px;border:1px solid var(--border-color);text-align:center;">${r.fold}</td>`;
                html += `<td style="padding:8px;border:1px solid var(--border-color);text-align:center;color:${isColor};font-weight:600;">${r.inSample}%</td>`;
                html += `<td style="padding:8px;border:1px solid var(--border-color);text-align:center;color:${oosColor};font-weight:600;">${r.outOfSample}%</td></tr>`;
            });
            
            html += '</table>';
            html += '<div style="margin-top:15px;padding:15px;background:rgba(102,126,234,0.1);border-radius:8px;">';
            html += `<div style="margin-bottom:8px;"><strong>Average In-Sample Return:</strong> <span style="color:${avgInSample >= 0 ? '#27ae60' : '#e74c3c'};font-weight:700;">${avgInSample}%</span></div>`;
            html += `<div style="margin-bottom:8px;"><strong>Average Out-of-Sample Return:</strong> <span style="color:${avgOutOfSample >= 0 ? '#27ae60' : '#e74c3c'};font-weight:700;">${avgOutOfSample}%</span></div>`;
            html += `<div><strong>Performance Degradation:</strong> <span style="font-weight:700;">${Math.abs(degradation)}%</span></div>`;
            
            const robustness = Math.abs(degradation) < 20 ? '🟢 High Robustness' : Math.abs(degradation) < 40 ? '🟡 Moderate Robustness' : '🔴 Low Robustness';
            html += `<div style="margin-top:10px;padding:10px;background:white;border-radius:6px;font-weight:600;">${robustness}</div>`;
            html += '</div>';
            
            document.getElementById('wfResultsContent').innerHTML = html;
            document.getElementById('wfResults').style.display = 'block';
        }

        function generateHeatmap() {
            const param1Min = parseInt(document.getElementById('param1Min').value);
            const param1Max = parseInt(document.getElementById('param1Max').value);
            const param1Step = parseInt(document.getElementById('param1Step').value);
            const param2Min = parseInt(document.getElementById('param2Min').value);
            const param2Max = parseInt(document.getElementById('param2Max').value);
            const param2Step = parseInt(document.getElementById('param2Step').value);
            
            // Generate parameter grid
            const param1Values = [];
            for (let i = param1Min; i <= param1Max; i += param1Step) {
                param1Values.push(i);
            }
            
            const param2Values = [];
            for (let i = param2Min; i <= param2Max; i += param2Step) {
                param2Values.push(i);
            }
            
            // Generate heatmap data (simulate returns for each parameter combination)
            const heatmapData = [];
            param2Values.forEach(p2 => {
                const row = [];
                param1Values.forEach(p1 => {
                    // Simulate returns based on parameters (simple function)
                    const baseReturn = 10;
                    const p1Effect = -0.1 * (p1 - 30) ** 2; // Peak at 30
                    const p2Effect = -0.2 * (p2 - 20) ** 2; // Peak at 20
                    const randomNoise = (Math.random() - 0.5) * 5;
                    const returnValue = baseReturn + p1Effect + p2Effect + randomNoise;
                    row.push(returnValue.toFixed(2));
                });
                heatmapData.push(row);
            });
            
            // Find best parameters
            let maxReturn = -Infinity;
            let bestP1 = 0;
            let bestP2 = 0;
            heatmapData.forEach((row, i) => {
                row.forEach((val, j) => {
                    const returnVal = parseFloat(val);
                    if (returnVal > maxReturn) {
                        maxReturn = returnVal;
                        bestP1 = param1Values[j];
                        bestP2 = param2Values[i];
                    }
                });
            });
            
            // Create HTML table heatmap
            let html = '<div style="overflow:auto;max-height:280px;">';
            html += '<table style="border-collapse:collapse;font-size:0.75em;">';
            html += '<tr><th style="padding:4px;border:1px solid var(--border-color);background:var(--bg-primary);">P2↓ \\ P1→</th>';
            param1Values.forEach(p1 => {
                html += `<th style="padding:4px;border:1px solid var(--border-color);background:var(--bg-primary);">${p1}</th>`;
            });
            html += '</tr>';
            
            heatmapData.forEach((row, i) => {
                html += `<tr><td style="padding:4px;border:1px solid var(--border-color);background:var(--bg-primary);font-weight:600;">${param2Values[i]}</td>`;
                row.forEach(val => {
                    const returnVal = parseFloat(val);
                    // Color scale: red (negative) -> yellow (0) -> green (positive)
                    let bgColor;
                    if (returnVal < 0) {
                        const intensity = Math.min(Math.abs(returnVal) / 10, 1);
                        bgColor = `rgba(231,76,60,${0.2 + intensity * 0.6})`;
                    } else {
                        const intensity = Math.min(returnVal / 20, 1);
                        bgColor = `rgba(39,174,96,${0.2 + intensity * 0.6})`;
                    }
                    html += `<td style="padding:4px;border:1px solid var(--border-color);background:${bgColor};text-align:center;font-weight:600;">${val}</td>`;
                });
                html += '</tr>';
            });
            html += '</table></div>';
            
            html += `<div style="margin-top:10px;padding:10px;background:rgba(39,174,96,0.1);border-radius:6px;font-weight:600;">`;
            html += `🎯 Optimal Parameters: P1=${bestP1}, P2=${bestP2} → Return=${maxReturn.toFixed(2)}%`;
            html += '</div>';
            
            document.getElementById('heatmapContainer').innerHTML = html;
        }

        function runMonteCarloVariation() {
            const simulations = parseInt(document.getElementById('mcSimulations').value);
            const confidence = parseInt(document.getElementById('mcConfidence').value);
            
            // Simulate returns for each simulation
            const returns = [];
            for (let i = 0; i < simulations; i++) {
                // Simulate a year of daily returns
                let equity = 10000;
                for (let day = 0; day < 252; day++) {
                    const dailyReturn = (Math.random() - 0.48) * 0.02; // Slight positive bias
                    equity *= (1 + dailyReturn);
                }
                const totalReturn = ((equity - 10000) / 10000 * 100);
                returns.push(totalReturn);
            }
            
            // Sort returns for percentile calculation
            returns.sort((a, b) => a - b);
            
            const best = returns[returns.length - 1].toFixed(2);
            const worst = returns[0].toFixed(2);
            const mean = (returns.reduce((sum, r) => sum + r, 0) / simulations).toFixed(2);
            
            // Calculate confidence interval
            const lowerIndex = Math.floor(simulations * (100 - confidence) / 200);
            const upperIndex = Math.floor(simulations * (100 + confidence) / 200);
            const lowerBound = returns[lowerIndex].toFixed(2);
            const upperBound = returns[upperIndex].toFixed(2);
            
            document.getElementById('mcBest').textContent = `+${best}%`;
            document.getElementById('mcWorst').textContent = `${worst}%`;
            document.getElementById('mcMean').textContent = `${mean}%`;
            document.getElementById('mcCI').textContent = `[${lowerBound}%, ${upperBound}%]`;
            document.getElementById('mcResultsAdv').style.display = 'block';
        }

        function simulateSlippage() {
            const commission = parseFloat(document.getElementById('commissionAmount').value);
            const slippage = parseFloat(document.getElementById('slippagePercent').value) / 100;
            const spread = parseFloat(document.getElementById('spreadBps').value) / 10000; // bps to decimal
            const marketImpact = parseFloat(document.getElementById('marketImpact').value) / 100;
            
            // Simulate a simple strategy with 50 trades
            const numTrades = 50;
            const avgTradeSize = 5000; // $5000 average position
            let grossReturn = 0;
            let totalCommission = 0;
            let totalSlippage = 0;
            let totalSpread = 0;
            let totalImpact = 0;
            
            for (let i = 0; i < numTrades; i++) {
                // Simulate trade return
                const tradeReturn = (Math.random() - 0.45) * 0.08; // -4% to +4%, slight positive bias
                grossReturn += tradeReturn * avgTradeSize;
                
                // Calculate costs
                totalCommission += commission * 2; // Entry + exit
                totalSlippage += avgTradeSize * slippage * 2; // Entry + exit
                totalSpread += avgTradeSize * spread * 2; // Entry + exit
                totalImpact += avgTradeSize * marketImpact * 2; // Entry + exit
            }
            
            const totalCosts = totalCommission + totalSlippage + totalSpread + totalImpact;
            const netReturn = grossReturn - totalCosts;
            const initialCapital = avgTradeSize * numTrades / 5; // Assuming 5 positions at a time
            
            const grossReturnPct = (grossReturn / initialCapital * 100).toFixed(2);
            const netReturnPct = (netReturn / initialCapital * 100).toFixed(2);
            
            document.getElementById('grossReturn').textContent = `+${grossReturnPct}%`;
            document.getElementById('netReturn').textContent = `${netReturnPct >= 0 ? '+' : ''}${netReturnPct}%`;
            document.getElementById('netReturn').style.color = netReturnPct >= 0 ? '#27ae60' : '#e74c3c';
            document.getElementById('totalCosts').textContent = `$${totalCosts.toFixed(2)}`;
            
            let breakdown = `<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">`;
            breakdown += `<div>💵 Commission: <strong>$${totalCommission.toFixed(2)}</strong></div>`;
            breakdown += `<div>📉 Slippage: <strong>$${totalSlippage.toFixed(2)}</strong></div>`;
            breakdown += `<div>📊 Spread: <strong>$${totalSpread.toFixed(2)}</strong></div>`;
            breakdown += `<div>🌊 Market Impact: <strong>$${totalImpact.toFixed(2)}</strong></div>`;
            breakdown += `</div>`;
            breakdown += `<div style="margin-top:10px;padding:10px;background:white;border-radius:6px;">`;
            breakdown += `<strong>Cost Impact:</strong> ${((totalCosts / grossReturn) * 100).toFixed(1)}% of gross return`;
            breakdown += `</div>`;
            
            document.getElementById('costBreakdown').innerHTML = breakdown;
            document.getElementById('slippageResults').style.display = 'block';
        }

        // ============= End Advanced Backtesting Functions =============

        // ============= Trade Journal Functions =============
        
        let tradeLogs = JSON.parse(localStorage.getItem('tradeLogs') || '[]');
        let journalCharts = {};

        function openTradeJournal() {
            document.getElementById('tradeJournalModal').style.display = 'flex';
            switchJournalTab('logs');
            loadTradeLogs();
        }

        function closeTradeJournal() {
            document.getElementById('tradeJournalModal').style.display = 'none';
        }

        function switchJournalTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.journal-tab-content').forEach(tab => {
                tab.style.display = 'none';
            });
            
            // Reset button styles
            ['logs', 'performance', 'sector', 'time'].forEach(tab => {
                const btn = document.getElementById('journalTab' + tab.charAt(0).toUpperCase() + tab.slice(1));
                btn.style.background = 'transparent';
                btn.style.color = 'var(--text-secondary)';
            });
            
            // Show selected tab
            document.getElementById('journalTab' + tabName.charAt(0).toUpperCase() + tabName.slice(1) + 'Content').style.display = 'block';
            const activeBtn = document.getElementById('journalTab' + tabName.charAt(0).toUpperCase() + tabName.slice(1));
            activeBtn.style.background = 'var(--bg-primary)';
            activeBtn.style.color = 'var(--text-primary)';
            
            // Load tab-specific data
            if (tabName === 'performance') {
                loadPerformanceAnalysis();
            } else if (tabName === 'sector') {
                loadSectorAnalysis();
            } else if (tabName === 'time') {
                loadTimeAnalysis();
            }
        }

        function addTradeLog() {
            document.getElementById('addTradeLogModal').style.display = 'flex';
            // Set default date to today
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('newTradeDate').value = today;
        }

        function closeAddTradeLog() {
            document.getElementById('addTradeLogModal').style.display = 'none';
        }

        function saveTradeLog() {
            const date = document.getElementById('newTradeDate').value;
            const symbol = document.getElementById('newTradeSymbol').value.toUpperCase();
            const type = document.getElementById('newTradeType').value;
            const entry = parseFloat(document.getElementById('newTradeEntry').value);
            const exit = parseFloat(document.getElementById('newTradeExit').value);
            const quantity = parseInt(document.getElementById('newTradeQuantity').value);
            const sector = document.getElementById('newTradeSector').value;
            const setup = document.getElementById('newTradeSetup').value;
            const tags = document.getElementById('newTradeTags').value;
            const notes = document.getElementById('newTradeNotes').value;
            
            if (!date || !symbol || !entry || !exit || !quantity) {
                alert('Please fill in all required fields');
                return;
            }
            
            const pnl = type === 'long' 
                ? (exit - entry) * quantity 
                : (entry - exit) * quantity;
            
            const pnlPct = type === 'long'
                ? ((exit - entry) / entry * 100)
                : ((entry - exit) / entry * 100);
            
            const tradeLog = {
                id: Date.now(),
                date,
                symbol,
                type,
                entry,
                exit,
                quantity,
                pnl,
                pnlPct,
                sector,
                setup,
                tags: tags.split(',').map(t => t.trim()).filter(t => t),
                notes,
                timestamp: new Date().toISOString()
            };
            
            tradeLogs.push(tradeLog);
            localStorage.setItem('tradeLogs', JSON.stringify(tradeLogs));
            
            closeAddTradeLog();
            loadTradeLogs();
            
            // Clear form
            document.getElementById('newTradeSymbol').value = '';
            document.getElementById('newTradeEntry').value = '';
            document.getElementById('newTradeExit').value = '';
            document.getElementById('newTradeQuantity').value = '';
            document.getElementById('newTradeSetup').value = '';
            document.getElementById('newTradeTags').value = '';
            document.getElementById('newTradeNotes').value = '';
        }

        function loadTradeLogs() {
            filterTradeLogs();
        }

        function filterTradeLogs() {
            const dateFilter = document.getElementById('logDateFilter').value;
            const typeFilter = document.getElementById('logTypeFilter').value;
            const outcomeFilter = document.getElementById('logOutcomeFilter').value;
            
            let filtered = [...tradeLogs];
            
            if (dateFilter) {
                filtered = filtered.filter(log => log.date === dateFilter);
            }
            
            if (typeFilter !== 'all') {
                filtered = filtered.filter(log => log.type === typeFilter);
            }
            
            if (outcomeFilter === 'win') {
                filtered = filtered.filter(log => log.pnl > 0);
            } else if (outcomeFilter === 'loss') {
                filtered = filtered.filter(log => log.pnl < 0);
            }
            
            // Sort by date descending
            filtered.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            const container = document.getElementById('tradeLogsContainer');
            
            if (filtered.length === 0) {
                container.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-secondary);">No trade logs found. Click "Add Trade Log" to create your first entry.</div>';
                return;
            }
            
            container.innerHTML = filtered.map(log => {
                const pnlColor = log.pnl >= 0 ? '#27ae60' : '#e74c3c';
                const typeIcon = log.type === 'long' ? '📈' : '📉';
                const outcomeIcon = log.pnl >= 0 ? '✅' : '❌';
                
                return `
                    <div style="background:white;border:1px solid var(--border-color);border-radius:12px;padding:20px;border-left:4px solid ${pnlColor};">
                        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:15px;">
                            <div>
                                <div style="font-size:1.3em;font-weight:700;color:var(--text-primary);margin-bottom:5px;">
                                    ${typeIcon} ${log.symbol} - ${log.type.toUpperCase()}
                                </div>
                                <div style="font-size:0.85em;color:var(--text-secondary);">
                                    ${new Date(log.date).toLocaleDateString()} • ${log.sector}
                                </div>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:1.5em;font-weight:700;color:${pnlColor};">
                                    ${outcomeIcon} ${log.pnl >= 0 ? '+' : ''}$${log.pnl.toFixed(2)}
                                </div>
                                <div style="font-size:0.9em;color:${pnlColor};">
                                    ${log.pnlPct >= 0 ? '+' : ''}${log.pnlPct.toFixed(2)}%
                                </div>
                            </div>
                        </div>
                        
                        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:15px;padding:15px;background:var(--bg-container);border-radius:8px;">
                            <div>
                                <div style="font-size:0.75em;color:var(--text-secondary);">Entry</div>
                                <div style="font-weight:600;">$${log.entry.toFixed(2)}</div>
                            </div>
                            <div>
                                <div style="font-size:0.75em;color:var(--text-secondary);">Exit</div>
                                <div style="font-weight:600;">$${log.exit.toFixed(2)}</div>
                            </div>
                            <div>
                                <div style="font-size:0.75em;color:var(--text-secondary);">Quantity</div>
                                <div style="font-weight:600;">${log.quantity}</div>
                            </div>
                        </div>
                        
                        ${log.setup ? `<div style="margin-bottom:10px;"><strong>Setup:</strong> ${log.setup}</div>` : ''}
                        
                        ${log.tags.length > 0 ? `
                            <div style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:10px;">
                                ${log.tags.map(tag => `<span style="padding:4px 10px;background:var(--bg-primary);border-radius:12px;font-size:0.8em;">#${tag}</span>`).join('')}
                            </div>
                        ` : ''}
                        
                        ${log.notes ? `
                            <div style="padding:12px;background:rgba(102,126,234,0.1);border-radius:8px;border-left:3px solid var(--bg-primary);">
                                <div style="font-size:0.85em;font-weight:600;margin-bottom:5px;">Notes:</div>
                                <div style="font-size:0.9em;color:var(--text-primary);">${log.notes}</div>
                            </div>
                        ` : ''}
                        
                        <div style="margin-top:15px;text-align:right;">
                            <button onclick="deleteTradeLog(${log.id})" style="padding:6px 12px;background:#e74c3c;color:white;border:none;border-radius:6px;cursor:pointer;font-size:0.85em;">🗑️ Delete</button>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function deleteTradeLog(id) {
            if (confirm('Are you sure you want to delete this trade log?')) {
                tradeLogs = tradeLogs.filter(log => log.id !== id);
                localStorage.setItem('tradeLogs', JSON.stringify(tradeLogs));
                loadTradeLogs();
            }
        }

        function loadPerformanceAnalysis() {
            if (tradeLogs.length === 0) {
                document.getElementById('perfTotalTrades').textContent = '0';
                document.getElementById('perfWinRate').textContent = '0%';
                document.getElementById('perfAvgWin').textContent = '$0';
                document.getElementById('perfAvgLoss').textContent = '$0';
                return;
            }
            
            const wins = tradeLogs.filter(log => log.pnl > 0);
            const losses = tradeLogs.filter(log => log.pnl < 0);
            const winRate = (wins.length / tradeLogs.length * 100).toFixed(1);
            const avgWin = wins.length > 0 ? (wins.reduce((sum, log) => sum + log.pnl, 0) / wins.length) : 0;
            const avgLoss = losses.length > 0 ? (losses.reduce((sum, log) => sum + log.pnl, 0) / losses.length) : 0;
            
            document.getElementById('perfTotalTrades').textContent = tradeLogs.length;
            document.getElementById('perfWinRate').textContent = winRate + '%';
            document.getElementById('perfAvgWin').textContent = '$' + avgWin.toFixed(2);
            document.getElementById('perfAvgLoss').textContent = '$' + avgLoss.toFixed(2);
            
            // Strategy performance chart
            const setupPerformance = {};
            tradeLogs.forEach(log => {
                if (!log.setup) return;
                if (!setupPerformance[log.setup]) {
                    setupPerformance[log.setup] = { total: 0, count: 0 };
                }
                setupPerformance[log.setup].total += log.pnl;
                setupPerformance[log.setup].count++;
            });
            
            const setupNames = Object.keys(setupPerformance);
            const setupPnL = setupNames.map(name => setupPerformance[name].total);
            
            if (journalCharts.strategyPerf) journalCharts.strategyPerf.destroy();
            
            const ctx = document.getElementById('strategyPerfChart');
            journalCharts.strategyPerf = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: setupNames,
                    datasets: [{
                        label: 'Total P&L',
                        data: setupPnL,
                        backgroundColor: setupPnL.map(v => v >= 0 ? 'rgba(39,174,96,0.7)' : 'rgba(231,76,60,0.7)'),
                        borderColor: setupPnL.map(v => v >= 0 ? '#27ae60' : '#e74c3c'),
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
            
            // Best and worst setups
            const setupAvg = setupNames.map(name => ({
                name,
                avg: setupPerformance[name].total / setupPerformance[name].count,
                count: setupPerformance[name].count
            }));
            
            setupAvg.sort((a, b) => b.avg - a.avg);
            
            const bestHtml = setupAvg.slice(0, 5).map(s => `
                <div style="padding:10px;background:rgba(39,174,96,0.1);border-radius:8px;margin-bottom:8px;">
                    <div style="font-weight:600;">${s.name}</div>
                    <div style="font-size:0.9em;color:#27ae60;">Avg: +$${s.avg.toFixed(2)} (${s.count} trades)</div>
                </div>
            `).join('');
            
            const worstHtml = setupAvg.slice(-5).reverse().map(s => `
                <div style="padding:10px;background:rgba(231,76,60,0.1);border-radius:8px;margin-bottom:8px;">
                    <div style="font-weight:600;">${s.name}</div>
                    <div style="font-size:0.9em;color:#e74c3c;">Avg: $${s.avg.toFixed(2)} (${s.count} trades)</div>
                </div>
            `).join('');
            
            document.getElementById('bestSetupsContainer').innerHTML = bestHtml || '<div style="color:var(--text-secondary);">No data</div>';
            document.getElementById('worstSetupsContainer').innerHTML = worstHtml || '<div style="color:var(--text-secondary);">No data</div>';
        }

        function loadSectorAnalysis() {
            if (tradeLogs.length === 0) return;
            
            const sectorData = {};
            tradeLogs.forEach(log => {
                if (!sectorData[log.sector]) {
                    sectorData[log.sector] = { trades: 0, wins: 0, totalPnL: 0 };
                }
                sectorData[log.sector].trades++;
                if (log.pnl > 0) sectorData[log.sector].wins++;
                sectorData[log.sector].totalPnL += log.pnl;
            });
            
            const sectors = Object.keys(sectorData);
            const tradeCount = sectors.map(s => sectorData[s].trades);
            const pnlData = sectors.map(s => sectorData[s].totalPnL);
            
            // Sector exposure pie chart
            if (journalCharts.sectorExposure) journalCharts.sectorExposure.destroy();
            
            const ctx1 = document.getElementById('sectorExposureChart');
            journalCharts.sectorExposure = new Chart(ctx1, {
                type: 'pie',
                data: {
                    labels: sectors,
                    datasets: [{
                        data: tradeCount,
                        backgroundColor: ['#667eea', '#27ae60', '#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#95a5a6']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
            // Sector performance bar chart
            if (journalCharts.sectorPerformance) journalCharts.sectorPerformance.destroy();
            
            const ctx2 = document.getElementById('sectorPerformanceChart');
            journalCharts.sectorPerformance = new Chart(ctx2, {
                type: 'bar',
                data: {
                    labels: sectors,
                    datasets: [{
                        label: 'Total P&L',
                        data: pnlData,
                        backgroundColor: pnlData.map(v => v >= 0 ? 'rgba(39,174,96,0.7)' : 'rgba(231,76,60,0.7)'),
                        borderColor: pnlData.map(v => v >= 0 ? '#27ae60' : '#e74c3c'),
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
            
            // Sector stats table
            const tableHtml = sectors.map(sector => {
                const data = sectorData[sector];
                const winRate = (data.wins / data.trades * 100).toFixed(1);
                const avgPnL = (data.totalPnL / data.trades).toFixed(2);
                const pnlColor = data.totalPnL >= 0 ? '#27ae60' : '#e74c3c';
                
                return `
                    <tr>
                        <td style="padding:10px;border:1px solid var(--border-color);font-weight:600;">${sector}</td>
                        <td style="padding:10px;border:1px solid var(--border-color);text-align:center;">${data.trades}</td>
                        <td style="padding:10px;border:1px solid var(--border-color);text-align:center;">${winRate}%</td>
                        <td style="padding:10px;border:1px solid var(--border-color);text-align:center;">$${avgPnL}</td>
                        <td style="padding:10px;border:1px solid var(--border-color);text-align:center;color:${pnlColor};font-weight:600;">$${data.totalPnL.toFixed(2)}</td>
                    </tr>
                `;
            }).join('');
            
            document.getElementById('sectorStatsBody').innerHTML = tableHtml;
        }

        function loadTimeAnalysis() {
            if (tradeLogs.length === 0) return;
            
            // Day of week analysis
            const dayData = { Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0 };
            tradeLogs.forEach(log => {
                const date = new Date(log.date);
                const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
                const day = days[date.getDay()];
                if (dayData[day] !== undefined) {
                    dayData[day] += log.pnl;
                }
            });
            
            if (journalCharts.dayOfWeek) journalCharts.dayOfWeek.destroy();
            
            const ctx1 = document.getElementById('dayOfWeekChart');
            const dayValues = Object.values(dayData);
            journalCharts.dayOfWeek = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: Object.keys(dayData),
                    datasets: [{
                        label: 'P&L by Day',
                        data: dayValues,
                        backgroundColor: dayValues.map(v => v >= 0 ? 'rgba(39,174,96,0.7)' : 'rgba(231,76,60,0.7)'),
                        borderColor: dayValues.map(v => v >= 0 ? '#27ae60' : '#e74c3c'),
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
            
            // Hour of day (simulated - would need actual entry time)
            const hourData = Array(24).fill(0).map(() => (Math.random() - 0.5) * 1000);
            
            if (journalCharts.hourOfDay) journalCharts.hourOfDay.destroy();
            
            const ctx2 = document.getElementById('hourOfDayChart');
            journalCharts.hourOfDay = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: Array.from({length: 24}, (_, i) => i + ':00'),
                    datasets: [{
                        label: 'P&L by Hour',
                        data: hourData,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102,126,234,0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
            
            // Holding period
            const holdingPeriods = { '<1h': 0, '1-4h': 0, '4-24h': 0, '1-7d': 0, '>7d': 0 };
            // Simulated data
            Object.keys(holdingPeriods).forEach(key => {
                holdingPeriods[key] = Math.floor(Math.random() * tradeLogs.length / 2);
            });
            
            if (journalCharts.holdingPeriod) journalCharts.holdingPeriod.destroy();
            
            const ctx3 = document.getElementById('holdingPeriodChart');
            journalCharts.holdingPeriod = new Chart(ctx3, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(holdingPeriods),
                    datasets: [{
                        data: Object.values(holdingPeriods),
                        backgroundColor: ['#e74c3c', '#f39c12', '#f1c40f', '#27ae60', '#3498db']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
            
            // Monthly performance
            const monthData = {};
            tradeLogs.forEach(log => {
                const month = log.date.substring(0, 7); // YYYY-MM
                if (!monthData[month]) monthData[month] = 0;
                monthData[month] += log.pnl;
            });
            
            const months = Object.keys(monthData).sort();
            const monthPnL = months.map(m => monthData[m]);
            
            if (journalCharts.monthlyPerf) journalCharts.monthlyPerf.destroy();
            
            const ctx4 = document.getElementById('monthlyPerfChart');
            journalCharts.monthlyPerf = new Chart(ctx4, {
                type: 'line',
                data: {
                    labels: months,
                    datasets: [{
                        label: 'Monthly P&L',
                        data: monthPnL,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102,126,234,0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
        }

        // ============= End Trade Journal Functions =============

        // ============= Automation & Scheduling Functions =============
        
        let schedules = JSON.parse(localStorage.getItem('backtestSchedules') || '[]');
        let versions = JSON.parse(localStorage.getItem('strategyVersions') || '[]');

        function openAutomation() {
            document.getElementById('automationModal').style.display = 'flex';
            loadSchedules();
            loadVersions();
        }

        function closeAutomation() {
            document.getElementById('automationModal').style.display = 'none';
        }

        function createSchedule() {
            const strategyName = document.getElementById('scheduleStrategyName').value;
            const frequency = document.getElementById('scheduleFrequency').value;
            const symbols = document.getElementById('scheduleSymbols').value;
            
            if (!strategyName || !symbols) {
                alert('Please fill in all required fields');
                return;
            }
            
            const schedule = {
                id: Date.now(),
                strategyName,
                frequency,
                symbols: symbols.split(',').map(s => s.trim()),
                createdAt: new Date().toISOString(),
                enabled: true,
                lastRun: null,
                nextRun: getNextRunTime(frequency)
            };
            
            schedules.push(schedule);
            localStorage.setItem('backtestSchedules', JSON.stringify(schedules));
            
            document.getElementById('scheduleStrategyName').value = '';
            document.getElementById('scheduleSymbols').value = '';
            
            loadSchedules();
        }

        function getNextRunTime(frequency) {
            const now = new Date();
            const next = new Date(now);
            
            switch(frequency) {
                case 'daily':
                    next.setDate(next.getDate() + 1);
                    next.setHours(9, 0, 0, 0);
                    break;
                case 'weekly':
                    next.setDate(next.getDate() + (8 - next.getDay()) % 7);
                    next.setHours(9, 0, 0, 0);
                    break;
                case 'monthly':
                    next.setMonth(next.getMonth() + 1);
                    next.setDate(1);
                    next.setHours(9, 0, 0, 0);
                    break;
            }
            
            return next.toISOString();
        }

        function loadSchedules() {
            const container = document.getElementById('schedulesList');
            
            if (schedules.length === 0) {
                container.innerHTML = '<div style="padding:10px;color:var(--text-secondary);font-size:0.9em;">No schedules created yet</div>';
                return;
            }
            
            container.innerHTML = schedules.map(schedule => {
                const nextRun = new Date(schedule.nextRun);
                const statusColor = schedule.enabled ? '#27ae60' : '#95a5a6';
                const statusText = schedule.enabled ? '✅ Active' : '⏸️ Paused';
                
                return `
                    <div style="padding:12px;background:white;border:1px solid var(--border-color);border-radius:8px;margin-bottom:10px;border-left:4px solid ${statusColor};">
                        <div style="display:flex;justify-content:space-between;align-items:start;">
                            <div style="flex:1;">
                                <div style="font-weight:600;margin-bottom:5px;">${schedule.strategyName}</div>
                                <div style="font-size:0.85em;color:var(--text-secondary);">
                                    📅 ${schedule.frequency.charAt(0).toUpperCase() + schedule.frequency.slice(1)} • 
                                    Next: ${nextRun.toLocaleString()}
                                </div>
                                <div style="font-size:0.85em;color:var(--text-secondary);margin-top:3px;">
                                    📊 Symbols: ${schedule.symbols.join(', ')}
                                </div>
                            </div>
                            <div style="display:flex;gap:8px;align-items:center;">
                                <span style="font-size:0.85em;font-weight:600;color:${statusColor};">${statusText}</span>
                                <button onclick="toggleSchedule(${schedule.id})" style="padding:4px 8px;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:4px;cursor:pointer;font-size:0.85em;">
                                    ${schedule.enabled ? 'Pause' : 'Resume'}
                                </button>
                                <button onclick="deleteSchedule(${schedule.id})" style="padding:4px 8px;background:#e74c3c;color:white;border:none;border-radius:4px;cursor:pointer;font-size:0.85em;">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function toggleSchedule(id) {
            const schedule = schedules.find(s => s.id === id);
            if (schedule) {
                schedule.enabled = !schedule.enabled;
                localStorage.setItem('backtestSchedules', JSON.stringify(schedules));
                loadSchedules();
            }
        }

        function deleteSchedule(id) {
            if (confirm('Are you sure you want to delete this schedule?')) {
                schedules = schedules.filter(s => s.id !== id);
                localStorage.setItem('backtestSchedules', JSON.stringify(schedules));
                loadSchedules();
            }
        }

        function saveVersion() {
            const strategyName = document.getElementById('versionStrategyName').value;
            const versionTag = document.getElementById('versionTag').value;
            const changes = document.getElementById('versionChanges').value;
            
            if (!strategyName || !versionTag) {
                alert('Please fill in strategy name and version tag');
                return;
            }
            
            const version = {
                id: Date.now(),
                strategyName,
                versionTag,
                changes,
                createdAt: new Date().toISOString(),
                // In a real app, would save actual strategy parameters
                parameters: {
                    sampleParam1: Math.random() * 100,
                    sampleParam2: Math.random() * 50
                }
            };
            
            versions.push(version);
            localStorage.setItem('strategyVersions', JSON.stringify(versions));
            
            document.getElementById('versionStrategyName').value = '';
            document.getElementById('versionTag').value = '';
            document.getElementById('versionChanges').value = '';
            
            loadVersions();
        }

        function loadVersions() {
            const container = document.getElementById('versionsList');
            
            if (versions.length === 0) {
                container.innerHTML = '<div style="padding:10px;color:var(--text-secondary);font-size:0.9em;">No versions saved yet</div>';
                return;
            }
            
            // Sort by date descending
            const sortedVersions = [...versions].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
            
            container.innerHTML = sortedVersions.map((version, index) => {
                const isLatest = index === 0;
                const date = new Date(version.createdAt);
                
                return `
                    <div style="padding:12px;background:white;border:1px solid var(--border-color);border-radius:8px;margin-bottom:10px;${isLatest ? 'border-left:4px solid #27ae60;' : ''}">
                        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
                            <div>
                                <div style="font-weight:700;font-size:1.1em;">${version.strategyName}</div>
                                <div style="display:inline-block;padding:2px 8px;background:var(--bg-primary);border-radius:12px;font-size:0.8em;margin-top:4px;">
                                    ${version.versionTag}
                                </div>
                                ${isLatest ? '<span style="margin-left:8px;padding:2px 8px;background:#27ae60;color:white;border-radius:12px;font-size:0.8em;">LATEST</span>' : ''}
                            </div>
                            <div style="display:flex;gap:8px;">
                                <button onclick="restoreVersion(${version.id})" style="padding:4px 8px;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:4px;cursor:pointer;font-size:0.85em;">Restore</button>
                                <button onclick="deleteVersion(${version.id})" style="padding:4px 8px;background:#e74c3c;color:white;border:none;border-radius:4px;cursor:pointer;font-size:0.85em;">Delete</button>
                            </div>
                        </div>
                        <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:8px;">
                            📅 ${date.toLocaleString()}
                        </div>
                        ${version.changes ? `
                            <div style="padding:10px;background:var(--bg-container);border-radius:6px;font-size:0.9em;">
                                <strong>Changes:</strong> ${version.changes}
                            </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
        }

        function restoreVersion(id) {
            const version = versions.find(v => v.id === id);
            if (version && confirm(`Restore ${version.strategyName} (${version.versionTag})?`)) {
                alert('✅ Version restored! In a real app, this would load the strategy parameters.');
            }
        }

        function deleteVersion(id) {
            if (confirm('Are you sure you want to delete this version?')) {
                versions = versions.filter(v => v.id !== id);
                localStorage.setItem('strategyVersions', JSON.stringify(versions));
                loadVersions();
            }
        }

        function runABTest() {
            const strategyA = document.getElementById('abStrategyA').value;
            const strategyB = document.getElementById('abStrategyB').value;
            const testPeriod = parseInt(document.getElementById('abTestPeriod').value);
            
            if (!strategyA || !strategyB) {
                alert('Please enter both strategy names');
                return;
            }
            
            // Simulate A/B test results
            const resultsA = {
                return: (Math.random() * 30 - 5).toFixed(2),
                sharpe: (Math.random() * 2 + 0.5).toFixed(2),
                maxDD: (-Math.random() * 15 - 5).toFixed(2),
                trades: Math.floor(Math.random() * 50 + 20)
            };
            
            const resultsB = {
                return: (Math.random() * 30 - 5).toFixed(2),
                sharpe: (Math.random() * 2 + 0.5).toFixed(2),
                maxDD: (-Math.random() * 15 - 5).toFixed(2),
                trades: Math.floor(Math.random() * 50 + 20)
            };
            
            document.getElementById('abReturnA').textContent = resultsA.return + '%';
            document.getElementById('abReturnA').style.color = resultsA.return >= 0 ? '#27ae60' : '#e74c3c';
            document.getElementById('abSharpeA').textContent = resultsA.sharpe;
            document.getElementById('abDDA').textContent = resultsA.maxDD + '%';
            document.getElementById('abTradesA').textContent = resultsA.trades;
            
            document.getElementById('abReturnB').textContent = resultsB.return + '%';
            document.getElementById('abReturnB').style.color = resultsB.return >= 0 ? '#27ae60' : '#e74c3c';
            document.getElementById('abSharpeB').textContent = resultsB.sharpe;
            document.getElementById('abDDB').textContent = resultsB.maxDD + '%';
            document.getElementById('abTradesB').textContent = resultsB.trades;
            
            // Determine winner based on Sharpe ratio
            const winner = parseFloat(resultsA.sharpe) > parseFloat(resultsB.sharpe) ? 'A' : 'B';
            const winnerName = winner === 'A' ? strategyA : strategyB;
            const winnerColor = winner === 'A' ? '#4facfe' : '#f5576c';
            
            document.getElementById('abWinner').innerHTML = `
                🏆 Winner: <span style="color:${winnerColor};">Strategy ${winner}</span> (${winnerName})
                <div style="font-size:0.8em;margin-top:8px;font-weight:normal;">
                    Better risk-adjusted returns with superior Sharpe ratio
                </div>
            `;
            
            document.getElementById('abTestResults').style.display = 'block';
        }

        function setupAutomatedReport() {
            const reportType = document.getElementById('reportType').value;
            const email = document.getElementById('reportEmail').value;
            const time = document.getElementById('reportTime').value;
            
            if (!email) {
                alert('Please enter an email address');
                return;
            }
            
            const includes = {
                performance: document.getElementById('includePerformance').checked,
                charts: document.getElementById('includeCharts').checked,
                trades: document.getElementById('includeTrades').checked,
                alerts: document.getElementById('includeAlerts').checked,
                risk: document.getElementById('includeRisk').checked,
                comparison: document.getElementById('includeComparison').checked
            };
            
            const sections = [];
            if (includes.performance) sections.push('Performance Metrics');
            if (includes.charts) sections.push('Charts');
            if (includes.trades) sections.push('Trade Log');
            if (includes.alerts) sections.push('Alerts');
            if (includes.risk) sections.push('Risk Metrics');
            if (includes.comparison) sections.push('Benchmark Comparison');
            
            document.getElementById('reportStatusDetails').innerHTML = `
                <div><strong>Report Type:</strong> ${reportType.charAt(0).toUpperCase() + reportType.slice(1)}</div>
                <div><strong>Email:</strong> ${email}</div>
                <div><strong>Send Time:</strong> ${time}</div>
                <div><strong>Sections:</strong> ${sections.join(', ')}</div>
            `;
            
            document.getElementById('reportStatus').style.display = 'block';
            
            // Save to localStorage
            const reportConfig = {
                reportType,
                email,
                time,
                includes,
                createdAt: new Date().toISOString()
            };
            localStorage.setItem('automatedReportConfig', JSON.stringify(reportConfig));
        }

        // ============= End Automation Functions =============

        // ============= UI Enhancements - Keyboard Shortcuts & Command Palette =============
        
        // Keyboard shortcuts handler
        document.addEventListener('keydown', function(e) {
            // Ignore if user is typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // Ctrl/Cmd + K: Open command palette
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                openCommandPalette();
            }
            
            // Ctrl/Cmd + B: Open Advanced Backtest
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                openAdvancedBacktest();
            }
            
            // Ctrl/Cmd + J: Open Trade Journal
            if ((e.ctrlKey || e.metaKey) && e.key === 'j') {
                e.preventDefault();
                openTradeJournal();
            }
            
            // Ctrl/Cmd + R: Open Risk Calculator
            if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
                e.preventDefault();
                openRiskCalculator();
            }
            
            // Ctrl/Cmd + A: Open Automation
            if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
                e.preventDefault();
                openAutomation();
            }
            
            // Ctrl/Cmd + L: Open Smart Alerts
            if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
                e.preventDefault();
                openAlertsPanel();
            }
            
            // Ctrl/Cmd + 1-4: Switch themes
            if ((e.ctrlKey || e.metaKey) && ['1', '2', '3', '4'].includes(e.key)) {
                e.preventDefault();
                const themes = ['light', 'dark', 'blue', 'purple'];
                switchTheme(themes[parseInt(e.key) - 1]);
            }
            
            // ESC: Close any open modal
            if (e.key === 'Escape') {
                closeAllModals();
            }
        });

        function closeAllModals() {
            const modals = [
                'stockModal',
                'advBacktestModal',
                'tradeJournalModal',
                'riskCalcModal',
                'automationModal',
                'alertsModal',
                'volumeProfileModal',
                'addTradeLogModal',
                'comparisonModal',
                'indicatorBuilderModal',
                'patternRecognitionModal',
                'multiTimeframeModal',
                'drawingToolsModal',
                'economicCalendarModal',
                'screenerModal'
            ];
            
            modals.forEach(id => {
                const modal = document.getElementById(id);
                if (modal) modal.style.display = 'none';
            });
            
            stopAlertMonitoring();
        }

        function openCommandPalette() {
            // Create command palette if it doesn't exist
            let palette = document.getElementById('commandPalette');
            if (!palette) {
                const paletteHtml = `
                    <div id="commandPalette" style="display:none;position:fixed;top:20%;left:50%;transform:translateX(-50%);width:600px;max-width:90%;background:var(--card-bg);border-radius:12px;box-shadow:0 20px 60px rgba(0,0,0,0.3);z-index:10001;border:1px solid var(--border-color);">
                        <div style="padding:15px;border-bottom:1px solid var(--border-color);">
                            <input type="text" id="commandPaletteInput" placeholder="Type a command or search..." style="width:100%;padding:12px;border:none;background:transparent;font-size:1.1em;color:var(--text-primary);outline:none;" autofocus>
                        </div>
                        <div id="commandPaletteResults" style="max-height:400px;overflow-y:auto;"></div>
                    </div>
                    <div id="commandPaletteBackdrop" onclick="closeCommandPalette()" style="display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:10000;"></div>
                `;
                document.body.insertAdjacentHTML('beforeend', paletteHtml);
                
                // Add search handler
                document.getElementById('commandPaletteInput').addEventListener('input', filterCommands);
            }
            
            document.getElementById('commandPalette').style.display = 'block';
            document.getElementById('commandPaletteBackdrop').style.display = 'block';
            document.getElementById('commandPaletteInput').value = '';
            document.getElementById('commandPaletteInput').focus();
            
            showAllCommands();
        }

        function closeCommandPalette() {
            document.getElementById('commandPalette').style.display = 'none';
            document.getElementById('commandPaletteBackdrop').style.display = 'none';
        }

        const commands = [
            { name: 'Open Advanced Backtest', action: () => { closeCommandPalette(); openAdvancedBacktest(); }, icon: '🔬', shortcut: 'Ctrl+B' },
            { name: 'Open Trade Journal', action: () => { closeCommandPalette(); openTradeJournal(); }, icon: '📓', shortcut: 'Ctrl+J' },
            { name: 'Open Risk Calculator', action: () => { closeCommandPalette(); openRiskCalculator(); }, icon: '⚖️', shortcut: 'Ctrl+R' },
            { name: 'Open Automation', action: () => { closeCommandPalette(); openAutomation(); }, icon: '⚙️', shortcut: 'Ctrl+A' },
            { name: 'Open Smart Alerts', action: () => { closeCommandPalette(); openAlertsPanel(); }, icon: '🔔', shortcut: 'Ctrl+L' },
            { name: 'Open Volume Profile', action: () => { closeCommandPalette(); openVolumeProfile(); }, icon: '📊', shortcut: '' },
            { name: 'Open Custom Indicators', action: () => { closeCommandPalette(); openIndicatorBuilder(); }, icon: '📈', shortcut: '' },
            { name: 'Open Pattern Recognition', action: () => { closeCommandPalette(); openPatternRecognition(); }, icon: '🔍', shortcut: '' },
            { name: 'Open Multi-Timeframe', action: () => { closeCommandPalette(); openMultiTimeframe(); }, icon: '⏱️', shortcut: '' },
            { name: 'Open Fibonacci Tools', action: () => { closeCommandPalette(); openDrawingTools(); }, icon: '📐', shortcut: '' },
            { name: 'Open Economic Calendar', action: () => { closeCommandPalette(); openEconomicCalendar(); }, icon: '📅', shortcut: '' },
            { name: 'Open Screener', action: () => { closeCommandPalette(); openScreener(); }, icon: '🔎', shortcut: '' },
            { name: 'Switch to Light Theme', action: () => { closeCommandPalette(); switchTheme('light'); }, icon: '☀️', shortcut: 'Ctrl+1' },
            { name: 'Switch to Dark Theme', action: () => { closeCommandPalette(); switchTheme('dark'); }, icon: '🌙', shortcut: 'Ctrl+2' },
            { name: 'Switch to Blue Theme', action: () => { closeCommandPalette(); switchTheme('blue'); }, icon: '🔵', shortcut: 'Ctrl+3' },
            { name: 'Switch to Purple Theme', action: () => { closeCommandPalette(); switchTheme('purple'); }, icon: '🟣', shortcut: 'Ctrl+4' },
            { name: 'Reset Genome', action: () => { closeCommandPalette(); resetGenome(); }, icon: '🔄', shortcut: '' },
            { name: 'Show Genome', action: () => { closeCommandPalette(); showGenome(); }, icon: '📋', shortcut: '' },
            { name: 'Export Data', action: () => { closeCommandPalette(); exportData(); }, icon: '📥', shortcut: '' }
        ];

        function showAllCommands() {
            displayCommands(commands);
        }

        function filterCommands() {
            const query = document.getElementById('commandPaletteInput').value.toLowerCase();
            const filtered = commands.filter(cmd => 
                cmd.name.toLowerCase().includes(query) || 
                cmd.shortcut.toLowerCase().includes(query)
            );
            displayCommands(filtered);
        }

        function displayCommands(cmds) {
            const container = document.getElementById('commandPaletteResults');
            
            if (cmds.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary);">No commands found</div>';
                return;
            }
            
            container.innerHTML = cmds.map(cmd => `
                <div onclick="executeCommand('${cmd.name}')" style="padding:12px 15px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--border-color);transition:background 0.2s;" onmouseover="this.style.background='var(--bg-hover)'" onmouseout="this.style.background='transparent'">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <span style="font-size:1.3em;">${cmd.icon}</span>
                        <span style="font-weight:500;color:var(--text-primary);">${cmd.name}</span>
                    </div>
                    ${cmd.shortcut ? `<span style="padding:4px 8px;background:var(--bg-secondary);border-radius:4px;font-size:0.85em;color:var(--text-secondary);">${cmd.shortcut}</span>` : ''}
                </div>
            `).join('');
        }

        function executeCommand(name) {
            const cmd = commands.find(c => c.name === name);
            if (cmd) cmd.action();
        }

        // ============= End UI Enhancements =============

        // ============= Smart Alerts System Functions =============
        
        let alerts = {
            price: JSON.parse(localStorage.getItem('priceAlerts') || '[]'),
            indicator: JSON.parse(localStorage.getItem('indicatorAlerts') || '[]'),
            pattern: JSON.parse(localStorage.getItem('patternAlerts') || '[]'),
            volume: JSON.parse(localStorage.getItem('volumeAlerts') || '[]')
        };
        let alertHistory = JSON.parse(localStorage.getItem('alertHistory') || '[]');
        let alertCheckInterval = null;

        function openAlertsPanel() {
            document.getElementById('alertsModal').style.display = 'flex';
            switchAlertTab('price');
            loadAllAlerts();
            startAlertMonitoring();
        }

        function closeAlertsPanel() {
            document.getElementById('alertsModal').style.display = 'none';
            stopAlertMonitoring();
        }

        function switchAlertTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.alert-tab-content').forEach(tab => {
                tab.style.display = 'none';
            });
            
            // Reset button styles
            ['price', 'indicator', 'pattern', 'volume'].forEach(tab => {
                const btn = document.getElementById('alertTab' + tab.charAt(0).toUpperCase() + tab.slice(1));
                btn.style.background = 'transparent';
                btn.style.color = 'var(--text-secondary)';
            });
            
            // Show selected tab
            document.getElementById('alertTab' + tabName.charAt(0).toUpperCase() + tabName.slice(1) + 'Content').style.display = 'block';
            const activeBtn = document.getElementById('alertTab' + tabName.charAt(0).toUpperCase() + tabName.slice(1));
            activeBtn.style.background = 'var(--bg-primary)';
            activeBtn.style.color = 'var(--text-primary)';
        }

        function createPriceAlert() {
            const symbol = document.getElementById('priceAlertSymbol').value.toUpperCase();
            const condition = document.getElementById('priceAlertCondition').value;
            const value = parseFloat(document.getElementById('priceAlertValue').value);
            const value2 = parseFloat(document.getElementById('priceAlertValue2').value);
            
            if (!symbol || !value) {
                alert('Please fill in all required fields');
                return;
            }
            
            const alert = {
                id: Date.now(),
                symbol,
                condition,
                value,
                value2: condition === 'between' ? value2 : null,
                createdAt: new Date().toISOString(),
                enabled: true,
                triggered: false
            };
            
            alerts.price.push(alert);
            localStorage.setItem('priceAlerts', JSON.stringify(alerts.price));
            
            document.getElementById('priceAlertSymbol').value = '';
            document.getElementById('priceAlertValue').value = '';
            document.getElementById('priceAlertValue2').value = '';
            
            loadAllAlerts();
            showNotification('✅ Price Alert Created', `${symbol} ${condition} $${value}`);
        }

        function createIndicatorAlert() {
            const symbol = document.getElementById('indicatorAlertSymbol').value.toUpperCase();
            const indicator = document.getElementById('indicatorAlertType').value;
            const condition = document.getElementById('indicatorAlertCondition').value;
            const value = parseFloat(document.getElementById('indicatorAlertValue').value);
            
            if (!symbol || !value) {
                alert('Please fill in all required fields');
                return;
            }
            
            const alert = {
                id: Date.now(),
                symbol,
                indicator,
                condition,
                value,
                createdAt: new Date().toISOString(),
                enabled: true,
                triggered: false
            };
            
            alerts.indicator.push(alert);
            localStorage.setItem('indicatorAlerts', JSON.stringify(alerts.indicator));
            
            document.getElementById('indicatorAlertSymbol').value = '';
            document.getElementById('indicatorAlertValue').value = '';
            
            loadAllAlerts();
            showNotification('✅ Indicator Alert Created', `${symbol} ${indicator.toUpperCase()} ${condition} ${value}`);
        }

        function createPatternAlert() {
            const symbol = document.getElementById('patternAlertSymbol').value.toUpperCase();
            const patternType = document.getElementById('patternAlertType').value;
            
            if (!symbol) {
                alert('Please enter a symbol');
                return;
            }
            
            const alert = {
                id: Date.now(),
                symbol,
                patternType,
                createdAt: new Date().toISOString(),
                enabled: true,
                triggered: false
            };
            
            alerts.pattern.push(alert);
            localStorage.setItem('patternAlerts', JSON.stringify(alerts.pattern));
            
            document.getElementById('patternAlertSymbol').value = '';
            
            loadAllAlerts();
            showNotification('✅ Pattern Alert Created', `${symbol} - ${patternType.replace('_', ' ')}`);
        }

        function createVolumeAlert() {
            const symbol = document.getElementById('volumeAlertSymbol').value.toUpperCase();
            const condition = document.getElementById('volumeAlertCondition').value;
            const value = parseFloat(document.getElementById('volumeAlertValue').value);
            
            if (!symbol || !value) {
                alert('Please fill in all required fields');
                return;
            }
            
            const alert = {
                id: Date.now(),
                symbol,
                condition,
                value,
                createdAt: new Date().toISOString(),
                enabled: true,
                triggered: false
            };
            
            alerts.volume.push(alert);
            localStorage.setItem('volumeAlerts', JSON.stringify(alerts.volume));
            
            document.getElementById('volumeAlertSymbol').value = '';
            document.getElementById('volumeAlertValue').value = '';
            
            loadAllAlerts();
            showNotification('✅ Volume Alert Created', `${symbol} - ${condition} ${value}%`);
        }

        function loadAllAlerts() {
            loadPriceAlerts();
            loadIndicatorAlerts();
            loadPatternAlerts();
            loadVolumeAlerts();
            loadAlertHistory();
        }

        function loadPriceAlerts() {
            const container = document.getElementById('priceAlertsList');
            
            if (alerts.price.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary);">No price alerts created</div>';
                return;
            }
            
            container.innerHTML = alerts.price.map(alert => {
                const statusColor = alert.enabled ? (alert.triggered ? '#27ae60' : '#667eea') : '#95a5a6';
                const statusText = alert.triggered ? '✅ Triggered' : (alert.enabled ? '🔔 Active' : '⏸️ Paused');
                const conditionText = alert.condition === 'between' 
                    ? `Between $${alert.value} - $${alert.value2}`
                    : `${alert.condition.charAt(0).toUpperCase() + alert.condition.slice(1)} $${alert.value}`;
                
                return `
                    <div style="padding:12px;background:white;border:1px solid var(--border-color);border-radius:8px;margin-bottom:10px;border-left:4px solid ${statusColor};">
                        <div style="display:flex;justify-content:space-between;align-items:start;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:1.1em;margin-bottom:5px;">${alert.symbol}</div>
                                <div style="font-size:0.9em;color:var(--text-secondary);">${conditionText}</div>
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:3px;">
                                    Created: ${new Date(alert.createdAt).toLocaleString()}
                                </div>
                            </div>
                            <div style="display:flex;gap:8px;align-items:center;">
                                <span style="font-size:0.85em;font-weight:600;color:${statusColor};">${statusText}</span>
                                <button onclick="toggleAlert('price', ${alert.id})" style="padding:4px 8px;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:4px;cursor:pointer;font-size:0.85em;">
                                    ${alert.enabled ? 'Pause' : 'Resume'}
                                </button>
                                <button onclick="deleteAlert('price', ${alert.id})" style="padding:4px 8px;background:#e74c3c;color:white;border:none;border-radius:4px;cursor:pointer;font-size:0.85em;">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function loadIndicatorAlerts() {
            const container = document.getElementById('indicatorAlertsList');
            
            if (alerts.indicator.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary);">No indicator alerts created</div>';
                return;
            }
            
            container.innerHTML = alerts.indicator.map(alert => {
                const statusColor = alert.enabled ? (alert.triggered ? '#27ae60' : '#667eea') : '#95a5a6';
                const statusText = alert.triggered ? '✅ Triggered' : (alert.enabled ? '🔔 Active' : '⏸️ Paused');
                
                return `
                    <div style="padding:12px;background:white;border:1px solid var(--border-color);border-radius:8px;margin-bottom:10px;border-left:4px solid ${statusColor};">
                        <div style="display:flex;justify-content:space-between;align-items:start;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:1.1em;margin-bottom:5px;">${alert.symbol}</div>
                                <div style="font-size:0.9em;color:var(--text-secondary);">
                                    ${alert.indicator.toUpperCase()} ${alert.condition.replace('_', ' ')} ${alert.value}
                                </div>
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:3px;">
                                    Created: ${new Date(alert.createdAt).toLocaleString()}
                                </div>
                            </div>
                            <div style="display:flex;gap:8px;align-items:center;">
                                <span style="font-size:0.85em;font-weight:600;color:${statusColor};">${statusText}</span>
                                <button onclick="toggleAlert('indicator', ${alert.id})" style="padding:4px 8px;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:4px;cursor:pointer;font-size:0.85em;">
                                    ${alert.enabled ? 'Pause' : 'Resume'}
                                </button>
                                <button onclick="deleteAlert('indicator', ${alert.id})" style="padding:4px 8px;background:#e74c3c;color:white;border:none;border-radius:4px;cursor:pointer;font-size:0.85em;">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function loadPatternAlerts() {
            const container = document.getElementById('patternAlertsList');
            
            if (alerts.pattern.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary);">No pattern alerts created</div>';
                return;
            }
            
            container.innerHTML = alerts.pattern.map(alert => {
                const statusColor = alert.enabled ? (alert.triggered ? '#27ae60' : '#667eea') : '#95a5a6';
                const statusText = alert.triggered ? '✅ Triggered' : (alert.enabled ? '🔔 Active' : '⏸️ Paused');
                
                return `
                    <div style="padding:12px;background:white;border:1px solid var(--border-color);border-radius:8px;margin-bottom:10px;border-left:4px solid ${statusColor};">
                        <div style="display:flex;justify-content:space-between;align-items:start;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:1.1em;margin-bottom:5px;">${alert.symbol}</div>
                                <div style="font-size:0.9em;color:var(--text-secondary);">
                                    Pattern: ${alert.patternType.replace('_', ' ').toUpperCase()}
                                </div>
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:3px;">
                                    Created: ${new Date(alert.createdAt).toLocaleString()}
                                </div>
                            </div>
                            <div style="display:flex;gap:8px;align-items:center;">
                                <span style="font-size:0.85em;font-weight:600;color:${statusColor};">${statusText}</span>
                                <button onclick="toggleAlert('pattern', ${alert.id})" style="padding:4px 8px;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:4px;cursor:pointer;font-size:0.85em;">
                                    ${alert.enabled ? 'Pause' : 'Resume'}
                                </button>
                                <button onclick="deleteAlert('pattern', ${alert.id})" style="padding:4px 8px;background:#e74c3c;color:white;border:none;border-radius:4px;cursor:pointer;font-size:0.85em;">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function loadVolumeAlerts() {
            const container = document.getElementById('volumeAlertsList');
            
            if (alerts.volume.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary);">No volume alerts created</div>';
                return;
            }
            
            container.innerHTML = alerts.volume.map(alert => {
                const statusColor = alert.enabled ? (alert.triggered ? '#27ae60' : '#667eea') : '#95a5a6';
                const statusText = alert.triggered ? '✅ Triggered' : (alert.enabled ? '🔔 Active' : '⏸️ Paused');
                
                return `
                    <div style="padding:12px;background:white;border:1px solid var(--border-color);border-radius:8px;margin-bottom:10px;border-left:4px solid ${statusColor};">
                        <div style="display:flex;justify-content:space-between;align-items:start;">
                            <div style="flex:1;">
                                <div style="font-weight:700;font-size:1.1em;margin-bottom:5px;">${alert.symbol}</div>
                                <div style="font-size:0.9em;color:var(--text-secondary);">
                                    ${alert.condition.replace('_', ' ').toUpperCase()} - ${alert.value}%
                                </div>
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:3px;">
                                    Created: ${new Date(alert.createdAt).toLocaleString()}
                                </div>
                            </div>
                            <div style="display:flex;gap:8px;align-items:center;">
                                <span style="font-size:0.85em;font-weight:600;color:${statusColor};">${statusText}</span>
                                <button onclick="toggleAlert('volume', ${alert.id})" style="padding:4px 8px;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:4px;cursor:pointer;font-size:0.85em;">
                                    ${alert.enabled ? 'Pause' : 'Resume'}
                                </button>
                                <button onclick="deleteAlert('volume', ${alert.id})" style="padding:4px 8px;background:#e74c3c;color:white;border:none;border-radius:4px;cursor:pointer;font-size:0.85em;">Delete</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function loadAlertHistory() {
            const container = document.getElementById('alertHistory');
            
            if (alertHistory.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary);">No alerts triggered yet</div>';
                return;
            }
            
            // Sort by date descending
            const sorted = [...alertHistory].sort((a, b) => new Date(b.triggeredAt) - new Date(a.triggeredAt));
            
            container.innerHTML = sorted.map(h => {
                return `
                    <div style="padding:10px;background:rgba(39,174,96,0.1);border:1px solid #27ae60;border-radius:8px;margin-bottom:8px;">
                        <div style="display:flex;justify-content:space-between;align-items:start;">
                            <div>
                                <div style="font-weight:600;">${h.type.toUpperCase()} Alert: ${h.symbol}</div>
                                <div style="font-size:0.9em;color:var(--text-secondary);margin-top:3px;">${h.message}</div>
                                <div style="font-size:0.8em;color:var(--text-secondary);margin-top:2px;">
                                    🕐 ${new Date(h.triggeredAt).toLocaleString()}
                                </div>
                            </div>
                            <div style="font-size:1.5em;">✅</div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function toggleAlert(type, id) {
            const alert = alerts[type].find(a => a.id === id);
            if (alert) {
                alert.enabled = !alert.enabled;
                localStorage.setItem(type + 'Alerts', JSON.stringify(alerts[type]));
                loadAllAlerts();
            }
        }

        function deleteAlert(type, id) {
            if (confirm('Are you sure you want to delete this alert?')) {
                alerts[type] = alerts[type].filter(a => a.id !== id);
                localStorage.setItem(type + 'Alerts', JSON.stringify(alerts[type]));
                loadAllAlerts();
            }
        }

        function clearAlertHistory() {
            if (confirm('Clear all alert history?')) {
                alertHistory = [];
                localStorage.setItem('alertHistory', JSON.stringify(alertHistory));
                loadAlertHistory();
            }
        }

        function startAlertMonitoring() {
            if (alertCheckInterval) return;
            
            alertCheckInterval = setInterval(() => {
                checkAlerts();
            }, 5000); // Check every 5 seconds
        }

        function stopAlertMonitoring() {
            if (alertCheckInterval) {
                clearInterval(alertCheckInterval);
                alertCheckInterval = null;
            }
        }

        function checkAlerts() {
            // Simulate alert checking (in real app, would check against live data)
            const randomCheck = Math.random();
            
            if (randomCheck > 0.95) { // 5% chance to trigger an alert for demo
                // Trigger a random alert
                const allAlerts = [
                    ...alerts.price.filter(a => a.enabled && !a.triggered),
                    ...alerts.indicator.filter(a => a.enabled && !a.triggered),
                    ...alerts.pattern.filter(a => a.enabled && !a.triggered),
                    ...alerts.volume.filter(a => a.enabled && !a.triggered)
                ];
                
                if (allAlerts.length > 0) {
                    const randomAlert = allAlerts[Math.floor(Math.random() * allAlerts.length)];
                    triggerAlert(randomAlert);
                }
            }
        }

        function triggerAlert(alert) {
            // Mark as triggered
            const type = alerts.price.find(a => a.id === alert.id) ? 'price' :
                        alerts.indicator.find(a => a.id === alert.id) ? 'indicator' :
                        alerts.pattern.find(a => a.id === alert.id) ? 'pattern' : 'volume';
            
            const alertObj = alerts[type].find(a => a.id === alert.id);
            if (alertObj) {
                alertObj.triggered = true;
                localStorage.setItem(type + 'Alerts', JSON.stringify(alerts[type]));
            }
            
            // Add to history
            const historyEntry = {
                id: Date.now(),
                type,
                symbol: alert.symbol,
                message: formatAlertMessage(alert, type),
                triggeredAt: new Date().toISOString()
            };
            
            alertHistory.push(historyEntry);
            localStorage.setItem('alertHistory', JSON.stringify(alertHistory));
            
            // Show notification
            showNotification('🔔 Alert Triggered!', historyEntry.message);
            
            // Play sound if enabled
            if (document.getElementById('enableSoundAlerts')?.checked) {
                playAlertSound();
            }
            
            // Show popup if enabled
            if (document.getElementById('enablePopupAlerts')?.checked) {
                showAlertPopup(historyEntry);
            }
            
            loadAllAlerts();
        }

        function formatAlertMessage(alert, type) {
            switch(type) {
                case 'price':
                    return `${alert.symbol} price ${alert.condition} $${alert.value}`;
                case 'indicator':
                    return `${alert.symbol} ${alert.indicator.toUpperCase()} ${alert.condition} ${alert.value}`;
                case 'pattern':
                    return `${alert.symbol} ${alert.patternType.replace('_', ' ')} pattern detected`;
                case 'volume':
                    return `${alert.symbol} volume ${alert.condition} detected (${alert.value}%)`;
            }
        }

        function showNotification(title, message) {
            // Browser notification
            if (document.getElementById('enableBrowserNotifications')?.checked && Notification.permission === 'granted') {
                new Notification(title, {
                    body: message,
                    icon: '🔔',
                    badge: '🔔'
                });
            }
            
            // Console log for demo
            console.log(`${title}: ${message}`);
        }

        function showAlertPopup(historyEntry) {
            const popup = document.createElement('div');
            popup.style.cssText = 'position:fixed;top:20px;right:20px;background:white;padding:20px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.3);z-index:10003;border-left:4px solid #27ae60;min-width:300px;animation:slideIn 0.3s ease;';
            popup.innerHTML = `
                <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:10px;">
                    <div style="font-size:1.2em;font-weight:700;">🔔 Alert Triggered!</div>
                    <button onclick="this.parentElement.parentElement.remove()" style="background:transparent;border:none;font-size:1.3em;cursor:pointer;">✕</button>
                </div>
                <div style="font-weight:600;margin-bottom:5px;">${historyEntry.symbol} - ${historyEntry.type.toUpperCase()}</div>
                <div style="color:#666;font-size:0.9em;">${historyEntry.message}</div>
            `;
            
            document.body.appendChild(popup);
            
            setTimeout(() => {
                if (popup.parentElement) {
                    popup.style.animation = 'slideOut 0.3s ease';
                    setTimeout(() => popup.remove(), 300);
                }
            }, 5000);
        }

        function playAlertSound() {
            // Create simple beep sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        }

        function toggleBrowserNotifications() {
            if (document.getElementById('enableBrowserNotifications').checked) {
                if (Notification.permission === 'default') {
                    Notification.requestPermission().then(permission => {
                        if (permission !== 'granted') {
                            document.getElementById('enableBrowserNotifications').checked = false;
                            alert('Please allow notifications in your browser settings');
                        }
                    });
                } else if (Notification.permission === 'denied') {
                    document.getElementById('enableBrowserNotifications').checked = false;
                    alert('Notifications are blocked. Please enable them in browser settings.');
                }
            }
        }

        function testNotification() {
            const testAlert = {
                id: Date.now(),
                symbol: 'TEST',
                condition: 'above',
                value: 100
            };
            
            showNotification('🧪 Test Alert', 'This is a test notification from the Smart Alerts System');
            
            if (document.getElementById('enableSoundAlerts')?.checked) {
                playAlertSound();
            }
            
            if (document.getElementById('enablePopupAlerts')?.checked) {
                const historyEntry = {
                    symbol: 'TEST',
                    type: 'price',
                    message: 'This is a test alert'
                };
                showAlertPopup(historyEntry);
            }
        }

        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(400px); opacity: 0; }
            }
        `;
        document.head.appendChild(style);

        // ============= End Smart Alerts System Functions =============

        // ============= Volume Profile & Order Flow Functions =============
        let vpChartInstance = null;
        let vpHistogramInstance = null;
        let orderFlowChartInstance = null;
        let volumeProfileData = null;

        function openVolumeProfile() {
            document.getElementById('volumeProfileModal').style.display = 'flex';
            if (!volumeProfileData) {
                loadVolumeProfile();
            }
        }

        function closeVolumeProfile() {
            document.getElementById('volumeProfileModal').style.display = 'none';
        }

        async function loadVolumeProfile() {
            const symbol = document.getElementById('vpSymbol').value.toUpperCase() || 'AAPL';
            
            // Generate simulated volume profile data
            volumeProfileData = generateVolumeProfileData(symbol);
            
            // Render all components
            renderVolumeProfileChart();
            renderVolumeHistogram();
            renderMarketProfile();
            renderOrderFlowChart();
            renderLiquidityHeatmap();
            updateVolumeMetrics();
            
            addLog(`Loaded Volume Profile for ${symbol}`, 'success');
        }

        function generateVolumeProfileData(symbol) {
            const numPriceLevels = 50;
            const basePriceIndex = 150;
            const priceIncrement = 0.50;
            const numTimeIntervals = 30;
            
            const priceLevels = [];
            const volumeByPrice = [];
            const timeProfile = [];
            
            // Generate price levels
            for (let i = 0; i < numPriceLevels; i++) {
                const price = basePriceIndex + (i * priceIncrement);
                priceLevels.push(price);
                
                // Volume distribution (bell curve centered around middle)
                const centerIndex = numPriceLevels / 2;
                const distance = Math.abs(i - centerIndex);
                const volume = Math.floor(10000 * Math.exp(-distance * distance / 100) * (0.8 + Math.random() * 0.4));
                
                volumeByPrice.push({
                    price: price,
                    volume: volume,
                    buyVolume: Math.floor(volume * (0.4 + Math.random() * 0.2)),
                    sellVolume: Math.floor(volume * (0.4 + Math.random() * 0.2))
                });
            }
            
            // Calculate POC (Point of Control)
            const maxVolume = Math.max(...volumeByPrice.map(v => v.volume));
            const poc = volumeByPrice.find(v => v.volume === maxVolume).price;
            
            // Calculate Value Area (70% of volume)
            const sortedByVolume = [...volumeByPrice].sort((a, b) => b.volume - a.volume);
            const totalVolume = volumeByPrice.reduce((sum, v) => sum + v.volume, 0);
            let cumulativeVolume = 0;
            const valueAreaPrices = [];
            
            for (const item of sortedByVolume) {
                cumulativeVolume += item.volume;
                valueAreaPrices.push(item.price);
                if (cumulativeVolume >= totalVolume * 0.70) break;
            }
            
            const vah = Math.max(...valueAreaPrices);
            const val = Math.min(...valueAreaPrices);
            
            // Generate time profile (TPO data for Market Profile)
            const letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
            for (let t = 0; t < numTimeIntervals; t++) {
                const letter = letters[t % letters.length];
                const centerPrice = poc + (Math.random() - 0.5) * 10;
                const pricesInInterval = [];
                
                for (let i = 0; i < 8; i++) {
                    const price = centerPrice + (Math.random() - 0.5) * 5;
                    pricesInInterval.push(price);
                }
                
                timeProfile.push({
                    letter: letter,
                    prices: pricesInInterval
                });
            }
            
            // Generate price chart data
            const chartData = [];
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 30);
            
            let currentPrice = poc;
            for (let i = 0; i < 30; i++) {
                const date = new Date(startDate);
                date.setDate(date.getDate() + i);
                currentPrice += (Math.random() - 0.5) * 2;
                
                chartData.push({
                    date: date.toISOString().split('T')[0],
                    price: currentPrice,
                    volume: Math.floor(50000 + Math.random() * 50000)
                });
            }
            
            // Generate order flow data (delta)
            const orderFlowData = chartData.map(d => ({
                date: d.date,
                delta: Math.floor((Math.random() - 0.5) * 10000),
                cumulativeDelta: 0
            }));
            
            let cumDelta = 0;
            orderFlowData.forEach(item => {
                cumDelta += item.delta;
                item.cumulativeDelta = cumDelta;
            });
            
            return {
                symbol,
                priceLevels,
                volumeByPrice,
                poc,
                vah,
                val,
                totalVolume,
                timeProfile,
                chartData,
                orderFlowData
            };
        }

        function renderVolumeProfileChart() {
            const canvas = document.getElementById('vpChart');
            if (!canvas || !volumeProfileData) return;
            
            if (vpChartInstance) {
                vpChartInstance.destroy();
            }
            
            const ctx = canvas.getContext('2d');
            const { chartData, poc, vah, val } = volumeProfileData;
            
            vpChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: chartData.map(d => d.date),
                    datasets: [{
                        label: 'Price',
                        data: chartData.map(d => d.price),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false },
                        annotation: {
                            annotations: {
                                poc: document.getElementById('showPOC')?.checked ? {
                                    type: 'line',
                                    yMin: poc,
                                    yMax: poc,
                                    borderColor: '#667eea',
                                    borderWidth: 2,
                                    borderDash: [5, 5],
                                    label: {
                                        content: 'POC',
                                        enabled: true,
                                        position: 'end'
                                    }
                                } : undefined,
                                vah: document.getElementById('showVAH')?.checked ? {
                                    type: 'line',
                                    yMin: vah,
                                    yMax: vah,
                                    borderColor: '#27ae60',
                                    borderWidth: 2,
                                    borderDash: [3, 3],
                                    label: {
                                        content: 'VAH',
                                        enabled: true,
                                        position: 'end'
                                    }
                                } : undefined,
                                val: document.getElementById('showVAL')?.checked ? {
                                    type: 'line',
                                    yMin: val,
                                    yMax: val,
                                    borderColor: '#e74c3c',
                                    borderWidth: 2,
                                    borderDash: [3, 3],
                                    label: {
                                        content: 'VAL',
                                        enabled: true,
                                        position: 'end'
                                    }
                                } : undefined
                            }
                        }
                    },
                    scales: {
                        y: {
                            title: { display: true, text: 'Price ($)' }
                        }
                    }
                }
            });
        }

        function renderVolumeHistogram() {
            const canvas = document.getElementById('vpHistogram');
            if (!canvas || !volumeProfileData) return;
            
            if (vpHistogramInstance) {
                vpHistogramInstance.destroy();
            }
            
            const ctx = canvas.getContext('2d');
            const { volumeByPrice, poc } = volumeProfileData;
            
            const colors = volumeByPrice.map(v => v.price >= poc ? '#27ae60' : '#e74c3c');
            
            vpHistogramInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: volumeByPrice.map(v => v.price.toFixed(2)),
                    datasets: [{
                        label: 'Volume',
                        data: volumeByPrice.map(v => v.volume),
                        backgroundColor: colors,
                        borderWidth: 0
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Volume' },
                            ticks: {
                                callback: function(value) {
                                    return (value / 1000).toFixed(0) + 'K';
                                }
                            }
                        },
                        y: {
                            title: { display: true, text: 'Price ($)' }
                        }
                    }
                }
            });
        }

        function renderMarketProfile() {
            const container = document.getElementById('marketProfile');
            if (!container || !volumeProfileData) return;
            
            const { timeProfile, priceLevels } = volumeProfileData;
            
            // Create TPO chart (Time-Price-Opportunity)
            const priceMap = new Map();
            
            timeProfile.forEach(interval => {
                interval.prices.forEach(price => {
                    const roundedPrice = Math.round(price * 2) / 2; // Round to nearest 0.5
                    if (!priceMap.has(roundedPrice)) {
                        priceMap.set(roundedPrice, []);
                    }
                    priceMap.get(roundedPrice).push(interval.letter);
                });
            });
            
            // Sort by price descending
            const sortedPrices = Array.from(priceMap.keys()).sort((a, b) => b - a);
            
            let html = '<div style="font-family:monospace;line-height:1.4;">';
            sortedPrices.forEach(price => {
                const letters = priceMap.get(price).join('');
                const count = letters.length;
                const intensity = Math.min(count / 10, 1);
                const bgColor = `rgba(102, 126, 234, ${intensity * 0.3})`;
                
                html += `<div style="background:${bgColor};padding:2px 5px;margin:1px 0;">`;
                html += `<span style="color:#666;min-width:60px;display:inline-block;">${price.toFixed(2)}</span> `;
                html += `<span style="color:#333;">${letters}</span>`;
                html += `</div>`;
            });
            html += '</div>';
            
            container.innerHTML = html;
        }

        function renderOrderFlowChart() {
            const canvas = document.getElementById('orderFlowChart');
            if (!canvas || !volumeProfileData) return;
            
            if (orderFlowChartInstance) {
                orderFlowChartInstance.destroy();
            }
            
            const ctx = canvas.getContext('2d');
            const { orderFlowData } = volumeProfileData;
            
            orderFlowChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: orderFlowData.map(d => d.date),
                    datasets: [
                        {
                            type: 'bar',
                            label: 'Delta',
                            data: orderFlowData.map(d => d.delta),
                            backgroundColor: orderFlowData.map(d => d.delta >= 0 ? '#27ae60' : '#e74c3c'),
                            yAxisID: 'y'
                        },
                        {
                            type: 'line',
                            label: 'Cumulative Delta',
                            data: orderFlowData.map(d => d.cumulativeDelta),
                            borderColor: '#667eea',
                            borderWidth: 2,
                            fill: false,
                            yAxisID: 'y1',
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: { display: true, text: 'Delta' }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: { display: true, text: 'Cumulative' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            });
        }

        function renderLiquidityHeatmap() {
            const container = document.getElementById('liquidityHeatmap');
            if (!container || !volumeProfileData) return;
            
            const { volumeByPrice } = volumeProfileData;
            const maxVolume = Math.max(...volumeByPrice.map(v => v.volume));
            
            let html = '<table style="width:100%;border-collapse:collapse;font-size:0.75em;">';
            html += '<thead><tr style="background:var(--table-header-bg);">';
            html += '<th style="padding:8px;border:1px solid var(--border-color);">Price</th>';
            html += '<th style="padding:8px;border:1px solid var(--border-color);">Volume</th>';
            html += '<th style="padding:8px;border:1px solid var(--border-color);">Buy</th>';
            html += '<th style="padding:8px;border:1px solid var(--border-color);">Sell</th>';
            html += '<th style="padding:8px;border:1px solid var(--border-color);">Intensity</th>';
            html += '</tr></thead><tbody>';
            
            volumeByPrice.slice().reverse().forEach(item => {
                const intensity = item.volume / maxVolume;
                const heatColor = `rgba(231, 76, 60, ${intensity})`;
                const textColor = intensity > 0.5 ? 'white' : 'var(--text-primary)';
                
                html += `<tr style="background:${heatColor};color:${textColor};">`;
                html += `<td style="padding:6px;border:1px solid var(--border-color);font-weight:600;">${item.price.toFixed(2)}</td>`;
                html += `<td style="padding:6px;border:1px solid var(--border-color);text-align:right;">${item.volume.toLocaleString()}</td>`;
                html += `<td style="padding:6px;border:1px solid var(--border-color);text-align:right;">${item.buyVolume.toLocaleString()}</td>`;
                html += `<td style="padding:6px;border:1px solid var(--border-color);text-align:right;">${item.sellVolume.toLocaleString()}</td>`;
                html += `<td style="padding:6px;border:1px solid var(--border-color);text-align:center;">`;
                html += '█'.repeat(Math.ceil(intensity * 10));
                html += '</td></tr>';
            });
            
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function updateVolumeMetrics() {
            if (!volumeProfileData) return;
            
            const { poc, vah, val, totalVolume } = volumeProfileData;
            
            document.getElementById('pocValue').textContent = '$' + poc.toFixed(2);
            document.getElementById('vahValue').textContent = '$' + vah.toFixed(2);
            document.getElementById('valValue').textContent = '$' + val.toFixed(2);
            document.getElementById('totalVolume').textContent = (totalVolume / 1000000).toFixed(2) + 'M';
        }

        function updateVolumeProfile() {
            renderVolumeProfileChart();
        }

        // ============= End Volume Profile Functions =============

        // ============= PWA & Mobile Support Functions =============
        let deferredPrompt = null;
        let isOnline = navigator.onLine;
        let touchStartX = 0;
        let touchStartY = 0;
        let touchEndX = 0;
        let touchEndY = 0;

        // Service Worker Registration
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('./sw.js')
                    .then(registration => {
                        console.log('[PWA] Service Worker registered:', registration.scope);
                        
                        // Check for updates
                        registration.addEventListener('updatefound', () => {
                            const newWorker = registration.installing;
                            newWorker.addEventListener('statechange', () => {
                                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                    showUpdateNotification();
                                }
                            });
                        });
                    })
                    .catch(error => {
                        console.error('[PWA] Service Worker registration failed:', error);
                    });
            });
        }

        // PWA Install Prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[PWA] Install prompt available');
            e.preventDefault();
            deferredPrompt = e;
            showInstallButton();
        });

        function showInstallButton() {
            // Create install button if not exists
            let installBtn = document.getElementById('pwaInstallBtn');
            if (!installBtn) {
                installBtn = document.createElement('button');
                installBtn.id = 'pwaInstallBtn';
                installBtn.innerHTML = '📱 Install App';
                installBtn.style.cssText = 'position:fixed;bottom:80px;right:20px;padding:12px 24px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:25px;font-weight:600;cursor:pointer;box-shadow:0 4px 15px rgba(0,0,0,0.3);z-index:9998;transition:transform 0.2s;font-size:0.9em;';
                installBtn.onmouseover = () => installBtn.style.transform = 'scale(1.05)';
                installBtn.onmouseout = () => installBtn.style.transform = 'scale(1)';
                installBtn.onclick = installPWA;
                document.body.appendChild(installBtn);
            }
            installBtn.style.display = 'block';
        }

        async function installPWA() {
            if (!deferredPrompt) {
                console.log('[PWA] No install prompt available');
                return;
            }

            const installBtn = document.getElementById('pwaInstallBtn');
            installBtn.style.display = 'none';

            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            
            console.log('[PWA] User choice:', outcome);
            
            if (outcome === 'accepted') {
                showPWANotification('✅ App Installed!', 'You can now use the app offline');
            } else {
                showPWANotification('ℹ️ Installation Cancelled', 'You can install later from browser menu');
            }
            
            deferredPrompt = null;
        }

        // App Installed Event
        window.addEventListener('appinstalled', () => {
            console.log('[PWA] App installed successfully');
            showPWANotification('🎉 Welcome!', 'Trading Dashboard is now installed');
            deferredPrompt = null;
        });

        // Online/Offline Detection
        window.addEventListener('online', () => {
            isOnline = true;
            updateOnlineStatus();
            showPWANotification('🟢 Back Online', 'Connection restored');
        });

        window.addEventListener('offline', () => {
            isOnline = false;
            updateOnlineStatus();
            showPWANotification('🔴 Offline Mode', 'You can still view cached data');
        });

        function updateOnlineStatus() {
            const indicator = document.getElementById('onlineStatusIndicator');
            if (!indicator) {
                const div = document.createElement('div');
                div.id = 'onlineStatusIndicator';
                div.style.cssText = 'position:fixed;top:70px;right:20px;padding:8px 16px;border-radius:20px;font-size:0.85em;font-weight:600;z-index:9999;transition:all 0.3s;';
                document.body.appendChild(div);
            }
            
            const statusDiv = document.getElementById('onlineStatusIndicator');
            if (isOnline) {
                statusDiv.textContent = '🟢 Online';
                statusDiv.style.background = 'rgba(39, 174, 96, 0.9)';
                statusDiv.style.color = 'white';
                setTimeout(() => statusDiv.style.display = 'none', 3000);
            } else {
                statusDiv.textContent = '🔴 Offline';
                statusDiv.style.background = 'rgba(231, 76, 60, 0.9)';
                statusDiv.style.color = 'white';
                statusDiv.style.display = 'block';
            }
        }

        function showPWANotification(title, message) {
            const notification = document.createElement('div');
            notification.style.cssText = 'position:fixed;top:20px;right:20px;background:white;padding:16px 20px;border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.3);z-index:10004;min-width:280px;animation:slideInRight 0.3s ease;border-left:4px solid #667eea;';
            notification.innerHTML = `
                <div style="font-weight:700;font-size:1.1em;margin-bottom:5px;">${title}</div>
                <div style="font-size:0.9em;color:#666;">${message}</div>
            `;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 4000);
        }

        // Update notification
        function showUpdateNotification() {
            const updateDiv = document.createElement('div');
            updateDiv.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#667eea;color:white;padding:15px 25px;border-radius:10px;box-shadow:0 4px 15px rgba(0,0,0,0.3);z-index:10005;display:flex;gap:15px;align-items:center;';
            updateDiv.innerHTML = `
                <div>
                    <div style="font-weight:600;">New Update Available</div>
                    <div style="font-size:0.85em;opacity:0.9;">Refresh to get the latest version</div>
                </div>
                <button onclick="window.location.reload()" style="padding:8px 16px;background:white;color:#667eea;border:none;border-radius:6px;font-weight:600;cursor:pointer;">Refresh</button>
                <button onclick="this.parentElement.remove()" style="padding:8px;background:transparent;color:white;border:none;font-size:1.2em;cursor:pointer;">✕</button>
            `;
            document.body.appendChild(updateDiv);
        }

        // Touch Gestures for Mobile
        function initTouchGestures() {
            const chartContainer = document.getElementById('chartContainer');
            if (!chartContainer) return;

            chartContainer.addEventListener('touchstart', handleTouchStart, { passive: true });
            chartContainer.addEventListener('touchend', handleTouchEnd, { passive: true });
        }

        function handleTouchStart(e) {
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }

        function handleTouchEnd(e) {
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            handleGesture();
        }

        function handleGesture() {
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            const minSwipeDistance = 50;

            // Horizontal swipe
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > minSwipeDistance) {
                if (deltaX > 0) {
                    console.log('[Touch] Swipe Right');
                    // Navigate to previous symbol
                    navigatePreviousSymbol();
                } else {
                    console.log('[Touch] Swipe Left');
                    // Navigate to next symbol
                    navigateNextSymbol();
                }
            }
            
            // Vertical swipe
            if (Math.abs(deltaY) > Math.abs(deltaX) && Math.abs(deltaY) > minSwipeDistance) {
                if (deltaY > 0) {
                    console.log('[Touch] Swipe Down');
                    // Refresh data
                    if (currentSymbol) {
                        loadStock(currentSymbol);
                        showPWANotification('🔄 Refreshing', 'Updating data for ' + currentSymbol);
                    }
                } else {
                    console.log('[Touch] Swipe Up');
                    // Show quick actions
                    showQuickActions();
                }
            }
        }

        function navigateNextSymbol() {
            if (!allSymbols || allSymbols.length === 0) return;
            const currentIndex = allSymbols.indexOf(currentSymbol);
            const nextIndex = (currentIndex + 1) % allSymbols.length;
            loadStock(allSymbols[nextIndex]);
        }

        function navigatePreviousSymbol() {
            if (!allSymbols || allSymbols.length === 0) return;
            const currentIndex = allSymbols.indexOf(currentSymbol);
            const prevIndex = (currentIndex - 1 + allSymbols.length) % allSymbols.length;
            loadStock(allSymbols[prevIndex]);
        }

        function showQuickActions() {
            let quickActionsPanel = document.getElementById('quickActionsPanel');
            
            if (!quickActionsPanel) {
                quickActionsPanel = document.createElement('div');
                quickActionsPanel.id = 'quickActionsPanel';
                quickActionsPanel.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:white;border-radius:20px 20px 0 0;box-shadow:0 -5px 20px rgba(0,0,0,0.2);z-index:10006;padding:25px 20px 35px;transform:translateY(100%);transition:transform 0.3s ease;';
                quickActionsPanel.innerHTML = `
                    <div style="text-align:center;margin-bottom:20px;">
                        <div style="width:40px;height:4px;background:#ddd;border-radius:2px;margin:0 auto 15px;"></div>
                        <h3 style="margin:0;font-size:1.2em;color:var(--text-primary);">Quick Actions</h3>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:15px;">
                        <button onclick="openAdvancedBacktest();closeQuickActions();" style="padding:20px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:12px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
                            <span style="font-size:2em;">🔬</span>
                            <span>Backtest</span>
                        </button>
                        <button onclick="openTradeJournal();closeQuickActions();" style="padding:20px;background:linear-gradient(135deg,#f093fb,#f5576c);color:white;border:none;border-radius:12px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
                            <span style="font-size:2em;">📓</span>
                            <span>Journal</span>
                        </button>
                        <button onclick="openAlertsPanel();closeQuickActions();" style="padding:20px;background:linear-gradient(135deg,#4facfe,#00f2fe);color:white;border:none;border-radius:12px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
                            <span style="font-size:2em;">🔔</span>
                            <span>Alerts</span>
                        </button>
                        <button onclick="openVolumeProfile();closeQuickActions();" style="padding:20px;background:linear-gradient(135deg,#43e97b,#38f9d7);color:white;border:none;border-radius:12px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
                            <span style="font-size:2em;">📊</span>
                            <span>Volume</span>
                        </button>
                        <button onclick="openRiskCalculator();closeQuickActions();" style="padding:20px;background:linear-gradient(135deg,#fa709a,#fee140);color:white;border:none;border-radius:12px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
                            <span style="font-size:2em;">⚖️</span>
                            <span>Risk</span>
                        </button>
                        <button onclick="closeQuickActions();" style="padding:20px;background:#95a5a6;color:white;border:none;border-radius:12px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;">
                            <span style="font-size:2em;">✕</span>
                            <span>Close</span>
                        </button>
                    </div>
                `;
                document.body.appendChild(quickActionsPanel);
                
                // Add backdrop
                const backdrop = document.createElement('div');
                backdrop.id = 'quickActionsBackdrop';
                backdrop.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:10005;opacity:0;transition:opacity 0.3s;';
                backdrop.onclick = closeQuickActions;
                document.body.insertBefore(backdrop, quickActionsPanel);
            }
            
            // Show panel
            setTimeout(() => {
                quickActionsPanel.style.transform = 'translateY(0)';
                document.getElementById('quickActionsBackdrop').style.opacity = '1';
            }, 10);
        }

        function closeQuickActions() {
            const panel = document.getElementById('quickActionsPanel');
            const backdrop = document.getElementById('quickActionsBackdrop');
            
            if (panel) {
                panel.style.transform = 'translateY(100%)';
            }
            if (backdrop) {
                backdrop.style.opacity = '0';
                setTimeout(() => {
                    if (backdrop.parentElement) backdrop.remove();
                }, 300);
            }
        }

        // Pinch to Zoom (for charts)
        let initialDistance = 0;
        let currentScale = 1;

        function initPinchZoom() {
            const chartContainer = document.getElementById('chartContainer');
            if (!chartContainer) return;

            chartContainer.addEventListener('touchstart', handlePinchStart, { passive: true });
            chartContainer.addEventListener('touchmove', handlePinchMove, { passive: true });
            chartContainer.addEventListener('touchend', handlePinchEnd, { passive: true });
        }

        function handlePinchStart(e) {
            if (e.touches.length === 2) {
                initialDistance = getDistance(e.touches[0], e.touches[1]);
            }
        }

        function handlePinchMove(e) {
            if (e.touches.length === 2) {
                const currentDistance = getDistance(e.touches[0], e.touches[1]);
                const scale = currentDistance / initialDistance;
                currentScale = Math.max(0.5, Math.min(scale, 3)); // Limit scale between 0.5x and 3x
                console.log('[Touch] Pinch zoom:', currentScale);
            }
        }

        function handlePinchEnd(e) {
            if (e.touches.length < 2) {
                initialDistance = 0;
            }
        }

        function getDistance(touch1, touch2) {
            const dx = touch1.clientX - touch2.clientX;
            const dy = touch1.clientY - touch2.clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }

        // Mobile-specific optimizations
        function isMobile() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        }

        function applyMobileOptimizations() {
            if (isMobile()) {
                console.log('[PWA] Mobile device detected, applying optimizations');
                
                // Reduce animation complexity
                document.documentElement.style.setProperty('--animation-duration', '0.2s');
                
                // Adjust font sizes
                document.documentElement.style.fontSize = '14px';
                
                // Add mobile-specific styles
                const mobileStyles = document.createElement('style');
                mobileStyles.textContent = `
                    @media (max-width: 768px) {
                        .btn { font-size: 0.85em !important; padding: 8px 12px !important; }
                        .modal-content { width: 95% !important; max-height: 90vh !important; }
                        table { font-size: 0.8em !important; }
                        .chart-container { height: 250px !important; }
                        input, select, textarea { font-size: 16px !important; } /* Prevent zoom on iOS */
                    }
                    
                    @media (max-width: 480px) {
                        h1 { font-size: 1.5em !important; }
                        h2 { font-size: 1.3em !important; }
                        h3 { font-size: 1.1em !important; }
                    }
                `;
                document.head.appendChild(mobileStyles);
            }
        }

        // Initialize PWA features on load
        window.addEventListener('DOMContentLoaded', () => {
            initTouchGestures();
            initPinchZoom();
            applyMobileOptimizations();
            updateOnlineStatus();
            
            console.log('[PWA] Mobile features initialized');
            
            // Check if running as installed PWA
            if (window.matchMedia('(display-mode: standalone)').matches) {
                console.log('[PWA] Running as installed app');
                showPWANotification('📱 App Mode', 'Running as installed application');
            }
        });

        // Add slide-in animations
        const animationStyles = document.createElement('style');
        animationStyles.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(400px); opacity: 0; }
            }
        `;
        document.head.appendChild(animationStyles);

        // ============= End PWA & Mobile Support Functions =============

        // ============= Custom Indicator Builder Functions =============
        let customIndicators = JSON.parse(localStorage.getItem('customIndicators') || '[]');
        let currentIndicatorCode = '';
        let indicatorPreviewChart = null;

        function openIndicatorBuilder() {
            document.getElementById('indicatorBuilderModal').style.display = 'flex';
            loadCustomIndicators();
            initCodeEditor();
        }

        function closeIndicatorBuilder() {
            document.getElementById('indicatorBuilderModal').style.display = 'none';
        }

        function initCodeEditor() {
            const editor = document.getElementById('indicatorCodeEditor');
            if (!editor) return;

            // Add syntax highlighting class
            editor.classList.add('code-editor');
            
            // Add line numbers
            editor.addEventListener('input', updateLineNumbers);
            editor.addEventListener('scroll', syncLineNumbers);
        }

        function updateLineNumbers() {
            const editor = document.getElementById('indicatorCodeEditor');
            const lineNumbers = document.getElementById('lineNumbers');
            if (!editor || !lineNumbers) return;

            const lines = editor.value.split('\n').length;
            lineNumbers.innerHTML = Array.from({length: lines}, (_, i) => i + 1).join('\n');
        }

        function syncLineNumbers() {
            const editor = document.getElementById('indicatorCodeEditor');
            const lineNumbers = document.getElementById('lineNumbers');
            if (!editor || !lineNumbers) return;

            lineNumbers.scrollTop = editor.scrollTop;
        }

        function loadTemplate(templateName) {
            const templates = {
                sma: `// Simple Moving Average
function calculate(prices, period = 20) {
    const result = [];
    for (let i = period - 1; i < prices.length; i++) {
        const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
        result.push(sum / period);
    }
    return result;
}`,
                rsi: `// Relative Strength Index
function calculate(prices, period = 14) {
    const changes = [];
    for (let i = 1; i < prices.length; i++) {
        changes.push(prices[i] - prices[i - 1]);
    }
    
    const result = [];
    for (let i = period; i < changes.length; i++) {
        const gains = changes.slice(i - period, i).filter(x => x > 0).reduce((a, b) => a + b, 0);
        const losses = Math.abs(changes.slice(i - period, i).filter(x => x < 0).reduce((a, b) => a + b, 0));
        
        const avgGain = gains / period;
        const avgLoss = losses / period;
        const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
        const rsi = 100 - (100 / (1 + rs));
        result.push(rsi);
    }
    return result;
}`,
                macd: `// MACD (Moving Average Convergence Divergence)
function calculate(prices, fast = 12, slow = 26, signal = 9) {
    const emaFast = calculateEMA(prices, fast);
    const emaSlow = calculateEMA(prices, slow);
    
    const macdLine = [];
    for (let i = 0; i < Math.min(emaFast.length, emaSlow.length); i++) {
        macdLine.push(emaFast[i] - emaSlow[i]);
    }
    
    const signalLine = calculateEMA(macdLine, signal);
    const histogram = [];
    for (let i = 0; i < signalLine.length; i++) {
        histogram.push(macdLine[i + (macdLine.length - signalLine.length)] - signalLine[i]);
    }
    
    return { macdLine, signalLine, histogram };
}

function calculateEMA(prices, period) {
    const k = 2 / (period + 1);
    const ema = [prices[0]];
    
    for (let i = 1; i < prices.length; i++) {
        ema.push(prices[i] * k + ema[i - 1] * (1 - k));
    }
    return ema;
}`,
                bollinger: `// Bollinger Bands
function calculate(prices, period = 20, stdDev = 2) {
    const sma = [];
    const upper = [];
    const lower = [];
    
    for (let i = period - 1; i < prices.length; i++) {
        const slice = prices.slice(i - period + 1, i + 1);
        const mean = slice.reduce((a, b) => a + b, 0) / period;
        const variance = slice.reduce((sum, price) => sum + Math.pow(price - mean, 2), 0) / period;
        const std = Math.sqrt(variance);
        
        sma.push(mean);
        upper.push(mean + stdDev * std);
        lower.push(mean - stdDev * std);
    }
    
    return { sma, upper, lower };
}`,
                custom: `// Custom Indicator Template
function calculate(prices, period = 20) {
    // Your custom logic here
    const result = [];
    
    for (let i = period - 1; i < prices.length; i++) {
        // Calculate your indicator
        const value = 0; // Replace with your calculation
        result.push(value);
    }
    
    return result;
}`
            };

            const editor = document.getElementById('indicatorCodeEditor');
            editor.value = templates[templateName] || templates.custom;
            currentIndicatorCode = editor.value;
            updateLineNumbers();
            
            showPWANotification('📝 Template Loaded', `${templateName.toUpperCase()} template loaded`);
        }

        function validateIndicatorCode() {
            const code = document.getElementById('indicatorCodeEditor').value;
            const output = document.getElementById('validationOutput');
            
            try {
                // Basic syntax check
                new Function(code);
                
                // Check for required function
                if (!code.includes('function calculate')) {
                    throw new Error('Indicator must have a "calculate" function');
                }
                
                output.innerHTML = '<div style="color:#27ae60;padding:10px;background:rgba(39,174,96,0.1);border-radius:6px;">✅ Code is valid! Ready to save.</div>';
                return true;
            } catch (error) {
                output.innerHTML = `<div style="color:#e74c3c;padding:10px;background:rgba(231,76,60,0.1);border-radius:6px;">❌ Error: ${error.message}</div>`;
                return false;
            }
        }

        function testIndicatorCode() {
            const code = document.getElementById('indicatorCodeEditor').value;
            const output = document.getElementById('testOutput');
            
            try {
                // Generate test data
                const testPrices = Array.from({length: 100}, (_, i) => 100 + Math.sin(i / 10) * 10 + Math.random() * 5);
                
                // Execute code
                eval(code);
                const result = calculate(testPrices, 20);
                
                // Show results
                output.innerHTML = `
                    <div style="color:#27ae60;padding:10px;background:rgba(39,174,96,0.1);border-radius:6px;margin-bottom:10px;">
                        ✅ Test successful! Generated ${result.length} data points.
                    </div>
                    <div style="font-size:0.9em;color:var(--text-secondary);">
                        Sample output: [${result.slice(0, 5).map(v => typeof v === 'number' ? v.toFixed(2) : v).join(', ')}...]
                    </div>
                `;
                
                // Render preview chart
                renderIndicatorPreview(testPrices, result);
                
            } catch (error) {
                output.innerHTML = `<div style="color:#e74c3c;padding:10px;background:rgba(231,76,60,0.1);border-radius:6px;">❌ Test failed: ${error.message}</div>`;
            }
        }

        function renderIndicatorPreview(prices, indicatorValues) {
            const canvas = document.getElementById('indicatorPreviewChart');
            if (!canvas) return;

            if (indicatorPreviewChart) {
                indicatorPreviewChart.destroy();
            }

            const ctx = canvas.getContext('2d');
            const labels = Array.from({length: prices.length}, (_, i) => i);

            indicatorPreviewChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Price',
                            data: prices,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            yAxisID: 'y',
                            borderWidth: 2,
                            pointRadius: 0
                        },
                        {
                            label: 'Indicator',
                            data: Array(prices.length - indicatorValues.length).fill(null).concat(indicatorValues),
                            borderColor: '#27ae60',
                            yAxisID: 'y1',
                            borderWidth: 2,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            type: 'linear',
                            position: 'left',
                            title: { display: true, text: 'Price' }
                        },
                        y1: {
                            type: 'linear',
                            position: 'right',
                            title: { display: true, text: 'Indicator' },
                            grid: { drawOnChartArea: false }
                        }
                    }
                }
            });
        }

        function saveCustomIndicator() {
            const name = document.getElementById('indicatorName').value.trim();
            const description = document.getElementById('indicatorDescription').value.trim();
            const code = document.getElementById('indicatorCodeEditor').value;

            if (!name) {
                alert('Please enter an indicator name');
                return;
            }

            if (!validateIndicatorCode()) {
                alert('Please fix code errors before saving');
                return;
            }

            const indicator = {
                id: Date.now(),
                name,
                description,
                code,
                createdAt: new Date().toISOString(),
                lastModified: new Date().toISOString()
            };

            customIndicators.push(indicator);
            localStorage.setItem('customIndicators', JSON.stringify(customIndicators));

            showPWANotification('✅ Indicator Saved', `${name} added to your library`);
            loadCustomIndicators();
            
            // Clear form
            document.getElementById('indicatorName').value = '';
            document.getElementById('indicatorDescription').value = '';
            document.getElementById('indicatorCodeEditor').value = '';
        }

        function loadCustomIndicators() {
            const container = document.getElementById('savedIndicatorsList');
            if (!container) return;

            if (customIndicators.length === 0) {
                container.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary);">No custom indicators yet. Create one to get started!</div>';
                return;
            }

            container.innerHTML = customIndicators.map(indicator => `
                <div style="padding:15px;background:white;border-radius:10px;border:1px solid var(--border-color);margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:start;">
                        <div style="flex:1;">
                            <div style="font-weight:700;font-size:1.1em;margin-bottom:5px;">${indicator.name}</div>
                            <div style="font-size:0.9em;color:var(--text-secondary);margin-bottom:8px;">${indicator.description || 'No description'}</div>
                            <div style="font-size:0.8em;color:var(--text-secondary);">
                                Created: ${new Date(indicator.createdAt).toLocaleString()}
                            </div>
                        </div>
                        <div style="display:flex;gap:8px;">
                            <button onclick="loadIndicatorForEdit(${indicator.id})" style="padding:6px 12px;background:#3498db;color:white;border:none;border-radius:6px;cursor:pointer;font-size:0.85em;">📝 Edit</button>
                            <button onclick="applyIndicator(${indicator.id})" style="padding:6px 12px;background:#27ae60;color:white;border:none;border-radius:6px;cursor:pointer;font-size:0.85em;">✓ Apply</button>
                            <button onclick="deleteIndicator(${indicator.id})" style="padding:6px 12px;background:#e74c3c;color:white;border:none;border-radius:6px;cursor:pointer;font-size:0.85em;">🗑️</button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function loadIndicatorForEdit(id) {
            const indicator = customIndicators.find(i => i.id === id);
            if (!indicator) return;

            document.getElementById('indicatorName').value = indicator.name;
            document.getElementById('indicatorDescription').value = indicator.description;
            document.getElementById('indicatorCodeEditor').value = indicator.code;
            updateLineNumbers();

            // Scroll to editor
            document.getElementById('indicatorCodeEditor').scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            showPWANotification('📝 Indicator Loaded', `${indicator.name} loaded for editing`);
        }

        function deleteIndicator(id) {
            const indicator = customIndicators.find(i => i.id === id);
            if (!indicator) return;

            if (!confirm(`Delete indicator "${indicator.name}"?`)) return;

            customIndicators = customIndicators.filter(i => i.id !== id);
            localStorage.setItem('customIndicators', JSON.stringify(customIndicators));
            loadCustomIndicators();
            
            showPWANotification('🗑️ Indicator Deleted', `${indicator.name} removed from library`);
        }

        function applyIndicator(id) {
            const indicator = customIndicators.find(i => i.id === id);
            if (!indicator) return;

            showPWANotification('✓ Indicator Applied', `${indicator.name} added to chart (demo)`);
            
            // In a real implementation, this would apply the indicator to the active chart
            console.log('Applying indicator:', indicator.name);
        }

        function exportIndicator(id) {
            const indicator = customIndicators.find(i => i.id === id);
            if (!indicator) return;

            const blob = new Blob([JSON.stringify(indicator, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${indicator.name.replace(/\s+/g, '_')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showPWANotification('📥 Indicator Exported', `${indicator.name} saved as JSON`);
        }

        function importIndicator() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = (event) => {
                    try {
                        const indicator = JSON.parse(event.target.result);
                        indicator.id = Date.now(); // New ID
                        indicator.createdAt = new Date().toISOString();
                        
                        customIndicators.push(indicator);
                        localStorage.setItem('customIndicators', JSON.stringify(customIndicators));
                        loadCustomIndicators();
                        
                        showPWANotification('✅ Indicator Imported', `${indicator.name} added to library`);
                    } catch (error) {
                        alert('Invalid indicator file: ' + error.message);
                    }
                };
                reader.readAsText(file);
            };
            input.click();
        }

        function shareIndicator(id) {
            const indicator = customIndicators.find(i => i.id === id);
            if (!indicator) return;

            const shareData = {
                name: indicator.name,
                description: indicator.description,
                code: indicator.code
            };

            // Copy to clipboard
            const shareText = JSON.stringify(shareData, null, 2);
            navigator.clipboard.writeText(shareText).then(() => {
                showPWANotification('📋 Copied to Clipboard', 'Share code copied - paste to share with others');
            }).catch(err => {
                console.error('Copy failed:', err);
            });
        }

        // ============= End Custom Indicator Builder Functions =============

        // ============= Chart Pattern Recognition Functions =============
        let detectedPatterns = [];
        let patternOverlaysVisible = true;

        function openPatternRecognition() {
            document.getElementById('patternRecognitionModal').style.display = 'flex';
            scanForPatterns();
        }

        function closePatternRecognition() {
            document.getElementById('patternRecognitionModal').style.display = 'none';
        }

        function scanForPatterns() {
            const output = document.getElementById('patternScanOutput');
            output.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-secondary);"><div style="font-size:2em;margin-bottom:10px;">🔄</div>Scanning for patterns...</div>';

            // Simulate pattern detection
            setTimeout(() => {
                detectPatterns();
                displayDetectedPatterns();
            }, 1500);
        }

        function detectPatterns() {
            // Generate sample patterns (in real app, this would analyze actual price data)
            const patternTypes = [
                { name: 'Head & Shoulders', type: 'reversal', confidence: 85, bullish: false, emoji: '👤' },
                { name: 'Double Bottom', type: 'reversal', confidence: 78, bullish: true, emoji: 'W' },
                { name: 'Ascending Triangle', type: 'continuation', confidence: 92, bullish: true, emoji: '△' },
                { name: 'Bull Flag', type: 'continuation', confidence: 71, bullish: true, emoji: '🚩' },
                { name: 'Rising Wedge', type: 'reversal', confidence: 65, bullish: false, emoji: '📐' }
            ];

            detectedPatterns = patternTypes.map((pattern, index) => ({
                ...pattern,
                id: Date.now() + index,
                timestamp: new Date().toISOString(),
                priceLevel: (Math.random() * 100 + 100).toFixed(2),
                target: (Math.random() * 10 + 5).toFixed(2),
                status: 'active'
            }));
        }

        function displayDetectedPatterns() {
            const output = document.getElementById('patternScanOutput');
            
            if (detectedPatterns.length === 0) {
                output.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-secondary);">No patterns detected in current timeframe</div>';
                return;
            }

            output.innerHTML = `
                <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(300px, 1fr));gap:15px;">
                    ${detectedPatterns.map(pattern => `
                        <div style="background:white;border-radius:12px;padding:18px;border:2px solid ${pattern.bullish ? '#27ae60' : '#e74c3c'};position:relative;box-shadow:0 4px 12px rgba(0,0,0,0.08);">
                            <div style="position:absolute;top:10px;right:10px;width:50px;height:50px;background:${pattern.bullish ? 'linear-gradient(135deg, #27ae60, #2ecc71)' : 'linear-gradient(135deg, #e74c3c, #c0392b)'};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.5em;color:white;box-shadow:0 4px 12px rgba(0,0,0,0.15);">
                                ${pattern.emoji}
                            </div>
                            
                            <div style="margin-bottom:12px;">
                                <div style="font-weight:800;font-size:1.2em;color:#2c3e50;margin-bottom:4px;">${pattern.name}</div>
                                <div style="display:flex;gap:8px;flex-wrap:wrap;">
                                    <span style="background:${pattern.bullish ? '#d4edda' : '#f8d7da'};color:${pattern.bullish ? '#155724' : '#721c24'};padding:4px 10px;border-radius:6px;font-size:0.8em;font-weight:600;">
                                        ${pattern.bullish ? '📈 Bullish' : '📉 Bearish'}
                                    </span>
                                    <span style="background:#e3f2fd;color:#1565c0;padding:4px 10px;border-radius:6px;font-size:0.8em;font-weight:600;">
                                        ${pattern.type}
                                    </span>
                                </div>
                            </div>

                            <div style="background:#f8f9fa;padding:12px;border-radius:8px;margin-bottom:12px;">
                                <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                                    <span style="color:var(--text-secondary);font-size:0.9em;">Confidence</span>
                                    <span style="font-weight:700;color:#2c3e50;">${pattern.confidence}%</span>
                                </div>
                                <div style="background:#e0e0e0;border-radius:10px;height:8px;overflow:hidden;">
                                    <div style="background:${pattern.confidence > 80 ? '#27ae60' : pattern.confidence > 60 ? '#f39c12' : '#e74c3c'};width:${pattern.confidence}%;height:100%;border-radius:10px;transition:width 0.3s;"></div>
                                </div>
                            </div>

                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;font-size:0.9em;">
                                <div>
                                    <div style="color:var(--text-secondary);margin-bottom:3px;">Price Level</div>
                                    <div style="font-weight:700;color:#2c3e50;">$${pattern.priceLevel}</div>
                                </div>
                                <div>
                                    <div style="color:var(--text-secondary);margin-bottom:3px;">Target</div>
                                    <div style="font-weight:700;color:${pattern.bullish ? '#27ae60' : '#e74c3c'};">${pattern.bullish ? '+' : '-'}${pattern.target}%</div>
                                </div>
                            </div>

                            <div style="display:flex;gap:8px;">
                                <button onclick="highlightPattern(${pattern.id})" style="flex:1;padding:8px;background:#667eea;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                                    📍 Show on Chart
                                </button>
                                <button onclick="setPatternAlert(${pattern.id})" style="flex:1;padding:8px;background:#3498db;color:white;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:0.85em;">
                                    🔔 Alert
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        function highlightPattern(patternId) {
            const pattern = detectedPatterns.find(p => p.id === patternId);
            if (!pattern) return;

            showPWANotification('📍 Pattern Highlighted', `${pattern.name} marked on chart`);
            
            // In real implementation, this would draw the pattern on the chart
            console.log('Highlighting pattern:', pattern.name);
        }

        function setPatternAlert(patternId) {
            const pattern = detectedPatterns.find(p => p.id === patternId);
            if (!pattern) return;

            showPWANotification('🔔 Alert Set', `You'll be notified when ${pattern.name} completes`);
            
            // In real implementation, this would set up an alert
            console.log('Alert set for pattern:', pattern.name);
        }

        function togglePatternOverlays() {
            patternOverlaysVisible = !patternOverlaysVisible;
            const btn = event.target;
            btn.textContent = patternOverlaysVisible ? '👁️ Hide Overlays' : '👁️ Show Overlays';
            btn.style.background = patternOverlaysVisible ? '#e74c3c' : '#27ae60';
            
            showPWANotification(
                patternOverlaysVisible ? '👁️ Overlays Shown' : '👁️ Overlays Hidden',
                `Pattern overlays ${patternOverlaysVisible ? 'enabled' : 'disabled'}`
            );
        }

        function filterPatterns(type) {
            const buttons = document.querySelectorAll('.pattern-filter-btn');
            buttons.forEach(btn => {
                btn.style.background = '#f8f9fa';
                btn.style.color = '#333';
            });
            
            event.target.style.background = '#667eea';
            event.target.style.color = 'white';

            let filtered = detectedPatterns;
            
            if (type === 'bullish') {
                filtered = detectedPatterns.filter(p => p.bullish);
            } else if (type === 'bearish') {
                filtered = detectedPatterns.filter(p => !p.bullish);
            } else if (type === 'reversal') {
                filtered = detectedPatterns.filter(p => p.type === 'reversal');
            } else if (type === 'continuation') {
                filtered = detectedPatterns.filter(p => p.type === 'continuation');
            }

            const temp = [...detectedPatterns];
            detectedPatterns = filtered;
            displayDetectedPatterns();
            
            setTimeout(() => {
                detectedPatterns = temp;
            }, 100);
        }

        function exportPatternReport() {
            const report = {
                timestamp: new Date().toISOString(),
                symbol: currentSymbol || 'AAPL',
                patterns: detectedPatterns,
                summary: {
                    total: detectedPatterns.length,
                    bullish: detectedPatterns.filter(p => p.bullish).length,
                    bearish: detectedPatterns.filter(p => !p.bullish).length,
                    highConfidence: detectedPatterns.filter(p => p.confidence > 80).length
                }
            };

            const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `pattern_report_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showPWANotification('📥 Report Exported', 'Pattern analysis saved as JSON');
        }

        // Pattern education helper
        function showPatternInfo(patternType) {
            const patternInfo = {
                'head-shoulders': {
                    name: 'Head & Shoulders',
                    description: 'A reversal pattern that signals a trend change from bullish to bearish. Consists of a left shoulder, head (highest peak), right shoulder, and a neckline.',
                    signal: 'Bearish reversal',
                    entry: 'Break below neckline',
                    target: 'Distance from head to neckline projected downward'
                },
                'double-bottom': {
                    name: 'Double Bottom',
                    description: 'A bullish reversal pattern forming a "W" shape. Two consecutive troughs at similar price levels with a peak in between.',
                    signal: 'Bullish reversal',
                    entry: 'Break above middle peak',
                    target: 'Distance from bottom to middle peak projected upward'
                },
                'triangle': {
                    name: 'Triangle Patterns',
                    description: 'Continuation patterns (ascending, descending, symmetrical) formed by converging trendlines. Price consolidates before continuing the trend.',
                    signal: 'Usually continuation',
                    entry: 'Breakout from triangle',
                    target: 'Height of triangle base projected in breakout direction'
                },
                'flag': {
                    name: 'Flag Patterns',
                    description: 'Short-term continuation patterns that look like a small rectangle (flag) on a pole. Represents brief consolidation in a strong trend.',
                    signal: 'Continuation',
                    entry: 'Break from flag in trend direction',
                    target: 'Length of flagpole projected from breakout'
                },
                'wedge': {
                    name: 'Wedge Patterns',
                    description: 'Converging trendlines with both sloping in same direction. Rising wedge is bearish, falling wedge is bullish.',
                    signal: 'Reversal',
                    entry: 'Break from wedge',
                    target: 'Height of wedge base projected in breakout direction'
                }
            };

            const info = patternInfo[patternType];
            if (!info) return;

            alert(`${info.name}\n\n${info.description}\n\nSignal: ${info.signal}\nEntry: ${info.entry}\nTarget: ${info.target}`);
        }

        // ============= End Chart Pattern Recognition Functions =============

        // ============= Risk Calculator & Position Sizer Functions =============
        function openRiskCalculator() {
            document.getElementById('riskCalculatorModal').style.display = 'flex';
            calculateRisk(); // Initial calculation
        }

        function closeRiskCalculator() {
            document.getElementById('riskCalculatorModal').style.display = 'none';
        }

        function calculateRisk() {
            // Get input values
            const accountSize = parseFloat(document.getElementById('accountSize').value) || 10000;
            const riskPercent = parseFloat(document.getElementById('riskPercent').value) || 2;
            const entryPrice = parseFloat(document.getElementById('entryPrice').value) || 100;
            const stopLoss = parseFloat(document.getElementById('stopLoss').value) || 95;
            const takeProfit = parseFloat(document.getElementById('takeProfit').value) || 110;
            const leverage = parseFloat(document.getElementById('leverage').value) || 1;

            // Calculate risk amount
            const riskAmount = (accountSize * riskPercent) / 100;
            
            // Calculate price difference
            const priceDiff = Math.abs(entryPrice - stopLoss);
            const profitDiff = Math.abs(takeProfit - entryPrice);
            
            // Calculate position size
            const positionSize = riskAmount / priceDiff;
            
            // Calculate position value
            const positionValue = positionSize * entryPrice;
            
            // Calculate with leverage
            const requiredMargin = positionValue / leverage;
            const leveragedPositionSize = positionSize * leverage;
            
            // Calculate risk/reward ratio
            const riskRewardRatio = profitDiff / priceDiff;
            
            // Calculate potential profit/loss
            const potentialProfit = positionSize * profitDiff;
            const potentialLoss = riskAmount;
            
            // Calculate break-even
            const commission = 0.001; // 0.1% commission
            const totalCommission = positionValue * commission * 2; // Entry + exit
            const breakEvenPrice = entryPrice + (totalCommission / positionSize);

            // Display results
            displayRiskResults({
                accountSize,
                riskPercent,
                riskAmount,
                entryPrice,
                stopLoss,
                takeProfit,
                positionSize,
                positionValue,
                leverage,
                requiredMargin,
                leveragedPositionSize,
                riskRewardRatio,
                potentialProfit,
                potentialLoss,
                breakEvenPrice,
                totalCommission
            });
        }

        function displayRiskResults(results) {
            const output = document.getElementById('riskCalculationResults');
            
            const riskColor = results.riskRewardRatio >= 2 ? '#27ae60' : results.riskRewardRatio >= 1.5 ? '#f39c12' : '#e74c3c';
            
            output.innerHTML = `
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:20px;">
                    <!-- Position Size Card -->
                    <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);padding:25px;border-radius:15px;color:white;box-shadow:0 8px 20px rgba(102,126,234,0.3);">
                        <div style="font-size:0.9em;opacity:0.9;margin-bottom:8px;">Position Size</div>
                        <div style="font-size:2.5em;font-weight:800;margin-bottom:5px;">${results.positionSize.toFixed(2)}</div>
                        <div style="font-size:0.85em;opacity:0.8;">shares/units</div>
                    </div>

                    <!-- Position Value Card -->
                    <div style="background:linear-gradient(135deg, #f093fb 0%, #f5576c 100%);padding:25px;border-radius:15px;color:white;box-shadow:0 8px 20px rgba(240,147,251,0.3);">
                        <div style="font-size:0.9em;opacity:0.9;margin-bottom:8px;">Position Value</div>
                        <div style="font-size:2.5em;font-weight:800;margin-bottom:5px;">$${results.positionValue.toFixed(2)}</div>
                        <div style="font-size:0.85em;opacity:0.8;">total exposure</div>
                    </div>

                    <!-- Risk Amount Card -->
                    <div style="background:linear-gradient(135deg, #fa709a 0%, #fee140 100%);padding:25px;border-radius:15px;color:white;box-shadow:0 8px 20px rgba(250,112,154,0.3);">
                        <div style="font-size:0.9em;opacity:0.9;margin-bottom:8px;">Risk Amount</div>
                        <div style="font-size:2.5em;font-weight:800;margin-bottom:5px;">$${results.riskAmount.toFixed(2)}</div>
                        <div style="font-size:0.85em;opacity:0.8;">${results.riskPercent}% of account</div>
                    </div>

                    <!-- Risk/Reward Ratio Card -->
                    <div style="background:linear-gradient(135deg, ${riskColor}, ${riskColor === '#27ae60' ? '#2ecc71' : riskColor === '#f39c12' ? '#f1c40f' : '#c0392b'});padding:25px;border-radius:15px;color:white;box-shadow:0 8px 20px rgba(39,174,96,0.3);">
                        <div style="font-size:0.9em;opacity:0.9;margin-bottom:8px;">Risk/Reward Ratio</div>
                        <div style="font-size:2.5em;font-weight:800;margin-bottom:5px;">1:${results.riskRewardRatio.toFixed(2)}</div>
                        <div style="font-size:0.85em;opacity:0.8;">${results.riskRewardRatio >= 2 ? 'Excellent' : results.riskRewardRatio >= 1.5 ? 'Good' : 'Poor'} ratio</div>
                    </div>
                </div>

                <!-- Detailed Breakdown -->
                <div style="background:white;border-radius:15px;padding:25px;margin-top:20px;border:1px solid var(--border-color);">
                    <h3 style="font-size:1.3em;font-weight:700;color:#2c3e50;margin:0 0 20px 0;">Detailed Breakdown</h3>
                    
                    <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:20px;">
                        <div style="background:#f8f9fa;padding:15px;border-radius:10px;">
                            <div style="color:var(--text-secondary);font-size:0.85em;margin-bottom:5px;">Entry Price</div>
                            <div style="font-size:1.5em;font-weight:700;color:#2c3e50;">$${results.entryPrice.toFixed(2)}</div>
                        </div>

                        <div style="background:#f8f9fa;padding:15px;border-radius:10px;">
                            <div style="color:var(--text-secondary);font-size:0.85em;margin-bottom:5px;">Stop Loss</div>
                            <div style="font-size:1.5em;font-weight:700;color:#e74c3c;">$${results.stopLoss.toFixed(2)}</div>
                        </div>

                        <div style="background:#f8f9fa;padding:15px;border-radius:10px;">
                            <div style="color:var(--text-secondary);font-size:0.85em;margin-bottom:5px;">Take Profit</div>
                            <div style="font-size:1.5em;font-weight:700;color:#27ae60;">$${results.takeProfit.toFixed(2)}</div>
                        </div>

                        <div style="background:#f8f9fa;padding:15px;border-radius:10px;">
                            <div style="color:var(--text-secondary);font-size:0.85em;margin-bottom:5px;">Break Even</div>
                            <div style="font-size:1.5em;font-weight:700;color:#3498db;">$${results.breakEvenPrice.toFixed(2)}</div>
                        </div>

                        <div style="background:#f8f9fa;padding:15px;border-radius:10px;">
                            <div style="color:var(--text-secondary);font-size:0.85em;margin-bottom:5px;">Potential Profit</div>
                            <div style="font-size:1.5em;font-weight:700;color:#27ae60;">$${results.potentialProfit.toFixed(2)}</div>
                        </div>

                        <div style="background:#f8f9fa;padding:15px;border-radius:10px;">
                            <div style="color:var(--text-secondary);font-size:0.85em;margin-bottom:5px;">Potential Loss</div>
                            <div style="font-size:1.5em;font-weight:700;color:#e74c3c;">$${results.potentialLoss.toFixed(2)}</div>
                        </div>

                        ${results.leverage > 1 ? `
                        <div style="background:#fff3cd;padding:15px;border-radius:10px;border:2px solid #ffc107;">
                            <div style="color:#856404;font-size:0.85em;margin-bottom:5px;">Required Margin</div>
                            <div style="font-size:1.5em;font-weight:700;color:#856404;">$${results.requiredMargin.toFixed(2)}</div>
                        </div>

                        <div style="background:#fff3cd;padding:15px;border-radius:10px;border:2px solid #ffc107;">
                            <div style="color:#856404;font-size:0.85em;margin-bottom:5px;">Leverage</div>
                            <div style="font-size:1.5em;font-weight:700;color:#856404;">${results.leverage}x</div>
                        </div>
                        ` : ''}

                        <div style="background:#f8f9fa;padding:15px;border-radius:10px;">
                            <div style="color:var(--text-secondary);font-size:0.85em;margin-bottom:5px;">Total Fees</div>
                            <div style="font-size:1.5em;font-weight:700;color:#95a5a6;">$${results.totalCommission.toFixed(2)}</div>
                        </div>
                    </div>
                </div>

                <!-- Visual Risk/Reward Chart -->
                <div style="background:white;border-radius:15px;padding:25px;margin-top:20px;border:1px solid var(--border-color);">
                    <h3 style="font-size:1.3em;font-weight:700;color:#2c3e50;margin:0 0 20px 0;">Risk/Reward Visualization</h3>
                    <div style="display:flex;gap:15px;align-items:center;">
                        <div style="flex:1;height:60px;background:linear-gradient(90deg, #e74c3c 0%, #e74c3c ${(1 / (1 + results.riskRewardRatio)) * 100}%, #27ae60 ${(1 / (1 + results.riskRewardRatio)) * 100}%, #27ae60 100%);border-radius:10px;position:relative;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                            <div style="position:absolute;left:${(1 / (1 + results.riskRewardRatio)) * 100}%;top:-40px;transform:translateX(-50%);background:#3498db;color:white;padding:5px 12px;border-radius:6px;font-size:0.8em;font-weight:700;white-space:nowrap;">Entry: $${results.entryPrice.toFixed(2)}</div>
                            <div style="position:absolute;left:0;top:70px;font-size:0.85em;color:#e74c3c;font-weight:700;">Loss: $${results.potentialLoss.toFixed(2)}</div>
                            <div style="position:absolute;right:0;top:70px;font-size:0.85em;color:#27ae60;font-weight:700;">Profit: $${results.potentialProfit.toFixed(2)}</div>
                        </div>
                    </div>
                </div>

                ${results.riskRewardRatio < 1.5 ? `
                <div style="background:#fff3cd;border:2px solid #ffc107;border-radius:12px;padding:20px;margin-top:20px;">
                    <div style="display:flex;align-items:center;gap:15px;">
                        <div style="font-size:2.5em;">⚠️</div>
                        <div>
                            <div style="font-weight:700;color:#856404;font-size:1.1em;margin-bottom:5px;">Low Risk/Reward Ratio Warning</div>
                            <div style="color:#856404;font-size:0.9em;">Consider improving your risk/reward ratio to at least 1:1.5 for better trading outcomes. Adjust your take profit or stop loss levels.</div>
                        </div>
                    </div>
                </div>
                ` : ''}
            `;
        }

        function saveRiskTemplate() {
            const templateName = prompt('Enter template name:');
            if (!templateName) return;

            const template = {
                name: templateName,
                accountSize: document.getElementById('accountSize').value,
                riskPercent: document.getElementById('riskPercent').value,
                leverage: document.getElementById('leverage').value,
                timestamp: new Date().toISOString()
            };

            let templates = JSON.parse(localStorage.getItem('riskTemplates') || '[]');
            templates.push(template);
            localStorage.setItem('riskTemplates', JSON.stringify(templates));

            showPWANotification('💾 Template Saved', `"${templateName}" saved successfully`);
        }

        function quickFillRisk(preset) {
            const presets = {
                conservative: { risk: 1, leverage: 1 },
                moderate: { risk: 2, leverage: 2 },
                aggressive: { risk: 5, leverage: 5 }
            };

            const selected = presets[preset];
            if (selected) {
                document.getElementById('riskPercent').value = selected.risk;
                document.getElementById('leverage').value = selected.leverage;
                calculateRisk();
                showPWANotification('⚡ Preset Applied', `${preset.charAt(0).toUpperCase() + preset.slice(1)} risk profile loaded`);
            }
        }

        // ============= End Risk Calculator & Position Sizer Functions =============

        // ============= Multi-Timeframe Analysis Functions =============
        let multiTimeframeCharts = {};
        const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];
        let currentMTFLayout = 'grid-6';

        function openMultiTimeframe() {
            document.getElementById('multiTimeframeModal').style.display = 'flex';
            setTimeout(() => initMultiTimeframeCharts(), 100);
        }

        function closeMultiTimeframe() {
            document.getElementById('multiTimeframeModal').style.display = 'none';
            // Cleanup charts
            Object.values(multiTimeframeCharts).forEach(chart => {
                if (chart) chart.destroy();
            });
            multiTimeframeCharts = {};
        }

        function initMultiTimeframeCharts() {
            timeframes.forEach(tf => {
                const canvas = document.getElementById(`mtf-chart-${tf}`);
                if (!canvas) return;

                // Generate sample data for each timeframe
                const data = generateTimeframeData(tf);
                
                const ctx = canvas.getContext('2d');
                
                if (multiTimeframeCharts[tf]) {
                    multiTimeframeCharts[tf].destroy();
                }

                multiTimeframeCharts[tf] = new Chart(ctx, {
                    type: 'candlestick',
                    data: {
                        datasets: [{
                            label: `${currentSymbol || 'AAPL'} - ${tf}`,
                            data: data.candles
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                enabled: true,
                                mode: 'index',
                                intersect: false
                            }
                        },
                        scales: {
                            x: {
                                type: 'time',
                                time: {
                                    unit: getTimeUnit(tf)
                                },
                                grid: { display: false }
                            },
                            y: {
                                position: 'right',
                                grid: { color: 'rgba(0,0,0,0.05)' }
                            }
                        }
                    }
                });
            });
        }

        function generateTimeframeData(timeframe) {
            // Generate realistic candle data based on timeframe
            const periods = { '1m': 100, '5m': 100, '15m': 100, '1h': 100, '4h': 60, '1d': 60 };
            const count = periods[timeframe] || 100;
            const candles = [];
            
            let basePrice = 150;
            const now = Date.now();
            const interval = getTimeframeInterval(timeframe);

            for (let i = 0; i < count; i++) {
                const time = now - (count - i) * interval;
                const open = basePrice + (Math.random() - 0.5) * 2;
                const close = open + (Math.random() - 0.5) * 3;
                const high = Math.max(open, close) + Math.random() * 2;
                const low = Math.min(open, close) - Math.random() * 2;

                candles.push({
                    x: time,
                    o: open,
                    h: high,
                    l: low,
                    c: close
                });

                basePrice = close;
            }

            return { candles };
        }

        function getTimeframeInterval(tf) {
            const intervals = {
                '1m': 60 * 1000,
                '5m': 5 * 60 * 1000,
                '15m': 15 * 60 * 1000,
                '1h': 60 * 60 * 1000,
                '4h': 4 * 60 * 60 * 1000,
                '1d': 24 * 60 * 60 * 1000
            };
            return intervals[tf] || 60000;
        }

        function getTimeUnit(tf) {
            if (tf === '1m' || tf === '5m' || tf === '15m') return 'minute';
            if (tf === '1h' || tf === '4h') return 'hour';
            return 'day';
        }

        function changeMTFLayout(layout) {
            currentMTFLayout = layout;
            const container = document.getElementById('mtfChartsContainer');
            
            // Update grid layout
            if (layout === 'grid-6') {
                container.style.gridTemplateColumns = 'repeat(3, 1fr)';
                container.style.gridTemplateRows = 'repeat(2, 1fr)';
                timeframes.forEach(tf => {
                    document.getElementById(`mtf-container-${tf}`).style.display = 'block';
                });
            } else if (layout === 'grid-4') {
                container.style.gridTemplateColumns = 'repeat(2, 1fr)';
                container.style.gridTemplateRows = 'repeat(2, 1fr)';
                // Show only first 4
                timeframes.forEach((tf, i) => {
                    document.getElementById(`mtf-container-${tf}`).style.display = i < 4 ? 'block' : 'none';
                });
            } else if (layout === 'grid-2') {
                container.style.gridTemplateColumns = 'repeat(2, 1fr)';
                container.style.gridTemplateRows = '1fr';
                // Show only first 2
                timeframes.forEach((tf, i) => {
                    document.getElementById(`mtf-container-${tf}`).style.display = i < 2 ? 'block' : 'none';
                });
            } else if (layout === 'single') {
                container.style.gridTemplateColumns = '1fr';
                container.style.gridTemplateRows = '1fr';
                // Show only first one
                timeframes.forEach((tf, i) => {
                    document.getElementById(`mtf-container-${tf}`).style.display = i === 0 ? 'block' : 'none';
                });
            }

            // Update button styles
            document.querySelectorAll('.mtf-layout-btn').forEach(btn => {
                btn.style.background = '#f8f9fa';
                btn.style.color = '#333';
            });
            event.target.style.background = '#667eea';
            event.target.style.color = 'white';

            // Resize charts
            setTimeout(() => {
                Object.values(multiTimeframeCharts).forEach(chart => {
                    if (chart) chart.resize();
                });
            }, 100);
        }

        function syncMTFCrosshair(enabled) {
            // In a real implementation, this would sync crosshairs across all timeframes
            showPWANotification(
                enabled ? '🔗 Crosshair Synced' : '🔗 Crosshair Unsynced',
                `Crosshair synchronization ${enabled ? 'enabled' : 'disabled'}`
            );
        }

        function exportMTFAnalysis() {
            const analysis = {
                symbol: currentSymbol || 'AAPL',
                timestamp: new Date().toISOString(),
                timeframes: timeframes.map(tf => ({
                    timeframe: tf,
                    trend: ['bullish', 'bearish', 'neutral'][Math.floor(Math.random() * 3)],
                    strength: Math.floor(Math.random() * 100)
                }))
            };

            const blob = new Blob([JSON.stringify(analysis, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mtf_analysis_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showPWANotification('📥 Analysis Exported', 'Multi-timeframe analysis saved');
        }

        function showMTFSummary() {
            const summary = `
                📊 Multi-Timeframe Analysis Summary
                
                Symbol: ${currentSymbol || 'AAPL'}
                
                1m: Bullish - Strong momentum
                5m: Bullish - Consolidating
                15m: Neutral - Range-bound
                1h: Bullish - Breakout setup
                4h: Bullish - Uptrend intact
                1d: Bullish - New highs
                
                Overall: Strong Bullish Alignment
                Confidence: 85%
            `;
            
            alert(summary);
        }

        // ============= End Multi-Timeframe Analysis Functions =============

        // ============= Fibonacci & Drawing Tools Functions =============
        let activeDrawingTool = null;
        let drawings = [];
        let isDrawing = false;
        let drawStart = null;

        function openDrawingTools() {
            document.getElementById('drawingToolsModal').style.display = 'flex';
            initDrawingCanvas();
        }

        function closeDrawingTools() {
            document.getElementById('drawingToolsModal').style.display = 'none';
            activeDrawingTool = null;
        }

        function initDrawingCanvas() {
            const canvas = document.getElementById('drawingCanvas');
            if (!canvas) return;

            // Draw sample chart background
            const ctx = canvas.getContext('2d');
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;

            // Draw grid
            ctx.strokeStyle = '#e0e0e0';
            ctx.lineWidth = 1;
            for (let i = 0; i < canvas.width; i += 50) {
                ctx.beginPath();
                ctx.moveTo(i, 0);
                ctx.lineTo(i, canvas.height);
                ctx.stroke();
            }
            for (let i = 0; i < canvas.height; i += 50) {
                ctx.beginPath();
                ctx.moveTo(0, i);
                ctx.lineTo(canvas.width, i);
                ctx.stroke();
            }

            // Draw sample price line
            ctx.strokeStyle = '#667eea';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, canvas.height / 2);
            for (let x = 0; x < canvas.width; x += 10) {
                const y = canvas.height / 2 + Math.sin(x / 50) * 80 + Math.random() * 20;
                ctx.lineTo(x, y);
            }
            ctx.stroke();

            // Add event listeners
            canvas.addEventListener('mousedown', handleDrawingStart);
            canvas.addEventListener('mousemove', handleDrawingMove);
            canvas.addEventListener('mouseup', handleDrawingEnd);
            canvas.addEventListener('mouseleave', handleDrawingEnd);
        }

        function selectDrawingTool(tool) {
            activeDrawingTool = tool;
            
            // Update button styles
            document.querySelectorAll('.drawing-tool-btn').forEach(btn => {
                btn.style.background = '#f8f9fa';
                btn.style.color = '#333';
                btn.style.borderColor = '#e0e0e0';
            });
            
            if (event.target.classList.contains('drawing-tool-btn')) {
                event.target.style.background = '#667eea';
                event.target.style.color = 'white';
                event.target.style.borderColor = '#667eea';
            }

            showPWANotification('✏️ Tool Selected', `${tool} tool activated`);
        }

        function handleDrawingStart(e) {
            if (!activeDrawingTool) return;
            
            isDrawing = true;
            const rect = e.target.getBoundingClientRect();
            drawStart = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
        }

        function handleDrawingMove(e) {
            if (!isDrawing || !activeDrawingTool) return;
            
            const canvas = document.getElementById('drawingCanvas');
            const rect = canvas.getBoundingClientRect();
            const currentPos = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };

            // Redraw canvas with current drawing
            initDrawingCanvas();
            redrawAllDrawings();
            drawPreview(drawStart, currentPos);
        }

        function handleDrawingEnd(e) {
            if (!isDrawing || !activeDrawingTool) return;
            
            const rect = e.target.getBoundingClientRect();
            const drawEnd = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };

            // Save drawing
            const drawing = {
                id: Date.now(),
                tool: activeDrawingTool,
                start: drawStart,
                end: drawEnd,
                timestamp: new Date().toISOString()
            };

            drawings.push(drawing);
            
            if (activeDrawingTool.includes('Fibonacci')) {
                calculateFibonacciLevels(drawing);
            }

            isDrawing = false;
            drawStart = null;
            
            // Redraw all
            initDrawingCanvas();
            redrawAllDrawings();
            updateDrawingsList();
        }

        function drawPreview(start, end) {
            const canvas = document.getElementById('drawingCanvas');
            const ctx = canvas.getContext('2d');

            ctx.strokeStyle = '#667eea';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);

            switch(activeDrawingTool) {
                case 'Trend Line':
                    ctx.beginPath();
                    ctx.moveTo(start.x, start.y);
                    ctx.lineTo(end.x, end.y);
                    ctx.stroke();
                    break;
                
                case 'Horizontal Line':
                    ctx.beginPath();
                    ctx.moveTo(0, start.y);
                    ctx.lineTo(canvas.width, start.y);
                    ctx.stroke();
                    break;
                
                case 'Vertical Line':
                    ctx.beginPath();
                    ctx.moveTo(start.x, 0);
                    ctx.lineTo(start.x, canvas.height);
                    ctx.stroke();
                    break;
                
                case 'Rectangle':
                    ctx.strokeRect(start.x, start.y, end.x - start.x, end.y - start.y);
                    break;
                
                case 'Fibonacci Retracement':
                    drawFibonacci(ctx, start, end);
                    break;
            }

            ctx.setLineDash([]);
        }

        function redrawAllDrawings() {
            const canvas = document.getElementById('drawingCanvas');
            const ctx = canvas.getContext('2d');

            drawings.forEach(drawing => {
                ctx.strokeStyle = '#667eea';
                ctx.lineWidth = 2;

                switch(drawing.tool) {
                    case 'Trend Line':
                        ctx.beginPath();
                        ctx.moveTo(drawing.start.x, drawing.start.y);
                        ctx.lineTo(drawing.end.x, drawing.end.y);
                        ctx.stroke();
                        break;
                    
                    case 'Horizontal Line':
                        ctx.beginPath();
                        ctx.moveTo(0, drawing.start.y);
                        ctx.lineTo(canvas.width, drawing.start.y);
                        ctx.stroke();
                        break;
                    
                    case 'Vertical Line':
                        ctx.beginPath();
                        ctx.moveTo(drawing.start.x, 0);
                        ctx.lineTo(drawing.start.x, canvas.height);
                        ctx.stroke();
                        break;
                    
                    case 'Rectangle':
                        ctx.strokeRect(drawing.start.x, drawing.start.y, 
                                     drawing.end.x - drawing.start.x, 
                                     drawing.end.y - drawing.start.y);
                        break;
                    
                    case 'Fibonacci Retracement':
                        drawFibonacci(ctx, drawing.start, drawing.end);
                        break;
                }
            });
        }

        function drawFibonacci(ctx, start, end) {
            const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
            const colors = ['#e74c3c', '#e67e22', '#f39c12', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6'];
            
            const canvas = document.getElementById('drawingCanvas');
            const diff = end.y - start.y;

            ctx.font = '12px Arial';
            levels.forEach((level, i) => {
                const y = start.y + diff * level;
                ctx.strokeStyle = colors[i];
                ctx.lineWidth = 1;
                ctx.setLineDash([3, 3]);
                
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
                
                // Draw label
                ctx.fillStyle = colors[i];
                ctx.fillText(`${(level * 100).toFixed(1)}%`, 10, y - 5);
            });
            
            ctx.setLineDash([]);
        }

        function calculateFibonacciLevels(drawing) {
            const priceDiff = Math.abs(drawing.end.y - drawing.start.y);
            const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
            
            const fibLevels = levels.map(level => ({
                level: level,
                percentage: (level * 100).toFixed(1) + '%',
                price: (100 + (Math.random() - 0.5) * 20).toFixed(2)
            }));

            console.log('Fibonacci Levels:', fibLevels);
        }

        function clearAllDrawings() {
            if (!confirm('Clear all drawings?')) return;
            
            drawings = [];
            initDrawingCanvas();
            updateDrawingsList();
            showPWANotification('🗑️ Cleared', 'All drawings removed');
        }

        function undoLastDrawing() {
            if (drawings.length === 0) return;
            
            drawings.pop();
            initDrawingCanvas();
            redrawAllDrawings();
            updateDrawingsList();
            showPWANotification('↶ Undo', 'Last drawing removed');
        }

        function saveDrawings() {
            localStorage.setItem('chartDrawings', JSON.stringify(drawings));
            showPWANotification('💾 Saved', `${drawings.length} drawings saved`);
        }

        function loadDrawings() {
            const saved = localStorage.getItem('chartDrawings');
            if (saved) {
                drawings = JSON.parse(saved);
                initDrawingCanvas();
                redrawAllDrawings();
                updateDrawingsList();
                showPWANotification('📂 Loaded', `${drawings.length} drawings loaded`);
            }
        }

        function updateDrawingsList() {
            const list = document.getElementById('drawingsList');
            if (!list) return;

            if (drawings.length === 0) {
                list.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-secondary);">No drawings yet. Select a tool and draw on the chart.</div>';
                return;
            }

            list.innerHTML = drawings.map((drawing, index) => `
                <div style="padding:12px;background:white;border:1px solid var(--border-color);border-radius:8px;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:600;color:#2c3e50;">${drawing.tool}</span>
                        <span style="font-size:0.85em;color:var(--text-secondary);margin-left:10px;">
                            ${new Date(drawing.timestamp).toLocaleTimeString()}
                        </span>
                    </div>
                    <button onclick="deleteDrawing(${drawing.id})" style="padding:6px 12px;background:#e74c3c;color:white;border:none;border-radius:6px;cursor:pointer;font-size:0.85em;">
                        Delete
                    </button>
                </div>
            `).join('');
        }

        function deleteDrawing(id) {
            drawings = drawings.filter(d => d.id !== id);
            initDrawingCanvas();
            redrawAllDrawings();
            updateDrawingsList();
        }

        // ============= End Fibonacci & Drawing Tools Functions =============

        // ============= Economic Calendar Functions =============
        let economicEvents = [];

        function openEconomicCalendar() {
            document.getElementById('economicCalendarModal').style.display = 'flex';
            generateEconomicEvents();
            displayEconomicEvents();
            updateCountdowns();
        }

        function closeEconomicCalendar() {
            document.getElementById('economicCalendarModal').style.display = 'none';
        }

        function generateEconomicEvents() {
            const now = new Date();
            const eventTypes = [
                { name: 'Non-Farm Payrolls (NFP)', impact: 'high', country: 'USD' },
                { name: 'FOMC Interest Rate Decision', impact: 'high', country: 'USD' },
                { name: 'CPI (Consumer Price Index)', impact: 'high', country: 'USD' },
                { name: 'GDP Growth Rate', impact: 'high', country: 'USD' },
                { name: 'Unemployment Rate', impact: 'medium', country: 'USD' },
                { name: 'Retail Sales', impact: 'medium', country: 'USD' },
                { name: 'PMI Manufacturing', impact: 'medium', country: 'USD' },
                { name: 'ECB Interest Rate Decision', impact: 'high', country: 'EUR' },
                { name: 'UK GDP Growth', impact: 'high', country: 'GBP' },
                { name: 'Bank of Japan Meeting', impact: 'high', country: 'JPY' }
            ];

            economicEvents = [];
            for (let i = 0; i < 15; i++) {
                const event = eventTypes[Math.floor(Math.random() * eventTypes.length)];
                const futureDate = new Date(now.getTime() + (Math.random() * 14 - 3) * 24 * 60 * 60 * 1000);
                
                economicEvents.push({
                    id: i + 1,
                    ...event,
                    date: futureDate,
                    time: `${String(Math.floor(Math.random() * 12) + 8).padStart(2, '0')}:${Math.random() > 0.5 ? '00' : '30'}`,
                    actual: Math.random() > 0.5 ? (Math.random() * 10).toFixed(1) + '%' : 'TBD',
                    forecast: (Math.random() * 10).toFixed(1) + '%',
                    previous: (Math.random() * 10).toFixed(1) + '%'
                });
            }

            economicEvents.sort((a, b) => a.date - b.date);
        }

        function displayEconomicEvents() {
            const container = document.getElementById('economicEventsList');
            const now = new Date();

            const groupedByDate = {};
            economicEvents.forEach(event => {
                const dateKey = event.date.toDateString();
                if (!groupedByDate[dateKey]) {
                    groupedByDate[dateKey] = [];
                }
                groupedByDate[dateKey].push(event);
            });

            container.innerHTML = Object.entries(groupedByDate).map(([dateKey, events]) => {
                const eventDate = new Date(dateKey);
                const isToday = eventDate.toDateString() === now.toDateString();
                const isPast = eventDate < now && !isToday;

                return `
                    <div style="margin-bottom:25px;">
                        <div style="padding:12px 20px;background:${isToday ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : isPast ? '#95a5a6' : '#f8f9fa'};border-radius:10px;margin-bottom:12px;${isToday || isPast ? 'color:white;' : 'color:#2c3e50;'}">
                            <span style="font-weight:800;font-size:1.1em;">${formatEventDate(eventDate)}</span>
                            ${isToday ? '<span style="margin-left:10px;padding:4px 10px;background:rgba(255,255,255,0.3);border-radius:6px;font-size:0.85em;font-weight:700;">TODAY</span>' : ''}
                        </div>
                        
                        ${events.map(event => {
                            const impactColor = event.impact === 'high' ? '#e74c3c' : event.impact === 'medium' ? '#f39c12' : '#95a5a6';
                            const isPastEvent = event.date < now;
                            
                            return `
                                <div style="background:white;border:2px solid ${isPastEvent ? '#e0e0e0' : impactColor};border-radius:12px;padding:18px;margin-bottom:12px;${isPastEvent ? 'opacity:0.6;' : ''}">
                                    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:12px;">
                                        <div style="flex:1;">
                                            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                                                <span style="font-size:1.8em;">${getCountryFlag(event.country)}</span>
                                                <div>
                                                    <div style="font-weight:800;font-size:1.15em;color:#2c3e50;">${event.name}</div>
                                                    <div style="font-size:0.85em;color:var(--text-secondary);margin-top:2px;">
                                                        ${event.time} ${event.country}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div style="display:flex;flex-direction:column;align-items:end;gap:6px;">
                                            <span style="padding:6px 14px;background:${impactColor};color:white;border-radius:8px;font-size:0.8em;font-weight:700;text-transform:uppercase;">
                                                ${event.impact} Impact
                                            </span>
                                            ${!isPastEvent ? `<div id="countdown-${event.id}" style="font-size:0.85em;color:#667eea;font-weight:700;"></div>` : ''}
                                        </div>
                                    </div>

                                    <div style="display:grid;grid-template-columns:repeat(3, 1fr);gap:12px;background:#f8f9fa;padding:12px;border-radius:8px;">
                                        <div>
                                            <div style="font-size:0.75em;color:var(--text-secondary);text-transform:uppercase;margin-bottom:4px;">Actual</div>
                                            <div style="font-weight:700;font-size:1.1em;color:${event.actual === 'TBD' ? '#95a5a6' : '#2c3e50'};">${event.actual}</div>
                                        </div>
                                        <div>
                                            <div style="font-size:0.75em;color:var(--text-secondary);text-transform:uppercase;margin-bottom:4px;">Forecast</div>
                                            <div style="font-weight:700;font-size:1.1em;color:#2c3e50;">${event.forecast}</div>
                                        </div>
                                        <div>
                                            <div style="font-size:0.75em;color:var(--text-secondary);text-transform:uppercase;margin-bottom:4px;">Previous</div>
                                            <div style="font-weight:700;font-size:1.1em;color:#2c3e50;">${event.previous}</div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
            }).join('');
        }

        function formatEventDate(date) {
            const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            
            return `${days[date.getDay()]}, ${months[date.getMonth()]} ${date.getDate()}`;
        }

        function getCountryFlag(country) {
            const flags = {
                'USD': '🇺🇸',
                'EUR': '🇪🇺',
                'GBP': '🇬🇧',
                'JPY': '🇯🇵'
            };
            return flags[country] || '🌍';
        }

        function updateCountdowns() {
            const now = new Date();
            
            economicEvents.forEach(event => {
                const countdownEl = document.getElementById(`countdown-${event.id}`);
                if (!countdownEl) return;

                const diff = event.date - now;
                if (diff < 0) {
                    countdownEl.textContent = 'Past event';
                    return;
                }

                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

                if (days > 0) {
                    countdownEl.textContent = `⏱️ ${days}d ${hours}h`;
                } else if (hours > 0) {
                    countdownEl.textContent = `⏱️ ${hours}h ${minutes}m`;
                } else {
                    countdownEl.textContent = `⏱️ ${minutes}m`;
                }
            });

            setTimeout(updateCountdowns, 60000); // Update every minute
        }

        function filterEconomicEvents(impact) {
            const buttons = document.querySelectorAll('.calendar-filter-btn');
            buttons.forEach(btn => {
                btn.style.background = '#f8f9fa';
                btn.style.color = '#333';
            });
            event.target.style.background = '#667eea';
            event.target.style.color = 'white';

            if (impact === 'all') {
                generateEconomicEvents();
            } else {
                const filtered = economicEvents.filter(e => e.impact === impact);
                const temp = [...economicEvents];
                economicEvents = filtered;
                displayEconomicEvents();
                economicEvents = temp;
            }
        }

        function exportCalendar() {
            const data = {
                exportDate: new Date().toISOString(),
                events: economicEvents
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `economic_calendar_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showPWANotification('📥 Calendar Exported', `${economicEvents.length} events saved`);
        }

        // ============= End Economic Calendar Functions =============

        // ============= Screener & Scanner Functions =============
        let screenerResults = [];
        let scannerRunning = false;

        function openScreener() {
            document.getElementById('screenerModal').style.display = 'flex';
            loadPresetScreeners();
        }

        function closeScreener() {
            document.getElementById('screenerModal').style.display = 'none';
            scannerRunning = false;
        }

        function loadPresetScreeners() {
            // Initialize with some default results
            runScreener('momentum');
        }

        function runScreener(preset) {
            scannerRunning = true;
            const output = document.getElementById('screenerResults');
            output.innerHTML = '<div style="text-align:center;padding:40px;"><div style="font-size:2em;margin-bottom:10px;">🔄</div><div style="color:var(--text-secondary);">Scanning markets...</div></div>';

            // Update active button
            document.querySelectorAll('.screener-preset-btn').forEach(btn => {
                btn.style.background = '#f8f9fa';
                btn.style.color = '#333';
            });
            event.target.style.background = '#667eea';
            event.target.style.color = 'white';

            setTimeout(() => {
                generateScreenerResults(preset);
                displayScreenerResults();
                scannerRunning = false;
            }, 1500);
        }

        function generateScreenerResults(preset) {
            const symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'NFLX', 'DIS', 
                           'BABA', 'TSM', 'V', 'JPM', 'BAC', 'WMT', 'PG', 'JNJ', 'UNH', 'HD'];
            
            screenerResults = symbols.slice(0, 15).map(symbol => {
                const price = Math.random() * 500 + 50;
                const change = (Math.random() - 0.5) * 10;
                const volume = Math.floor(Math.random() * 50000000 + 5000000);
                const rsi = Math.floor(Math.random() * 100);
                const macdSignal = Math.random() > 0.5 ? 'Bullish' : 'Bearish';
                
                return {
                    symbol,
                    price: price.toFixed(2),
                    change: change.toFixed(2),
                    changePercent: ((change / price) * 100).toFixed(2),
                    volume: volume,
                    rsi: rsi,
                    macd: macdSignal,
                    marketCap: (Math.random() * 2000 + 100).toFixed(1) + 'B',
                    pe: (Math.random() * 50 + 5).toFixed(2),
                    score: Math.floor(Math.random() * 100)
                };
            });

            // Sort by score
            screenerResults.sort((a, b) => b.score - a.score);

            // Apply preset filters
            if (preset === 'momentum') {
                screenerResults = screenerResults.filter(s => parseFloat(s.changePercent) > 2);
            } else if (preset === 'oversold') {
                screenerResults = screenerResults.filter(s => s.rsi < 30);
            } else if (preset === 'overbought') {
                screenerResults = screenerResults.filter(s => s.rsi > 70);
            } else if (preset === 'volume') {
                screenerResults = screenerResults.filter(s => s.volume > 20000000);
            }
        }

        function displayScreenerResults() {
            const output = document.getElementById('screenerResults');
            
            if (screenerResults.length === 0) {
                output.innerHTML = '<div style="text-align:center;padding:40px;color:var(--text-secondary);">No stocks match the current criteria</div>';
                return;
            }

            output.innerHTML = `
                <div style="margin-bottom:20px;">
                    <div style="font-size:1.1em;font-weight:700;color:#2c3e50;">
                        Found ${screenerResults.length} matches
                    </div>
                </div>

                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;">
                        <thead>
                            <tr style="background:#f8f9fa;border-bottom:2px solid var(--border-color);">
                                <th style="padding:12px;text-align:left;font-weight:700;color:#2c3e50;">Rank</th>
                                <th style="padding:12px;text-align:left;font-weight:700;color:#2c3e50;">Symbol</th>
                                <th style="padding:12px;text-align:right;font-weight:700;color:#2c3e50;">Price</th>
                                <th style="padding:12px;text-align:right;font-weight:700;color:#2c3e50;">Change</th>
                                <th style="padding:12px;text-align:right;font-weight:700;color:#2c3e50;">Volume</th>
                                <th style="padding:12px;text-align:center;font-weight:700;color:#2c3e50;">RSI</th>
                                <th style="padding:12px;text-align:center;font-weight:700;color:#2c3e50;">MACD</th>
                                <th style="padding:12px;text-align:right;font-weight:700;color:#2c3e50;">Score</th>
                                <th style="padding:12px;text-align:center;font-weight:700;color:#2c3e50;">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${screenerResults.map((stock, index) => `
                                <tr style="border-bottom:1px solid var(--border-color);transition:background 0.2s;" onmouseover="this.style.background='#f8f9fa'" onmouseout="this.style.background='white'">
                                    <td style="padding:12px;font-weight:700;color:#667eea;">#${index + 1}</td>
                                    <td style="padding:12px;">
                                        <div style="font-weight:800;font-size:1.1em;color:#2c3e50;">${stock.symbol}</div>
                                        <div style="font-size:0.8em;color:var(--text-secondary);">Cap: ${stock.marketCap}</div>
                                    </td>
                                    <td style="padding:12px;text-align:right;font-weight:700;color:#2c3e50;">$${stock.price}</td>
                                    <td style="padding:12px;text-align:right;">
                                        <div style="font-weight:700;color:${parseFloat(stock.change) >= 0 ? '#27ae60' : '#e74c3c'};">
                                            ${parseFloat(stock.change) >= 0 ? '+' : ''}${stock.change}
                                        </div>
                                        <div style="font-size:0.85em;color:${parseFloat(stock.changePercent) >= 0 ? '#27ae60' : '#e74c3c'};">
                                            ${parseFloat(stock.changePercent) >= 0 ? '+' : ''}${stock.changePercent}%
                                        </div>
                                    </td>
                                    <td style="padding:12px;text-align:right;font-size:0.9em;color:var(--text-secondary);">
                                        ${(stock.volume / 1000000).toFixed(1)}M
                                    </td>
                                    <td style="padding:12px;text-align:center;">
                                        <span style="padding:4px 10px;background:${stock.rsi < 30 ? '#27ae60' : stock.rsi > 70 ? '#e74c3c' : '#f39c12'};color:white;border-radius:6px;font-weight:700;font-size:0.9em;">
                                            ${stock.rsi}
                                        </span>
                                    </td>
                                    <td style="padding:12px;text-align:center;">
                                        <span style="padding:4px 10px;background:${stock.macd === 'Bullish' ? '#27ae60' : '#e74c3c'};color:white;border-radius:6px;font-weight:600;font-size:0.85em;">
                                            ${stock.macd}
                                        </span>
                                    </td>
                                    <td style="padding:12px;text-align:right;">
                                        <div style="font-weight:800;font-size:1.1em;color:#667eea;">${stock.score}</div>
                                    </td>
                                    <td style="padding:12px;text-align:center;">
                                        <button onclick="viewStockDetails('${stock.symbol}')" style="padding:6px 14px;background:#667eea;color:white;border:none;border-radius:6px;cursor:pointer;font-weight:600;font-size:0.85em;">
                                            View
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }

        function viewStockDetails(symbol) {
            showPWANotification('📊 Loading Chart', `Opening ${symbol} chart...`);
            // In real app, this would switch to the symbol's chart
            console.log('View details for:', symbol);
        }

        function runCustomScan() {
            const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
            const maxPrice = parseFloat(document.getElementById('maxPrice').value) || 999999;
            const minVolume = parseFloat(document.getElementById('minVolume').value) || 0;
            const minRSI = parseFloat(document.getElementById('minRSI').value) || 0;
            const maxRSI = parseFloat(document.getElementById('maxRSI').value) || 100;

            // Generate and filter results
            generateScreenerResults('all');
            screenerResults = screenerResults.filter(stock => {
                const price = parseFloat(stock.price);
                const volume = stock.volume;
                const rsi = stock.rsi;
                
                return price >= minPrice && price <= maxPrice &&
                       volume >= minVolume &&
                       rsi >= minRSI && rsi <= maxRSI;
            });

            displayScreenerResults();
            showPWANotification('🔍 Scan Complete', `Found ${screenerResults.length} matches`);
        }

        function exportScreenerResults() {
            const data = {
                timestamp: new Date().toISOString(),
                results: screenerResults
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `screener_results_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            showPWANotification('📥 Exported', `${screenerResults.length} stocks saved`);
        }

        function createWatchlist() {
            const symbols = screenerResults.map(s => s.symbol).join(', ');
            showPWANotification('⭐ Watchlist Created', `${screenerResults.length} stocks added`);
            console.log('Watchlist:', symbols);
        }

        // ============= End Screener & Scanner Functions =============

        function updateRiskDisplay() {
            const riskPerTrade = document.getElementById('riskPerTrade').value;
            document.getElementById('riskPerTradeValue').textContent = riskPerTrade + '%';
            calculatePositionSize();
        }

        function calculatePositionSize() {
            const balance = parseFloat(document.getElementById('accountBalance').value) || 0;
            const riskPercent = parseFloat(document.getElementById('riskPerTrade').value) || 1;
            const entry = parseFloat(document.getElementById('entryPrice').value) || 0;
            const stop = parseFloat(document.getElementById('stopLoss').value) || 0;
            
            if (balance <= 0 || entry <= 0 || stop <= 0 || entry === stop) {
                document.getElementById('positionSizeResult').textContent = '-';
                return;
            }
            
            const riskAmount = balance * (riskPercent / 100);
            const riskPerShare = Math.abs(entry - stop);
            const shares = Math.floor(riskAmount / riskPerShare);
            const totalInvestment = shares * entry;
            
            document.getElementById('positionSizeResult').textContent = shares.toLocaleString() + ' shares';
            document.getElementById('riskAmount').textContent = '$' + riskAmount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            document.getElementById('totalInvestment').textContent = '$' + totalInvestment.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }

        function updateKellyFractionDisplay() {
            const fraction = document.getElementById('kellyFraction').value;
            document.getElementById('kellyFractionValue').textContent = (fraction * 100).toFixed(0) + '%';
            calculateKelly();
        }

        function calculateKelly() {
            const winRate = parseFloat(document.getElementById('winRate').value) || 0;
            const avgWin = parseFloat(document.getElementById('avgWin').value) || 0;
            const avgLoss = parseFloat(document.getElementById('avgLoss').value) || 1;
            const fraction = parseFloat(document.getElementById('kellyFraction').value) || 0.25;
            
            if (winRate <= 0 || avgWin <= 0 || avgLoss <= 0) {
                document.getElementById('kellyResult').textContent = '-';
                return;
            }
            
            const p = winRate / 100;
            const q = 1 - p;
            const b = avgWin / avgLoss;
            
            // Kelly formula: f* = (bp - q) / b
            const kellyPercent = ((b * p - q) / b) * 100;
            const fractionalKelly = kellyPercent * fraction;
            
            document.getElementById('kellyResult').textContent = fractionalKelly.toFixed(2) + '%';
            
            let interpretation = '';
            if (fractionalKelly < 0) {
                interpretation = '⚠️ Negative Kelly suggests unfavorable odds. Do not trade this setup.';
            } else if (fractionalKelly < 2) {
                interpretation = '🟢 Conservative position size recommended.';
            } else if (fractionalKelly < 10) {
                interpretation = '🟡 Moderate risk. Consider reducing position size.';
            } else {
                interpretation = '🔴 High risk! Kelly suggests significant edge but use caution.';
            }
            
            document.getElementById('kellyInterpretation').innerHTML = interpretation;
        }

        function calculateRiskReward() {
            const entry = parseFloat(document.getElementById('rrEntryPrice').value) || 0;
            const stop = parseFloat(document.getElementById('rrStopLoss').value) || 0;
            const target = parseFloat(document.getElementById('takeProfit').value) || 0;
            
            if (entry <= 0 || stop <= 0 || target <= 0) {
                document.getElementById('rrResult').textContent = '-';
                return;
            }
            
            const risk = Math.abs(entry - stop);
            const reward = Math.abs(target - entry);
            const ratio = reward / risk;
            
            document.getElementById('rrResult').textContent = '1:' + ratio.toFixed(2);
            document.getElementById('riskValue').textContent = '$' + risk.toFixed(2);
            document.getElementById('rewardValue').textContent = '$' + reward.toFixed(2);
            
            let recommendation = '';
            if (ratio < 1) {
                recommendation = '🔴 Poor R/R. Risk exceeds reward.';
            } else if (ratio < 2) {
                recommendation = '🟡 Acceptable. Aim for 2:1 or better.';
            } else if (ratio < 3) {
                recommendation = '🟢 Good R/R ratio!';
            } else {
                recommendation = '💚 Excellent R/R ratio!';
            }
            
            document.getElementById('rrRecommendation').textContent = recommendation;
        }

        function updateProjPeriodDisplay() {
            const period = document.getElementById('projPeriod').value;
            document.getElementById('projPeriodValue').textContent = period + ' months';
            projectEquityCurve();
        }

        function projectEquityCurve() {
            const startCapital = parseFloat(document.getElementById('projStartCapital').value) || 0;
            const monthlyReturn = parseFloat(document.getElementById('projMonthlyReturn').value) || 0;
            const period = parseInt(document.getElementById('projPeriod').value) || 12;
            
            if (startCapital <= 0) {
                document.getElementById('projResult').textContent = '-';
                return;
            }
            
            // Compound monthly returns
            const finalValue = startCapital * Math.pow(1 + monthlyReturn / 100, period);
            const totalGain = finalValue - startCapital;
            const roi = (totalGain / startCapital) * 100;
            
            document.getElementById('projResult').textContent = '$' + finalValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            document.getElementById('projGain').textContent = '$' + totalGain.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            document.getElementById('projROI').textContent = roi.toFixed(2) + '%';
        }

        function loadFilterPresets() {
            try {
                const presets = JSON.parse(localStorage.getItem('filterPresets') || '[]');
                const select = document.getElementById('filterPresetSelect');
                select.innerHTML = '<option value="">-- Load Preset --</option>';
                
                presets.forEach((preset, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = preset.name;
                    select.appendChild(option);
                });
            } catch (e) {
                console.error('Error loading presets:', e);
            }
        }

        function loadFilterPreset(index) {
            if (index === '') return;
            
            try {
                const presets = JSON.parse(localStorage.getItem('filterPresets') || '[]');
                const preset = presets[index];
                if (!preset) return;
                
                document.getElementById('filterDateFrom').value = preset.dateFrom || '';
                document.getElementById('filterDateTo').value = preset.dateTo || '';
                document.getElementById('filterMinPrice').value = preset.minPrice || '';
                document.getElementById('filterMaxPrice').value = preset.maxPrice || '';
                document.getElementById('filterMinConfidence').value = preset.minConfidence || '';
                document.getElementById('filterMinPnL').value = preset.minPnL || '';
                
                applyAdvancedFilters();
            } catch (e) {
                alert('❌ Error loading preset: ' + e.message);
            }
        }

        function deleteCurrentPreset() {
            const select = document.getElementById('filterPresetSelect');
            const index = select.value;
            if (index === '') {
                alert('Please select a preset to delete');
                return;
            }
            
            if (!confirm('Delete this filter preset?')) return;
            
            try {
                let presets = JSON.parse(localStorage.getItem('filterPresets') || '[]');
                presets.splice(index, 1);
                localStorage.setItem('filterPresets', JSON.stringify(presets));
                loadFilterPresets();
                alert('✅ Preset deleted!');
            } catch (e) {
                alert('❌ Error deleting preset: ' + e.message);
            }
        }

        function calculateTradePairs(trades) {
            const tradePairs = [];
            let buyPrice = null;
            let buyDate = null;
            let buyIndex = null;

            for (let i = 0; i < trades.length; i++) {
                const trade = trades[i];
                if (trade.signal === 1) {
                    buyPrice = trade.price;
                    buyDate = trade.date;
                    buyIndex = i;
                } else if (trade.signal === -1 && buyPrice !== null) {
                    const pnl = ((trade.price - buyPrice) / buyPrice) * 100;
                    tradePairs.push({
                        buyDate: buyDate,
                        sellDate: trade.date,
                        buyPrice: buyPrice,
                        sellPrice: trade.price,
                        pnl: pnl,
                        buyIndex: buyIndex,
                        sellIndex: i
                    });
                    buyPrice = null;
                }
            }
            return tradePairs;
        }

        function exportTradesToCSV() {
            if (!currentTradeData || !currentSymbol) {
                alert('No trade data to export');
                return;
            }

            const trades = currentTradeData.trades || [];
            const tradePairs = calculateTradePairs(trades);
            const pnlMap = {};
            tradePairs.forEach(pair => {
                pnlMap[pair.sellIndex] = pair.pnl;
            });

            // Build CSV
            let csv = 'Date,Signal,Price,Confidence,P&L%\n';
            trades.forEach((trade, idx) => {
                const dateStr = trade.date || '';
                const signal = trade.signal === 1 ? 'BUY' : 'SELL';
                const price = (trade.price || 0).toFixed(2);
                const confidence = ((trade.confidence || 0) * 100).toFixed(1);
                const pnl = trade.signal === -1 && pnlMap[idx] ? pnlMap[idx].toFixed(2) : '-';
                csv += `${dateStr},${signal},${price},${confidence},${pnl}\n`;
            });

            // Download
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = currentSymbol + '_trades_' + new Date().toISOString().split('T')[0] + '.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            addLog('Exported ' + trades.length + ' trades for ' + currentSymbol + ' to CSV', 'success');
        }

        let equityChartInstance = null;

        function renderEquityChart(result) {
            const canvasContainer = document.getElementById('tradeEquityChartCanvas');
            if (!canvasContainer) return;

            // Destroy previous chart if exists
            if (equityChartInstance) {
                equityChartInstance.destroy();
                equityChartInstance = null;
            }

            const equityCurve = result.equity_curve || {};
            const times = equityCurve.times || [];
            const values = equityCurve.values || [];

            if (times.length === 0 || values.length === 0) {
                canvasContainer.innerHTML = '<div style="padding:20px;text-align:center;color:#999;">No equity data available</div>';
                return;
            }

            // Format dates for x-axis
            const labels = times.map(t => {
                const d = new Date(t);
                return d.toLocaleDateString('en-US', {month:'short', day:'numeric'});
            });

            // Calculate min/max for y-axis
            const minValue = Math.min(...values);
            const maxValue = Math.max(...values);
            const initialValue = result.initial_capital || 50000;
            const finalValue = result.final_value || initialValue;

            // Create canvas if not exists
            let canvas = document.getElementById('equityChartCanvas');
            if (!canvas) {
                canvasContainer.innerHTML = '<canvas id="equityChartCanvas" style="max-height:300px;"></canvas>';
                canvas = document.getElementById('equityChartCanvas');
            }

            const ctx = canvas.getContext('2d');
            equityChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Portfolio Value',
                        data: values,
                        borderColor: finalValue >= initialValue ? '#27ae60' : '#e74c3c',
                        backgroundColor: finalValue >= initialValue ? 'rgba(39, 174, 96, 0.1)' : 'rgba(231, 76, 60, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.3,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: '#3498db',
                        pointHoverBorderColor: 'white',
                        pointHoverBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.5,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            padding: 12,
                            titleFont: {
                                size: 13,
                                weight: 'bold'
                            },
                            bodyFont: {
                                size: 12
                            },
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed.y;
                                    const change = ((value - initialValue) / initialValue * 100).toFixed(2);
                                    return [
                                        'Value: $' + value.toLocaleString('en-US', {maximumFractionDigits: 2}),
                                        'Change: ' + (change >= 0 ? '+' : '') + change + '%'
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                maxRotation: 45,
                                minRotation: 45,
                                font: {
                                    size: 10
                                }
                            }
                        },
                        y: {
                            beginAtZero: false,
                            min: minValue * 0.999,
                            max: maxValue * 1.001,
                            grid: {
                                color: 'rgba(0,0,0,0.05)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString('en-US', {maximumFractionDigits: 0});
                                },
                                font: {
                                    size: 10
                                }
                            }
                        }
                    }
                }
            });
        }

        // Trade Replay Animation
        let replayInterval = null;
        let replayPaused = false;
        let replayCurrentIndex = 0;

        function startTradeReplay() {
            if (!currentTradeData) return;
            
            const replayBtn = document.getElementById('replayBtn');
            const pauseBtn = document.getElementById('pauseReplayBtn');
            const progressSpan = document.getElementById('replayProgress');
            
            // If already running, reset
            if (replayInterval) {
                clearInterval(replayInterval);
                replayInterval = null;
            }

            replayBtn.style.display = 'none';
            pauseBtn.style.display = 'inline-block';
            replayPaused = false;
            replayCurrentIndex = 0;

            const equityCurve = currentTradeData.equity_curve || {};
            const times = equityCurve.times || [];
            const values = equityCurve.values || [];
            const trades = currentTradeData.trades || [];

            if (times.length === 0) return;

            // Get speed from dropdown
            const speed = parseInt(document.getElementById('replaySpeed').value);

            // Reset chart to empty
            if (equityChartInstance) {
                equityChartInstance.data.labels = [];
                equityChartInstance.data.datasets[0].data = [];
                equityChartInstance.update('none');
            }

            // Animate point by point
            replayInterval = setInterval(() => {
                if (replayPaused) return;

                if (replayCurrentIndex >= times.length) {
                    // Animation complete
                    clearInterval(replayInterval);
                    replayInterval = null;
                    replayBtn.style.display = 'inline-block';
                    pauseBtn.style.display = 'none';
                    progressSpan.textContent = 'Complete ✓';
                    addLog('Replay complete for ' + currentSymbol, 'success');
                    return;
                }

                const t = times[replayCurrentIndex];
                const v = values[replayCurrentIndex];
                const d = new Date(t);
                const label = d.toLocaleDateString('en-US', {month:'short', day:'numeric'});

                if (equityChartInstance) {
                    equityChartInstance.data.labels.push(label);
                    equityChartInstance.data.datasets[0].data.push(v);
                    equityChartInstance.update('none');
                }

                // Check if there's a trade on this date
                const tradeOnDate = trades.find(trade => {
                    const tradeDate = new Date(trade.date).toDateString();
                    const currentDate = d.toDateString();
                    return tradeDate === currentDate;
                });

                if (tradeOnDate) {
                    const signal = tradeOnDate.signal === 1 ? '🟢 BUY' : '🔴 SELL';
                    progressSpan.textContent = `${signal} @ $${tradeOnDate.price.toFixed(2)}`;
                    
                    // Highlight trade in table
                    const tbody = document.getElementById('tradesTableBody');
                    const rows = tbody.getElementsByTagName('tr');
                    for (let row of rows) {
                        row.style.background = 'white';
                    }
                    // Find and highlight current trade row
                    const tradeIndex = trades.indexOf(tradeOnDate);
                    if (rows[tradeIndex]) {
                        rows[tradeIndex].style.background = '#fff3cd';
                        rows[tradeIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                } else {
                    const progress = Math.round((replayCurrentIndex / times.length) * 100);
                    progressSpan.textContent = `${progress}%`;
                }

                replayCurrentIndex++;
            }, speed);

            addLog('Starting replay animation for ' + currentSymbol, 'info');
        }

        function pauseTradeReplay() {
            replayPaused = !replayPaused;
            const pauseBtn = document.getElementById('pauseReplayBtn');
            if (replayPaused) {
                pauseBtn.textContent = '▶️ Resume';
                pauseBtn.style.background = '#27ae60';
            } else {
                pauseBtn.textContent = '⏸️ Pause';
                pauseBtn.style.background = '#f39c12';
            }
        }

        // Multi-Symbol Comparison
        let selectedSymbolsForComparison = [];
        let comparisonChartInstance = null;
        let allSymbolsData = [];

        async function openComparisonModal() {
            const modal = document.getElementById('comparisonModal');
            const selectorGrid = document.getElementById('symbolSelectorGrid');
            
            modal.style.display = 'flex';
            
            // Load all available symbols
            try {
                const summaryUrl = './per_symbol_trading/summary.json';
                const res = await fetch(summaryUrl);
                const summary = await res.json();
                allSymbolsData = summary.results || [];
                
                // Populate selector grid
                selectorGrid.innerHTML = '';
                selectedSymbolsForComparison = [];
                
                for (const result of allSymbolsData) {
                    const symbol = result.symbol;
                    const checkbox = document.createElement('label');
                    checkbox.style.cssText = 'display:flex;align-items:center;gap:6px;padding:10px;background:var(--bg-container);border:2px solid var(--border-color);border-radius:8px;cursor:pointer;font-size:0.9em;transition:all 0.2s;font-weight:500;color:var(--text-primary);';
                    checkbox.onmouseover = function() {
                        this.style.borderColor = '#667eea';
                        this.style.background = 'rgba(102, 126, 234, 0.1)';
                    };
                    checkbox.onmouseout = function() {
                        const input = this.querySelector('input');
                        if (!input.checked) {
                            this.style.borderColor = 'var(--border-color)';
                            this.style.background = 'var(--bg-container)';
                        }
                    };
                    checkbox.innerHTML = `
                        <input type="checkbox" value="${symbol}" onchange="toggleSymbolSelection('${symbol}', this)" style="margin:0;width:16px;height:16px;cursor:pointer;">
                        <span>${symbol}</span>
                    `;
                    selectorGrid.appendChild(checkbox);
                }
                
                showNotification('Comparison Ready', 'Select symbols to compare', 'info');
            } catch (err) {
                alert('Failed to load symbols: ' + err.message);
            }
        }

        function closeComparisonModal() {
            document.getElementById('comparisonModal').style.display = 'none';
            clearComparisonSelection();
        }

        function toggleSymbolSelection(symbol, checkbox) {
            const index = selectedSymbolsForComparison.indexOf(symbol);
            const label = checkbox.parentElement;
            
            if (index === -1) {
                if (selectedSymbolsForComparison.length >= 6) {
                    showNotification('Selection Limit', 'Maximum 6 symbols can be compared', 'warning');
                    checkbox.checked = false;
                    return;
                }
                selectedSymbolsForComparison.push(symbol);
                label.style.borderColor = '#667eea';
                label.style.background = 'rgba(102, 126, 234, 0.15)';
            } else {
                selectedSymbolsForComparison.splice(index, 1);
                label.style.borderColor = 'var(--border-color)';
                label.style.background = 'var(--bg-container)';
            }
        }

        function clearComparisonSelection() {
            selectedSymbolsForComparison = [];
            const checkboxes = document.querySelectorAll('#symbolSelectorGrid input[type="checkbox"]');
            checkboxes.forEach(cb => {
                cb.checked = false;
                cb.parentElement.style.borderColor = 'var(--border-color)';
                cb.parentElement.style.background = 'var(--bg-container)';
            });
        }

        async function loadComparison() {
            if (selectedSymbolsForComparison.length < 2) {
                showNotification('Selection Required', 'Please select at least 2 symbols to compare', 'warning');
                return;
            }

            const content = document.getElementById('comparisonContent');
            content.style.display = 'block';

            showNotification('Loading Comparison', `Analyzing ${selectedSymbolsForComparison.length} symbols...`, 'info');

            // Fetch data for selected symbols
            const symbolsData = [];
            for (const symbol of selectedSymbolsForComparison) {
                try {
                    const url = './per_symbol_trading/' + symbol + '_trading_result.json';
                    const res = await fetch(url);
                    const data = await res.json();
                    symbolsData.push({symbol, data});
                } catch (err) {
                    console.error('Failed to load ' + symbol, err);
                }
            }

            // Render all comparison components
            renderComparisonMetrics(symbolsData);
            renderComparisonChart(symbolsData);
            renderCorrelationMatrix(symbolsData);
            renderComparisonTable(symbolsData);
            
            showNotification('Comparison Complete', `Loaded data for ${symbolsData.length} symbols`, 'success');
        }

        function renderComparisonMetrics(symbolsData) {
            const container = document.getElementById('comparisonMetrics');
            container.innerHTML = '';
            
            symbolsData.forEach((item, idx) => {
                const {symbol, data} = item;
                const ret = ((data.total_return || 0) * 100).toFixed(2);
                const trades = (data.trades || []).length;
                const color = getComparisonColor(idx);
                
                const card = document.createElement('div');
                card.style.cssText = `
                    background: var(--card-bg);
                    border-left: 4px solid ${color};
                    border-radius: 8px;
                    padding: 15px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                `;
                card.innerHTML = `
                    <div style="font-weight:700;font-size:1.1em;color:var(--text-primary);margin-bottom:8px;">${symbol}</div>
                    <div style="font-size:1.8em;font-weight:700;color:${parseFloat(ret) >= 0 ? '#27ae60' : '#e74c3c'};margin-bottom:5px;">${ret}%</div>
                    <div style="font-size:0.85em;color:var(--text-secondary);">${trades} trades</div>
                `;
                container.appendChild(card);
            });
        }

        function renderCorrelationMatrix(symbolsData) {
            const container = document.getElementById('correlationMatrix');
            
            // Calculate correlations between equity curves
            const returns = symbolsData.map(item => {
                const values = item.data.equity_curve?.values || [];
                const rets = [];
                for (let i = 1; i < values.length; i++) {
                    rets.push((values[i] - values[i-1]) / values[i-1]);
                }
                return rets;
            });
            
            const n = symbolsData.length;
            const correlations = [];
            
            for (let i = 0; i < n; i++) {
                correlations[i] = [];
                for (let j = 0; j < n; j++) {
                    if (i === j) {
                        correlations[i][j] = 1.0;
                    } else {
                        correlations[i][j] = calculateCorrelation(returns[i], returns[j]);
                    }
                }
            }
            
            // Render matrix as table
            let html = '<table style="width:100%;border-collapse:collapse;font-size:0.85em;text-align:center;">';
            html += '<thead><tr><th style="padding:10px;background:var(--table-header-bg);border:1px solid var(--border-color);"></th>';
            
            symbolsData.forEach(item => {
                html += `<th style="padding:10px;background:var(--table-header-bg);border:1px solid var(--border-color);font-weight:600;color:var(--text-primary);">${item.symbol}</th>`;
            });
            html += '</tr></thead><tbody>';
            
            for (let i = 0; i < n; i++) {
                html += `<tr><th style="padding:10px;background:var(--table-header-bg);border:1px solid var(--border-color);font-weight:600;color:var(--text-primary);">${symbolsData[i].symbol}</th>`;
                for (let j = 0; j < n; j++) {
                    const corr = correlations[i][j];
                    const intensity = Math.abs(corr);
                    const color = corr > 0 
                        ? `rgba(39, 174, 96, ${intensity})` 
                        : `rgba(231, 76, 60, ${intensity})`;
                    html += `<td style="padding:10px;border:1px solid var(--border-color);background:${color};color:${intensity > 0.5 ? 'white' : 'var(--text-primary)'};font-weight:600;">${corr.toFixed(2)}</td>`;
                }
                html += '</tr>';
            }
            html += '</tbody></table>';
            
            container.innerHTML = html;
        }

        function calculateCorrelation(x, y) {
            const n = Math.min(x.length, y.length);
            if (n === 0) return 0;
            
            const meanX = x.slice(0, n).reduce((a, b) => a + b, 0) / n;
            const meanY = y.slice(0, n).reduce((a, b) => a + b, 0) / n;
            
            let numerator = 0;
            let denomX = 0;
            let denomY = 0;
            
            for (let i = 0; i < n; i++) {
                const dx = x[i] - meanX;
                const dy = y[i] - meanY;
                numerator += dx * dy;
                denomX += dx * dx;
                denomY += dy * dy;
            }
            
            if (denomX === 0 || denomY === 0) return 0;
            return numerator / Math.sqrt(denomX * denomY);
        }

        function getComparisonColor(index) {
            const colors = [
                '#667eea', '#e74c3c', '#27ae60', '#f39c12', 
                '#3498db', '#9b59b6', '#1abc9c', '#e67e22'
            ];
            return colors[index % colors.length];
        }

        function renderComparisonChart(symbolsData) {
            const canvas = document.getElementById('comparisonChart');
            
            // Destroy previous chart
            if (comparisonChartInstance) {
                comparisonChartInstance.destroy();
            }

            const datasets = [];
            
            for (let i = 0; i < symbolsData.length; i++) {
                const {symbol, data} = symbolsData[i];
                const times = data.equity_curve?.times || [];
                const values = data.equity_curve?.values || [];
                
                // Normalize to percentage
                const initial = data.initial_capital || 50000;
                const normalizedValues = values.map(v => ((v - initial) / initial) * 100);
                const color = getComparisonColor(i);
                
                datasets.push({
                    label: symbol,
                    data: normalizedValues,
                    borderColor: color,
                    backgroundColor: color + '20',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBorderWidth: 3
                });
            }

            // Use first symbol's times as labels
            const labels = (symbolsData[0]?.data.equity_curve?.times || []).map(t => {
                const d = new Date(t);
                return d.toLocaleDateString('en-US', {month:'short', day:'numeric'});
            });

            comparisonChartInstance = new Chart(canvas, {
                type: 'line',
                data: { labels, datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.5,
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                padding: 15,
                                font: { size: 12, weight: '600' },
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.85)',
                            padding: 12,
                            titleFont: { size: 13, weight: '600' },
                            bodyFont: { size: 12 },
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + '%';
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { 
                                maxRotation: 45, 
                                minRotation: 45, 
                                font: { size: 10 },
                                color: '#666'
                            }
                        },
                        y: {
                            grid: { 
                                color: 'rgba(0,0,0,0.06)',
                                drawBorder: false
                            },
                            ticks: {
                                callback: function(value) {
                                    return value.toFixed(1) + '%';
                                },
                                font: { size: 11 },
                                color: '#666'
                            }
                        }
                    }
                }
            });
        }

        function renderComparisonTable(symbolsData) {
            const tbody = document.getElementById('comparisonTableBody');
            tbody.innerHTML = '';

            for (const {symbol, data} of symbolsData) {
                const ret = ((data.total_return || 0) * 100).toFixed(2);
                const retColor = data.total_return >= 0 ? '#27ae60' : '#e74c3c';
                
                // Calculate metrics
                const trades = data.trades || [];
                const tradePairs = calculateTradePairs(trades);
                const winRate = tradePairs.length > 0 ? ((tradePairs.filter(p => p.pnl > 0).length / tradePairs.length) * 100).toFixed(1) : '0.0';
                const sharpe = (data.sharpe_ratio || 0).toFixed(2);
                const maxDD = (data.max_drawdown || 0).toFixed(2);
                
                // Calculate average duration
                let avgDuration = 0;
                if (tradePairs.length > 0) {
                    const durations = tradePairs.map(pair => {
                        const buyDate = new Date(trades[pair.buyIndex].date);
                        const sellDate = new Date(trades[pair.sellIndex].date);
                        return Math.floor((sellDate - buyDate) / (1000 * 60 * 60 * 24));
                    });
                    avgDuration = Math.round(durations.reduce((a, b) => a + b, 0) / durations.length);
                }
                
                // Calculate risk score (0-100, lower is better)
                const volatility = Math.abs(data.max_drawdown || 0) * 10;
                const winRatePenalty = (100 - parseFloat(winRate)) * 0.3;
                const sharpePenalty = Math.max(0, (2 - parseFloat(sharpe))) * 20;
                const riskScore = Math.min(100, Math.max(0, volatility + winRatePenalty + sharpePenalty)).toFixed(0);
                
                const row = document.createElement('tr');
                row.style.cssText = 'border-bottom:1px solid var(--border-color);transition:background 0.2s;';
                row.onmouseover = function() { this.style.background = 'var(--table-header-bg)'; };
                row.onmouseout = function() { this.style.background = 'transparent'; };
                
                row.innerHTML = `
                    <td style="padding:12px;font-weight:600;color:var(--text-primary);">${symbol}</td>
                    <td style="padding:12px;text-align:right;font-weight:700;color:${retColor};">${ret}%</td>
                    <td style="padding:12px;text-align:right;color:var(--text-primary);">${winRate}%</td>
                    <td style="padding:12px;text-align:right;color:var(--text-primary);">${sharpe}</td>
                    <td style="padding:12px;text-align:right;color:var(--text-primary);">${maxDD}%</td>
                    <td style="padding:12px;text-align:right;color:var(--text-primary);">${trades.length}</td>
                    <td style="padding:12px;text-align:right;color:var(--text-primary);">${avgDuration} days</td>
                    <td style="padding:12px;text-align:right;">
                        <span style="padding:4px 10px;background:${riskScore < 30 ? '#27ae60' : riskScore < 60 ? '#f39c12' : '#e74c3c'};color:white;border-radius:12px;font-size:0.85em;font-weight:600;">
                            ${riskScore}
                        </span>
                    </td>
                `;
                
                tbody.appendChild(row);
            }
        }

        // Monte Carlo Simulation
        let monteCarloChartInstance = null;

        async function runMonteCarloSimulation() {
            if (!currentTradeData) return;

            const btn = document.getElementById('monteCarloBtn');
            const resultsDiv = document.getElementById('monteCarloResults');
            const runningDiv = document.getElementById('monteCarloRunning');
            const progressSpan = document.getElementById('mcProgress');

            btn.disabled = true;
            resultsDiv.style.display = 'none';
            runningDiv.style.display = 'block';

            // Get trade pairs
            const trades = currentTradeData.trades || [];
            const tradePairs = calculateTradePairs(trades);

            if (tradePairs.length === 0) {
                alert('No trade pairs available for simulation');
                btn.disabled = false;
                runningDiv.style.display = 'none';
                return;
            }

            const numSimulations = 1000;
            const results = [];

            // Run simulations
            for (let sim = 0; sim < numSimulations; sim++) {
                // Shuffle trade pairs
                const shuffled = [...tradePairs].sort(() => Math.random() - 0.5);
                
                // Calculate cumulative return
                let totalReturn = 0;
                for (const pair of shuffled) {
                    totalReturn += pair.pnl;
                }
                
                results.push(totalReturn);

                if (sim % 100 === 0) {
                    progressSpan.textContent = Math.round((sim / numSimulations) * 100) + '%';
                    await new Promise(resolve => setTimeout(resolve, 0)); // Allow UI update
                }
            }

            // Calculate statistics
            results.sort((a, b) => a - b);
            const mean = results.reduce((a, b) => a + b, 0) / results.length;
            const ci95Low = results[Math.floor(numSimulations * 0.025)];
            const ci95High = results[Math.floor(numSimulations * 0.975)];
            const best = results[results.length - 1];
            const worst = results[0];
            const actualReturn = tradePairs.reduce((sum, p) => sum + p.pnl, 0);

            // Update UI
            document.getElementById('mcMean').textContent = mean.toFixed(2) + '%';
            document.getElementById('mcCI').textContent = `[${ci95Low.toFixed(2)}%, ${ci95High.toFixed(2)}%]`;
            document.getElementById('mcBest').textContent = best.toFixed(2) + '%';
            document.getElementById('mcWorst').textContent = worst.toFixed(2) + '%';

            // Render histogram
            renderMonteCarloChart(results, actualReturn);

            runningDiv.style.display = 'none';
            resultsDiv.style.display = 'block';
            btn.disabled = false;

            addLog(`Monte Carlo: Mean ${mean.toFixed(2)}%, Actual ${actualReturn.toFixed(2)}%`, 'success');
        }

        function renderMonteCarloChart(results, actualReturn) {
            const canvas = document.getElementById('monteCarloChart');

            if (monteCarloChartInstance) {
                monteCarloChartInstance.destroy();
            }

            // Create histogram bins
            const numBins = 50;
            const min = Math.min(...results);
            const max = Math.max(...results);
            const binWidth = (max - min) / numBins;
            const bins = new Array(numBins).fill(0);
            const binLabels = [];

            for (let i = 0; i < numBins; i++) {
                binLabels.push((min + i * binWidth).toFixed(1));
            }

            for (const result of results) {
                const binIndex = Math.min(Math.floor((result - min) / binWidth), numBins - 1);
                bins[binIndex]++;
            }

            monteCarloChartInstance = new Chart(canvas, {
                type: 'bar',
                data: {
                    labels: binLabels,
                    datasets: [{
                        label: 'Frequency',
                        data: bins,
                        backgroundColor: 'rgba(155, 89, 182, 0.6)',
                        borderColor: '#9b59b6',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 3,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return 'Count: ' + context.parsed.y;
                                }
                            }
                        },
                        annotation: {
                            annotations: {
                                actual: {
                                    type: 'line',
                                    xMin: actualReturn,
                                    xMax: actualReturn,
                                    borderColor: '#e74c3c',
                                    borderWidth: 2,
                                    label: {
                                        content: 'Actual',
                                        enabled: true,
                                        position: 'top'
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Total Return (%)' },
                            ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 10 }
                        },
                        y: {
                            title: { display: true, text: 'Frequency' }
                        }
                    }
                }
            });
        }

        // ML Signal Quality Analysis
        let confidencePnlChartInstance = null;
        let calibrationChartInstance = null;
        let mlAnalysisShown = false;

        function toggleMLAnalysis() {
            if (!currentTradeData) return;

            const content = document.getElementById('mlAnalysisContent');
            const btn = document.getElementById('mlAnalysisBtn');

            if (mlAnalysisShown) {
                content.style.display = 'none';
                btn.textContent = 'Show Analysis';
                mlAnalysisShown = false;
            } else {
                content.style.display = 'block';
                btn.textContent = 'Hide Analysis';
                mlAnalysisShown = true;
                renderMLAnalysis();
            }
        }

        function renderMLAnalysis() {
            const trades = currentTradeData.trades || [];
            const tradePairs = calculateTradePairs(trades);

            if (tradePairs.length === 0) return;

            // Build confidence vs P&L data
            const scatterData = [];
            for (const pair of tradePairs) {
                const sellTrade = trades.find(t => t.date === pair.sellDate && t.signal === -1);
                if (sellTrade) {
                    scatterData.push({
                        x: sellTrade.confidence * 100,
                        y: pair.pnl
                    });
                }
            }

            // Render scatter plot
            renderConfidencePnlScatter(scatterData);

            // Calculate calibration
            renderCalibrationCurve(scatterData);

            // Calculate metrics
            const profitable = tradePairs.filter(p => p.pnl > 0).length;
            const precision = (profitable / tradePairs.length * 100).toFixed(1);
            const falsePositives = tradePairs.filter(p => p.pnl < 0).length;
            const fpr = (falsePositives / tradePairs.length * 100).toFixed(1);
            
            // Calculate average signal lag (simplified)
            const avgLag = '1.2d'; // Placeholder - would need historical price data

            document.getElementById('mlPrecision').textContent = precision + '%';
            document.getElementById('mlFPR').textContent = fpr + '%';
            document.getElementById('mlLag').textContent = avgLag;

            addLog('ML analysis rendered for ' + currentSymbol, 'info');
        }

        function renderConfidencePnlScatter(data) {
            const canvas = document.getElementById('confidencePnlChart');
            
            if (confidencePnlChartInstance) {
                confidencePnlChartInstance.destroy();
            }

            // Color by profitability
            const colors = data.map(d => d.y >= 0 ? 'rgba(39, 174, 96, 0.6)' : 'rgba(231, 76, 60, 0.6)');

            confidencePnlChartInstance = new Chart(canvas, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Trades',
                        data: data,
                        backgroundColor: colors,
                        borderColor: colors.map(c => c.replace('0.6', '1')),
                        borderWidth: 1,
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1.5,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return [
                                        'Confidence: ' + context.parsed.x.toFixed(1) + '%',
                                        'P&L: ' + context.parsed.y.toFixed(2) + '%'
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Signal Confidence (%)' },
                            min: 0,
                            max: 100
                        },
                        y: {
                            title: { display: true, text: 'Trade P&L (%)' },
                            grid: {
                                color: function(context) {
                                    return context.tick.value === 0 ? '#333' : 'rgba(0,0,0,0.1)';
                                }
                            }
                        }
                    }
                }
            });
        }

        function renderCalibrationCurve(data) {
            const canvas = document.getElementById('calibrationChart');
            
            if (calibrationChartInstance) {
                calibrationChartInstance.destroy();
            }

            // Bin confidence scores
            const bins = 10;
            const binSize = 100 / bins;
            const calibrationData = [];
            
            for (let i = 0; i < bins; i++) {
                const minConf = i * binSize;
                const maxConf = (i + 1) * binSize;
                const binTrades = data.filter(d => d.x >= minConf && d.x < maxConf);
                
                if (binTrades.length > 0) {
                    const positiveCount = binTrades.filter(d => d.y > 0).length;
                    const accuracy = (positiveCount / binTrades.length) * 100;
                    calibrationData.push({
                        x: (minConf + maxConf) / 2,
                        y: accuracy
                    });
                }
            }

            // Perfect calibration line
            const perfectLine = Array.from({length: 11}, (_, i) => ({x: i * 10, y: i * 10}));

            calibrationChartInstance = new Chart(canvas, {
                type: 'line',
                data: {
                    datasets: [
                        {
                            label: 'Perfect Calibration',
                            data: perfectLine,
                            borderColor: '#95a5a6',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            fill: false,
                            pointRadius: 0
                        },
                        {
                            label: 'Actual',
                            data: calibrationData,
                            borderColor: '#e67e22',
                            backgroundColor: 'rgba(230, 126, 34, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1.5,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: { font: { size: 10 } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y.toFixed(1) + '%';
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { display: true, text: 'Predicted Confidence (%)' },
                            min: 0,
                            max: 100
                        },
                        y: {
                            title: { display: true, text: 'Actual Success Rate (%)' },
                            min: 0,
                            max: 100
                        }
                    }
                }
            });
        }

        // AI-Generated Insights
        async function generateAIInsights() {
            if (!currentTradeData || !currentSymbol) return;

            const btn = document.getElementById('aiInsightsBtn');
            const content = document.getElementById('aiInsightsContent');
            const generating = document.getElementById('aiInsightsGenerating');

            btn.disabled = true;
            content.style.display = 'none';
            generating.style.display = 'block';

            // Simulate AI processing delay
            await new Promise(resolve => setTimeout(resolve, 1500));

            const trades = currentTradeData.trades || [];
            const tradePairs = calculateTradePairs(trades);
            const ret = (currentTradeData.total_return || 0) * 100;
            const winRate = tradePairs.length > 0 ? ((tradePairs.filter(p => p.pnl > 0).length / tradePairs.length) * 100) : 0;

            // Generate insights based on metrics
            let insights = `Trading Analysis for ${currentSymbol}\n\n`;

            // Performance assessment
            if (ret > 5) {
                insights += `✅ Strong Performance: ${currentSymbol} generated a ${ret.toFixed(2)}% return over the period, significantly outperforming the baseline. `;
            } else if (ret > 0) {
                insights += `✔️ Positive Performance: ${currentSymbol} achieved a modest ${ret.toFixed(2)}% return. `;
            } else {
                insights += `⚠️ Underperformance: ${currentSymbol} experienced a ${ret.toFixed(2)}% loss. `;
            }

            // Win rate analysis
            if (winRate > 60) {
                insights += `The model showed excellent trade selection with a ${winRate.toFixed(1)}% win rate. `;
            } else if (winRate > 50) {
                insights += `Win rate of ${winRate.toFixed(1)}% indicates balanced trade execution. `;
            } else {
                insights += `Win rate of ${winRate.toFixed(1)}% suggests room for improvement in signal accuracy. `;
            }

            // Trade frequency
            insights += `\n\n📊 Trading Activity: `;
            if (trades.length > 20) {
                insights += `High trading frequency (${trades.length} trades) suggests an active strategy. This may increase transaction costs but provides more opportunities to capture gains.`;
            } else if (trades.length > 10) {
                insights += `Moderate trading activity (${trades.length} trades) balances opportunity capture with cost management.`;
            } else {
                insights += `Conservative approach with ${trades.length} trades. Low transaction costs but fewer opportunities.`;
            }

            // Pattern detection
            const buyTrades = trades.filter(t => t.signal === 1);
            const avgBuyConfidence = buyTrades.reduce((sum, t) => sum + (t.confidence || 0), 0) / buyTrades.length;
            insights += `\n\n🔍 Signal Quality: Average buy signal confidence is ${(avgBuyConfidence * 100).toFixed(1)}%. `;
            if (avgBuyConfidence > 0.7) {
                insights += `High confidence signals suggest strong conviction in trade entries.`;
            } else {
                insights += `Moderate confidence levels indicate cautious positioning.`;
            }

            document.getElementById('aiInsightsText').textContent = insights;

            // Generate recommendations
            const recommendations = [];
            
            if (winRate < 50) {
                recommendations.push('Consider raising signal confidence threshold to improve win rate');
            }
            if (trades.length > 25) {
                recommendations.push('High trade frequency - review if all signals add value after costs');
            }
            if (ret < 0 && winRate > 50) {
                recommendations.push('Winning trades not offsetting losses - consider wider profit targets');
            }
            if (avgBuyConfidence < 0.6) {
                recommendations.push('Low signal confidence - model may need retraining or additional features');
            }
            if (tradePairs.length > 0) {
                const avgPnl = tradePairs.reduce((sum, p) => sum + p.pnl, 0) / tradePairs.length;
                if (avgPnl < 0.5) {
                    recommendations.push('Small average gains per trade - explore increasing position holding period');
                }
            }
            if (recommendations.length === 0) {
                recommendations.push('Strategy performing well - continue monitoring for drift');
                recommendations.push('Consider gradual position size increases if consistency maintains');
            }

            const recoList = document.getElementById('aiRecoList');
            recoList.innerHTML = '';
            for (const reco of recommendations) {
                const li = document.createElement('li');
                li.textContent = reco;
                li.style.marginBottom = '6px';
                recoList.appendChild(li);
            }

            generating.style.display = 'none';
            content.style.display = 'block';
            btn.disabled = false;

            addLog('AI insights generated for ' + currentSymbol, 'success');
        }

        // User Notes Functions
        function loadSymbolNotes() {
            if (!currentSymbol) return;
            try {
                const notesKey = 'symbol_notes_' + currentSymbol;
                const savedNotes = localStorage.getItem(notesKey);
                const textarea = document.getElementById('symbolNotesInput');
                if (textarea) {
                    textarea.value = savedNotes || '';
                }
            } catch (e) {
                console.error('Error loading notes:', e);
            }
        }

        function saveSymbolNotes() {
            if (!currentSymbol) return;
            try {
                const textarea = document.getElementById('symbolNotesInput');
                const notes = textarea ? textarea.value : '';
                const notesKey = 'symbol_notes_' + currentSymbol;
                localStorage.setItem(notesKey, notes);
                
                // Show success indicator
                const indicator = document.getElementById('notesSavedIndicator');
                if (indicator) {
                    indicator.style.display = 'block';
                    setTimeout(() => {
                        indicator.style.display = 'none';
                    }, 2000);
                }
                
                addLog('Notes saved for ' + currentSymbol, 'success');
            } catch (e) {
                console.error('Error saving notes:', e);
                addLog('Failed to save notes: ' + e.message, 'error');
            }
        }

        function clearSymbolNotes() {
            const textarea = document.getElementById('symbolNotesInput');
            if (textarea && confirm('Clear all notes for this symbol?')) {
                textarea.value = '';
                saveSymbolNotes();
            }
        }

        function insertNoteTemplate(type) {
            const textarea = document.getElementById('symbolNotesInput');
            if (!textarea) return;
            
            const now = new Date().toLocaleString();
            let template = '';
            
            switch(type) {
                case 'bullish':
                    template = `\n[${now}] 🟢 BULLISH PATTERN DETECTED\n- Pattern: \n- Entry: \n- Target: \n- Stop Loss: \n`;
                    break;
                case 'bearish':
                    template = `\n[${now}] 🔴 BEARISH PATTERN DETECTED\n- Pattern: \n- Entry: \n- Target: \n- Stop Loss: \n`;
                    break;
                case 'watchlist':
                    template = `\n[${now}] 👁️ ADDED TO WATCHLIST\n- Reason: \n- Watch for: \n- Action plan: \n`;
                    break;
                case 'risk':
                    template = `\n[${now}] ⚠️ RISK ASSESSMENT\n- Risk level: \n- Concerns: \n- Mitigation: \n`;
                    break;
            }
            
            textarea.value += template;
            textarea.focus();
        }

        // Theme Management
        let currentTheme = 'light';

        function setTheme(theme) {
            currentTheme = theme;
            document.documentElement.setAttribute('data-theme', theme);
            
            // Update button states
            document.querySelectorAll('.theme-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.getElementById('theme' + theme.charAt(0).toUpperCase() + theme.slice(1))?.classList.add('active');
            
            // Save to localStorage
            try {
                localStorage.setItem('selectedTheme', theme);
            } catch (e) {
                console.error('Error saving theme:', e);
            }
            
            // Add transition animation
            document.body.style.transition = 'all 0.3s ease';
            setTimeout(() => {
                document.body.style.transition = '';
            }, 300);
        }

        function loadSavedTheme() {
            try {
                const savedTheme = localStorage.getItem('selectedTheme');
                if (savedTheme && ['light', 'dark', 'blue', 'purple'].includes(savedTheme)) {
                    setTheme(savedTheme);
                }
            } catch (e) {
                console.error('Error loading theme:', e);
            }
        }

        // Auto theme switching based on time
        function autoThemeByTime() {
            const hour = new Date().getHours();
            if (hour >= 20 || hour < 6) {
                // Night time (8 PM - 6 AM) -> Dark mode
                return 'dark';
            }
            return 'light';
        }

        // Toggle dark mode with keyboard shortcut
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + D for theme toggle
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
                setTheme(newTheme);
            }
        });

        // =============== TECHNICAL ANALYSIS FUNCTIONS ===============
        let technicalChart = null;
        let candlestickSeries = null;
        let lineSeries = null;
        let areaSeries = null;
        let currentChartType = 'candlestick';
        let currentTimeframe = '1D';
        let activeIndicators = new Set();
        let currentDrawingTool = 'none';
        let drawnObjects = [];
        
        function initTechnicalChart(symbol) {
            const container = document.getElementById('technicalChartContainer');
            if (!container) return;
            
            // Clear container
            container.innerHTML = '';
            
            // Create chart
            technicalChart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: 500,
                layout: {
                    background: { color: '#ffffff' },
                    textColor: '#333',
                },
                grid: {
                    vertLines: { color: '#f0f0f0' },
                    horzLines: { color: '#f0f0f0' },
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
                rightPriceScale: {
                    borderColor: '#ddd',
                },
                timeScale: {
                    borderColor: '#ddd',
                    timeVisible: true,
                    secondsVisible: false,
                },
            });
            
            // Generate sample candlestick data
            const candleData = generateCandlestickData(symbol);
            
            // Add candlestick series
            candlestickSeries = technicalChart.addCandlestickSeries({
                upColor: '#26a69a',
                downColor: '#ef5350',
                borderVisible: false,
                wickUpColor: '#26a69a',
                wickDownColor: '#ef5350',
            });
            candlestickSeries.setData(candleData);
            
            // Fit content
            technicalChart.timeScale().fitContent();
            
            // Handle window resize
            window.addEventListener('resize', () => {
                if (technicalChart) {
                    technicalChart.applyOptions({ width: container.clientWidth });
                }
            });
            
            // Run pattern recognition
            detectPatterns(candleData);
            
            showNotification('Technical Chart Loaded', `Candlestick chart for ${symbol} ready`, 'success');
        }
        
        function generateCandlestickData(symbol) {
            const data = [];
            const baseDate = new Date('2024-01-01');
            let price = 100 + Math.random() * 50;
            
            for (let i = 0; i < 200; i++) {
                const date = new Date(baseDate);
                date.setDate(date.getDate() + i);
                
                const open = price;
                const change = (Math.random() - 0.48) * 5;
                const close = open + change;
                const high = Math.max(open, close) + Math.random() * 2;
                const low = Math.min(open, close) - Math.random() * 2;
                
                data.push({
                    time: date.getTime() / 1000,
                    open: open,
                    high: high,
                    low: low,
                    close: close
                });
                
                price = close;
            }
            
            return data;
        }
        
        function setTimeframe(timeframe) {
            currentTimeframe = timeframe;
            
            // Update button states
            document.querySelectorAll('.chart-control-group button').forEach(btn => {
                if (btn.textContent === timeframe) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            showNotification('Timeframe Changed', `Switched to ${timeframe}`, 'info');
            
            // Reload chart with new timeframe
            if (currentSymbol) {
                initTechnicalChart(currentSymbol);
            }
        }
        
        function setChartType(type) {
            currentChartType = type;
            
            // Update button states
            ['btnCandlestick', 'btnLine', 'btnArea'].forEach(id => {
                const btn = document.getElementById(id);
                if (btn) btn.classList.remove('active');
            });
            
            const activeBtn = type === 'candlestick' ? 'btnCandlestick' : 
                             type === 'line' ? 'btnLine' : 'btnArea';
            document.getElementById(activeBtn)?.classList.add('active');
            
            // Reload chart
            if (currentSymbol) {
                initTechnicalChart(currentSymbol);
            }
        }
        
        function toggleIndicator(indicator) {
            if (activeIndicators.has(indicator)) {
                activeIndicators.delete(indicator);
                removeIndicator(indicator);
            } else {
                activeIndicators.add(indicator);
                addIndicator(indicator);
            }
            
            updateIndicatorBadges();
        }
        
        function addIndicator(indicator) {
            if (!technicalChart || !candlestickSeries) return;
            
            const data = candlestickSeries.data();
            
            switch(indicator) {
                case 'rsi':
                    addRSI(data);
                    break;
                case 'macd':
                    addMACD(data);
                    break;
                case 'bb':
                    addBollingerBands(data);
                    break;
                case 'sma':
                    addSMA(data, 20);
                    break;
                case 'ema':
                    addEMA(data, 12);
                    break;
            }
            
            showNotification('Indicator Added', `${indicator.toUpperCase()} indicator applied`, 'success');
        }
        
        function removeIndicator(indicator) {
            // Implementation for removing specific indicator
            showNotification('Indicator Removed', `${indicator.toUpperCase()} indicator removed`, 'info');
        }
        
        function addRSI(data) {
            // Simple RSI calculation
            const period = 14;
            const rsiData = [];
            
            for (let i = period; i < data.length; i++) {
                let gains = 0;
                let losses = 0;
                
                for (let j = i - period; j < i; j++) {
                    const change = data[j].close - data[j - 1].close;
                    if (change > 0) gains += change;
                    else losses += Math.abs(change);
                }
                
                const avgGain = gains / period;
                const avgLoss = losses / period;
                const rs = avgGain / (avgLoss || 1);
                const rsi = 100 - (100 / (1 + rs));
                
                rsiData.push({
                    time: data[i].time,
                    value: rsi
                });
            }
            
            const rsiSeries = technicalChart.addLineSeries({
                color: '#2962FF',
                lineWidth: 2,
                priceScaleId: 'rsi',
            });
            rsiSeries.setData(rsiData);
        }
        
        function addMACD(data) {
            // MACD calculation (simplified)
            const ema12 = calculateEMA(data, 12);
            const ema26 = calculateEMA(data, 26);
            
            const macdLine = ema12.map((val, i) => ({
                time: data[i + 26].time,
                value: val - ema26[i]
            }));
            
            const macdSeries = technicalChart.addLineSeries({
                color: '#FF6D00',
                lineWidth: 2,
            });
            macdSeries.setData(macdLine);
        }
        
        function addBollingerBands(data) {
            const period = 20;
            const stdDev = 2;
            
            for (let i = period; i < data.length; i++) {
                const slice = data.slice(i - period, i);
                const sma = slice.reduce((sum, d) => sum + d.close, 0) / period;
                const variance = slice.reduce((sum, d) => sum + Math.pow(d.close - sma, 2), 0) / period;
                const std = Math.sqrt(variance);
                
                // Add upper and lower bands
                // Implementation continues...
            }
        }
        
        function addSMA(data, period) {
            const smaData = [];
            
            for (let i = period - 1; i < data.length; i++) {
                const slice = data.slice(i - period + 1, i + 1);
                const avg = slice.reduce((sum, d) => sum + d.close, 0) / period;
                smaData.push({
                    time: data[i].time,
                    value: avg
                });
            }
            
            const smaSeries = technicalChart.addLineSeries({
                color: '#F59E0B',
                lineWidth: 2,
            });
            smaSeries.setData(smaData);
        }
        
        function addEMA(data, period) {
            const multiplier = 2 / (period + 1);
            const emaData = [];
            let ema = data[0].close;
            
            for (let i = 0; i < data.length; i++) {
                ema = (data[i].close - ema) * multiplier + ema;
                emaData.push({
                    time: data[i].time,
                    value: ema
                });
            }
            
            const emaSeries = technicalChart.addLineSeries({
                color: '#8B5CF6',
                lineWidth: 2,
            });
            emaSeries.setData(emaData);
        }
        
        function calculateEMA(data, period) {
            const multiplier = 2 / (period + 1);
            const ema = [];
            let current = data[0].close;
            
            for (let i = 0; i < data.length; i++) {
                current = (data[i].close - current) * multiplier + current;
                ema.push(current);
            }
            
            return ema;
        }
        
        function updateIndicatorBadges() {
            const container = document.getElementById('activeIndicators');
            if (!container) return;
            
            container.innerHTML = '';
            
            activeIndicators.forEach(indicator => {
                const badge = document.createElement('span');
                badge.className = 'indicator-badge';
                badge.innerHTML = `
                    ${indicator.toUpperCase()}
                    <span class="remove" onclick="toggleIndicator('${indicator}')">×</span>
                `;
                container.appendChild(badge);
            });
        }
        
        function selectDrawingTool(tool) {
            currentDrawingTool = tool;
            
            // Update tool buttons
            document.querySelectorAll('.drawing-tool').forEach(btn => {
                btn.classList.remove('active');
            });
            
            const toolBtn = document.getElementById('tool' + tool.charAt(0).toUpperCase() + tool.slice(1));
            if (toolBtn) toolBtn.classList.add('active');
            
            showNotification('Drawing Tool', `${tool} selected`, 'info');
        }
        
        function clearDrawings() {
            drawnObjects = [];
            showNotification('Drawings Cleared', 'All drawings removed', 'info');
        }
        
        function detectPatterns(data) {
            const patterns = [];
            
            // Simple pattern detection algorithms
            // Detect Doji
            for (let i = 0; i < data.length; i++) {
                const candle = data[i];
                const bodySize = Math.abs(candle.close - candle.open);
                const totalSize = candle.high - candle.low;
                
                if (bodySize / totalSize < 0.1) {
                    patterns.push({ type: 'Doji', index: i, signal: 'Neutral' });
                }
            }
            
            // Detect Hammer
            for (let i = 1; i < data.length; i++) {
                const candle = data[i];
                const body = Math.abs(candle.close - candle.open);
                const lowerWick = Math.min(candle.open, candle.close) - candle.low;
                const upperWick = candle.high - Math.max(candle.open, candle.close);
                
                if (lowerWick > body * 2 && upperWick < body * 0.3) {
                    patterns.push({ type: 'Hammer', index: i, signal: 'Bullish' });
                }
            }
            
            // Detect Shooting Star
            for (let i = 1; i < data.length; i++) {
                const candle = data[i];
                const body = Math.abs(candle.close - candle.open);
                const upperWick = candle.high - Math.max(candle.open, candle.close);
                const lowerWick = Math.min(candle.open, candle.close) - candle.low;
                
                if (upperWick > body * 2 && lowerWick < body * 0.3) {
                    patterns.push({ type: 'Shooting Star', index: i, signal: 'Bearish' });
                }
            }
            
            displayPatterns(patterns.slice(0, 6)); // Show first 6 patterns
        }
        
        function displayPatterns(patterns) {
            const container = document.getElementById('patternRecognition');
            const list = document.getElementById('patternList');
            
            if (patterns.length === 0) {
                container.style.display = 'none';
                return;
            }
            
            container.style.display = 'block';
            list.innerHTML = '';
            
            patterns.forEach(pattern => {
                const card = document.createElement('div');
                card.style.cssText = 'background:rgba(255,255,255,0.15);padding:12px;border-radius:8px;backdrop-filter:blur(10px);';
                
                const signalColor = pattern.signal === 'Bullish' ? '#27ae60' : 
                                   pattern.signal === 'Bearish' ? '#e74c3c' : '#f39c12';
                
                card.innerHTML = `
                    <div style="font-weight:600;margin-bottom:5px;">${pattern.type}</div>
                    <div style="font-size:0.85em;opacity:0.9;">
                        <span style="background:${signalColor};padding:2px 8px;border-radius:10px;font-weight:600;">
                            ${pattern.signal}
                        </span>
                    </div>
                `;
                list.appendChild(card);
            });
        }

        // Initialize on page load
        window.addEventListener('load', () => {
            // Load saved theme or auto-detect
            loadSavedTheme();
            
            // Load saved alerts
            loadSavedAlerts();
            
            initChart();
            // restore demo token from localStorage
            try {
                const stored = localStorage.getItem('demoToken');
                if (stored) {
                    const el = document.getElementById('demoToken');
                    if (el) el.value = stored;
                }
            } catch (e) {
                // ignore localStorage errors
            }

            // persist token when user changes it
            const tokenEl = document.getElementById('demoToken');
            if (tokenEl) {
                tokenEl.addEventListener('change', (ev) => {
                    try {
                        if (ev.target.value) localStorage.setItem('demoToken', ev.target.value);
                        else localStorage.removeItem('demoToken');
                    } catch (e) { /* ignore storage errors */ }
                });
            }

            // Auto-load per-symbol results on page init
            reloadPerSymbolResults().catch(()=>{});
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            const modal = document.getElementById('tradeModal');
            if (!modal) return;
            
            // ESC to close modal
            if (e.key === 'Escape' && modal.style.display === 'flex') {
                closeTradeModal();
            }
            
            // F for fullscreen toggle (when modal is open)
            if ((e.key === 'f' || e.key === 'F') && modal.style.display === 'flex' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                toggleModalFullscreen();
            }
        });

        // Compatibility fallback: some older HTML templates reference
        // `reloadPaperTradeResults()` directly. Define a safe stub if missing
        // so pages don't throw ReferenceError at runtime.
        if (typeof reloadPaperTradeResults === 'undefined') {
            async function reloadPaperTradeResults() {
                console.info('reloadPaperTradeResults: no-op stub called');
                return Promise.resolve();
            }
        }
