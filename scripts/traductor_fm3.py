#!/usr/bin/env python3
"""
Traductor Front Mission 3
Herramienta para gestionar traducciones con IA + revisión humana
"""

import sys
import csv
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QComboBox, QFileDialog, QMessageBox, QProgressBar, QHeaderView,
    QSplitter, QTextEdit, QGroupBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPalette


class TraductorFM3(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Traductor Front Mission 3")
        self.setGeometry(100, 100, 1400, 800)
        
        self.csv_file = None
        self.data = []
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Toolbar superior
        toolbar = QHBoxLayout()
        
        self.btn_open = QPushButton("Abrir CSV")
        self.btn_open.clicked.connect(self.open_csv)
        toolbar.addWidget(self.btn_open)
        
        self.btn_save = QPushButton("Guardar CSV")
        self.btn_save.clicked.connect(self.save_csv)
        self.btn_save.setEnabled(False)
        toolbar.addWidget(self.btn_save)
        
        toolbar.addSpacing(20)
        
        # Búsqueda
        toolbar.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en texto original o traducciones...")
        self.search_input.textChanged.connect(self.apply_filters)
        toolbar.addWidget(self.search_input)
        
        toolbar.addSpacing(20)
        
        # Filtro por tipo
        toolbar.addWidget(QLabel("Tipo:"))
        self.filter_type = QComboBox()
        self.filter_type.addItem("Todos", "all")
        self.filter_type.addItem("Diálogos", "dialogo")
        self.filter_type.addItem("Menús", "menu")
        self.filter_type.addItem("Misiones", "mision")
        self.filter_type.addItem("Sistema", "sistema")
        self.filter_type.addItem("Créditos", "creditos")
        self.filter_type.addItem("Correo", "correo")
        self.filter_type.addItem("Resultados", "resultados")
        self.filter_type.currentIndexChanged.connect(self.apply_filters)
        toolbar.addWidget(self.filter_type)
        
        layout.addLayout(toolbar)
        
        # Splitter principal
        splitter = QSplitter(Qt.Vertical)
        
        # Tabla principal
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Archivo", "Offset", "Tipo", "Texto Original", 
            "Traducción IA", "Traducción Revisada", "Longitud"
        ])
        
        # Configurar anchos de columna
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Archivo
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Offset
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Tipo
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Texto Original
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Traducción IA
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Traducción Revisada
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Longitud
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.currentCellChanged.connect(self.on_row_selected)
        
        splitter.addWidget(self.table)
        
        # Panel inferior con detalles
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        # Panel de texto completo
        text_group = QGroupBox("Texto Completo (fila seleccionada)")
        text_layout = QVBoxLayout(text_group)
        
        self.text_detail = QTextEdit()
        self.text_detail.setReadOnly(True)
        self.text_detail.setMaximumHeight(150)
        self.text_detail.setPlaceholderText("Selecciona una fila para ver el texto completo...")
        text_layout.addWidget(self.text_detail)
        
        details_layout.addWidget(text_group)
        
        # Grupo de estadísticas
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout(stats_group)
        
        self.lbl_total = QLabel("Total: 0")
        stats_layout.addWidget(self.lbl_total)
        
        self.lbl_traducidos = QLabel("Traducidos: 0")
        stats_layout.addWidget(self.lbl_traducidos)
        
        self.lbl_revisados = QLabel("Revisados: 0")
        stats_layout.addWidget(self.lbl_revisados)
        
        self.lbl_pendientes = QLabel("Pendientes: 0")
        stats_layout.addWidget(self.lbl_pendientes)
        
        stats_layout.addStretch()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(300)
        stats_layout.addWidget(self.progress_bar)
        
        details_layout.addWidget(stats_group)
        
        # Grupo de contador de caracteres
        char_group = QGroupBox("Contador de Caracteres")
        char_layout = QHBoxLayout(char_group)
        
        self.lbl_char_original = QLabel("Original: 0")
        char_layout.addWidget(self.lbl_char_original)
        
        self.lbl_char_ia = QLabel("IA: 0")
        char_layout.addWidget(self.lbl_char_ia)
        
        self.lbl_char_revisada = QLabel("Revisada: 0")
        char_layout.addWidget(self.lbl_char_revisada)
        
        self.lbl_char_diff = QLabel("Diferencia: 0")
        char_layout.addWidget(self.lbl_char_diff)
        
        char_layout.addStretch()
        
        details_layout.addWidget(char_group)
        
        splitter.addWidget(details_widget)
        splitter.setSizes([600, 200])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Listo. Abre un archivo CSV para comenzar.")
        
    def open_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
            
        self.csv_file = Path(file_path)
        self.load_csv()
        
    def load_csv(self):
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.data = list(reader)
                
            self.populate_table()
            self.btn_save.setEnabled(True)
            self.statusBar().showMessage(f"Cargado: {self.csv_file.name} ({len(self.data)} textos)")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar CSV:\n{str(e)}")
            
    def populate_table(self):
        self.table.setRowCount(len(self.data))
        
        for row_idx, row_data in enumerate(self.data):
            # ID
            item = QTableWidgetItem(row_data.get('id', ''))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 0, item)
            
            # Archivo
            item = QTableWidgetItem(row_data.get('archivo', ''))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 1, item)
            
            # Offset
            item = QTableWidgetItem(row_data.get('offset', ''))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 2, item)
            
            # Tipo
            item = QTableWidgetItem(row_data.get('tipo', ''))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 3, item)
            
            # Texto Original
            item = QTableWidgetItem(row_data.get('texto_original', ''))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 4, item)
            
            # Traducción IA
            item = QTableWidgetItem(row_data.get('traduccion_ia', ''))
            self.table.setItem(row_idx, 5, item)
            
            # Traducción Revisada
            item = QTableWidgetItem(row_data.get('traduccion', ''))
            self.table.setItem(row_idx, 6, item)
            
            # Longitud
            original_len = len(row_data.get('texto_original', ''))
            item = QTableWidgetItem(str(original_len))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row_idx, 7, item)
            
        self.update_stats()
        
    def on_row_selected(self, current_row, current_col, prev_row, prev_col):
        if current_row < 0 or current_row >= len(self.data):
            return
            
        row_data = self.data[current_row]
        
        # Mostrar texto completo en el panel
        original = row_data.get('texto_original', '')
        ia_item = self.table.item(current_row, 5)
        ia_text = ia_item.text() if ia_item else ''
        rev_item = self.table.item(current_row, 6)
        rev_text = rev_item.text() if rev_item else ''
        
        detail_html = f"""
        <b>Texto Original:</b><br>
        <span style="background-color: #f0f0f0; padding: 5px; display: block;">{original}</span>
        <br>
        <b>Traducción IA:</b><br>
        <span style="background-color: #fffacd; padding: 5px; display: block;">{ia_text if ia_text else '(vacía)'}</span>
        <br>
        <b>Traducción Revisada:</b><br>
        <span style="background-color: #e6f3ff; padding: 5px; display: block;">{rev_text if rev_text else '(vacía)'}</span>
        """
        self.text_detail.setHtml(detail_html)
        
        # Actualizar contadores
        original_len = len(row_data.get('texto_original', ''))
        ia_item = self.table.item(current_row, 5)
        ia_len = len(ia_item.text()) if ia_item else 0
        rev_item = self.table.item(current_row, 6)
        rev_len = len(rev_item.text()) if rev_item else 0
        
        self.lbl_char_original.setText(f"Original: {original_len}")
        self.lbl_char_ia.setText(f"IA: {ia_len}")
        self.lbl_char_revisada.setText(f"Revisada: {rev_len}")
        
        # Calcular diferencia
        diff = rev_len - original_len if rev_len > 0 else ia_len - original_len
        diff_text = f"Diferencia: {diff:+d}"
        self.lbl_char_diff.setText(diff_text)
        
        # Colorear según diferencia
        if diff > 10:
            self.lbl_char_diff.setStyleSheet("color: red; font-weight: bold;")
        elif diff > 0:
            self.lbl_char_diff.setStyleSheet("color: orange;")
        else:
            self.lbl_char_diff.setStyleSheet("color: green;")
        
        # Advertir si hay caracteres fuera del rango Latin-1
        special_chars = set()
        for c in original:
            try:
                c.encode('latin-1')
            except UnicodeEncodeError:
                special_chars.add(c)
        if special_chars:
            chars_str = ''.join(sorted(special_chars))
            warning = f"<br><b style='color: orange;'>⚠ Algunos caracteres no estan en Latin-1: {chars_str}</b>"
            detail_html += warning
            self.text_detail.setHtml(detail_html)
            
    def apply_filters(self):
        search_text = self.search_input.text().lower()
        filter_type = self.filter_type.currentData()
        
        visible_rows = 0
        for row_idx in range(self.table.rowCount()):
            row_data = self.data[row_idx]
            
            # Filtro por tipo
            if filter_type != "all" and row_data.get('tipo', '') != filter_type:
                self.table.setRowHidden(row_idx, True)
                continue
                
            # Filtro por búsqueda
            if search_text:
                original = row_data.get('texto_original', '').lower()
                ia = row_data.get('traduccion_ia', '').lower()
                revisada = row_data.get('traduccion', '').lower()
                
                if search_text not in original and search_text not in ia and search_text not in revisada:
                    self.table.setRowHidden(row_idx, True)
                    continue
                    
            self.table.setRowHidden(row_idx, False)
            visible_rows += 1
            
        self.statusBar().showMessage(f"Mostrando {visible_rows} de {len(self.data)} textos")
        
    def update_stats(self):
        total = len(self.data)
        traducidos = sum(1 for row in self.data if row.get('traduccion_ia', '').strip())
        revisados = sum(1 for row in self.data if row.get('traduccion', '').strip())
        pendientes = total - revisados
        
        self.lbl_total.setText(f"Total: {total}")
        self.lbl_traducidos.setText(f"Traducidos IA: {traducidos}")
        self.lbl_revisados.setText(f"Revisados: {revisados}")
        self.lbl_pendientes.setText(f"Pendientes: {pendientes}")
        
        # Actualizar barra de progreso
        if total > 0:
            progress = int((revisados / total) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{progress}% ({revisados}/{total})")
            
    def save_csv(self):
        if not self.csv_file:
            return
            
        # Actualizar datos desde la tabla
        for row_idx in range(self.table.rowCount()):
            if row_idx >= len(self.data):
                break
                
            ia_item = self.table.item(row_idx, 5)
            rev_item = self.table.item(row_idx, 6)
            
            if ia_item:
                self.data[row_idx]['traduccion_ia'] = ia_item.text()
            if rev_item:
                self.data[row_idx]['traduccion'] = rev_item.text()
                
        # Guardar CSV
        try:
            fieldnames = ['id', 'archivo', 'offset', 'tipo', 'longitud_original', 
                         'texto_original', 'traduccion_ia', 'traduccion']
                         
            with open(self.csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for row in self.data:
                    # Asegurar que todos los campos existan
                    for field in fieldnames:
                        if field not in row:
                            row[field] = ''
                    writer.writerow(row)
                    
            self.statusBar().showMessage(f"Guardado: {self.csv_file.name}")
            self.update_stats()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar CSV:\n{str(e)}")


def main():
    app = QApplication(sys.argv)
    
    # Configurar estilo
    app.setStyle('Fusion')
    
    window = TraductorFM3()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
