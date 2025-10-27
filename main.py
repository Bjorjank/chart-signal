from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
import json
import uvicorn
from datetime import datetime
import os
from typing import Optional

# Buat folder jika belum ada
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("data", exist_ok=True)

app = FastAPI(title="Trading Chart App")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

@app.get("/", response_class=HTMLResponse)
async def serve_chart():
    """Serve the main chart page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trading Chart with Signals</title>
        <script src="https://unpkg.com/lightweight-charts@4.0.1/dist/lightweight-charts.standalone.production.js"></script>
        <script src="https://unpkg.com/papaparse@5.4.1/papaparse.min.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; 
                padding: 20px; 
            }
            .container {
                max-width: 1400px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 15px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: #2c3e50; 
                color: white; 
                padding: 20px 30px; 
                text-align: center;
            }
            .header h1 { font-size: 28px; margin-bottom: 10px; }
            .controls {
                background: #34495e; 
                padding: 15px 30px; 
                display: flex; 
                justify-content: space-between; 
                align-items: center;
                flex-wrap: wrap;
            }
            .legend { display: flex; gap: 20px; flex-wrap: wrap; }
            .legend-item { 
                display: flex; 
                align-items: center; 
                gap: 8px; 
                color: white; 
                font-size: 14px;
            }
            .legend-color { 
                width: 20px; 
                height: 20px; 
                border-radius: 4px; 
                border: 2px solid rgba(255,255,255,0.3);
            }
            .stats { display: flex; gap: 20px; color: white; font-size: 14px; }
            .stat-item { 
                background: rgba(255,255,255,0.1); 
                padding: 5px 12px; 
                border-radius: 20px;
            }
            #chart-container { 
                width: 100%; 
                height: 600px; 
                background: white;
            }
            .upload-area {
                padding: 30px;
                background: #f8f9fa;
                border-top: 1px solid #e9ecef;
            }
            .file-inputs {
                display: flex;
                gap: 20px;
                justify-content: center;
                margin: 20px 0;
            }
            button {
                background: #3498db;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
            }
            button:hover { background: #2980b9; }
            .loading { display: none; text-align: center; padding: 20px; }
            .error { 
                background: #e74c3c; 
                color: white; 
                padding: 15px; 
                border-radius: 8px; 
                margin: 15px 0; 
                display: none;
            }
            .success {
                background: #27ae60;
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 Trading Chart with Signals</h1>
                <p>Visualize Entry, Stop Loss, and Take Profit signals</p>
            </div>
            
            <div class="controls">
                <button id="toggle-hover" onclick="toggleHover()" style="background:#8e44ad;">Levels: ON</button>
                <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #2ecc71;"></div>
                    <span>ENTRY (PROFIT/DEFAULT)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #e74c3c;"></div>
                    <span>ENTRY (LOSS)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #FF0000;"></div>
                    <span>STOP LOSS (level)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #0000FF;"></div>
                    <span>TAKE PROFIT (level)</span>
                </div>
                </div>

                
                <div class="stats">
                    <div class="stat-item" id="candle-count">Candles: 0</div>
                    <div class="stat-item" id="signal-count">Signals: 0</div>
                </div>
            </div>
            
            <div id="chart-container"></div>
            
            <div class="upload-area">
                <h3 style="text-align: center; margin-bottom: 20px;">Upload Your Trading Data</h3>
                <div class="file-inputs">
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 10px;">
                        <label style="font-weight: 600;">📊 OHLCV Data (CSV)</label>
                        <input type="file" id="ohlcv-file" accept=".csv">
                    </div>
                    <div style="display: flex; flex-direction: column; align-items: center; gap: 10px;">
                        <label style="font-weight: 600;">🎯 Trades Data (CSV)</label>
                        <input type="file" id="trades-file" accept=".csv">
                    </div>
                </div>
                <div style="text-align: center;">
                    <button onclick="processData()" style="padding: 15px 30px; font-size: 18px;">
                        🚀 Generate Chart
                    </button>
                </div>
                
                <div class="loading" id="loading">
                    <p>📊 Processing data and generating chart...</p>
                </div>
                
                <div class="error" id="error-message"></div>
                <div class="success" id="success-message"></div>
            </div>
        </div>

        <script>
            let chart = null;
            let candleSeries = null;
            let _signalsGlobal = [];     // simpan signals terakhir
            let _hoverLines = [];        // kumpulan priceLine aktif saat hover
            let _hoverEnabled = true;    // toggle jika mau dimatikan nanti

            function toggleHover() {
            _hoverEnabled = !_hoverEnabled;
            document.getElementById('toggle-hover').textContent = `Levels: ${_hoverEnabled ? 'ON' : 'OFF'}`;
            if (!_hoverEnabled) clearHoverLines();
            }


            // Initialize empty chart
            function initChart() {
                const container = document.getElementById('chart-container');
                
                // Clear previous chart
                if (chart) {
                    container.innerHTML = '';
                }
                
                chart = LightweightCharts.createChart(container, {
                    width: container.clientWidth,
                    height: 600,
                    layout: {
                        background: { color: '#ffffff' },
                        textColor: '#191919',
                    },
                    grid: {
                        vertLines: { color: '#e6e6e6' },
                        horzLines: { color: '#e6e6e6' },
                    },
                    rightPriceScale: {
                        borderColor: '#e6e6e6',
                        scaleMargins: { top: 0.2, bottom: 0.2 },
                    },
                    timeScale: {
                        borderColor: '#e6e6e6',
                        timeVisible: true,
                        secondsVisible: false,
                    }
                });

                candleSeries = chart.addCandlestickSeries({
                    upColor: '#26a69a',
                    downColor: '#ef5350',
                    borderUpColor: '#26a69a',
                    borderDownColor: '#ef5350',
                    wickUpColor: '#26a69a',
                    wickDownColor: '#ef5350',
                });

                console.log("✅ Chart initialized successfully!");
            }

            // Process uploaded data
            async function processData() {
                const ohlcvFile  = document.getElementById('ohlcv-file').files[0];
                const tradesFile = document.getElementById('trades-file').files[0];

                // ⇩⇩⇩ Ubah: fallback ke default bila belum ada file ⇩⇩⇩
                if (!ohlcvFile || !tradesFile) {
                    console.log('No uploads. Falling back to default /data/*.csv');
                    await processDefault();
                    return;
                }

                showLoading();
                hideError();
                hideSuccess();

                try {
                    console.log("📁 Reading files...");
                    
                    // Read files
                    const ohlcvText = await readFile(ohlcvFile);
                    const tradesText = await readFile(tradesFile);
                    
                    console.log("🔄 Processing data...");
                    // Process data using PapaParse for efficiency
                    const result = await processDataFiles(ohlcvText, tradesText);
                    
                    console.log("📊 Updating chart...");
                    // Update chart
                    updateChart(result.ohlcv, result.signals);
                    
                    showSuccess(`✅ Chart updated! ${result.ohlcv.length} candles, ${result.signals.length} signals`);
                    
                } catch (error) {
                    showError('❌ Error: ' + error.message);
                    console.error("Error details:", error);
                } finally {
                    hideLoading();
                }
            }

            function readFile(file) {
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = e => resolve(e.target.result);
                    reader.onerror = e => reject(e);
                    reader.readAsText(file);
                });
            }

            function processDataFiles(ohlcvCsv, tradesCsv) {
                return new Promise((resolve, reject) => {
                    console.log("Processing OHLCV data with PapaParse...");
                    // Parse OHLCV with PapaParse for better performance on large files
                    Papa.parse(ohlcvCsv, {
                        header: true,
                        skipEmptyLines: true,
                        dynamicTyping: false,
                        transformHeader: h => h.trim().toLowerCase(),
                        complete: function(ohlcvResults) {
                            const ohlcvData = ohlcvResults.data;
                            console.log("Processing trades data with PapaParse...");
                            Papa.parse(tradesCsv, {
                                header: true,
                                skipEmptyLines: true,
                                dynamicTyping: false,
                                transformHeader: h => h.trim().toLowerCase(),
                                complete: function(tradesResults) {
                                    const tradesData = tradesResults.data;
                                    
                                    console.log("Converting OHLCV for chart...");
                                    // Process OHLCV for chart - optimized loop
                                    const ohlcv = [];
                                    for (let i = 0; i < ohlcvData.length; i++) {
                                        const row = ohlcvData[i];
                                        const dateStr = row.datetime || row.timestamp || row.date || row.time;
                                        let timestamp;
                                        if (dateStr) {
                                            // Coba angka (epoch)
                                            if (!isNaN(dateStr)) {
                                                const num = Number(dateStr);
                                                // Heuristik: epoch ms jika > 10^12
                                                timestamp = (num > 1e12) ? Math.floor(num / 1000) : num;
                                            } else {
                                                const d = new Date(dateStr);
                                                timestamp = Math.floor(d.getTime() / 1000);
                                            }
                                            if (!isFinite(timestamp) || timestamp <= 0) continue;
                                        } else {
                                            continue;
                                        }
                                        
                                        const openVal = parseFloat(row.open || row.o || 0);
                                        const highVal = parseFloat(row.high || row.h || 0);
                                        const lowVal = parseFloat(row.low || row.l || 0);
                                        const closeVal = parseFloat(row.close || row.c || 0);
                                        
                                        if (isNaN(openVal) || isNaN(highVal) || isNaN(lowVal) || isNaN(closeVal)) {
                                            console.warn("Invalid OHLC values:", row);
                                            continue;
                                        }
                                        
                                        ohlcv.push({
                                            time: timestamp,
                                            open: openVal,
                                            high: highVal,
                                            low: lowVal,
                                            close: closeVal,
                                        });
                                    }

                                    console.log("Processing signals...");
                                    // helper normalisasi string
                                    const norm = (v) => (v ?? "").toString().trim().toUpperCase();

                                    const signals = [];
                                    for (let i = 0; i < tradesData.length; i++) {
                                    const trade = tradesData[i];

                                    // --- waktu trade ---
                                    let timestamp;
                                    const dateStr = trade.datetime || trade.timestamp || trade.date || trade.time;
                                    if (dateStr) {
                                        if (!isNaN(dateStr)) {
                                        const num = Number(dateStr);
                                        timestamp = (num > 1e12) ? Math.floor(num / 1000) : num; // epoch ms → s
                                        } else {
                                        const d = new Date(dateStr);
                                        timestamp = Math.floor(d.getTime() / 1000);
                                        }
                                        if (!isFinite(timestamp) || timestamp <= 0) {
                                        console.warn(`Invalid trade date at row ${i + 1}:`, dateStr);
                                        continue;
                                        }
                                    } else {
                                        console.warn(`No date in trade row ${i + 1}`);
                                        continue;
                                    }

                                    // --- side / arah ---
                                    const sideRaw = (trade.signal || trade.side || trade.direction || 'buy').toString().toLowerCase();
                                    const side = (sideRaw === 'sell' || sideRaw === 'short') ? 'sell' : 'buy';

                                    // --- field umum untuk status & level ---
                                    const outcomeStr = norm(trade.outcome || trade.result || trade.status);
                                    const pnlNum     = Number(trade.pnl ?? trade.profit ?? trade.net ?? NaN);
                                    const entryPrice = Number(trade.entry_price ?? trade.entry ?? trade.price_entry ?? trade.price ?? NaN);
                                    const exitPrice  = Number(trade.exit_price  ?? trade.exit  ?? trade.price_exit  ?? NaN);
                                    const slPrice    = Number(trade.sl_price    ?? trade.sl    ?? trade.stop_loss   ?? trade.stop ?? NaN);
                                    const tpPrice    = Number(trade.tp_price    ?? trade.tp    ?? trade.take_profit ?? trade.target ?? NaN);

                                    // --- tentukan PROFIT / LOSS ---
                                    let isLoss = false, isProfit = false;
                                    if (["SL","LOSS","LOST","-1"].includes(outcomeStr)) {
                                        isLoss = true;
                                    } else if (["TP","WIN","TAKE_PROFIT","PROFIT","1"].includes(outcomeStr)) {
                                        isProfit = true;
                                    }
                                    if (!isLoss && !isProfit && Number.isFinite(pnlNum)) {
                                        if (pnlNum > 0) isProfit = true;
                                        else if (pnlNum < 0) isLoss = true;
                                    }
                                    if (!isLoss && !isProfit && Number.isFinite(entryPrice) && Number.isFinite(exitPrice)) {
                                        if (side === "buy") {
                                        if (exitPrice > entryPrice) isProfit = true;
                                        else if (exitPrice < entryPrice) isLoss = true;
                                        } else {
                                        if (exitPrice < entryPrice) isProfit = true;
                                        else if (exitPrice > entryPrice) isLoss = true;
                                        }
                                    }
                                    if (!isLoss && !isProfit && Number.isFinite(exitPrice) && Number.isFinite(slPrice) && Number.isFinite(tpPrice)) {
                                        const dTP = Math.abs(exitPrice - tpPrice);
                                        const dSL = Math.abs(exitPrice - slPrice);
                                        if (dTP < dSL) isProfit = true; else if (dSL < dTP) isLoss = true;
                                    }

                                    // --- ENTRY marker: simpan level supaya bisa ditampilkan saat hover ---
                                    if (Number.isFinite(entryPrice)) {
                                        const entryColor = isLoss ? '#e74c3c' : '#2ecc71'; // merah kalau loss, hijau default/profit
                                        const entryText  = isLoss ? `LOSS ${side.toUpperCase()}` : (isProfit ? `TP ${side.toUpperCase()}` : `ENTRY ${side.toUpperCase()}`);
                                        const entryShape = (side === 'buy')
                                        ? (isLoss ? 'arrowDown' : 'arrowUp')
                                        : (isLoss ? 'arrowUp'   : 'arrowDown');

                                        // >>>> simpan juga level entry/sl/tp di object entry:
                                        signals.push({
                                        time: timestamp,
                                        price: entryPrice,
                                        type: 'entry',
                                        side: side,
                                        color: entryColor,
                                        text: entryText,
                                        shape: entryShape,
                                        entryLevel: entryPrice,
                                        slLevel: Number.isFinite(slPrice) ? slPrice : null,
                                        tpLevel: Number.isFinite(tpPrice) ? tpPrice : null
                                        });
                                    }

                                    // --- SL marker (level referensi) ---
                                    if (Number.isFinite(slPrice)) {
                                        signals.push({
                                        time: timestamp,
                                        price: slPrice,
                                        type: 'sl',
                                        side: side,
                                        color: '#FF0000',
                                        text: 'SL',
                                        shape: side === 'buy' ? 'arrowDown' : 'arrowUp'
                                        });
                                    }

                                    // --- TP marker (level referensi) ---
                                    if (Number.isFinite(tpPrice)) {
                                        signals.push({
                                        time: timestamp,
                                        price: tpPrice,
                                        type: 'tp',
                                        side: side,
                                        color: '#0000FF',
                                        text: 'TP',
                                        shape: side === 'buy' ? 'arrowUp' : 'arrowDown'
                                        });
                                    }
                                    }

                                    console.log(`Processed ${ohlcv.length} candles and ${signals.length} signals`);
                                    resolve({ ohlcv, signals });
                                },
                                error: function(error) {
                                    reject(error);
                                }
                            });
                        },
                        error: function(error) {
                            reject(error);
                        }
                    });
                });
            }
              async function fetchText(url) {
                const res = await fetch(url, { cache: 'no-store' });
                if (!res.ok) throw new Error(`Fetch failed: ${url}`);
                return await res.text();
            }

            async function processDefault() {
                showLoading(); hideError(); hideSuccess();
                try {
                    const ohlcvCsv = await fetchText('/data/sample_ohlcv.csv');
                    const tradesCsv = await fetchText('/data/sample_trades.csv');

                    const result = await processDataFiles(ohlcvCsv, tradesCsv);
                    updateChart(result.ohlcv, result.signals);
                    showSuccess(`✅ Default chart loaded! ${result.ohlcv.length} candles, ${result.signals.length} signals`);
                } catch (err) {
                    showError('❌ Gagal memuat data default: ' + err.message);
                    console.error(err);
                } finally {
                    hideLoading();
                }
            }
            function formatPrice(p) {
                if (!Number.isFinite(p)) return '';
                const ap = Math.abs(p);
                if (ap >= 1000) return p.toFixed(1);
                if (ap >= 1)    return p.toFixed(2);
                if (ap >= 0.1)  return p.toFixed(3);
                if (ap >= 0.01) return p.toFixed(4);
                return p.toFixed(5);
                }

            function updateChart(ohlcvData, signalsData) {
            if (ohlcvData.length === 0) {
                showError('❌ No valid OHLCV data found');
                return;
            }

            // Sort & set
            ohlcvData.sort((a, b) => a.time - b.time);
            candleSeries.setData(ohlcvData);

            signalsData.sort((a, b) => a.time - b.time);
            const markers = signalsData.map(signal => {
            let txt = signal.text || '';
            // ringkas angka untuk SL/TP saja
            if (signal.type === 'sl' && Number.isFinite(signal.price)) {
                txt = `SL ${formatPrice(signal.price)}`;
            } else if (signal.type === 'tp' && Number.isFinite(signal.price)) {
                txt = `TP ${formatPrice(signal.price)}`;
            }
            // entry dibiarkan apa adanya (warna sudah membedakan win/loss)
            return {
                time: signal.time,
                position: signal.side === 'buy' ? 'belowBar' : 'aboveBar',
                color: signal.color,
                shape: signal.shape,
                text: txt,
            };
            });

            candleSeries.setMarkers(markers);

            // >>>>>> simpan untuk hover highlight
            _signalsGlobal = signalsData;

            // >>>>>> pasang listener crosshair untuk hover
            attachCrosshairHover();

            chart.timeScale().fitContent();
            document.getElementById('candle-count').textContent = `Candles: ${ohlcvData.length}`;
            document.getElementById('signal-count').textContent = `Signals: ${signalsData.length}`;
            }
            function clearHoverLines() {
            if (!_hoverLines || !_hoverLines.length) return;
            for (const pl of _hoverLines) {
                try { candleSeries.removePriceLine(pl); } catch (e) {}
            }
            _hoverLines = [];
            }

            function addHoverLine(price, color, title) {
            const pl = candleSeries.createPriceLine({
                price: price,
                color: color,
                lineWidth: 1,
                lineStyle: LightweightCharts.LineStyle.Dashed,
                axisLabelVisible: true,               // <— tampilkan label di sumbu harga
                title: title || ''                    // <— isi label (mis. "SL 1.2345")
            });
            _hoverLines.push(pl);
            }


            function attachCrosshairHover() {
            if (!chart || !candleSeries) return;

            // hindari dobel binding: hapus dahulu dengan membuat handler tunggal
            if (attachCrosshairHover._attached) return;
            attachCrosshairHover._attached = true;

            chart.subscribeCrosshairMove(param => {
                if (!_hoverEnabled) return;
                // kalau mouse keluar chart
                if (!param || !param.time) {
                clearHoverLines();
                return;
                }
                const hoveredTime = (typeof param.time === 'object' && 'timestamp' in param.time)
                ? param.time.timestamp
                : param.time;

                // cari entry signal terdekat di waktu ini
                // toleransi: +/- 1 bar (waktu sama)
                // NOTE: markers di-set per bar, jadi cocokkan time persis lebih stabil
                const entriesAtTime = _signalsGlobal.filter(s => s.type === 'entry' && s.time === hoveredTime);

                // jika tidak ada entry di bar ini, bersihkan garis
                if (!entriesAtTime.length) {
                clearHoverLines();
                return;
                }

                // pilih satu entry (kalau multiple, ambil pertama)
                const s = entriesAtTime[0];

                // render ulang garis hover
                clearHoverLines();

                // style warna transparan
                const colEntry = 'rgba(46, 204, 113, 0.35)'; // sedikit lebih jelas
                const colSL    = 'rgba(231, 76, 60, 0.35)';
                const colTP    = 'rgba(52, 152, 219, 0.35)';

                if (Number.isFinite(s.entryLevel)) addHoverLine(s.entryLevel, colEntry, `E ${formatPrice(s.entryLevel)}`);
                if (Number.isFinite(s.slLevel))    addHoverLine(s.slLevel,    colSL,    `SL ${formatPrice(s.slLevel)}`);
                if (Number.isFinite(s.tpLevel))    addHoverLine(s.tpLevel,    colTP,    `TP ${formatPrice(s.tpLevel)}`);

            });
            }


            function showLoading() {
                document.getElementById('loading').style.display = 'block';
            }

            function hideLoading() {
                document.getElementById('loading').style.display = 'none';
            }

            function showError(message) {
                const errorEl = document.getElementById('error-message');
                errorEl.textContent = message;
                errorEl.style.display = 'block';
            }

            function hideError() {
                document.getElementById('error-message').style.display = 'none';
            }

            function showSuccess(message) {
                const successEl = document.getElementById('success-message');
                successEl.textContent = message;
                successEl.style.display = 'block';
            }

            function hideSuccess() {
                document.getElementById('success-message').style.display = 'none';
            }

            // Handle window resize
            window.addEventListener('resize', () => {
                if (chart) {
                    chart.applyOptions({
                        width: document.getElementById('chart-container').clientWidth
                    });
                }
            });

            // Initialize chart on load
            document.addEventListener('DOMContentLoaded', async () => {
            initChart();
            await processDefault();  // auto muat data default agar chart & markers langsung tampil
            });

        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    print("🚀 Starting Trading Chart App...")
    print("📊 Open: http://localhost:8000")
    print("✅ Chart will work 100% - No Streamlit restrictions!")
    
    # Hilangkan reload untuk menghilangkan warning
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)