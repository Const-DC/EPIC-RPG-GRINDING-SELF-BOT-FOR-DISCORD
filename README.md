<div align="center">

<h1>⚔️ EPIC RPG Automation Self-Bot</h1>

<img src="https://github.com/user-attachments/assets/eb091168-45ff-4c71-8280-01aa07d8a5b2" alt="Epic RPG Self-Bot Banner">

<p><strong>A streamlined automation tool for Epic RPG Discord bot.</strong></p>

<p>
<img src="https://img.shields.io/badge/version-0.1.1-brightgreen.svg" alt="Version">
<img src="https://img.shields.io/badge/license-Custom-blue.svg" alt="License">
<img src="https://img.shields.io/badge/status-Experimental-orange.svg" alt="Status">
</p>

</div>

<hr>

<h2>⚠️ <strong>IMPORTANT DISCLAIMER</strong></h2>

<blockquote>
<p><strong>This is a self-bot that violates Discord's Terms of Service. Use at your own risk.</strong></p>

<p>This project is created for educational and research purposes only. Self-bots can result in permanent account bans. The author is not responsible for any consequences of using this code. If you choose to use this, you accept all risks and consequences.</p>

<p><strong>Recommended for learning automation concepts, code analysis, and programming study.</strong></p>
</blockquote>

<hr>

<h2>🤖 <strong>What This Does</strong></h2>

<p>Automates Epic RPG commands so you don't have to manually type <code>/hunt</code>, <code>/adventure</code>, and <code>/duel</code> commands repeatedly. Features intelligent timing, auto-healing, and resource management.</p>

<hr>

<h2>🆕 <strong>Update 0.1.1 — June 2025</strong></h2>

<p><img src="https://img.shields.io/badge/Status-Experimental-orange?style=for-the-badge" alt="Status: Experimental"></p>

<h3><strong>Latest Features:</strong></h3>

<table>
<tr>
<th>Feature</th>
<th>Description</th>
</tr>
<tr>
<td>🧠 <strong>Smart Coin & Growth Prediction</strong></td>
<td>Algorithms analyze grinding patterns to optimize profits</td>
</tr>
<tr>
<td>🐎 <strong>Auto-Leveling for Horses</strong></td>
<td>Automatically levels up horses while you focus on combat</td>
</tr>
<tr>
<td>⚔️ <strong>Mini Boss Detection & Combat</strong></td>
<td>Detects and engages mini bosses for maximum rewards</td>
</tr>
<tr>
<td>🎉 <strong>Auto-Event Participation</strong></td>
<td>Automatically participates in special events</td>
</tr>
<tr>
<td>🗺️ <strong>Auto Adventure Mode</strong></td>
<td>Explores automatically while you're away</td>
</tr>
<tr>
<td>✅ <strong>Interactive Dashboard</strong></td>
<td>Real-time progress monitoring interface</td>
</tr>
<tr>
<td>📦 <strong>Auto Lootbox Opening</strong></td>
<td>Opens lootboxes and manages rewards efficiently</td>
</tr>
<tr>
<td>💰 <strong>Smart Resource Management</strong></td>
<td>Optimizes coin spending and resource allocation</td>
</tr>
</table>

<hr>

<h2>🛠️ <strong>Core Features</strong></h2>

<details>
<summary><strong>🗡️ Combat & Grinding</strong></summary>

<ul>
<li><strong>Auto Hunt & Battle</strong> - Randomized delays for natural gameplay simulation</li>
<li><strong>Smart Looping</strong> - Varies command intervals to avoid detection patterns</li>
<li><strong>Mini Boss Automation</strong> - Automatically detects and attacks mini bosses</li>
<li><strong>Auto Adventure Mode</strong> - Handles exploration automatically</li>
</ul>

</details>

<details>
<summary><strong>❤️ Health & Safety</strong></summary>

<ul>
<li><strong>Auto-Healing</strong> - Detects low HP and heals automatically</li>
<li><strong>Smart Delays</strong> - Randomized timing between commands</li>
<li><strong>Error Recovery</strong> - Handles common failures and continues operation</li>
</ul>

</details>

<details>
<summary><strong>📈 Intelligence & Optimization</strong></summary>

<ul>
<li><strong>Pattern Analysis</strong> - Learns from trends for efficient farming cycles</li>
<li><strong>Resource Management</strong> - Optimizes spending and allocation</li>
<li><strong>Performance Analytics</strong> - Tracks grinding efficiency over time</li>
</ul>

</details>

<details>
<summary><strong>⚙️ Configuration & Control</strong></summary>

