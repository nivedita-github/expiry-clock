🕒 Expiry Clock - Inventory Management System

A desktop application for inventory management with expiry alerts, sales tracking, and reporting.


✨ Features

- 📦 Product Management (CRUD operations)
- 🔔 Automatic Expiry Alerts (Windows notifications)
- 💰 Sales Recording & Reporting
- 📊 Dashboard Analytics
- 🌙 Dark/Light Mode Toggle
- 🕒 Background Thread Monitoring

🛠️ Installation

1. Prerequisites:
   - Python 3.8+
   - Windows 10/11 (for toast notifications)

2. Install dependencies:
   pip install PyQt5 win10toast

   
Run the application:
python main.py


🖥️ Usage
Add Products:
Name, category, quantity, price, expiry date
Input validation for dates (DD-MM-YYYY)

Manage Inventory:
Edit/delete products
Record sales (auto-updates stock)

View Alerts:
Low stock (<5 items)
Expiring soon (≤10 days)

Generate Reports:
Filter sales by date range
Export to CSV

🏗️ Project Structure
Expiry-Clock/
├── main.py            # Main application entry
├── database.db        # SQLite database (auto-created)
├── icon/              # Toolbar icons
│   ├── add.png
│   ├── cart.png
│   └── ...
├── README.md          # This file
└── requirements.txt   # Dependencies


🔧 Technical Details
Database: SQLite with automatic schema migration

GUI: PyQt5 (QMainWindow, QTableWidget, QDialog)

Notifications: win10toast (Windows 10 toast alerts)

Threading: QThread for background expiry checks

📜 License
MIT License - See LICENSE file

🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first.
