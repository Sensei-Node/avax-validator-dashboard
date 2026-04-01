const DEFAULT_REFRESH_INTERVAL_MS = 600000; // 10 minutes
const UPTIME_THRESHOLD_HIGH = 95; // Uptime >= UPTIME_THRESHOLD_HIGH% is considered high
const UPTIME_THRESHOLD_MEDIUM = 90; // Uptime >= UPTIME_THRESHOLD_MEDIUM% is considered medium

let isLoading = true;

function formatNumber(num) {
    return parseFloat(num).toLocaleString();
}

function getUptimeClass(uptime) {
    if (uptime >= UPTIME_THRESHOLD_HIGH) return 'uptime-high';
    if (uptime >= UPTIME_THRESHOLD_MEDIUM) return 'uptime-medium';
    return 'uptime-low';
}

function setLoading(loading) {
    isLoading = loading;
    if (loading) {
        $("#loading").show();
        $("#validators").hide();
    } else {
        $("#loading").hide();
        $("#validators").show();
    }
}

function showError(message) {
    $("#error-container").html(`<div class="error-message">${message}</div>`);
}

function clearError() {
    $("#error-container").empty();
}

function fetchData() {
    setLoading(true);
    clearError();
    
    // Use a relative path to avoid issues
    const dataUrl = window.location.pathname.endsWith('/') ? 'data' : '/data';
    
    $.ajax({
        url: dataUrl,
        type: "GET",
        dataType: "json",
        success: function(data) {
            let content = "";
            
            if (!data || Object.keys(data).length === 0) {
                showError("No validator data available.");
                setLoading(false);
                return;
            }
            
            Object.keys(data).forEach(function(nodeId) {
                let details = data[nodeId];
                
                // Calculate total stake - ensure values are numbers
                const selfStake = parseFloat(details.stake_from_self) || 0;
                const delegationStake = parseFloat(details.stake_from_delegations) || 0;
                const totalStake = selfStake + delegationStake;
                
                content += `
                    <div class='validator'>
                        <div class='validator-header'>
                            <p class='validator-id'><a href='https://avascan.info/staking/validator/${nodeId}' target='_blank'>${nodeId}</a></p>
                        </div>
                        <div class='validator-body'>
                            <div class='validator-detail'>
                                <span class='detail-label'>Location:</span>
                                <span>${details.location || 'Unknown'}</span>
                            </div>
                            <div class='validator-detail'>
                                <span class='detail-label'>Uptime:</span>
                                <span class='${getUptimeClass(details.uptime)}'>${details.uptime}%</span>
                            </div>
                            <div class='validator-detail'>
                                <span class='detail-label'>Expiration Date:</span>
                                <span>${details.expiration_date || 'Unknown'}</span>
                            </div>
                            <div class='validator-detail'>
                                <span class='detail-label'>Stake from Self:</span>
                                <span>${formatNumber(selfStake)} AVAX</span>
                            </div>
                            <div class='validator-detail'>
                                <span class='detail-label'>Stake from Delegations:</span>
                                <span>${formatNumber(delegationStake)} AVAX</span>
                            </div>
                            <div class='validator-detail total-stake'>
                                <span class='detail-label'>Total Stake:</span>
                                <span>${formatNumber(totalStake)} AVAX</span>
                            </div>
                        </div>
                    </div>`;
            });
            
            $("#validators").html(content);
        },
        error: function(xhr, status, error) {
            console.error("Error details:", xhr, status, error);
            showError("API Error: Unable to fetch latest validator data.");
        },
        complete: function() {
            setLoading(false);
        }
    });
}

$(document).ready(function() {
    fetchData();
    
    $.ajax({
        url: window.location.pathname.endsWith('/') ? 'config' : '/config',
        type: "GET",
        dataType: "json",
        success: function(config) {
            const refreshInterval = config.refresh_interval_ms || DEFAULT_REFRESH_INTERVAL_MS;
            setInterval(fetchData, refreshInterval);
        },
        error: function() {
            // Fallback to default if config fetch fails
            setInterval(fetchData, DEFAULT_REFRESH_INTERVAL_MS);
        }
    });
});
