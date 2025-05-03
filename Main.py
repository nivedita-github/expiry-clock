
import sys
import sqlite3
import os
import time
from datetime import datetime, date, timedelta
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from win10toast import ToastNotifier

class WorkerThread(QThread):
    def run(self):
        while True:
            conn = None
            try:
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                
                today = date.today()
                warning_date = (today + timedelta(days=10)).strftime("%d-%m-%Y")
                
                # Check expiring products
                c.execute("""
                    SELECT name, quantity, expiry_date 
                    FROM products 
                    WHERE quantity > 0 
                    AND expiry_date IS NOT NULL
                """)
                
                for name, qty, exp_date_str in c.fetchall():
                    try:
                        exp_date = datetime.strptime(exp_date_str, "%d-%m-%Y").date()
                        days_left = (exp_date - today).days
                        
                        if 0 <= days_left <= 10:
                            try:
                                # Simple notification without icon to avoid issues
                                notifier = ToastNotifier()
                                notifier.show_toast(
                                    f"EXPIRING SOON: {name}",
                                    f"{qty} units left - expires in {days_left} days",
                                    duration=10
                                )
                            except Exception as e:
                                print(f"Notification failed for {name}: {str(e)}")
                                
                    except ValueError:
                        print(f"Invalid date format for {name}: {exp_date_str}")
                
                # Check low stock
                c.execute("SELECT name, quantity FROM products WHERE quantity < 5")
                for name, qty in c.fetchall():
                    try:
                        notifier = ToastNotifier()
                        notifier.show_toast(
                            "LOW STOCK",
                            f"{name} is running low ({qty} left)",
                            duration=5
                        )
                    except:
                        pass
                
            except Exception as e:
                print(f"Database error in worker thread: {str(e)}")
            finally:
                if conn:
                    conn.close()
            
            time.sleep(3600)

class InsertDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Product")
        self.setFixedSize(400, 300)
        
        # Create layout first
        layout = QFormLayout()
        
        # Widgets
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Beverage", "Food", "Cosmetics", "Toiletries",
            "Dairy", "Snacks", "Other"
        ])
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setValue(1)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 9999)
        self.price_input.setPrefix("$ ")
        self.price_input.setValue(0)
        
        self.expiry_input = QLineEdit()
        self.expiry_input.setPlaceholderText("DD-MM-YYYY")
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Notes")
        
        btn_submit = QPushButton("Add Product")
        btn_cancel = QPushButton("Cancel")
        
        # Add widgets to layout
        layout.addRow("Name:", self.name_input)
        layout.addRow("Category:", self.category_combo)
        layout.addRow("Quantity:", self.quantity_spin)
        layout.addRow("Price:", self.price_input)
        layout.addRow("Expiry Date:", self.expiry_input)
        layout.addRow("Notes:", self.notes_input)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_submit)
        button_layout.addWidget(btn_cancel)
        layout.addRow(button_layout)
        
        self.setLayout(layout)
        
        btn_submit.clicked.connect(self.add_product)
        btn_cancel.clicked.connect(self.reject)
    
    def add_product(self):
        name = self.name_input.text().strip()
        category = self.category_combo.currentText()
        quantity = self.quantity_spin.value()
        price = self.price_input.value()
        expiry = self.expiry_input.text().strip()
        notes = self.notes_input.text()
        
        if not name:
            QMessageBox.warning(self, "Error", "Product name is required")
            return
            
        if expiry:
            try:
                datetime.strptime(expiry, "%d-%m-%Y")
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid date format (use DD-MM-YYYY)")
                return
        
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            c.execute("""
                INSERT INTO products 
                (name, category, quantity, price, expiry_date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, category, quantity, price, expiry, notes))
            
            conn.commit()
            QMessageBox.information(self, "Success", "Product added successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

class EditDialog(QDialog):
    def __init__(self, product_id, parent=None):
        super().__init__(parent)
        self.product_id = product_id
        self.setWindowTitle("Edit Product")
        self.setFixedSize(400, 300)
        
        # Create layout first
        layout = QFormLayout()
        
        # Widgets
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Beverage", "Food", "Cosmetics", "Toiletries",
            "Dairy", "Snacks", "Other"
        ])
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(0, 9999)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 9999)
        self.price_input.setPrefix("$ ")
        
        self.expiry_input = QLineEdit()
        self.expiry_input.setPlaceholderText("DD-MM-YYYY")
        
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Notes")
        
        btn_submit = QPushButton("Update Product")
        btn_cancel = QPushButton("Cancel")
        
        # Add widgets to layout
        layout.addRow("Name:", self.name_input)
        layout.addRow("Category:", self.category_combo)
        layout.addRow("Quantity:", self.quantity_spin)
        layout.addRow("Price:", self.price_input)
        layout.addRow("Expiry Date:", self.expiry_input)
        layout.addRow("Notes:", self.notes_input)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_submit)
        button_layout.addWidget(btn_cancel)
        layout.addRow(button_layout)
        
        self.setLayout(layout)
        
        btn_submit.clicked.connect(self.update_product)
        btn_cancel.clicked.connect(self.reject)
        
        self.load_product_data()
    
    def load_product_data(self):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            c.execute("""
                SELECT name, category, quantity, price, expiry_date, notes
                FROM products
                WHERE id = ?
            """, (self.product_id,))
            
            product_data = c.fetchone()
            if product_data:
                self.name_input.setText(product_data[0])
                self.category_combo.setCurrentText(product_data[1])
                self.quantity_spin.setValue(product_data[2])
                self.price_input.setValue(product_data[3])
                self.expiry_input.setText(product_data[4] if product_data[4] else "")
                self.notes_input.setText(product_data[5] if product_data[5] else "")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load product data: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def update_product(self):
        name = self.name_input.text().strip()
        category = self.category_combo.currentText()
        quantity = self.quantity_spin.value()
        price = self.price_input.value()
        expiry = self.expiry_input.text().strip()
        notes = self.notes_input.text()
        
        if not name:
            QMessageBox.warning(self, "Error", "Product name is required")
            return
            
        if expiry:
            try:
                datetime.strptime(expiry, "%d-%m-%Y")
            except ValueError:
                QMessageBox.warning(self, "Error", "Invalid date format (use DD-MM-YYYY)")
                return
        
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            c.execute("""
                UPDATE products 
                SET name = ?, 
                    category = ?, 
                    quantity = ?, 
                    price = ?, 
                    expiry_date = ?, 
                    notes = ?
                WHERE id = ?
            """, (name, category, quantity, price, expiry, notes, self.product_id))
            
            conn.commit()
            QMessageBox.information(self, "Success", "Product updated successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

class PurchaseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Record Sale")
        self.setFixedSize(400, 200)
        
        layout = QFormLayout()
        
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        
        self.completer = QCompleter()
        self.product_combo.setCompleter(self.completer)
        self.product_combo.editTextChanged.connect(self.update_completer)
        
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setValue(1)
        
        btn_submit = QPushButton("Record Sale")
        btn_cancel = QPushButton("Cancel")
        
        layout.addRow("Product:", self.product_combo)
        layout.addRow("Quantity:", self.quantity_spin)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(btn_submit)
        button_layout.addWidget(btn_cancel)
        layout.addRow(button_layout)
        
        self.setLayout(layout)
        
        btn_submit.clicked.connect(self.record_sale)
        btn_cancel.clicked.connect(self.reject)
        
        self.load_products()
    
    def update_completer(self, text):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT name FROM products WHERE name LIKE ? AND quantity > 0", (f"%{text}%",))
            self.completer.setModel(QStringListModel([item[0] for item in c.fetchall()]))
        except Exception as e:
            print(f"Completer error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def load_products(self):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT DISTINCT name FROM products WHERE quantity > 0")
            self.product_combo.addItems([item[0] for item in c.fetchall()])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Couldn't load products: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def record_sale(self):
        product_name = self.product_combo.currentText().strip()
        quantity = self.quantity_spin.value()
        
        if not product_name:
            QMessageBox.warning(self, "Error", "Please enter a product name")
            return
            
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            c.execute("SELECT id, quantity FROM products WHERE name=?", (product_name,))
            product = c.fetchone()
            
            if not product:
                QMessageBox.warning(self, "Error", "Product not found in inventory")
                return
                
            product_id, current_qty = product
            if quantity > current_qty:
                QMessageBox.warning(self, "Error", f"Only {current_qty} units available")
                return
            
            c.execute("UPDATE products SET quantity=quantity-? WHERE id=?", (quantity, product_id))
            c.execute("""
                INSERT INTO purchases (product_id, quantity_sold, sale_date)
                VALUES (?, ?, datetime('now'))
            """, (product_id, quantity))
            
            conn.commit()
            QMessageBox.information(self, "Success", "Sale recorded successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

class DeleteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Delete Product")
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        self.product_combo = QComboBox()
        btn_delete = QPushButton("Delete")
        
        layout.addWidget(QLabel("Select Product to Delete:"))
        layout.addWidget(self.product_combo)
        layout.addWidget(btn_delete)
        
        self.setLayout(layout)
        btn_delete.clicked.connect(self.delete_product)
        
        self.load_products()
    
    def load_products(self):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT id, name FROM products")
            self.product_combo.addItems([f"{row[0]} - {row[1]}" for row in c.fetchall()])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Couldn't load products: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def delete_product(self):
        selected = self.product_combo.currentText()
        if not selected:
            return
            
        product_id = selected.split(" - ")[0]
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Delete product {selected}? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = sqlite3.connect("database.db")
                c = conn.cursor()
                
                # First delete related purchases
                c.execute("DELETE FROM purchases WHERE product_id=?", (product_id,))
                # Then delete the product
                c.execute("DELETE FROM products WHERE id=?", (product_id,))
                
                conn.commit()
                QMessageBox.information(self, "Success", "Product deleted successfully!")
                self.accept()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
            finally:
                if conn:
                    conn.close()

class ReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sales Report")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Date range controls
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.date_from)
        
        date_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_to)
        
        btn_generate = QPushButton("Generate Report")
        btn_export = QPushButton("Export to CSV")
        
        date_layout.addWidget(btn_generate)
        date_layout.addWidget(btn_export)
        
        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Product", "Quantity", "Total"])
        
        layout.addLayout(date_layout)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        btn_generate.clicked.connect(self.generate_report)
        btn_export.clicked.connect(self.export_csv)
    
    def generate_report(self):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            c.execute("""
                SELECT p.name, ps.quantity_sold, ps.sale_date, 
                       (ps.quantity_sold * p.price) as total
                FROM purchases ps
                JOIN products p ON ps.product_id = p.id
                WHERE date(ps.sale_date) BETWEEN ? AND ?
                ORDER BY ps.sale_date DESC
            """, (
                self.date_from.date().toString("yyyy-MM-dd"), 
                self.date_to.date().toString("yyyy-MM-dd")
            ))
            
            self.table.setRowCount(0)
            for row_num, row_data in enumerate(c.fetchall()):
                self.table.insertRow(row_num)
                for col_num, data in enumerate(row_data):
                    self.table.setItem(row_num, col_num, QTableWidgetItem(str(data)))
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def export_csv(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No data to export")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Report", "", "CSV Files (*.csv)")
        
        if not path:
            return
            
        try:
            with open(path, 'w') as f:
                # Write headers
                headers = []
                for col in range(self.table.columnCount()):
                    headers.append(self.table.horizontalHeaderItem(col).text())
                f.write(','.join(headers) + '\n')
                
                # Write data
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    f.write(','.join(row_data) + '\n')
                
            QMessageBox.information(self, "Success", "Report exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

class Dashboard(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.refresh_stats()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Stats cards
        cards = QHBoxLayout()
        
        self.total_products = QLabel("0")
        self.expiring_soon = QLabel("0")
        self.low_stock = QLabel("0")
        self.total_sales = QLabel("0")
        
        for widget, title, color in zip(
            [self.total_products, self.expiring_soon, self.low_stock, self.total_sales],
            ["Total Products", "Expiring Soon", "Low Stock", "Monthly Sales"],
            ["#4CAF50", "#FF9800", "#F44336", "#2196F3"]
        ):
            card = QGroupBox(title)
            card.setStyleSheet(f"""
                QGroupBox {{
                    border: 2px solid {color};
                    border-radius: 5px;
                    margin-top: 10px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    color: {color};
                }}
            """)
            card_layout = QVBoxLayout()
            widget.setStyleSheet(f"font-size: 24px; color: {color}; font-weight: bold;")
            widget.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(widget)
            card.setLayout(card_layout)
            cards.addWidget(card)
        
        # Chart placeholder
        self.chart_view = QLabel("Sales Chart Will Appear Here")
        self.chart_view.setAlignment(Qt.AlignCenter)
        self.chart_view.setStyleSheet("""
            background: white; 
            border: 1px solid #ddd; 
            min-height: 300px;
            margin-top: 20px;
        """)
        
        layout.addLayout(cards)
        layout.addWidget(self.chart_view)
        
        self.setLayout(layout)
    
    def refresh_stats(self):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            # Total products
            c.execute("SELECT COUNT(*) FROM products")
            self.total_products.setText(str(c.fetchone()[0]))
            
            # Expiring soon
            today = date.today()
            warning_date = (today + timedelta(days=10)).strftime("%Y-%m-%d")
            c.execute("""
                SELECT COUNT(*) FROM products 
                WHERE expiry_date <= ? 
                AND quantity > 0
            """, (warning_date,))
            self.expiring_soon.setText(str(c.fetchone()[0]))
            
            # Low stock
            c.execute("SELECT COUNT(*) FROM products WHERE quantity < 5")
            self.low_stock.setText(str(c.fetchone()[0]))
            
            # Monthly sales
            c.execute("""
                SELECT SUM(quantity_sold) FROM purchases
                WHERE strftime('%m', sale_date) = strftime('%m', 'now')
            """)
            result = c.fetchone()
            self.total_sales.setText(str(result[0] if result[0] else 0))
            
        except Exception as e:
            print(f"Dashboard error: {str(e)}")
        finally:
            if conn:
                conn.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EXPIRY CLOCK")
        self.setMinimumSize(1000, 700)
        self.dark_mode = False
        
        # Initialize database
        self.init_db()
        self.migrate_db()
        
        # Setup UI
        self.setup_ui()
        self.setup_styles()
        
        # Start notification thread
        self.notification_thread = WorkerThread()
        self.notification_thread.start()
        
        # Load initial data
        self.load_data()
    
    def init_db(self):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            # Create products table
            c.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT,
                    quantity INTEGER DEFAULT 0,
                    price REAL DEFAULT 0,
                    expiry_date TEXT,
                    notes TEXT
                )
            """)
            
            # Create purchases table
            c.execute("""
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER,
                    quantity_sold INTEGER,
                    sale_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(product_id) REFERENCES products(id)
                )
            """)
            
            conn.commit()
        except Exception as e:
            print(f"Database initialization error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def migrate_db(self):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            # Check if price column exists
            c.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in c.fetchall()]
            
            if 'price' not in columns:
                c.execute("ALTER TABLE products ADD COLUMN price REAL DEFAULT 0")
                conn.commit()
                
        except Exception as e:
            print(f"Migration error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def setup_ui(self):
        # Create main widgets
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Category", "Qty", "Price", "Expiry", "Notes"
        ])
        
        self.table.doubleClicked.connect(self.show_edit_dialog)

        # Set equal column widths
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setColumnWidth(0, 70)    # ID
        self.table.setColumnWidth(1, 230)   # Name
        self.table.setColumnWidth(2, 300)   # Category
        self.table.setColumnWidth(3, 150)    # Quantity
        self.table.setColumnWidth(4, 150)    # Price
        self.table.setColumnWidth(5, 200)   # Expiry
        self.table.setColumnWidth(6, 800)   # Notes
        
        self.dashboard = Dashboard(self)
        
        # Create tab interface
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.table, "Inventory")
        self.tab_widget.addTab(self.dashboard, "Dashboard")
        self.setCentralWidget(self.tab_widget)
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(toolbar)
        
        # Create actions
        actions = [
            ("Add Product", "icon/add.png", self.show_add_dialog),
            ("Edit Product", "icon/edit.png", self.show_edit_dialog),
            ("Record Sale", "icon/cart.png", self.show_purchase_dialog),
            ("Delete Product", "icon/delete.png", self.show_delete_dialog),
            ("Generate Report", "icon/report.png", self.show_report_dialog),
            ("Refresh", "icon/refresh.png", self.load_data),
            ("Dark Mode", "icon/dark_mode.png", self.toggle_dark_mode)
        ]
        
        for text, icon_path, handler in actions:
            action = QAction(QIcon(icon_path), text, self)
            action.triggered.connect(handler)
            toolbar.addAction(action)
    
    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f0f0f0;
                gridline-color: #ddd;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QToolBar {
                background: #e0e0e0;
                border: none;
                padding: 5px;
            }
            QToolButton {
                padding: 5px;
                margin: 2px;
            }
            QDialog {
                background: white;
            }
            QPushButton {
                padding: 5px;
                min-width: 80px;
            }
        """)

    def show_edit_dialog(self):
        selected_row = self.table.currentRow()
        if selected_row == -1:  # No row selected
            QMessageBox.warning(self, "Error", "Please select a product to edit.")
            return
    
        product_id = int(self.table.item(selected_row, 0).text())  # Get ID from the first column
        dialog = EditDialog(product_id, self)  # Open EditDialog with the selected product ID
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()  # Refresh the table after editing

    def toggle_dark_mode(self):
        if self.dark_mode:
            # Light mode
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QTableWidget {
                    background-color: white;
                    alternate-background-color: #f0f0f0;
                    gridline-color: #ddd;
                }
                QHeaderView::section {
                    background-color: #4CAF50;
                    color: white;
                    padding: 5px;
                    font-weight: bold;
                }
                QToolBar {
                    background: #e0e0e0;
                    border: none;
                    padding: 5px;
                }
                QToolButton {
                    padding: 5px;
                    margin: 2px;
                }
                QDialog {
                    background: white;
                }
                QPushButton {
                    padding: 5px;
                    min-width: 80px;
                }
            """)
            self.dark_mode = False
        else:
            # Dark mode
            self.setStyleSheet("""
                QMainWindow, QDialog {
                    background-color: #333;
                }
                QWidget {
                    color: #eee;
                }
                QTableWidget {
                    background-color: #444;
                    color: white;
                    gridline-color: #555;
                }
                QHeaderView::section {
                    background-color: #2E7D32;
                    color: white;
                }
                QToolBar {
                    background: #555;
                }
                QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                    background: #555;
                    color: white;
                    border: 1px solid #666;
                }
                QPushButton {
                    background: #666;
                    color: white;
                    border: 1px solid #777;
                    padding: 5px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: #777;
                }
            """)
            self.dark_mode = True
    
    def load_data(self):
        conn = None
        try:
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            
            c.execute("""
                SELECT id, name, category, quantity, price, expiry_date, notes
                FROM products
                ORDER BY name
            """)
            
            self.table.setRowCount(0)
            for row_num, row_data in enumerate(c.fetchall()):
                self.table.insertRow(row_num)
                
                # Add data columns
                for col_num, data in enumerate(row_data):
                    item = QTableWidgetItem(str(data))
                    
                    # Highlight low stock items
                    if col_num == 3 and int(data) < 5:  # Quantity column
                        item.setBackground(QColor(255, 204, 203))  # Light red
                    
                    # Highlight expiring soon items
                    if col_num == 5 and data:  # Expiry date column
                        try:
                            exp_date = datetime.strptime(data, "%d-%m-%Y").date()
                            days_left = (exp_date - date.today()).days
                            if 0 <= days_left <= 10:
                                item.setBackground(QColor(255, 255, 153))  # Light yellow
                        except ValueError:
                            pass
                    
                    self.table.setItem(row_num, col_num, item)
            
            self.dashboard.refresh_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def show_add_dialog(self):
        dialog = InsertDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def show_purchase_dialog(self):
        dialog = PurchaseDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def show_delete_dialog(self):
        dialog = DeleteDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()
    
    def show_report_dialog(self):
        dialog = ReportDialog(self)
        dialog.exec_()

if __name__ == "__main__":
    # Create required directories
    if not os.path.exists("icon"):
        os.makedirs("icon")
    
    # Set application style
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())