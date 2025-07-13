// TCAP v2 - Crypto Trading Analysis Platform
// Main JavaScript functionality

class TCAPApp {
    constructor() {
        this.cryptoData = [];
        this.alerts = new Map();
        this.isLoading = false;
        this.lastUpdate = null;
        this.continuousMode = true;  // Enable continuous monitoring
        this.autoRefreshInterval = null;
        this.sessionInterval = null;
        this.sessionStartTime = new Date();
        this.filters = {
            minGain: 1,  // Lowered from 10% to 1% to see more data
            minVolume: 1,  // Lowered from $10M to $1M to see more pairs
            sortBy: 'gain'
        };
        
        this.init();
    }

    async init() {
        // Hide loading overlay initially
        this.hideLoading();
        
        this.setupEventListeners();
        this.requestNotificationPermission();
        
        // Load initial filter values from backend
        await this.loadInitialFilters();
        
        this.startContinuousMonitoring();
        
        // Start continuous data fetching every 15 seconds
        this.startAutoRefresh();
        
        // Start session time tracking
        this.startSessionTimer();
        
        // Load server startup time
        this.loadServerStartupTime();
        
        // Update server startup time display every 5 minutes
        this.startServerTimeUpdater();
    }

    setupEventListeners() {
        // Refresh button - now forces immediate update with loading overlay
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadLiveData(true); // Show loading overlay for manual refresh
        });

        // Filter inputs
        document.getElementById('minGain').addEventListener('input', (e) => {
            const oldMinGain = this.filters.minGain;
            const newMinGain = parseFloat(e.target.value) || 0;
            
            console.log(`🔄 Min Gain changed: ${oldMinGain}% → ${newMinGain}%`);
            
            this.filters.minGain = newMinGain;
            this.updateBackendFilters();
            this.filterAndDisplayData();
            
            // Auto-reset first hits if threshold changed significantly (more than 0.5%)
            if (Math.abs(oldMinGain - newMinGain) > 0.5) {
                console.log(`🔄 Threshold changed significantly (${oldMinGain}% → ${newMinGain}%), auto-resetting first hits`);
                this.resetFirstHits();
            }
        });

        document.getElementById('minVolume').addEventListener('input', (e) => {
            const oldMinVolume = this.filters.minVolume;
            const newMinVolume = parseFloat(e.target.value) || 0;
            
            console.log(`🔄 Min Volume changed: $${oldMinVolume}M → $${newMinVolume}M`);
            
            this.filters.minVolume = newMinVolume;
            this.updateBackendFilters();
            this.filterAndDisplayData();
        });

        document.getElementById('sortBy').addEventListener('change', (e) => {
            this.filters.sortBy = e.target.value;
            this.filterAndDisplayData();
        });

        // Export button
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportToCSV();
        });

        // First hits reset button
        document.getElementById('resetFirstHits').addEventListener('click', () => {
            this.resetFirstHits();
        });

        // Sync filters button
        document.getElementById('syncFiltersBtn').addEventListener('click', () => {
            this.manualSyncFilters();
        });

        // Modal events
        document.getElementById('closeModal').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('cancelAlert').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('saveAlert').addEventListener('click', () => {
            this.saveAlert();
        });

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('alertModal');
            if (e.target === modal) {
                this.closeModal();
            }
        });
    }

    async requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            await Notification.requestPermission();
        }
    }

    showLoading() {
        this.isLoading = true;
        document.getElementById('loadingOverlay').classList.remove('hidden');
        document.getElementById('statusText').textContent = 'Loading...';
        document.getElementById('statusDot').classList.remove('connected');
    }

    hideLoading() {
        this.isLoading = false;
        document.getElementById('loadingOverlay').classList.add('hidden');
        document.getElementById('statusText').textContent = 'Connected';
        document.getElementById('statusDot').classList.add('connected');
    }

    async startContinuousMonitoring() {
        try {
            // Start backend continuous monitoring
            await this.fetchFromBackend('/api/monitoring/start');
            console.log('✅ Continuous monitoring started on backend');
        } catch (error) {
            console.warn('⚠️ Could not start backend monitoring, using manual refresh');
            this.continuousMode = false;
        }
    }

    startAutoRefresh() {
        // Clear any existing interval
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }

        // Initial load without loading overlay
        this.loadLiveData(false);

        // Set up continuous refresh every 15 seconds (no loading overlay)
        this.autoRefreshInterval = setInterval(() => {
            if (!this.isLoading) {
                this.loadLiveData(false); // No loading overlay for auto-refresh
            }
        }, 15000);

        console.log('🔄 Auto-refresh started (every 15 seconds)');
    }

    async loadLiveData(showLoading = false) {
        // Only show loading overlay if explicitly requested (manual refresh)
        if (showLoading) {
            this.showLoading();
        } else {
            // Show subtle update indicator in status for background updates
            document.getElementById('statusText').textContent = 'Updating...';
        }
        
        this.isLoading = true;
        
        try {
            const params = new URLSearchParams({
                min_gain: this.filters.minGain,
                min_volume: this.filters.minVolume
            });

            const response = this.continuousMode 
                ? await this.fetchFromBackend(`/api/live-data?${params}`)
                : await this.fetchFromBackend(`/api/top-movers?${params}&max_results=100`);
            
            this.cryptoData = response.data || [];

            // Update status 
            document.getElementById('statusText').textContent = 
                this.continuousMode ? 'Live Monitoring' : 'Connected';
            document.getElementById('statusDot').classList.add('connected');

            this.lastUpdate = new Date();
            this.updateStats();
            this.filterAndDisplayData();
            this.checkAlerts();
            
            // Load first hits data
            this.loadFirstHits();
            
        } catch (error) {
            console.error('Error loading live data:', error);
            document.getElementById('statusText').textContent = 'Connection Error';
            
            // Fall back to demo data only if we have no data at all
            if (this.cryptoData.length === 0) {
                this.loadDemoData();
            }
        } finally {
            this.isLoading = false;
            if (showLoading) {
                this.hideLoading();
            }
        }
    }

    async fetchFromBackend(endpoint) {
        const baseUrl = 'http://localhost:5000';
        try {
            const response = await fetch(`${baseUrl}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Backend API error:', error);
            throw error;
        }
    }

    async updateBackendFilters() {
        /**
         * Send updated filter parameters to backend for continuous monitoring
         */
        try {
            const filterData = {
                min_gain: this.filters.minGain,
                min_volume: this.filters.minVolume
            };

            console.log('🔄 Sending filter update to backend:', filterData);

            const response = await fetch('http://localhost:5000/api/monitoring/filters', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(filterData)
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Backend filters updated successfully:', result.current_filters);
                
                // Show visual confirmation
                this.showNotification(`Filters updated: ${filterData.min_gain}% gain, $${filterData.min_volume}M volume`, 'success');
            } else {
                console.error('❌ Failed to update backend filters. Status:', response.status);
                const errorText = await response.text();
                console.error('Error details:', errorText);
                this.showNotification('Failed to update backend filters', 'error');
            }
        } catch (error) {
            console.error('❌ Could not update backend filters:', error);
            this.showNotification('Network error updating filters', 'error');
        }
    }

    async loadInitialFilters() {
        /**
         * Load initial filter values from backend and update UI (only if not already set by user)
         */
        try {
            const response = await this.fetchFromBackend('/api/monitoring/filters');
            if (response && response.current_filters) {
                // Only update if the UI inputs are still at default values
                const currentMinGain = parseFloat(document.getElementById('minGain').value);
                const currentMinVolume = parseFloat(document.getElementById('minVolume').value);
                
                // Only override if user hasn't changed from defaults
                if (currentMinGain === 1 && currentMinVolume === 1) {
                    this.filters.minGain = response.current_filters.min_gain;
                    this.filters.minVolume = response.current_filters.min_volume;
                    
                    // Update UI inputs to match backend values
                    document.getElementById('minGain').value = this.filters.minGain;
                    document.getElementById('minVolume').value = this.filters.minVolume;
                    
                    console.log('✅ Loaded initial filters from backend:', response.current_filters);
                } else {
                    console.log('🔧 User has custom filter values, keeping current settings');
                    // Send current user values to backend instead
                    this.filters.minGain = currentMinGain;
                    this.filters.minVolume = currentMinVolume;
                    this.updateBackendFilters();
                }
            }
        } catch (error) {
            console.warn('⚠️ Could not load initial filters from backend, using current values');
            // Ensure UI matches internal values
            document.getElementById('minGain').value = this.filters.minGain;
            document.getElementById('minVolume').value = this.filters.minVolume;
        }
    }

    loadDemoData() {
        // Demo data for testing the interface
        this.cryptoData = [
            {
                symbol: 'BTCUSDT',
                currentPrice: 45250.50,
                price1hAgo: 43800.00,
                gainPct: 3.31,
                volume24h: 1250000000,
                timestamp: Date.now()
            },
            {
                symbol: 'ETHUSDT',
                currentPrice: 3125.75,
                price1hAgo: 2850.25,
                gainPct: 9.66,
                volume24h: 850000000,
                timestamp: Date.now()
            },
            {
                symbol: 'ADAUSDT',
                currentPrice: 0.8945,
                price1hAgo: 0.7650,
                gainPct: 16.93,
                volume24h: 125000000,
                timestamp: Date.now()
            },
            {
                symbol: 'SOLUSDT',
                currentPrice: 185.40,
                price1hAgo: 162.30,
                gainPct: 14.23,
                volume24h: 275000000,
                timestamp: Date.now()
            },
            {
                symbol: 'DOTUSDT',
                currentPrice: 8.75,
                price1hAgo: 7.45,
                gainPct: 17.45,
                volume24h: 89000000,
                timestamp: Date.now()
            },
            {
                symbol: 'LINKUSDT',
                currentPrice: 18.95,
                price1hAgo: 16.80,
                gainPct: 12.80,
                volume24h: 145000000,
                timestamp: Date.now()
            },
            {
                symbol: 'AVAXUSDT',
                currentPrice: 42.15,
                price1hAgo: 35.90,
                gainPct: 17.41,
                volume24h: 95000000,
                timestamp: Date.now()
            }
        ];

        this.lastUpdate = new Date();
        this.updateStats();
        this.filterAndDisplayData();
    }

    filterAndDisplayData() {
        // When using backend data, it's already filtered, but we can apply additional client-side filtering
        let filteredData = this.cryptoData.filter(item => {
            const meetsGainCriteria = item.gain_pct >= this.filters.minGain;
            const meetsVolumeCriteria = (item.volume_24h / 1000000) >= this.filters.minVolume;
            return meetsGainCriteria && meetsVolumeCriteria;
        });

        // Sort data
        filteredData.sort((a, b) => {
            switch (this.filters.sortBy) {
                case 'gain':
                    return (b.gain_pct || b.gainPct) - (a.gain_pct || a.gainPct);
                case 'volume':
                    return (b.volume_24h || b.volume24h) - (a.volume_24h || a.volume24h);
                case 'symbol':
                    return a.symbol.localeCompare(b.symbol);
                default:
                    return (b.gain_pct || b.gainPct) - (a.gain_pct || a.gainPct);
            }
        });

        this.displayData(filteredData);
        this.updateLastUpdateTime();
    }

    displayData(data) {
        const tableBody = document.getElementById('tableBody');
        
        if (data.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center" style="padding: 40px;">
                        <i class="fas fa-search" style="font-size: 48px; color: #9ca3af; margin-bottom: 16px;"></i>
                        <p style="color: #6b7280; font-size: 18px;">No coins match your current criteria</p>
                        <p style="color: #9ca3af; font-size: 14px;">Try adjusting your filters</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = data.map(item => {
            // Handle both backend and demo data formats
            const gainPct = item.gain_pct || item.gainPct;
            const currentPrice = item.current_price || item.currentPrice;
            const price1hAgo = item.price_1h_ago || item.price1hAgo;
            const volume24h = item.volume_24h || item.volume24h;
            
            const gainClass = gainPct >= 0 ? 'gain-positive' : 'gain-negative';
            const gainIcon = gainPct >= 0 ? '↗' : '↘';
            
            return `
                <tr class="fade-in">
                    <td class="symbol-cell">${item.symbol}</td>
                    <td class="price-cell">$${this.formatPrice(currentPrice)}</td>
                    <td class="price-cell">$${this.formatPrice(price1hAgo)}</td>
                    <td class="${gainClass}">
                        ${gainIcon} ${gainPct.toFixed(2)}%
                    </td>
                    <td class="volume-cell">$${this.formatVolume(volume24h)}</td>
                    <td>
                        <button class="action-btn" onclick="tcapApp.showAlertModal('${item.symbol}')">
                            <i class="fas fa-bell"></i> Alert
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    updateStats() {
        const totalPairs = this.cryptoData.length;
        const topMovers = this.cryptoData.filter(item => {
            const gainPct = item.gain_pct || item.gainPct;
            return gainPct >= this.filters.minGain;
        }).length;
        const highVolume = this.cryptoData.filter(item => {
            const volume = item.volume_24h || item.volume24h;
            return (volume / 1000000) >= this.filters.minVolume;
        }).length;
        const activeAlerts = this.alerts.size;

        document.getElementById('totalPairs').textContent = totalPairs;
        document.getElementById('topMovers').textContent = topMovers;
        document.getElementById('highVolume').textContent = highVolume;
        document.getElementById('alerts').textContent = activeAlerts;
    }

    updateLastUpdateTime() {
        if (this.lastUpdate) {
            document.getElementById('lastUpdate').textContent = this.lastUpdate.toLocaleTimeString();
        }
    }

    formatPrice(price) {
        if (price >= 1) {
            return price.toLocaleString('en-US', { 
                minimumFractionDigits: 2, 
                maximumFractionDigits: 2 
            });
        } else {
            return price.toFixed(6);
        }
    }

    formatVolume(volume) {
        if (volume >= 1000000000) {
            return (volume / 1000000000).toFixed(2) + 'B';
        } else if (volume >= 1000000) {
            return (volume / 1000000).toFixed(1) + 'M';
        } else if (volume >= 1000) {
            return (volume / 1000).toFixed(1) + 'K';
        } else {
            return volume.toFixed(0);
        }
    }

    showAlertModal(symbol) {
        document.getElementById('alertSymbol').textContent = symbol;
        document.getElementById('alertModal').style.display = 'block';
    }

    closeModal() {
        document.getElementById('alertModal').style.display = 'none';
    }

    saveAlert() {
        const symbol = document.getElementById('alertSymbol').textContent;
        const threshold = parseFloat(document.getElementById('alertThreshold').value);
        const method = document.getElementById('alertMethod').value;

        this.alerts.set(symbol, { threshold, method });
        
        this.showNotification(
            'Alert Set',
            `Alert set for ${symbol} when gain exceeds ${threshold}%`
        );
        
        this.closeModal();
        this.updateStats();
    }

    checkAlerts() {
        this.alerts.forEach((alert, symbol) => {
            const coinData = this.cryptoData.find(item => item.symbol === symbol);
            if (coinData && coinData.gainPct >= alert.threshold) {
                this.triggerAlert(symbol, coinData.gainPct, alert);
            }
        });
    }

    triggerAlert(symbol, gainPct, alert) {
        const message = `🚀 ${symbol} is up ${gainPct.toFixed(2)}%! Alert threshold of ${alert.threshold}% exceeded.`;
        
        if (alert.method === 'browser') {
            this.showNotification(`TCAP Alert: ${symbol}`, message);
        }
        
        // Add visual indicator to the table row
        const rows = document.querySelectorAll('#tableBody tr');
        rows.forEach(row => {
            if (row.cells[0]?.textContent === symbol) {
                row.style.background = 'linear-gradient(90deg, rgba(34, 197, 94, 0.1), rgba(255, 255, 255, 0.1))';
                row.style.border = '2px solid #22c55e';
            }
        });
    }

    showNotification(title, message) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/favicon.ico',
                badge: '/favicon.ico'
            });
        } else {
            // Fallback to browser alert
            alert(`${title}\n${message}`);
        }
    }

    showError(message) {
        console.error(message);
        // You could implement a toast notification system here
    }

    exportToCSV() {
        const filteredData = this.cryptoData.filter(item => {
            const meetsGainCriteria = item.gainPct >= this.filters.minGain;
            const meetsVolumeCriteria = (item.volume24h / 1000000) >= this.filters.minVolume;
            return meetsGainCriteria && meetsVolumeCriteria;
        });

        if (filteredData.length === 0) {
            alert('No data to export');
            return;
        }

        const headers = ['Symbol', '1h Ago Price', 'Current Price', '% Gain', '24h Volume'];
        const csvContent = [
            headers.join(','),
            ...filteredData.map(item => [
                item.symbol,
                item.price1hAgo.toFixed(6),
                item.currentPrice.toFixed(6),
                item.gainPct.toFixed(2),
                item.volume24h.toFixed(0)
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `tcap-data-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    // First Hits Functionality
    startSessionTimer() {
        this.sessionInterval = setInterval(() => {
            this.updateSessionTime();
        }, 1000); // Update every second
        this.updateSessionTime(); // Initial update
    }

    updateSessionTime() {
        const now = new Date();
        const diffMs = now - this.sessionStartTime;
        const diffMins = Math.floor(diffMs / 60000);
        const diffSecs = Math.floor((diffMs % 60000) / 1000);
        
        document.getElementById('sessionTime').textContent = 
            diffMins > 0 ? `Session: ${diffMins}m ${diffSecs}s` : `Session: ${diffSecs}s`;
    }

    async loadFirstHits() {
        try {
            const response = await fetch('http://localhost:5000/api/first-hits');
            const result = await response.json();
            
            if (result.success) {
                this.displayFirstHits(result.data.leaderboard || []);
                
                // Update threshold display
                if (result.data.current_threshold !== undefined) {
                    document.getElementById('currentThreshold').textContent = 
                        `Threshold: ${result.data.current_threshold}%`;
                    
                    // Update the title to show current threshold
                    document.getElementById('firstHitsTitle').textContent = 
                        `First to Hit ${result.data.current_threshold}% - Leaderboard`;
                }
                
                // Update session start time if available from backend
                if (result.session_start || result.data.session_start) {
                    this.sessionStartTime = new Date(result.session_start || result.data.session_start);
                }
            }
        } catch (error) {
            console.warn('First hits data not available:', error.message);
        }
    }

    displayFirstHits(firstHits) {
        const container = document.getElementById('firstHitsContainer');
        const currentThreshold = this.filters.minGain;
        
        if (!firstHits || firstHits.length === 0) {
            container.innerHTML = `
                <div class="first-hits-empty">
                    <i class="fas fa-clock"></i>
                    <p>Waiting for first hits...</p>
                    <small>The first coins to hit ${currentThreshold}% gain will appear here</small>
                </div>
            `;
            return;
        }

        const firstHitsHTML = firstHits.map((hit, index) => {
            const usedThreshold = hit.threshold_used !== undefined ? hit.threshold_used : currentThreshold;
            const hitGain = hit.first_hit_gain !== undefined ? hit.first_hit_gain : hit.gain_pct || 0;
            const hitVolume = hit.volume !== undefined ? hit.volume : hit.volume_24h || 0;
            const hitTime = hit.first_hit_time || hit.timestamp;
            
            return `
                <div class="first-hit-card">
                    <div class="first-hit-rank">${index + 1}</div>
                    <div class="first-hit-symbol">${hit.symbol}</div>
                    <div class="first-hit-details">
                        <span class="first-hit-gain">+${hitGain.toFixed(2)}%</span>
                        <span class="first-hit-volume">$${(hitVolume / 1000000).toFixed(1)}M</span>
                    </div>
                    <div class="first-hit-time">
                        First hit: ${this.formatTime(hitTime)}
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="first-hits-grid">${firstHitsHTML}</div>`;
    }

    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) {
            return 'Just now';
        } else if (diffMins < 60) {
            return `${diffMins}m ago`;
        } else {
            const diffHours = Math.floor(diffMins / 60);
            return `${diffHours}h ${diffMins % 60}m ago`;
        }
    }

    async resetFirstHits() {
        try {
            const response = await fetch('http://localhost:5000/api/first-hits/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reset local session timer
                this.sessionStartTime = new Date(result.session_start);
                this.updateSessionTime();
                
                // Clear first hits display
                this.displayFirstHits([]);
                
                // Show success notification
                this.showNotification('First hits tracking has been reset', 'success');
            }
        } catch (error) {
            console.error('Error resetting first hits:', error);
            this.showNotification('Failed to reset first hits', 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Create a simple notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    async loadServerStartupTime() {
        /**
         * Load server startup time from backend health check
         */
        try {
            const response = await this.fetchFromBackend('/api/health');
            if (response && response.server_startup_time) {
                const startupTime = new Date(response.server_startup_time);
                const formattedTime = this.formatServerTime(startupTime);
                document.getElementById('serverStartupTime').textContent = `Server: ${formattedTime}`;
                
                // Also update the table area server info
                const uptimeInfo = document.getElementById('serverUptimeInfo');
                if (uptimeInfo) {
                    uptimeInfo.textContent = `Server started: ${formattedTime}`;
                }
                
                console.log('✅ Server started at:', formattedTime);
            }
        } catch (error) {
            console.warn('⚠️ Could not load server startup time');
            document.getElementById('serverStartupTime').textContent = 'Server: Unknown';
        }
    }

    formatServerTime(date) {
        /**
         * Format server startup time for display
         */
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        // Show relative time for recent startups
        if (diffMins < 1) {
            return 'Just started';
        } else if (diffMins < 60) {
            return `${diffMins}m ago`;
        } else if (diffHours < 24) {
            return `${diffHours}h ${diffMins % 60}m ago`;
        } else if (diffDays < 7) {
            return `${diffDays}d ${diffHours % 24}h ago`;
        } else {
            // Show actual time for older startups
            return date.toLocaleString();
        }
    }

    startServerTimeUpdater() {
        /**
         * Update server startup time display every 5 minutes
         */
        setInterval(() => {
            this.loadServerStartupTime();
        }, 5 * 60 * 1000); // 5 minutes
    }

    manualSyncFilters() {
        /**
         * Manually sync current filter values from UI to backend
         */
        console.log('🔧 Manual filter sync triggered');
        
        // Get current values from UI
        const minGain = parseFloat(document.getElementById('minGain').value) || 1;
        const minVolume = parseFloat(document.getElementById('minVolume').value) || 1;
        
        // Update internal values
        this.filters.minGain = minGain;
        this.filters.minVolume = minVolume;
        
        console.log(`🔧 Syncing filters: Min Gain ${minGain}%, Min Volume $${minVolume}M`);
        
        // Force send to backend
        this.updateBackendFilters();
        
        // Also trigger data refresh
        this.loadLiveData(false);
    }
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.tcapApp = new TCAPApp();
});

// Service Worker Registration for PWA capabilities (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
