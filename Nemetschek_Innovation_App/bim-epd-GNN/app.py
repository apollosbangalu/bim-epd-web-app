"""
BIM-EPD Material Matcher - Final Version
Matches actual EPD JSON structure with all environmental indicators
"""

from flask import Flask, jsonify, request
import json
import os
import pandas as pd

app = Flask(__name__)

# Configuration
NEW_MATCHING_RESULTS = 'all_matches_final_complete.json'
NEW_BIM_MATERIALS = 'bim_materials_reduced.json'
NEW_EPD_DATA = 'epd_data_reduced.json'
OUTPUT_FOLDER = 'outputs3'
EPD_JSON_FOLDER = 'Ecoplatform_Restructured_translation_Json'
BIM_COMPLETE_JSON = os.path.join(OUTPUT_FOLDER, 'bim_materials_complete.json')

# HTML TEMPLATE with corrected indicator names
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIM-EPD Material Matcher</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
        }
        .matches-sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 350px;
            height: 100vh;
            background: rgba(255, 255, 255, 0.98);
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.1);
            padding: 20px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
        }
        .matches-sidebar.active { display: block; }
        .matches-sidebar h2 {
            color: #667eea;
            font-size: 1.2em;
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e5e7eb;
        }
        .match-count {
            background: #f0f9ff;
            color: #0369a1;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 600;
        }
        .epd-list-item {
            background: #f9fafb;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }
        .epd-list-item:hover {
            background: #f0f9ff;
            border-left-color: #667eea;
            transform: translateX(3px);
        }
        .epd-list-item.selected {
            background: #e0e7ff;
            border-left-color: #667eea;
        }
        .epd-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }
        .epd-item-rank {
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
        }
        .epd-item-checkbox {
            width: 16px;
            height: 16px;
            cursor: pointer;
            accent-color: #667eea;
        }
        .epd-item-name {
            font-size: 13px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 5px;
            line-height: 1.3;
        }
        .epd-item-meta {
            font-size: 11px;
            color: #6b7280;
            line-height: 1.4;
        }
        .container {
            flex: 1;
            margin-left: 0;
            padding: 20px;
            transition: margin-left 0.3s;
        }
        .container.with-sidebar { margin-left: 370px; }
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .search-container {
            position: relative;
            margin-bottom: 30px;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        #searchBox {
            width: 100%;
            padding: 18px 24px;
            font-size: 18px;
            border: none;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            outline: none;
            transition: all 0.3s ease;
        }
        #searchBox:focus {
            box-shadow: 0 6px 30px rgba(0,0,0,0.2);
            transform: translateY(-2px);
        }
        #autocomplete {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border-radius: 12px;
            margin-top: 8px;
            max-height: 400px;
            overflow-y: auto;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            z-index: 1000;
            display: none;
        }
        .autocomplete-item {
            padding: 14px 20px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
            transition: background 0.2s;
        }
        .autocomplete-item:hover { background: #f8f9ff; }
        .autocomplete-item:last-child { border-bottom: none; }
        .selected-material-info {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            display: none;
            max-width: 800px;
            margin-left: auto;
            margin-right: auto;
        }
        .selected-material-info h3 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .selected-material-info p {
            color: #1f2937;
            font-size: 16px;
            font-weight: 500;
        }
        .compare-container {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 100;
        }
        .compare-btn {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            border: none;
            padding: 16px 35px;
            border-radius: 50px;
            font-size: 17px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
            transition: all 0.3s ease;
            display: none;
        }
        .compare-btn.active { display: block; }
        .compare-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(16, 185, 129, 0.5);
        }
        #detailsPanel {
            display: none;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            max-width: 1400px;
            margin-left: auto;
            margin-right: auto;
        }
        .details-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
        }
        .details-title {
            font-size: 1.6em;
            color: #1f2937;
        }
        .close-btn {
            background: #ef4444;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: background 0.2s;
        }
        .close-btn:hover { background: #dc2626; }
        .details-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-bottom: 30px;
        }
        .details-section {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
        }
        .details-section h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.15em;
        }
        .details-section p {
            margin: 10px 0;
            color: #4b5563;
            line-height: 1.6;
            word-wrap: break-word;
            font-size: 14px;
        }
        .details-section strong { color: #1f2937; }
        .gwp-section {
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .gwp-section h3 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        .gwp-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
        }
        .gwp-item {
            background: #f9fafb;
            padding: 18px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .gwp-item.total {
            border-left-color: #ef4444;
            background: #fef2f2;
        }
        .gwp-label {
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 8px;
            font-weight: 500;
        }
        .gwp-value {
            font-size: 22px;
            font-weight: 700;
            color: #1f2937;
        }
        .gwp-unit {
            font-size: 13px;
            color: #9ca3af;
            margin-left: 4px;
            font-weight: 400;
        }
        .chart-container {
            background: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .chart-container h3 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        canvas {
            max-height: 450px !important;
            height: 400px;
        }
        .export-btn {
            background: #10b981;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-left: 10px;
            transition: background 0.2s;
        }
        .export-btn:hover { background: #059669; }
        .json-viewer {
            background: #1f2937;
            color: #10b981;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 500px;
            overflow-y: auto;
        }
        .json-viewer h3 {
            color: white;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        #comparisonPanel {
            display: none;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            max-width: 1400px;
            margin-left: auto;
            margin-right: auto;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #6b7280;
            font-size: 18px;
        }
        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 14px;
        }
        .insight-box {
            background: #f0f9ff;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 14px;
            color: #1e40af;
            border-left: 3px solid #0369a1;
        }
    </style>
</head>
<body>
    <div class="matches-sidebar" id="matchesSidebar">
        <h2>📦 Matched EPDs</h2>
        <div class="match-count" id="matchCount">No material selected</div>
        <div id="epdList"></div>
    </div>
    
    <div class="container" id="mainContainer">
        <h1>🏗️ BIM-EPD Material Matcher</h1>
        
        <div class="search-container">
            <input type="text" id="searchBox" placeholder="Search BIM materials... (e.g., concrete, steel, acoustic)" autocomplete="off">
            <div id="autocomplete"></div>
        </div>
        
        <div class="selected-material-info" id="selectedMaterialInfo">
            <h3>Selected Material</h3>
            <p id="selectedMaterialName"></p>
        </div>
        
        <div class="compare-container">
            <button class="compare-btn" id="compareBtn" onclick="compareSelected()">
                Compare (<span id="selectedCount">0</span>)
            </button>
        </div>
        
        <div id="comparisonPanel">
            <div class="details-header">
                <h2 class="details-title">Environmental Impact Comparison</h2>
                <div>
                    <button class="export-btn" onclick="exportComparison()">📊 Export</button>
                    <button class="close-btn" onclick="closeComparison()">Close</button>
                </div>
            </div>
            <div id="comparisonCharts"></div>
        </div>
        
        <div id="detailsPanel">
            <div class="details-header">
                <h2 class="details-title" id="detailsPanelTitle">EPD Details</h2>
                <button class="close-btn" onclick="closeDetails()">Close</button>
            </div>
            
            <div class="details-grid">
                <div class="details-section">
                    <h3>BIM Material</h3>
                    <div id="bimDetails"></div>
                </div>
                <div class="details-section">
                    <h3>EPD Summary</h3>
                    <div id="epdSummary"></div>
                </div>
            </div>
            
            <div class="gwp-section" id="gwpSection" style="display: none;">
                <h3>🌍 Environmental Impact (Global Warming Potential)</h3>
                <div class="gwp-grid" id="gwpGrid"></div>
            </div>
            
            <div class="chart-container" id="envChartsSection" style="display: none;">
                <h3>📊 Environmental Indicators (Production Phase A1-A3)
                    <button class="export-btn" onclick="exportSingleChart()">Export</button>
                </h3>
                <canvas id="envChart"></canvas>
            </div>
            
            <div class="json-viewer">
                <h3>Complete EPD JSON Data</h3>
                <pre id="jsonData"></pre>
            </div>
        </div>
    </div>
    
    <script>
        let currentMaterial = null;
        let currentMatches = [];
        let selectedEPDs = new Set();
        let currentChart = null;
        let comparisonCharts = [];
        
        function formatUnit(unit) {
            if (!unit) return '';
            unit = unit.replace(/CO_?\\(?\\s*2\\s*\\)?-?Äq\\.?/gi, 'CO₂-eq');
            unit = unit.replace(/CO_?\\(?\\s*2\\s*\\)?/gi, 'CO₂');
            unit = unit.replace(/H\\^?\\+?\\(?\\s*\\+\\s*\\)?-?Äq\\.?/gi, 'H⁺-eq');
            unit = unit.replace(/H\\^?\\+/gi, 'H⁺');
            unit = unit.replace(/PO_?\\(?\\s*4\\s*\\)?-?Äq\\.?/gi, 'PO₄-eq');
            unit = unit.replace(/PO_?\\(?\\s*4\\s*\\)?/gi, 'PO₄');
            unit = unit.replace(/m\\^?\\(?\\s*3\\s*\\)?/gi, 'm³');
            unit = unit.replace(/_\\(2\\)/g, '₂').replace(/_2/g, '₂');
            unit = unit.replace(/_\\(3\\)/g, '₃').replace(/_3/g, '₃');
            unit = unit.replace(/_\\(4\\)/g, '₄').replace(/_4/g, '₄');
            unit = unit.replace(/\\^\\(2\\)/g, '²').replace(/\\^2/g, '²');
            unit = unit.replace(/\\^\\(3\\)/g, '³').replace(/\\^3/g, '³');
            unit = unit.replace(/Äq\\./g, 'eq').replace(/Äq/g, 'eq');
            // Additional formatting for specific units
            unit = unit.replace(/mol H\\+/gi, 'mol H⁺');
            unit = unit.replace(/kg P eq/gi, 'kg P-eq');
            unit = unit.replace(/kg N eq/gi, 'kg N-eq');
            unit = unit.replace(/mol N eq/gi, 'mol N-eq');
            unit = unit.replace(/kg NMVOC eq/gi, 'kg NMVOC-eq');
            unit = unit.replace(/kg Sb eq/gi, 'kg Sb-eq');
            unit = unit.replace(/kg CFC-11 eq/gi, 'kg CFC-11-eq');
            unit = unit.replace(/m3 world eq\\. deprived/gi, 'm³ world-eq deprived');
            return unit;
        }
        
        const searchBox = document.getElementById('searchBox');
        const autocomplete = document.getElementById('autocomplete');
        
        searchBox.addEventListener('input', async (e) => {
            const query = e.target.value.trim();
            if (query.length < 2) {
                autocomplete.style.display = 'none';
                return;
            }
            try {
                const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const materials = await response.json();
                if (materials.length === 0) {
                    autocomplete.style.display = 'none';
                    return;
                }
                autocomplete.innerHTML = materials
                    .map(name => `<div class="autocomplete-item" onclick="selectMaterial('${name.replace(/'/g, "\\\\'")}')">${name}</div>`)
                    .join('');
                autocomplete.style.display = 'block';
            } catch (error) {
                console.error('Search error:', error);
            }
        });
        
        document.addEventListener('click', (e) => {
            if (!searchBox.contains(e.target) && !autocomplete.contains(e.target)) {
                autocomplete.style.display = 'none';
            }
        });
        
        async function selectMaterial(materialName) {
            currentMaterial = materialName;
            searchBox.value = materialName;
            autocomplete.style.display = 'none';
            document.getElementById('selectedMaterialName').textContent = materialName;
            document.getElementById('selectedMaterialInfo').style.display = 'block';
            document.getElementById('detailsPanel').style.display = 'none';
            document.getElementById('comparisonPanel').style.display = 'none';
            await loadMatches(materialName);
        }
        
        async function loadMatches(materialName) {
            try {
                const response = await fetch(`/api/matches/${encodeURIComponent(materialName)}`);
                if (!response.ok) throw new Error('Material not found');
                currentMatches = await response.json();
                document.getElementById('matchesSidebar').classList.add('active');
                document.getElementById('mainContainer').classList.add('with-sidebar');
                document.getElementById('matchCount').textContent = `${currentMatches.length} EPDs found`;
                const list = document.getElementById('epdList');
                list.innerHTML = currentMatches.map(match => {
                    const shortName = match.epd_name.length > 45 ? match.epd_name.substring(0, 45) + '...' : match.epd_name;
                    const category = (match.hierarchy_l2 || match.hierarchy_l1 || '').replace('OEKOBAU.DAT:', '').replace(/^[0-9.]+\\s*/, '').trim();
                    return `
                        <div class="epd-list-item" onclick="showDetailsFromList('${match.epd_uuid}')" data-uuid="${match.epd_uuid}">
                            <div class="epd-item-header">
                                <span class="epd-item-rank">Rank ${match.rank}</span>
                                <input type="checkbox" class="epd-item-checkbox" data-uuid="${match.epd_uuid}" data-name="${match.epd_name.replace(/"/g, '&quot;')}" onchange="toggleSelection(this)" onclick="event.stopPropagation()">
                            </div>
                            <div class="epd-item-name">${shortName}</div>
                            <div class="epd-item-meta"><strong>Category:</strong> ${category || 'N/A'}<br><strong>Location:</strong> ${match.location}</div>
                        </div>
                    `;
                }).join('');
                selectedEPDs.clear();
                updateCompareButton();
            } catch (error) {
                alert(`Error loading matches: ${error.message}`);
            }
        }
        
        function showDetailsFromList(epdUuid) {
            showDetails(currentMaterial, epdUuid);
            document.querySelectorAll('.epd-list-item').forEach(item => item.classList.remove('selected'));
            const selectedItem = document.querySelector(`.epd-list-item[data-uuid="${epdUuid}"]`);
            if (selectedItem) selectedItem.classList.add('selected');
        }
        
        function toggleSelection(checkbox) {
            const uuid = checkbox.dataset.uuid;
            const name = checkbox.dataset.name;
            if (checkbox.checked) {
                selectedEPDs.add(JSON.stringify({uuid, name}));
            } else {
                selectedEPDs.delete(JSON.stringify({uuid, name}));
            }
            updateCompareButton();
        }
        
        function updateCompareButton() {
            const btn = document.getElementById('compareBtn');
            const count = document.getElementById('selectedCount');
            count.textContent = selectedEPDs.size;
            if (selectedEPDs.size >= 2) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
        
        async function showDetails(bimName, epdUuid) {
            const panel = document.getElementById('detailsPanel');
            panel.style.display = 'block';
            panel.scrollIntoView({ behavior: 'smooth' });
            document.getElementById('bimDetails').innerHTML = '<div class="loading">Loading...</div>';
            document.getElementById('epdSummary').innerHTML = '<div class="loading">Loading...</div>';
            document.getElementById('jsonData').textContent = 'Loading...';
            document.getElementById('gwpSection').style.display = 'none';
            document.getElementById('envChartsSection').style.display = 'none';
            try {
                const response = await fetch(`/api/details?bim=${encodeURIComponent(bimName)}&epd=${encodeURIComponent(epdUuid)}`);
                if (!response.ok) throw new Error('Failed to load details');
                const data = await response.json();
                const epdName = data.epd_summary?.product_name || 'EPD Details';
                document.getElementById('detailsPanelTitle').textContent = epdName.length > 60 ? epdName.substring(0, 60) + '...' : epdName;
                let bimHtml = '';
                if (data.bim) {
                    const cleanPrimaryCategory = (data.bim.primary_category || 'N/A').replace(/^[0-9.]+\\s*/, '');
                    const cleanSecondaryCategory = (data.bim.secondary_category || 'N/A').replace(/^[0-9.]+\\s*/, '');
                    bimHtml = `<p><strong>Material:</strong> ${data.bim.material_name || 'N/A'}</p><p><strong>Category:</strong> ${cleanPrimaryCategory}</p><p><strong>Type:</strong> ${cleanSecondaryCategory}</p><p><strong>Description:</strong> ${data.bim.description || 'N/A'}</p><p><strong>Details:</strong> ${data.bim.rdfs_comment || 'N/A'}</p>`;
                } else {
                    bimHtml = '<p>No BIM data available</p>';
                }
                document.getElementById('bimDetails').innerHTML = bimHtml;
                let epdHtml = '';
                if (data.epd_original) {
                    try {
                        const processData = Array.isArray(data.epd_original) ? data.epd_original[0] : data.epd_original;
                        const processInfo = processData['Process Data set']?.['Process information'];
                        if (processInfo) {
                            const name = processInfo['Name'] || processInfo['name_en'] || 'N/A';
                            const mainCategory = (processInfo['main_category'] || 'N/A').replace(/^[0-9.]+\\s*/, '');
                            const subCategory = (processInfo['subcategory'] || processInfo['product_type'] || 'N/A').replace(/^[0-9.]+\\s*/, '');
                            const techPurpose = processInfo['Technical purpose of product or process'] || '';
                            const techDescription = processInfo['Technology description including background system'] || '';
                            epdHtml = `<p><strong>Product:</strong> ${name}</p><p><strong>Category:</strong> ${mainCategory}</p><p><strong>Type:</strong> ${subCategory}</p>`;
                            if (techPurpose) epdHtml += `<p><strong>Purpose:</strong> ${techPurpose}</p>`;
                            if (techDescription) epdHtml += `<p><strong>Technology:</strong> ${techDescription}</p>`;
                        } else {
                            epdHtml = '<p>No EPD process information available</p>';
                        }
                    } catch (error) {
                        console.error('Error extracting EPD info:', error);
                        epdHtml = '<p>Error loading EPD information</p>';
                    }
                } else if (data.epd_summary) {
                    const cleanMainCat = (data.epd_summary.hierarchy_l1 || 'N/A').replace('OEKOBAU.DAT:', '').replace(/^[0-9.]+\\s*/, '').trim();
                    const cleanSubCat = (data.epd_summary.hierarchy_l2 || 'N/A').replace(/^[0-9.]+\\s*/, '').trim();
                    epdHtml = `<p><strong>Product:</strong> ${data.epd_summary.product_name || 'N/A'}</p><p><strong>Category:</strong> ${cleanMainCat}</p><p><strong>Type:</strong> ${cleanSubCat}</p>`;
                    if (data.epd_summary.technical_purpose && data.epd_summary.technical_purpose !== 'N/A') {
                        epdHtml += `<p><strong>Purpose:</strong> ${data.epd_summary.technical_purpose}</p>`;
                    }
                } else {
                    epdHtml = '<p>No EPD summary available</p>';
                }
                document.getElementById('epdSummary').innerHTML = epdHtml;
                if (data.epd_original) {
                    extractGWPData(data.epd_original);
                    generateEnvChart(data.epd_original);
                    document.getElementById('jsonData').textContent = JSON.stringify(data.epd_original, null, 2);
                } else {
                    document.getElementById('jsonData').textContent = 'Original EPD JSON not found';
                }
            } catch (error) {
                console.error('Error loading details:', error);
                document.getElementById('bimDetails').innerHTML = `<div class="error">${error.message}</div>`;
                document.getElementById('epdSummary').innerHTML = `<div class="error">${error.message}</div>`;
                document.getElementById('jsonData').textContent = 'Error loading data';
            }
        }
        
        function extractGWPData(epdData) {
            try {
                const processData = Array.isArray(epdData) ? epdData[0] : epdData;
                const envIndicators = processData['Process Data set']?.['Environmental indicators']?.['Environmental Impact Indicators'];
                if (!envIndicators) {
                    document.getElementById('gwpSection').style.display = 'none';
                    return;
                }
                const gwpTotal = envIndicators['Global Warming Potential - total (GWP-total)'];
                const gwpBiogenic = envIndicators['Global Warming Potential - biogenic (GWP-biogenic)'];
                const gwpFossil = envIndicators['Global Warming Potential - fossil fuels (GWP-fossil)'];
                const gwpLuluc = envIndicators['Global Warming Potential - land use and land use change (GWP-luluc)'];
                let gwpHtml = '';
                if (gwpTotal) {
                    const totalA1A3 = parseFloat(gwpTotal.Values['Production A1-A3']) || 0;
                    gwpHtml += `<div class="gwp-item total"><div class="gwp-label">GWP Total (A1-A3)</div><div class="gwp-value">${totalA1A3.toFixed(3)}<span class="gwp-unit">${formatUnit(gwpTotal.Unit || 'kg CO₂-eq')}</span></div></div>`;
                }
                if (gwpFossil) {
                    const fossilA1A3 = parseFloat(gwpFossil.Values['Production A1-A3']) || 0;
                    gwpHtml += `<div class="gwp-item"><div class="gwp-label">GWP Fossil (A1-A3)</div><div class="gwp-value">${fossilA1A3.toFixed(3)}<span class="gwp-unit">${formatUnit(gwpFossil.Unit || 'kg CO₂-eq')}</span></div></div>`;
                }
                if (gwpBiogenic) {
                    const biogenicA1A3 = parseFloat(gwpBiogenic.Values['Production A1-A3']) || 0;
                    gwpHtml += `<div class="gwp-item"><div class="gwp-label">GWP Biogenic (A1-A3)</div><div class="gwp-value">${biogenicA1A3.toFixed(3)}<span class="gwp-unit">${formatUnit(gwpBiogenic.Unit || 'kg CO₂-eq')}</span></div></div>`;
                }
                if (gwpLuluc) {
                    const lulucA1A3 = parseFloat(gwpLuluc.Values['Production A1-A3']) || 0;
                    gwpHtml += `<div class="gwp-item"><div class="gwp-label">GWP LULUC (A1-A3)</div><div class="gwp-value">${lulucA1A3.toFixed(3)}<span class="gwp-unit">${formatUnit(gwpLuluc.Unit || 'kg CO₂-eq')}</span></div></div>`;
                }
                if (gwpHtml) {
                    document.getElementById('gwpGrid').innerHTML = gwpHtml;
                    document.getElementById('gwpSection').style.display = 'block';
                } else {
                    document.getElementById('gwpSection').style.display = 'none';
                }
            } catch (error) {
                console.error('Error extracting GWP:', error);
                document.getElementById('gwpSection').style.display = 'none';
            }
        }
        
        function generateEnvChart(epdData) {
            try {
                const processData = Array.isArray(epdData) ? epdData[0] : epdData;
                const envIndicators = processData['Process Data set']?.['Environmental indicators']?.['Environmental Impact Indicators'];
                if (!envIndicators) {
                    document.getElementById('envChartsSection').style.display = 'none';
                    return;
                }
                
                // Updated indicator names to match actual JSON structure
                const indicators = [
                    { full: 'Global Warming Potential - total (GWP-total)', short: 'GWP Total' },
                    { full: 'Acidifcation potential, Accumulated Exceedance (AP)', short: 'Acidification' },
                    { full: 'Europhication potential - freshwater (EP-freshwater)', short: 'Eutrophication Freshwater' },
                    { full: 'Photochemical Ozone Creation Potential (POCP)', short: 'Ozone Formation' },
                    { full: 'Abiotic depletion potential - fossil resources (ADPF)', short: 'Fossil Depletion' },
                    { full: 'Water (user) deprivation potential (WDP)', short: 'Water Deprivation' }
                ];
                
                const labels = [];
                const values = [];
                const units = [];
                const fullNames = [];
                indicators.forEach(indicator => {
                    if (envIndicators[indicator.full]) {
                        const data = envIndicators[indicator.full];
                        const value = parseFloat(data.Values['Production A1-A3']) || 0;
                        labels.push(indicator.short);
                        values.push(value);
                        units.push(data.Unit || '');
                        fullNames.push(indicator.full.split('(')[0].trim());
                    }
                });
                if (labels.length === 0) {
                    document.getElementById('envChartsSection').style.display = 'none';
                    return;
                }
                const maxValue = Math.max(...values);
                const minValue = Math.min(...values.filter(v => v > 0));
                const useLogScale = (maxValue / minValue) > 100;
                if (currentChart) currentChart.destroy();
                const ctx = document.getElementById('envChart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Impact Value',
                            data: values,
                            backgroundColor: 'rgba(102, 126, 234, 0.7)',
                            borderColor: 'rgba(102, 126, 234, 1)',
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                callbacks: {
                                    title: function(context) {
                                        return fullNames[context[0].dataIndex];
                                    },
                                    label: function(context) {
                                        return `${context.parsed.y.toFixed(3)} ${formatUnit(units[context.dataIndex])}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                type: useLogScale ? 'logarithmic' : 'linear',
                                beginAtZero: !useLogScale,
                                title: {
                                    display: true,
                                    text: useLogScale ? 'Impact Value (log scale)' : 'Impact Value',
                                    font: { size: 14, weight: 'bold' }
                                }
                            },
                            x: {
                                ticks: { font: { size: 12 } }
                            }
                        }
                    }
                });
                document.getElementById('envChartsSection').style.display = 'block';
            } catch (error) {
                console.error('Error generating chart:', error);
                document.getElementById('envChartsSection').style.display = 'none';
            }
        }
        
        function closeDetails() {
            document.getElementById('detailsPanel').style.display = 'none';
            document.querySelectorAll('.epd-list-item').forEach(item => item.classList.remove('selected'));
        }
        
        async function compareSelected() {
            if (selectedEPDs.size < 2) {
                alert('Please select at least 2 EPDs to compare');
                return;
            }
            const epds = Array.from(selectedEPDs).map(s => JSON.parse(s));
            const uuids = epds.map(e => e.uuid);
            document.getElementById('comparisonPanel').style.display = 'block';
            document.getElementById('comparisonCharts').innerHTML = '<div class="loading">Loading comparison...</div>';
            document.getElementById('comparisonPanel').scrollIntoView({ behavior: 'smooth' });
            document.getElementById('detailsPanel').style.display = 'none';
            try {
                const response = await fetch('/api/compare', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ epd_uuids: uuids })
                });
                if (!response.ok) throw new Error('Comparison failed');
                const compareData = await response.json();
                generateComparisonCharts(compareData);
            } catch (error) {
                document.getElementById('comparisonCharts').innerHTML = `<div class="error">Error: ${error.message}</div>`;
            }
        }
        
        function generateComparisonCharts(compareData) {
            comparisonCharts.forEach(chart => chart.destroy());
            comparisonCharts = [];
            
            // Updated indicator names to match actual JSON structure
            const indicators = [
                { full: 'Global Warming Potential - total (GWP-total)', short: 'GWP Total' },
                { full: 'Acidifcation potential, Accumulated Exceedance (AP)', short: 'Acidification' },
                { full: 'Europhication potential - freshwater (EP-freshwater)', short: 'Eutrophication Freshwater' },
                { full: 'Photochemical Ozone Creation Potential (POCP)', short: 'Ozone Formation' },
                { full: 'Abiotic depletion potential - fossil resources (ADPF)', short: 'Fossil Depletion' },
                { full: 'Water (user) deprivation potential (WDP)', short: 'Water Deprivation' }
            ];
            
            const colors = [
                'rgba(102, 126, 234, 0.7)',
                'rgba(118, 75, 162, 0.7)',
                'rgba(16, 185, 129, 0.7)',
                'rgba(239, 68, 68, 0.7)',
                'rgba(245, 158, 11, 0.7)',
                'rgba(59, 130, 246, 0.7)'
            ];
            let chartsHtml = '';
            indicators.forEach((indicator, idx) => {
                chartsHtml += `<div class="chart-container"><h3>${indicator.short}</h3><div id="insight${idx}" class="insight-box" style="display: none;"></div><canvas id="compareChart${idx}"></canvas></div>`;
            });
            document.getElementById('comparisonCharts').innerHTML = chartsHtml;
            indicators.forEach((indicator, idx) => {
                try {
                    const labels = [];
                    const values = [];
                    const fullNames = [];
                    let unit = '';
                    compareData.forEach((epd, epdIdx) => {
                        const processData = Array.isArray(epd.data) ? epd.data[0] : epd.data;
                        const envIndicators = processData['Process Data set']?.['Environmental indicators']?.['Environmental Impact Indicators'];
                        if (envIndicators && envIndicators[indicator.full]) {
                            const data = envIndicators[indicator.full];
                            const value = parseFloat(data.Values['Production A1-A3']) || 0;
                            unit = data.Unit || '';
                            const shortName = epd.name.length > 35 ? epd.name.substring(0, 35) + '...' : epd.name;
                            labels.push(shortName);
                            values.push(value);
                            fullNames.push(epd.name);
                        }
                    });
                    if (values.length > 0) {
                        const minValue = Math.min(...values);
                        const maxValue = Math.max(...values);
                        const minIndex = values.indexOf(minValue);
                        const maxIndex = values.indexOf(maxValue);
                        const positiveValues = values.filter(v => v > 0);
                        const minPositive = positiveValues.length > 0 ? Math.min(...positiveValues) : 0;
                        const useLogScale = positiveValues.length > 0 && (maxValue / minPositive) > 100;
                        const insightDiv = document.getElementById(`insight${idx}`);
                        const formattedUnit = formatUnit(unit);
                        insightDiv.innerHTML = `<span style="color: #059669; font-weight: 600;">✓ Best: ${fullNames[minIndex]}</span> (${minValue.toFixed(3)} ${formattedUnit}) • <span style="color: #dc2626; font-weight: 600;">✗ Worst: ${fullNames[maxIndex]}</span> (${maxValue.toFixed(3)} ${formattedUnit})${useLogScale ? ' <em style="color: #6b7280; font-weight: 400;">(Log scale)</em>' : ''}`;
                        insightDiv.style.display = 'block';
                        const ctx = document.getElementById(`compareChart${idx}`).getContext('2d');
                        const chart = new Chart(ctx, {
                            type: 'bar',
                            data: {
                                labels: labels,
                                datasets: [{
                                    label: `A1-A3 (${formattedUnit})`,
                                    data: values,
                                    backgroundColor: values.map((v, i) => i === minIndex ? 'rgba(16, 185, 129, 0.8)' : i === maxIndex ? 'rgba(239, 68, 68, 0.8)' : colors[i % colors.length]),
                                    borderWidth: 2
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: true,
                                plugins: {
                                    legend: { display: true, position: 'top' },
                                    tooltip: {
                                        callbacks: {
                                            title: function(context) {
                                                return fullNames[context[0].dataIndex];
                                            },
                                            label: function(context) {
                                                const idx = context.dataIndex;
                                                let prefix = '';
                                                if (idx === minIndex) prefix = '✓ Best: ';
                                                if (idx === maxIndex) prefix = '✗ Worst: ';
                                                return `${prefix}${context.parsed.y.toFixed(3)} ${formattedUnit}`;
                                            }
                                        }
                                    }
                                },
                                scales: {
                                    y: {
                                        type: useLogScale ? 'logarithmic' : 'linear',
                                        beginAtZero: !useLogScale,
                                        title: { display: true, text: formattedUnit }
                                    },
                                    x: {
                                        ticks: { autoSkip: false, maxRotation: 45, minRotation: 45 }
                                    }
                                }
                            }
                        });
                        comparisonCharts.push(chart);
                    }
                } catch (error) {
                    console.error(`Error generating chart ${idx}:`, error);
                }
            });
        }
        
        function closeComparison() {
            document.getElementById('comparisonPanel').style.display = 'none';
        }
        
        function exportSingleChart() {
            if (!currentChart) return;
            const link = document.createElement('a');
            link.download = 'environmental_impact_chart.png';
            link.href = currentChart.toBase64Image();
            link.click();
        }
        
        function exportComparison() {
            if (comparisonCharts.length === 0) return;
            comparisonCharts.forEach((chart, idx) => {
                const link = document.createElement('a');
                link.download = `comparison_chart_${idx + 1}.png`;
                link.href = chart.toBase64Image();
                link.click();
            });
        }
    </script>
</body>
</html>
"""

# Load data code (same as before)
print("Loading data...")
with open(NEW_MATCHING_RESULTS, 'r', encoding='utf-8') as f:
    new_matches = json.load(f)
print(f"✓ {len(new_matches)} matches")

with open(NEW_BIM_MATERIALS, 'r', encoding='utf-8') as f:
    new_bim_materials = json.load(f)
bim_lookup_new = {mat['material_name']: mat for mat in new_bim_materials}
print(f"✓ {len(new_bim_materials)} BIM materials")

with open(NEW_EPD_DATA, 'r', encoding='utf-8') as f:
    new_epd_data = json.load(f)
epd_lookup_new = {epd['uuid']: epd for epd in new_epd_data if epd.get('uuid')}
print(f"✓ {len(new_epd_data)} EPD entries")

if os.path.exists(BIM_COMPLETE_JSON):
    with open(BIM_COMPLETE_JSON, 'r', encoding='utf-8') as f:
        old_bim_materials = json.load(f)
    bim_lookup_old = {}
    for mat in old_bim_materials:
        material_name = mat.get('material_name')
        material_id = mat.get('material_id')
        if material_name:
            bim_lookup_old[material_name] = mat
        if material_id and material_id != material_name:
            bim_lookup_old[material_id] = mat
    print(f"✓ {len(old_bim_materials)} BIM (fallback)")
else:
    bim_lookup_old = {}

matching_records = []
for match in new_matches:
    epd_uuid = match.get('epd_uuid')
    matched_bim = match.get('matched_bim')
    if matched_bim == 'NO_MATCH':
        continue
    epd = epd_lookup_new.get(epd_uuid)
    if not epd:
        continue
    matching_records.append({
        'BIM_Material': matched_bim,
        'EPD_UUID': epd_uuid,
        'EPD_Name': epd.get('name', 'Unknown'),
        'EPD_Filename': epd.get('filename', ''),
        'EPD_Hierarchy_L1': epd.get('main_category', 'N/A'),
        'EPD_Hierarchy_L2': epd.get('subcategory', 'N/A'),
        'EPD_Hierarchy_L3': epd.get('product_type', 'N/A'),
        'EPD_Location': 'Unknown',
        'Match_Score': 1.0,
        'BIM_Category': bim_lookup_new.get(matched_bim, {}).get('primary_category', 'N/A')
    })

matching_df = pd.DataFrame(matching_records)
matching_df['Match_Rank'] = matching_df.groupby('BIM_Material').cumcount() + 1
bim_material_names = sorted(matching_df['BIM_Material'].unique().tolist())
print(f"✓ {len(matching_df)} records, {len(bim_material_names)} materials")

# Diagnostic: Check BIM data availability
print("\n🔍 BIM Data Diagnostic:")
sample_materials = bim_material_names[:3] if len(bim_material_names) >= 3 else bim_material_names
for mat in sample_materials:
    in_new = mat in bim_lookup_new
    in_old = mat in bim_lookup_old if bim_lookup_old else False
    status = "✓" if (in_new or in_old) else "✗"
    print(f"  {status} '{mat}' - New: {in_new}, Old: {in_old}")

if bim_lookup_new:
    print(f"\n📦 New BIM Data Sample Fields:")
    sample_bim = list(bim_lookup_new.values())[0]
    print(f"  Fields: {list(sample_bim.keys())[:8]}")
    
if bim_lookup_old:
    print(f"\n📦 Old BIM Data Sample Fields:")
    sample_bim = list(bim_lookup_old.values())[0]
    print(f"  Fields: {list(sample_bim.keys())[:8]}")

print()  # Empty line

# Routes (same as before)
@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    if not query or len(query) < 2:
        return jsonify([])
    matches = [name for name in bim_material_names if query in name.lower()]
    return jsonify(matches[:20])

@app.route('/api/matches/<path:material_name>')
def get_matches(material_name):
    matches = matching_df[matching_df['BIM_Material'] == material_name].copy()
    if len(matches) == 0:
        return jsonify({'error': 'Material not found'}), 404
    matches = matches.sort_values('Match_Rank')
    results = []
    for _, row in matches.iterrows():
        results.append({
            'rank': int(row['Match_Rank']),
            'epd_name': row['EPD_Name'],
            'epd_uuid': row['EPD_UUID'],
            'epd_filename': row['EPD_Filename'],
            'score': float(row['Match_Score']),
            'hierarchy_l1': row['EPD_Hierarchy_L1'],
            'hierarchy_l2': row['EPD_Hierarchy_L2'],
            'hierarchy_l3': row['EPD_Hierarchy_L3'],
            'location': row['EPD_Location']
        })
    return jsonify(results)

@app.route('/api/details')
def get_details():
    bim_name = request.args.get('bim')
    epd_uuid = request.args.get('epd')
    
    if not bim_name or not epd_uuid:
        return jsonify({'error': 'Missing parameters'}), 400
    
    # Try to get BIM data from new lookup first
    bim_data = bim_lookup_new.get(bim_name)
    
    # If not found, try old lookup
    if not bim_data and bim_lookup_old:
        bim_data = bim_lookup_old.get(bim_name)
        if bim_data:
            print(f"✓ Found BIM data in old lookup for: {bim_name}")
    
    # If still not found, try to find by ID in old lookup
    if not bim_data and bim_lookup_old:
        # Try searching with cleaned name (remove numbers, special chars)
        cleaned_name = bim_name.strip()
        for key in bim_lookup_old.keys():
            if key.lower() == cleaned_name.lower():
                bim_data = bim_lookup_old[key]
                print(f"✓ Found BIM data with case-insensitive match: {key}")
                break
    
    if not bim_data:
        print(f"⚠️  BIM data not found for: '{bim_name}'")
        print(f"   Available in new lookup: {bim_name in bim_lookup_new}")
        print(f"   Available in old lookup: {bim_name in bim_lookup_old if bim_lookup_old else False}")
        # Create minimal BIM data from matching record
        match_row = matching_df[matching_df['BIM_Material'] == bim_name]
        if len(match_row) > 0:
            row = match_row.iloc[0]
            bim_data = {
                'material_name': bim_name,
                'primary_category': row['BIM_Category'],
                'secondary_category': 'N/A',
                'description': f'BIM Material: {bim_name}',
                'rdfs_comment': 'Detailed information not available'
            }
            print(f"   Created minimal BIM data from matching record")
    
    epd = epd_lookup_new.get(epd_uuid)
    if not epd:
        return jsonify({'error': 'EPD not found'}), 404
    
    match_row = matching_df[(matching_df['BIM_Material'] == bim_name) & (matching_df['EPD_UUID'] == epd_uuid)]
    if len(match_row) == 0:
        return jsonify({'error': 'Match not found'}), 404
    
    row = match_row.iloc[0]
    
    epd_summary = {
        'product_name': epd.get('name', 'N/A'),
        'hierarchy_l1': epd.get('main_category', 'N/A'),
        'hierarchy_l2': epd.get('subcategory', 'N/A'),
        'hierarchy_l3': epd.get('product_type', 'N/A'),
        'product_location': 'Unknown',
        'filename': epd.get('filename', ''),
        'manufacturer_name': 'N/A',
        'technical_purpose': epd.get('technical_purpose', 'N/A')
    }
    
    match_info = {
        'rank': int(row['Match_Rank']),
        'score': float(row['Match_Score']),
        'bim_category': row['BIM_Category']
    }
    
    original_epd = None
    filename = epd.get('filename', '')
    if filename:
        epd_json_path = os.path.join(EPD_JSON_FOLDER, filename)
        if os.path.exists(epd_json_path):
            try:
                with open(epd_json_path, 'r', encoding='utf-8') as f:
                    original_epd = json.load(f)
            except Exception as e:
                print(f"Error loading EPD JSON: {e}")
    
    return jsonify({
        'bim': bim_data,
        'epd_summary': epd_summary,
        'epd_original': original_epd,
        'match_info': match_info
    })

@app.route('/api/compare', methods=['POST'])
def compare_epds():
    epd_uuids = request.json.get('epd_uuids', [])
    if not epd_uuids or len(epd_uuids) < 2:
        return jsonify({'error': 'At least 2 EPDs required'}), 400
    comparison_data = []
    for epd_uuid in epd_uuids:
        epd = epd_lookup_new.get(epd_uuid)
        if not epd:
            continue
        original_epd = None
        filename = epd.get('filename', '')
        if filename:
            epd_json_path = os.path.join(EPD_JSON_FOLDER, filename)
            if os.path.exists(epd_json_path):
                try:
                    with open(epd_json_path, 'r', encoding='utf-8') as f:
                        original_epd = json.load(f)
                except Exception as e:
                    print(f"Error: {e}")
        comparison_data.append({
            'uuid': epd_uuid,
            'filename': filename,
            'name': epd.get('name', 'Unknown'),
            'data': original_epd
        })
    return jsonify(comparison_data)

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🏗️  BIM-EPD Material Matcher - FINAL")
    print("=" * 70)
    print(f"\n📊 {len(matching_df):,} matches | {len(bim_material_names)} materials")
    print(f"\n🌐 http://localhost:5001")
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=5001)