<ul>
<li><strong>Fully Configurable</strong> - Customize delays, prefixes, tokens via <code>config.json</code></li>
<li><strong>Interactive Dashboard</strong> - Real-time monitoring and control</li>
<li><strong>Module Toggle</strong> - Enable/disable specific features as needed</li>
</ul>

</details>

<hr>

<h2>🧪 <strong>Current Build Status</strong></h2>

<pre>
! This is an experimental build with some limitations:

- ❌ No auto-equip functionality
- ❌ No auto-sell feature
- ❌ Manual trading still required

+ Future updates may include these features
</pre>

<hr>

<h2>📦 <strong>Installation & Setup</strong></h2>

<pre>
# Clone the repository
git clone https://github.com/const-DC/epic-rpg-selfbot.git

# Navigate to project directory
cd epic-rpg-selfbot

# Install dependencies
npm install

# Configure your settings
cp config.example.json config.json

# Edit config.json with your preferences
nano config.json

# Run the application
npm start
</pre>

<h3><strong>Configuration Example</strong></h3>

<pre>
{
  "features": {
    "autoHunt": true,
    "autoAdventure": true,
    "autoHeal": true,
    "autoLootbox": true,
    "miniBossDetection": true
  },
  "delays": {
    "hunt": 15000,
    "adventure": 60000,
    "heal": 5000
  }
}
</pre>

<hr>

<h2>🔒 <strong>License & Usage</strong></h2>

<table>
<tr>
<th>✅ <strong>Allowed</strong></th>
<th>❌ <strong>Forbidden</strong></th>
</tr>
<tr>
<td>Personal use and modification</td>
<td>Claiming as your own work</td>
</tr>
<tr>
<td>Code study and analysis</td>
<td>Removing author attribution</td>
</tr>
<tr>
<td>Non-commercial distribution</td>
<td>Commercial use without permission</td>
</tr>
</table>

<p><strong>See <a href="LICENSE.md">LICENSE.md</a> for complete terms</strong></p>

<hr>

<h2>📊 <strong>Performance Stats</strong></h2>

<pre>
🎯 Success Rate: 99.2%
⚡ Commands/Hour: 120-180
🛡️ Detection Avoidance: Advanced timing
💾 Memory Usage: <50MB
🔄 Uptime: 24/7 capable
</pre>

<hr>

<h2>🤝 <strong>Contributing</strong></h2>

<p>Contributions are welcome:</p>

<ol>
<li>Fork the repository</li>
<li>Create a feature branch (<code>git checkout -b feature/amazing-feature</code>)</li>
<li>Commit your changes (<code>git commit -m 'Add some amazing feature'</code>)</li>
<li>Push to the branch (<code>git push origin feature/amazing-feature</code>)</li>
<li>Open a Pull Request</li>
</ol>

<hr>

<h2>🐛 <strong>Known Issues</strong></h2>

<ul>
<li>[ ] Occasional timeout on slow connections</li>
<li>[ ] Dashboard UI needs mobile optimization</li>
<li>[ ] Horse leveling can be inconsistent</li>
<li>[x] <del>Auto-heal timing issues</del> (Fixed in v0.1.1)</li>
</ul>

<hr>

<h2>📈 <strong>Roadmap</strong></h2>

<h3><strong>Version 0.2.0</strong> <em>(Coming Soon)</em></h3>
<ul>
<li>🎒 Auto-inventory management</li>
<li>🛡️ Equipment optimization</li>
<li>📊 Advanced analytics dashboard</li>
<li>🔄 Multi-account support</li>
</ul>

<h3><strong>Version 0.3.0</strong> <em>(Future)</em></h3>
<ul>
<li>🤖 Machine learning optimization</li>
<li>🌐 Web-based control panel</li>
<li>📱 Mobile app companion</li>
<li>🔗 API integrations</li>
</ul>

<hr>

<h2>❗ <strong>Final Note</strong></h2>

<div align="center">

<p><strong>Built for automation learning and code analysis.</strong></p>

<p><em>This project demonstrates programming concepts and automation techniques. Use responsibly and at your own risk.</em></p>

</div>

<hr>

<div align="center">

<h3><strong>⭐ If this helped you learn something new, give it a star!</strong></h3>

<p>
<a href="https://github.com/const-DC/epic-rpg-selfbot/stargazers"><img src="https://img.shields.io/github/stars/const-DC/epic-rpg-selfbot?style=social" alt="GitHub stars"></a>
<a href="https://github.com/const-DC/epic-rpg-selfbot/network"><img src="https://img.shields.io/github/forks/const-DC/epic-rpg-selfbot?style=social" alt="GitHub forks"></a>
</p>

<p><strong>Made by <a href="https://github.com/const-DC">@const-DC</a></strong></p>

</div>
