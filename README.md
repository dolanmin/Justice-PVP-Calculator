# Justice-PVP-Calculator

⚔️ Justice Online PVP Calculator
A specialized damage calculation and attribute analysis tool designed for "Justice Online" players (specifically for level 79 PVP environments). Unlike traditional Excel spreadsheets, this program offers a modern GUI with Auto-Save, Smart Attribute Recommendations, and Kill Time Estimation.

✨ Key Features
📊 Precise Damage Calculation:

Accurate implementation of defense reduction and elemental resistance formulas.

Uses the real three-stage shield formula for precise shield-breaking calculations.

Displays Non-Crit (White), Crit (Yellow), and Expected Damage clearly.

🤖 Smart Attribute Recommendations:

Offensive: Automatically calculates and ranks the damage increase % for every 100 points added to stats like Attack, Break Def, Element, Crit, etc.

Defensive: Calculates damage reduction % for defensive stats like Defense, Shield, Resist, etc.

Data-driven advice on which stats to prioritize.

💀 Combat Assessment:

Calculates "Hits to Kill" based on enemy HP and your expected damage.

Shows actual Hit Rate and Crit Rate after accounting for level suppression and resistances.

💾 Auto-Save Functionality:

Automatically saves your input data (justice_save.json) upon calculation.

Reloads your last used stats automatically when you reopen the program.

🛠️ Highly Customizable:

Supports custom Skill Multipliers, allowing you to calculate damage for any skill (Basic Attack, Ultimate, DOTs).

Input fields come with clear formatting hints to prevent errors.

📥 Download & Installation
For Players:

Go to the Releases page.

Download the latest .exe file.

Run it directly (No Python installation required).

For Developers:

Clone the repository:

Bash

git clone https://github.com/YonaYouta/Justice-PVP-Calculator.git
Ensure Python 3.x and tkinter are installed.

Run the script:

Bash

python justice_calc.py
⚠️ Notes
Antivirus Warning: Since the program is packaged with PyInstaller, some antivirus software (like Windows Defender) might flag it as unknown. This is a common false positive for Python executables; it is safe to run.

Data Source: The formulas are based on theoretical models derived from community testing (Level 29 skill coefficients). Actual in-game damage may vary slightly due to RNG.

📜 Author
Designed by NAYUTA
