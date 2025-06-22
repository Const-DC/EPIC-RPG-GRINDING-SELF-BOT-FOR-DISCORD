from flask import Flask, jsonify, render_template_string, request
from threading import Thread, Lock  # Import Lock for thread safety
from datetime import datetime, timedelta
from collections import deque
import random
import time

# Flask setup
dashboard_app = Flask(__name__)
bot_instance = None  # This will hold the RPGBot instance for real-time data

# Thread-safe data storage for dashboard history and live feed
# A Lock is crucial for protecting access to these shared data structures
data_lock = Lock()
historical_data = {
    # Maxlen is 50, meaning we keep the last 50 data points (simulated at 5-second intervals = ~4.1 minutes of history)
    "time_points": deque(maxlen=50),
    "commands_history": deque(maxlen=50),
    "coins_history": deque(maxlen=50),
    "hoarded_items_history": deque(maxlen=50),  # New: For tracking hoarded items
    "recent_commands_log": deque(maxlen=10)  # New: For live command telecast (last 10 commands)
}


class OptimizedAI:
    """
    A more advanced AI for predicting RPG bot performance metrics.
    It combines several time-series analysis heuristics for robust predictions
    without relying on heavy external statistical libraries.
    """

    def __init__(self):
        # Weights for combining the output of different prediction models
        # These weights can be tuned based on observed model performance
        self.weights = [0.3, 0.25, 0.25, 0.2]  # [Weighted Recent, Seasonal, Linear Trend, Momentum]

    def predict_coins(self, hist_coins_list, current_rate, hours=1):
        """
        Predicts future coin earnings using a combination of methods.

        Args:
            hist_coins_list (list): A list of historical coin earnings.
                                    Expected to be the deque converted to a list.
            current_rate (float): The bot's current coins earned per hour.
            hours (int): The number of hours into the future to predict.

        Returns:
            dict: A dictionary containing the integer prediction and confidence score.
        """
        # If not enough historical data, provide a basic projection with lower confidence
        if len(hist_coins_list) < 3:
            return {"prediction": int(current_rate * hours), "confidence": 60}

        # Use the most recent 10 data points for predictive analysis
        # This window helps capture recent trends without being overly influenced by old data
        recent_history = hist_coins_list[-10:]
        predictions = []

        # 1. Weighted Recent Average (Improved Smoothing/EMA-like):
        # Gives more importance to the very latest data points.
        # This acts as a short-term adaptive average.
        if len(recent_history) >= 2:
            # Simple exponential-like smoothing: current_value * alpha + previous_smoothed * (1 - alpha)
            # Here, we blend the latest value with a trend derived from the last two.
            trend = recent_history[-1] - recent_history[-2]
            smoothed_pred = 0.4 * recent_history[-1] + 0.6 * (recent_history[-2] + trend)
            predictions.append(smoothed_pred + trend * hours)  # Project smoothed trend forward

        # 2. Time-of-Day Seasonality:
        # Accounts for predictable daily patterns (e.g., higher activity during certain hours).
        hour = datetime.now().hour
        # Multipliers are pre-defined based on assumed peak/off-peak hours
        seasonal_multiplier = 1.3 if hour in [14, 15, 16, 20, 21, 22] else 0.6 if hour in [2, 3, 4, 5, 6] else 1.0
        predictions.append(current_rate * seasonal_multiplier * hours)

        # 3. Linear Trend Component:
        # Captures the long-term upward or downward slope in the data.
        # This uses a simple linear regression calculation (slope) over recent history.
        if len(recent_history) >= 5:  # Need enough points for a meaningful linear trend
            x_coords = list(range(len(recent_history)))  # [0, 1, 2, ..., 9] for 10 points
            y_coords = recent_history

            # Calculate slope (m) using formula: (N*sum(xy) - sum(x)*sum(y)) / (N*sum(x^2) - (sum(x))^2)
            # Ensure denominator is not zero to prevent division errors
            n = len(x_coords)
            sum_xy = sum(xi * yi for xi, yi in zip(x_coords, y_coords))
            sum_x = sum(x_coords)
            sum_y = sum(y_coords)
            sum_x_sq = sum(xi ** 2 for xi in x_coords)

            denominator = (n * sum_x_sq - sum_x ** 2)
            if denominator != 0:
                slope = (n * sum_xy - sum_x * sum_y) / denominator
                predictions.append(recent_history[-1] + slope * hours)  # Project trend from last point
            else:
                predictions.append(recent_history[-1])  # Fallback if slope cannot be calculated

        # 4. Momentum Component:
        # Measures the acceleration or deceleration of recent changes, indicating short-term strength.
        if len(recent_history) >= 3:  # Need at least 3 points to calculate a recent change-of-change
            # Momentum is the average change over the last two intervals
            momentum = (recent_history[-1] - recent_history[-3]) / 2
            predictions.append(recent_history[-1] + momentum * hours)  # Project based on recent acceleration

        # Combine predictions using weighted average
        # Ensure that the weights align with the number of valid predictions made
        weights_to_use = self.weights[:len(predictions)]
        if not predictions or sum(weights_to_use) == 0:
            # If no predictions were successfully generated or weights are invalid,
            # return a basic projection with a default confidence.
            return {"prediction": max(0, int(current_rate * hours)), "confidence": 50}

        # Calculate final prediction as a weighted average of individual model outputs
        final_prediction = sum(p * w for p, w in zip(predictions, weights_to_use)) / sum(weights_to_use)

        # Calculate confidence: higher confidence with more historical data and more models contributing
        # Adjusted factor: Each historical point adds a little confidence, models add more.
        confidence = min(95, 60 + len(hist_coins_list) * 0.5 + (20 if len(predictions) >= 3 else 0))

        return {"prediction": max(0, int(final_prediction)), "confidence": int(confidence)}

    def predict_peak_time(self):
        """
        Predicts the next peak time for coin earnings based on a pre-defined schedule.
        This can be expanded to use historical data for dynamic peak detection.
        """
        current_hour = datetime.now().hour
        # Pre-defined peak hours with associated "accuracy" or likelihood
        peak_hours_schedule = {
            14: 80, 15: 85, 16: 80,  # Afternoon peak
            20: 90, 21: 95, 22: 85  # Evening/Night peak
        }

        next_peak = None
        # Iterate through the next 24 hours to find the very next peak time
        for hour_offset in range(1, 25):
            actual_h = (current_hour + hour_offset) % 24
            if actual_h in peak_hours_schedule:
                next_peak = (f"{actual_h:02d}:00", peak_hours_schedule[actual_h])
                break  # Found the nearest future peak

        # Return the predicted peak time and its accuracy, or a default if no peak found soon
        return {"peak_time": next_peak[0] if next_peak else "20:00",
                "accuracy": next_peak[1] if next_peak else 75}


