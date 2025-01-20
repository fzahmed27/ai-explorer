class SearchHistory {
    constructor() {
        this.storageKey = 'wikiSearchHistory';
        this.maxHistory = 10;
    }

    // Get all search history
    getHistory() {
        const history = localStorage.getItem(this.storageKey);
        return history ? JSON.parse(history) : [];
    }

    // Add new search to history
    addToHistory(query, summary) {
        const history = this.getHistory();
        const timestamp = new Date().toISOString();
        
        // Add new search at the beginning
        history.unshift({
            id: Date.now(),
            query,
            summary,
            timestamp
        });

        // Keep only the latest searches
        const updatedHistory = history.slice(0, this.maxHistory);
        
        localStorage.setItem(this.storageKey, JSON.stringify(updatedHistory));
        this.updateHistoryUI();
    }

    // Delete specific search from history
    deleteFromHistory(id) {
        const history = this.getHistory();
        const updatedHistory = history.filter(item => item.id !== id);
        localStorage.setItem(this.storageKey, JSON.stringify(updatedHistory));
        this.updateHistoryUI();
    }

    // Clear all search history
    clearHistory() {
        localStorage.removeItem(this.storageKey);
        this.updateHistoryUI();
    }

    // Format date for display
    formatDate(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        };
        return new Date(dateString).toLocaleDateString(undefined, options);
    }

    // Update the history UI
    updateHistoryUI() {
        const historyContainer = document.getElementById('searchHistory');
        const history = this.getHistory();

        if (history.length === 0) {
            historyContainer.innerHTML = '<p class="text-muted text-center">No search history</p>';
            return;
        }

        const historyHTML = history.map(item => `
            <div class="history-item">
                <div class="history-content">
                    <h4 class="history-query">${item.query}</h4>
                    <small class="text-muted">${this.formatDate(item.timestamp)}</small>
                    <p class="history-summary">${item.summary.substring(0, 150)}...</p>
                </div>
                <div class="history-actions">
                    <button class="btn btn-sm btn-outline-primary" onclick="searchHistory.rerunSearch('${item.query}')">
                        <i class="fas fa-redo"></i> Search Again
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="searchHistory.deleteFromHistory(${item.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');

        historyContainer.innerHTML = `
            <div class="history-header">
                <h3>Search History</h3>
                <button class="btn btn-danger btn-sm" onclick="searchHistory.clearHistory()">
                    <i class="fas fa-trash-alt"></i> Clear All
                </button>
            </div>
            ${historyHTML}
        `;
    }

    // Rerun a previous search
    rerunSearch(query) {
        document.getElementById('query').value = query;
        document.getElementById('searchForm').dispatchEvent(new Event('submit'));
    }
} 