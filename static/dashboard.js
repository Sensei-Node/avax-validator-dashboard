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
                
                // Handle case where details might be a string
                if (typeof details === 'string') {
                    content += `
                        <div class='validator'>
                            <div class='validator-header'>
                                <p class='validator-id'><a href='https://avascan.info/staking/validator/${nodeId}' target='_blank'>${nodeId}</a></p>
                            </div>
                            <div class='validator-body'>
                                <div class='validator-detail'>
                                    <span>Status: ${details}</span>
                                </div>
                            </div>
                        </div>`;
                    return;
                }
                
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
            showError("Failed to fetch validator data. Please try again.");
            
            // If we have no data yet, show sample data as fallback
            if ($("#validators").children().length === 0) {
                const fallbackData = {
                    "NodeID-F3SZA2ZNdRjTBe3GYyRQFDaCXB3DyaZQQ": {
                        "name": "Sample Validator 1",
                        "location": "New York, USA",
                        "uptime": 99.8,
                        "stake_from_self": 2000,
                        "stake_from_delegations": 5000
                    },
                    "NodeID-C6MR4QwFVyf7vxttwLFbxopJrD5ce4Mwv": {
                        "name": "Sample Validator 2",
                        "location": "London, UK",
                        "uptime": 98.5,
                        "stake_from_self": 1500,
                        "stake_from_delegations": 3500
                    }
                };
                
                let fallbackContent = "";
                Object.keys(fallbackData).forEach(function(nodeId) {
                    let details = fallbackData[nodeId];
                    fallbackContent += `
                        <div class='validator'>
                            <div class='validator-header'>
                                <p class='validator-id'><a href='https://avascan.info/staking/validator/${nodeId}' target='_blank'>${nodeId}</a> (SAMPLE DATA)</p>
                            </div>
                            <div class='validator-body'>
                                <div class='validator-detail'>
                                    <span class='detail-label'>Location:</span>
                                    <span>${details.location}</span>
                                </div>
                                <div class='validator-detail'>
                                    <span class='detail-label'>Uptime:</span>
                                    <span class='${getUptimeClass(details.uptime)}'>${details.uptime}%</span>
                                </div>
                                <div class='validator-detail'>
                                    <span class='detail-label'>Stake from Self:</span>
                                    <span>${formatNumber(details.stake_from_self)} AVAX</span>
                                </div>
                                <div class='validator-detail'>
                                    <span class='detail-label'>Stake from Delegations:</span>
                                    <span>${formatNumber(details.stake_from_delegations)} AVAX</span>
                                </div>
                                <div class='validator-detail total-stake'>
                                    <span class='detail-label'>Total Stake:</span>
                                    <span>${formatNumber(details.stake_from_self + details.stake_from_delegations)} AVAX</span>
                                </div>
                            </div>
                        </div>`;
                });
                
                $("#validators").html(fallbackContent);
                $("#error-container").append(
                    "<div class='error-message' style='background-color: #fff3cd; color: #856404;'>" +
                    "Showing sample data. The actual data could not be loaded.</div>"
                );
            }
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