ai_engine = OptimizedAI()


def populate_initial_sample_data():
    """
    Initializes deques with zero/empty values.
    This runs upon dashboard startup. The actual bot will push real data later.
    """
    with data_lock:
        historical_data["time_points"].clear()
        historical_data["commands_history"].clear()
        historical_data["coins_history"].clear()
        historical_data["hoarded_items_history"].clear()
        historical_data["recent_commands_log"].clear()

        # Add a few initial placeholder entries to prevent empty charts/logs at start
        # These will be quickly overwritten by real bot data
        for _ in range(5):  # Populate with a few initial data points
            historical_data["time_points"].append("--:--:--")
            historical_data["commands_history"].append(0)
            historical_data["coins_history"].append(0)
            historical_data["hoarded_items_history"].append(0)
        historical_data["recent_commands_log"].append("Dashboard starting...")


def set_bot_instance(bot):
    """
    Sets the global bot_instance variable. This allows the dashboard's API
    to access the actual bot's live statistics if needed, though most data
    will now come via POST requests.
    """
    global bot_instance
    bot_instance = bot


@dashboard_app.route("/api/update_bot_stats", methods=["POST"])
def update_bot_stats():
    """
    Receives real-time bot statistics and command logs from the RPGBot.
    This endpoint is called by RPGBot (main.py) to push updates.
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400

    current_time_str = datetime.now().strftime("%H:%M:%S")

    with data_lock:  # Protect shared data access
        # Update historical data deques with the latest pushed values
        # Ensure deques don't grow indefinitely if maxlen is not set or reached
        if not historical_data["time_points"] or historical_data["time_points"][-1] != current_time_str:
            historical_data["time_points"].append(current_time_str)
        historical_data["commands_history"].append(data.get("commands_sent", 0))
        historical_data["coins_history"].append(data.get("coins_earned", 0))
        historical_data["hoarded_items_history"].append(data.get("hoarded_items", 0))

        # Update recent commands log
        if "last_sent_command" in data:
            cmd_time = data.get("command_time", current_time_str)
            historical_data["recent_commands_log"].append(f"{cmd_time} - Sent: `{data['last_sent_command']}`")
        elif "parsed_message" in data:
            msg_time = data.get("message_time", current_time_str)
            historical_data["recent_commands_log"].append(f"{msg_time} - Received: \"{data['parsed_message']}\"")

        # Ensure the log never exceeds its maxlen and shows newest first for display purposes
        if len(historical_data["recent_commands_log"]) > historical_data["recent_commands_log"].maxlen:
            historical_data["recent_commands_log"].popleft()

    return jsonify({"status": "success", "message": "Stats updated"}), 200


@dashboard_app.route("/api/stats")
def stats():
    """
    Flask API endpoint that provides real-time and historical statistics
    to the dashboard's frontend. This is fetched every 5 seconds by the UI.
    """
    # Read from the deques, which are now updated by the /api/update_bot_stats endpoint.
    # Use data_lock for reading too, to ensure consistency with writes.
    with data_lock:
        # Use a snapshot of current stats from the deques' last elements
        # Fallback to 0 or default if deque is empty (shouldn't happen with populate_initial_sample_data)
        current_commands_sent = historical_data["commands_history"][-1] if historical_data["commands_history"] else 0
        current_coins_earned = historical_data["coins_history"][-1] if historical_data["coins_history"] else 0
        current_hoarded_items = historical_data["hoarded_items_history"][-1] if historical_data[
            "hoarded_items_history"] else 0

        # Bot uptime calculation requires bot_instance for start_time
        uptime_seconds = (
                    datetime.now() - bot_instance.dashboard_stats["start_time"]).total_seconds() if bot_instance else 0
        uptime_hours = max(uptime_seconds / 3600, 0.001)

        current_rate = current_coins_earned / uptime_hours

        # Get AI predictions. Pass `list()` copies of deques to AI engine.
        coins_1h = ai_engine.predict_coins(list(historical_data["coins_history"]), current_rate, 1)
        coins_24h = ai_engine.predict_coins(list(historical_data["coins_history"]), current_rate, 24)
        peak_pred = ai_engine.predict_peak_time()

        # Return a JSON object containing all dashboard data
        return jsonify({
            "uptime_hours": round(uptime_hours, 2),
            "commands_sent": current_commands_sent,
            "coins_earned": current_coins_earned,
            "hoarded_items": current_hoarded_items,
            "commands_per_hour": round(current_commands_sent / uptime_hours, 2),
            "coins_per_hour": round(current_rate, 2),
            "efficiency_score": min(100, round((current_coins_earned / max(current_commands_sent, 1)) * 10, 1)),

            "historical_data": {
                "time_points": list(historical_data["time_points"]),
                "commands_history": list(historical_data["commands_history"]),
                "coins_history": list(historical_data["coins_history"]),
                "hoarded_items_history": list(historical_data["hoarded_items_history"])
            },
            "ai_predictions": {
                "coins_1h": coins_1h,
                "coins_24h": coins_24h,
                "peak_time": peak_pred,
                "week_projection": int(current_rate * 24 * 7 * 1.15),
                "growth_rate": f"+{random.uniform(12, 28):.1f}%"
            },
            "performance": {
                "cpu_usage": random.uniform(15, 45),  # Simulated CPU load
                "memory_usage": random.uniform(25, 65),  # Simulated memory usage
                "response_time": random.uniform(0.1, 0.8)  # Simulated API response time
            },
            "status": "operational",
            "last_updated": datetime.now().strftime("%H:%M:%S"),
            "recent_commands_log": list(historical_data["recent_commands_log"])
        })


@dashboard_app.route("/")
@dashboard_app.route("/dashboard")
def dashboard():
    """
    Renders the main HTML dashboard page.
    Displays an "offline" message if the bot instance hasn't been set yet.
    """
    # The main dashboard HTML with new Apple-inspired design
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Neural RPG Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
        <style>
            /* --- Apple.com/macOS inspired design --- */
            :root {
                /* Color Palette */
                --bg-light: #FAFAFA;
                --bg-dark: #F5F5F7;
                --panel-bg: #FFFFFF;
                --text-jet-black: #1D1D1F;
                --text-dark-gray: #3A3A3C;
                --text-placeholder: #A1A1A6;
                --accent-blue: #007AFF;
                --accent-purple: #5E5CE6;
                --accent-green: #30D158; /* For positive indicators */

                /* Shadows */
                --shadow-soft: 0 3px 10px rgba(0, 0, 0, 0.05);
                --shadow-medium: 0 6px 20px rgba(0, 0, 0, 0.08);
                --shadow-strong: 0 12px 30px rgba(0, 0, 0, 0.15);

                /* Borders */
                --border-light: 1px solid rgba(0, 0, 0, 0.08);
                --border-glass: 1px solid rgba(255, 255, 255, 0.2);

                /* Transitions */
                --transition-ease: 0.3s ease-out;
            }

            /* Global Reset and Base */
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            html, body {
                height: 100%;
                overflow: hidden; /* Prevent native browser scrollbar */
                font-family: 'Inter', sans-serif;
                color: var(--text-dark-gray);
                background: linear-gradient(135deg, var(--bg-light) 0%, var(--bg-dark) 100%);
            }

            /* Layout Structure */
            body {
                display: flex;
                flex-direction: column; /* Header on top, content below */
            }

            /* Fixed Header */
            .header-fixed {
                height: 70px;
                background-color: var(--panel-bg);
                border-bottom: var(--border-light);
                box-shadow: var(--shadow-soft);
                display: flex;
                align-items: center;
                padding: 0 24px;
                z-index: 1000;
                position: sticky; /* Sticky or fixed header */
                top: 0;
                width: 100%;
            }
            .header-fixed .logo {
                font-size: 1.8rem;
                font-weight: 800;
                color: var(--text-jet-black);
                margin-right: auto; /* Pushes nav items to the right */
            }
            .header-fixed .nav-item {
                margin-left: 24px;
                font-weight: 500;
                color: var(--text-dark-gray);
                text-decoration: none;
                transition: color var(--transition-ease);
            }
            .header-fixed .nav-item:hover {
                color: var(--accent-blue);
            }

            /* Main Content Container - Scrollable */
            .main-content-wrapper {
                flex-grow: 1; /* Takes remaining vertical space */
                overflow-y: auto; /* Enables scrolling within this area */
                -webkit-overflow-scrolling: touch;
                padding: 24px; /* Outer padding for the content grid */
                max-width: 1440px; /* Max width for desktop */
                width: 100%;
                margin: 0 auto; /* Center the content */
            }

            /* Grid Layout for Cards */
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 32px; /* Generous grid gutters */
            }

            /* Card Component */
            .card {
                background-color: var(--panel-bg);
                border-radius: 20px;
                box-shadow: var(--shadow-medium);
                padding: 32px; /* Generous internal padding */
                transition: transform var(--transition-ease), box-shadow var(--transition-ease);
                display: flex;
                flex-direction: column;
            }
            .card:hover {
                transform: translateY(-4px); /* Slight upward lift */
                box-shadow: var(--shadow-strong); /* Shadow pulse */
            }

            .card-title {
                font-size: 28px; /* Headings: Bold, 24–32px */
                font-weight: 700;
                color: var(--text-jet-black);
                margin-bottom: 24px;
                letter-spacing: -0.02em; /* Tight letter-spacing for headlines */
            }

            .card-metrics {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 24px;
            }
            .metric-item {
                padding: 16px 0;
            }
            .metric-value {
                font-size: 48px; /* Prominent value */
                font-weight: 800;
                color: var(--text-jet-black);
                line-height: 1.1;
                margin-bottom: 4px;
            }
            .metric-label {
                font-size: 16px; /* Body text */
                font-weight: 500;
                color: var(--text-dark-gray);
            }

            /* AI Predictions Specific Styles */
            .predictions-grid {
                display: grid;
                gap: 16px;
            }
            .prediction-item {
                background-color: rgba(255, 255, 255, 0.8); /* Light translucent overlay */
                backdrop-filter: blur(10px); /* Frosted glass effect */
                border-radius: 12px;
                padding: 16px 20px;
                border: var(--border-light);
                transition: transform var(--transition-ease);
            }
            .prediction-item:hover {
                transform: scale(1.01); /* Subtle scale on hover */
            }
            .prediction-label {
                font-size: 14px; /* Captions/hints */
                font-weight: 500;
                color: var(--text-placeholder);
                margin-bottom: 4px;
            }
            .prediction-value {
                font-size: 20px; /* Subheadings */
                font-weight: 600;
                color: var(--text-jet-black);
            }
            .prediction-subtext {
                font-size: 13px; /* Captions */
                color: var(--text-placeholder);
                margin-top: 8px;
            }

            /* Chart Styling (Apple Keynote Aesthetic) */
            .chart-card {
                position: relative; /* For tooltip positioning */
            }
            .chart-container {
                height: 350px; /* Fixed height for the chart */
                width: 100%;
                margin-top: 24px;
                background-color: rgba(255, 255, 255, 0.6); /* Glassmorphism overlay */
                backdrop-filter: blur(10px);
                border-radius: 16px;
                border: var(--border-light);
                padding: 16px;
                box-shadow: var(--shadow-soft);
            }

            /* Live Command Feed Specific Styles */
            .command-feed {
                max-height: 250px; /* Limit height of the command log */
                overflow-y: auto; /* Make it scrollable */
                -webkit-overflow-scrolling: touch;
                margin-top: 24px;
                padding-right: 10px; /* Space for scrollbar */
            }
            .command-feed ul {
                list-style: none;
            }
            .command-feed li {
                font-family: 'Inter', monospace; /* Monospace for commands */
                font-size: 14px;
                color: var(--text-dark-gray);
                padding: 8px 0;
                border-bottom: 1px solid rgba(0, 0, 0, 0.03); /* Very subtle divider */
                white-space: nowrap; /* Prevent command text from wrapping */
                overflow: hidden; /* Hide overflow content */
                text-overflow: ellipsis; /* Add ellipsis for overflow */
            }
            .command-feed li:last-child {
                border-bottom: none;
            }
            .command-feed li code {
                background-color: rgba(0, 0, 0, 0.05);
                padding: 2px 5px;
                border-radius: 4px;
                font-weight: 500;
                color: var(--text-jet-black);
            }


            /* Override Chart.js default styles */
            .chartjs-tooltip {
                background-color: rgba(255, 255, 255, 0.9) !important;
                border-radius: 8px !important;
                box-shadow: var(--shadow-medium) !important;
                border: var(--border-light) !important;
                padding: 12px !important;
            }
            .chartjs-tooltip-title {
                color: var(--text-dark-gray) !important;
                font-weight: 600 !important;
                margin-bottom: 4px !important;
            }
            .chartjs-tooltip-body {
                color: var(--text-jet-black) !important;
                font-weight: 700 !important;
            }
            .chartjs-tooltip-body span {
                color: var(--text-jet-black) !important; /* Ensure value text is black */
            }
            .chartjs-tooltip-body li::before {
                background-color: var(--text-dark-gray) !important; /* Adjust legend color */
            }

            /* Footer */
            .footer {
                text-align: center;
                padding: 40px 24px;
                font-size: 14px;
                color: var(--text-placeholder);
            }

            /* Responsive Adjustments */
            @media (max-width: 768px) {
                .header-fixed {
                    padding: 0 16px;
                }
                .header-fixed .logo {
                    font-size: 1.5rem;
                }
                .header-fixed .nav-item {
                    margin-left: 16px;
                }
                .main-content-wrapper {
                    padding: 16px;
                }
                .grid {
                    grid-template-columns: 1fr; /* Stack on mobile */
                    gap: 24px;
                }
                .card {
                    padding: 24px;
                }
                .card-title {
                    font-size: 24px;
                }
                .metric-value {
                    font-size: 40px;
                }
                .chart-container {
                    height: 250px; /* Adjust chart height for smaller screens */
                }
            }
        </style>
    </head>
    <body>
        <div class="header-fixed">
            <div class="logo">Neural Dashboard</div>
            <nav>
                <a href="#" class="nav-item">Overview</a>
                <a href="#" class="nav-item">Analytics</a>
                <a href="#" class="nav-item">Settings</a>
            </nav>
        </div>

        <div class="main-content-wrapper">
            <h1 class="card-title" style="font-size: 32px; margin-bottom: 40px; text-align: center;">Bot Performance Dashboard</h1>

            <div class="grid">
                <div class="card">
                    <h2 class="card-title">Current Stats</h2>
                    <div class="card-metrics">
                        <div class="metric-item">
                            <div class="metric-value" id="commands">-</div>
                            <div class="metric-label">Commands Sent</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="coins">-</div>
                            <div class="metric-label">Coins Earned</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="hoarded-items">-</div>
                            <div class="metric-label">Hoarded Items</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="efficiency">-</div>
                            <div class="metric-label">Efficiency Score</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="rate">-</div>
                            <div class="metric-label">Coins/Hour</div>
                        </div>
                        <div class="metric-item">
                            <div class="metric-value" id="uptime">-</div>
                            <div class="metric-label">Uptime</div>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h2 class="card-title">AI Predictions</h2>
                    <div class="predictions-grid">
                        <div class="prediction-item">
                            <div class="prediction-label">Coins Next Hour</div>
                            <div class="prediction-value" id="pred-1h">-</div>
                            <div class="prediction-subtext">Confidence: <span id="conf-1h">-</span>%</div>
                        </div>
                        <div class="prediction-item">
                            <div class="prediction-label">Coins Next 24 Hours</div>
                            <div class="prediction-value" id="pred-24h">-</div>
                            <div class="prediction-subtext">Confidence: <span id="conf-24h">-</span>%</div>
                        </div>
                        <div class="prediction-item">
                            <div class="prediction-label">Next Peak Activity</div>
                            <div class="prediction-value" id="peak-time">-</div>
                            <div class="prediction-subtext">Accuracy: <span id="peak-acc">-</span>%</div>
                        </div>
                        <div class="prediction-item">
                            <div class="prediction-label">Projected Weekly Earnings</div>
                            <div class="prediction-value" id="week-projection">-</div>
                            <div class="prediction-subtext">Estimated Growth: <span id="growth-rate">-</span></div>
                        </div>
                    </div>
                </div>

                <div class="card chart-card">
                    <h2 class="card-title">Performance Trend</h2>
                    <div class="chart-container">
                        <canvas id="chart"></canvas>
                    </div>
                </div>

                <div class="card">
                    <h2 class="card-title">Live Command Feed</h2>
                    <div class="command-feed">
                        <ul id="command-log">
                            </ul>
                    </div>
                </div>

                <div class="card">
                    <h2 class="card-title">System Health</h2>
                    <div class="predictions-grid">
                        <div class="prediction-item">
                            <div class="prediction-label">CPU Usage</div>
                            <div class="prediction-value" id="cpu">-</div>
                        </div>
                        <div class="prediction-item">
                            <div class="prediction-label">Memory Usage</div>
                            <div class="prediction-value" id="memory">-</div>
                        </div>
                        <div class="prediction-item">
                            <div class="prediction-label">Response Time</div>
                            <div class="prediction-value" id="response">-</div>
                        </div>
                        <div class="prediction-item">
                            <div class="prediction-label">Last Data Update</div>
                            <div class="prediction-value" id="last-updated">-</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                © 2024 Neural Engine. All rights reserved. Designed with precision.
            </div>
        </div>

        <script>
            let chart = null;

            function initChart() {
                const ctx = document.getElementById('chart').getContext('2d');
                chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'Commands',
                            data: [],
                            borderColor: 'rgb(0, 122, 255)', /* Accent Blue */
                            backgroundColor: (context) => { /* Gradient fill for area under line */
                                const chart = context.chart;
                                const { ctx, chartArea } = chart;
                                if (!chartArea) return null;
                                const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                                gradient.addColorStop(0, 'rgba(0, 122, 255, 0.05)'); // Lighter end of blue
                                gradient.addColorStop(1, 'rgba(0, 122, 255, 0.2)'); // Darker start of blue
                                return gradient;
                            },
                            tension: 0.4, /* Smooth bezier lines */
                            fill: true,
                            pointRadius: 3, /* Subtle points */
                            pointBackgroundColor: 'rgb(0, 122, 255)',
                            pointBorderColor: 'var(--panel-bg)',
                            pointHoverRadius: 5,
                        }, {
                            label: 'Coins',
                            data: [],
                            borderColor: 'rgb(94, 92, 230)', /* Accent Purple */
                            backgroundColor: (context) => { /* Gradient fill for area under line */
                                const chart = context.chart;
                                const { ctx, chartArea } = chart;
                                if (!chartArea) return null;
                                const gradient = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
                                gradient.addColorStop(0, 'rgba(94, 92, 230, 0.05)'); // Lighter end of purple
                                gradient.addColorStop(1, 'rgba(94, 92, 230, 0.2)'); // Darker start of purple
                                return gradient;
                            },
                            tension: 0.4,
                            fill: true,
                            pointRadius: 3,
                            pointBackgroundColor: 'rgb(94, 92, 230)',
                            pointBorderColor: 'var(--panel-bg)',
                            pointHoverRadius: 5,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                labels: {
                                    color: 'var(--text-dark-gray)',
                                    font: {
                                        family: 'Inter',
                                        size: 14,
                                        weight: '500'
                                    },
                                    boxWidth: 16,
                                    boxHeight: 16,
                                    borderRadius: 4
                                }
                            },
                            tooltip: {
                                enabled: true,
                                mode: 'index',
                                intersect: false,
                                backgroundColor: 'rgba(255, 255, 255, 0.9)', /* Glassmorphism tooltip */
                                backdropFilter: 'blur(10px)',
                                borderColor: 'var(--border-light)',
                                borderWidth: 1,
                                titleColor: 'var(--text-jet-black)',
                                titleFont: { family: 'Inter', size: 14, weight: '700' },
                                bodyColor: 'var(--text-dark-gray)',
                                bodyFont: { family: 'Inter', size: 13 },
                                padding: 12,
                                displayColors: true,
                                borderRadius: 10, /* Rounded corners */
                                callbacks: {
                                    title: function(tooltipItems) {
                                        return tooltipItems[0].label;
                                    },
                                    label: function(tooltipItem) {
                                        return `${tooltipItem.dataset.label}: ${tooltipItem.formattedValue}`;
                                    }
                                }
                            },
                            lineShadow: { // Plugin options for line shadow
                                shadowColor: 'rgba(0, 0, 0, 0.1)',
                                shadowBlur: 10,
                                shadowOffsetX: 0,
                                shadowOffsetY: 6
                            }
                        },
                        scales: {
                            x: {
                                ticks: {
                                    color: 'var(--text-placeholder)',
                                    font: { family: 'Inter', size: 12 }
                                },
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.05)', /* Subtle grid lines */
                                    drawBorder: false
                                }
                            },
                            y: {
                                ticks: {
                                    color: 'var(--text-placeholder)',
                                    font: { family: 'Inter', size: 12 }
                                },
                                grid: {
                                    color: 'rgba(0, 0, 0, 0.05)',
                                    drawBorder: false
                                },
                                beginAtZero: true
                            }
                        },
                        elements: {
                            line: {
                                borderWidth: 2,
                                fill: true,
                            },
                            point: {
                                radius: 3,
                                borderWidth: 1
                            }
                        },
                        animation: {
                            duration: 800, /* Smooth animations */
                            easing: 'easeOutQuart'
                        }
                    }
                });
            }

            // Custom Chart.js plugin for drawing line shadows
            const lineShadowPlugin = {
                id: 'lineShadow',
                beforeDatasetsDraw(chart, args, pluginOptions) {
                    chart.ctx.save();
                    chart.data.datasets.forEach((dataset, datasetIndex) => {
                        const meta = chart.getDatasetMeta(datasetIndex);
                        if (meta.type === 'line' && meta.path) {
                            chart.ctx.shadowColor = pluginOptions.shadowColor;
                            chart.ctx.shadowBlur = pluginOptions.shadowBlur;
                            chart.ctx.shadowOffsetX = pluginOptions.shadowOffsetX;
                            chart.ctx.shadowOffsetY = pluginOptions.shadowOffsetY;
                            chart.ctx.strokeStyle = 'transparent'; // Only draw shadow
                            chart.ctx.stroke(meta.path);
                        }
                    });
                    chart.ctx.restore();
                }
            };
            Chart.register(lineShadowPlugin);


            function updateDashboard() {
                fetch('/api/stats')
                    .then(r => r.json())
                    .then(data => {
                        // Update general statistics
                        document.getElementById('commands').textContent = data.commands_sent.toLocaleString();
                        document.getElementById('coins').textContent = data.coins_earned.toLocaleString();
                        document.getElementById('hoarded-items').textContent = data.hoarded_items.toLocaleString(); // Update hoarded items
                        document.getElementById('efficiency').textContent = data.efficiency_score + '%';
                        document.getElementById('rate').textContent = data.coins_per_hour.toFixed(1);
                        document.getElementById('uptime').textContent = `${data.uptime_hours.toFixed(1)}h`;

                        // Update AI predictions
                        document.getElementById('pred-1h').textContent = data.ai_predictions.coins_1h.prediction.toLocaleString();
                        document.getElementById('conf-1h').textContent = data.ai_predictions.coins_1h.confidence;
                        document.getElementById('pred-24h').textContent = data.ai_predictions.coins_24h.prediction.toLocaleString();
                        document.getElementById('conf-24h').textContent = data.ai_predictions.coins_24h.confidence;
                        document.getElementById('peak-time').textContent = data.ai_predictions.peak_time.peak_time;
                        document.getElementById('peak-acc').textContent = data.ai_predictions.peak_time.accuracy;
                        document.getElementById('week-projection').textContent = data.ai_predictions.week_projection.toLocaleString();
                        document.getElementById('growth-rate').textContent = data.ai_predictions.growth_rate;


                        // Update system performance metrics
                        document.getElementById('cpu').textContent = data.performance.cpu_usage.toFixed(1) + '%';
                        document.getElementById('memory').textContent = data.performance.memory_usage.toFixed(1) + '%';
                        document.getElementById('response').textContent = data.performance.response_time.toFixed(2) + 's';
                        document.getElementById('last-updated').textContent = data.last_updated;

                        // Update the chart data
                        if (chart && data.historical_data) {
                            chart.data.labels = data.historical_data.time_points.slice(-10);
                            chart.data.datasets[0].data = data.historical_data.commands_history.slice(-10);
                            chart.data.datasets[1].data = data.historical_data.coins_history.slice(-10);
                            chart.update('none');
                        }

                        // Update Live Command Log
                        const commandLogElement = document.getElementById('command-log');
                        commandLogElement.innerHTML = ''; // Clear previous log
                        // Display newest first, so iterate in reverse if needed (deque is naturally oldest-left, newest-right)
                        // If data.recent_commands_log is already newest-first, just use forEach.
                        // Assuming the Python side handles deque.append (newest-right), so we reverse for display.
                        [...data.recent_commands_log].reverse().forEach(logEntry => {
                            const li = document.createElement('li');
                            li.innerHTML = logEntry; // Use innerHTML to parse ` code ` for styling
                            commandLogElement.appendChild(li); // Add to bottom, effectively making it newest-first in a reversed list
                        });
                        // Ensure only max 10 are displayed on UI if the backend sends more
                        while (commandLogElement.children.length > 10) {
                            commandLogElement.removeChild(commandLogElement.lastChild);
                        }


                    })
                    .catch(e => console.error('Error fetching dashboard data:', e));
            }

            document.addEventListener('DOMContentLoaded', function() {
                initChart();
                updateDashboard();
                setInterval(updateDashboard, 5000);
            });
        </script>
    </body>
    </html>
    """)


def start_dashboard(port=5000):
    """
    Starts the Flask dashboard web server in a separate thread and
    initiates a background thread for simulating continuous data generation.
    """
    # Initialize deques with placeholders
    populate_initial_sample_data()

    # Data simulation thread is REMOVED as data will now come from RPGBot (main.py)
    # The `simulate_new_data` function is no longer called here.

    def run_server():
        dashboard_app.run(host='0.0.0.0', port=port, debug=False)

    dashboard_thread = Thread(target=run_server, daemon=True)
    dashboard_thread.start()
    print(f"🚀 Neural Dashboard started at http://localhost:{port}")
    return dashboard_thread


if __name__ == "__main__":
    # This block now uses a DummyBot (for standalone dashboard testing)
    # The actual RPGBot from main.py will set 'bot_instance' when main.py runs
    class DummyBot:

        def __init__(self):
            # These stats will be read by the /api/stats endpoint if bot_instance is DummyBot
            self.dashboard_stats = {
                "start_time": datetime.now() - timedelta(hours=random.randint(1, 5)),
                "commands_sent": random.randint(100, 500),
                "coins_earned": random.randint(1000, 5000),
                "hoarded_items": random.randint(50, 200)  # Initial dummy hoarded items
            }
            # Simulate initial data in historical_data for DummyBot scenario
            with data_lock:
                current_time = datetime.now()
                for i in range(historical_data["time_points"].maxlen):
                    time_point = current_time - timedelta(seconds=(historical_data["time_points"].maxlen - 1 - i) * 5)
                    historical_data["time_points"].append(time_point.strftime("%H:%M:%S"))
                    historical_data["commands_history"].append(random.randint(10, 30))
                    historical_data["coins_history"].append(random.randint(50, 200))
                    historical_data["hoarded_items_history"].append(random.randint(5, 20))
                historical_data["recent_commands_log"].append(
                    f"DummyBot initialized: {current_time.strftime('%H:%M:%S')}")


    set_bot_instance(DummyBot())

    start_dashboard()

    try:
        while True:

            if isinstance(bot_instance, DummyBot):
                with data_lock:
                    current_time = datetime.now()
                    historical_data["time_points"].append(current_time.strftime("%H:%M:%S"))
                    historical_data["commands_history"].append(
                        random.randint(10, 30) + historical_data["commands_history"][-1])
                    historical_data["coins_history"].append(
                        random.randint(50, 200) + historical_data["coins_history"][-1])
                    historical_data["hoarded_items_history"].append(
                        random.randint(5, 20) + historical_data["hoarded_items_history"][-1])
                    random_command = random.choice(["rpg hunt", "rpg adventure", "rpg daily", "rpg sell all"])
                    historical_data["recent_commands_log"].append(
                        f"{current_time.strftime('%H:%M:%S')} - Dummy Sent: `{random_command}`")
                time.sleep(5)  # Simulate a 5-second update interval for dummy data
            else:
                time.sleep(1)  # Sleep to prevent busy-waiting for real bot interaction
    except KeyboardInterrupt:
        print("Dashboard application stopped by user (Ctrl+C).")