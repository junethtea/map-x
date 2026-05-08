#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
#  Map-X - QGIS Floating Planning Tool (Lite Version)
# ---------------------------------------------------------------------------
#  PLUGIN NAME : Map-X
#  DESCRIPTION : Advanced spatial sync & compare tool (Lite) with smart Z-ordering and real-time statistical legend.
#  AUTHOR      : Jujun Junaedi
#  EMAIL       : jujun.junaedi@outlook.com
#  VERSION     : 1.0.2-lite
#  COPYRIGHT   : (c) 2024-2026 by Jujun Junaedi
#  LICENSE     : GPL-2.0-or-later
#  MOTTO       : "Sebaik-baiknya Manusia adalah yang bermanfaat bagi sesama"
# ---------------------------------------------------------------------------

import os
from qgis.PyQt.QtCore import Qt, QSize, QUrl
from qgis.PyQt.QtWidgets import (QAction, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                                 QPushButton, QLabel, QFrame, QMenu, QScrollArea, QMessageBox)
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom
from qgis.core import QgsProject, QgsSymbolLayerUtils, QgsRectangle, QgsCoordinateTransform

try:
    QT_WINDOW = Qt.Window
    QT_HORIZONTAL = Qt.Horizontal
    QT_VERTICAL = Qt.Vertical
    QT_SCROLL_AS_NEEDED = Qt.ScrollBarAsNeeded
    QT_SCROLL_ALWAYS_OFF = Qt.ScrollBarAlwaysOff
    QT_ALIGN_TOP = Qt.AlignTop
    QT_RICH_TEXT = Qt.RichText
    QMSG_INFO = QMessageBox.Information
    QMSG_WARN = QMessageBox.Warning
    QT_TEXT_BROWSER_INTERACTION = Qt.TextBrowserInteraction
except AttributeError:
    QT_WINDOW = Qt.WindowType.Window
    QT_HORIZONTAL = Qt.Orientation.Horizontal
    QT_VERTICAL = Qt.Orientation.Vertical
    QT_SCROLL_AS_NEEDED = Qt.ScrollBarPolicy.ScrollBarAsNeeded
    QT_SCROLL_ALWAYS_OFF = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    QT_ALIGN_TOP = Qt.AlignmentFlag.AlignTop
    QT_RICH_TEXT = Qt.TextFormat.RichText
    QMSG_INFO = QMessageBox.Icon.Information
    QMSG_WARN = QMessageBox.Icon.Warning
    QT_TEXT_BROWSER_INTERACTION = Qt.TextInteractionFlag.TextBrowserInteraction

STYLE_QSS = """
QWidget#MainWindow { background-color: #f8f9fa; }
QFrame#MapContainer { background-color: #ffffff; border: 1px solid #adb5bd; border-radius: 0px; }

QSplitter::handle { background-color: #dee2e6; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
QSplitter::handle:hover { background-color: #007bff; }

QPushButton#ToolBtn { 
    background-color: #ffffff; border: 1px solid #ced4da; border-radius: 1px; 
    font-weight: bold; min-width: 20px; max-width: 20px; height: 18px; font-size: 10px; margin: 0px; padding: 0px;
    color: #000000;
}
QPushButton#ToolBtn:hover { background-color: #e9ecef; color: #000000; }
QPushButton#ToolBtn:checked { background-color: #007bff; color: white; border-color: #0056b3; }

QPushButton#LayerBtn {
    background-color: #ffffff; border: 1px solid #ced4da; border-radius: 1px;
    padding: 0px 4px; height: 18px; font-size: 10px;
    color: #000000;
}
QPushButton#LayerBtn:hover { background-color: #e9ecef; color: #000000; }

QLabel#Title { font-weight: bold; font-size: 10px; color: #495057; margin-right: 3px; }
QFrame#LegendFrame { background-color: rgba(255, 255, 255, 235); border: 1px solid #6c757d; border-radius: 2px; }
QLabel#LegendHeader { font-size: 9px; font-weight: bold; color: #000; padding-bottom: 1px; text-decoration: underline; margin-top: 2px; }
QLabel#LegendLabel { font-size: 9px; color: #212529; }
"""

class MapXPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.main_canvas = self.iface.mapCanvas()
        self.window = None
        self.is_synced = False
        self.is_refreshing = False
        self.views = [] 
        self.current_splitter = None
        
        self.action_run = None
        self.action_about = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        icon = QIcon(icon_path)
        
        self.action_run = QAction(icon, "Map-X", self.iface.mainWindow())
        self.action_run.triggered.connect(self.run)
        
        self.action_about = QAction(icon, "About Map-X", self.iface.mainWindow())
        self.action_about.triggered.connect(self.show_about_dialog)
        
        self.iface.addToolBarIcon(self.action_run)
        self.iface.addPluginToMenu("&Map-X", self.action_run)
        self.iface.addPluginToMenu("&Map-X", self.action_about)

    def unload(self):
        self.iface.removeToolBarIcon(self.action_run)
        self.iface.removePluginMenu("&Map-X", self.action_run)
        self.iface.removePluginMenu("&Map-X", self.action_about)

    def show_about_dialog(self):
        msg = QMessageBox(self.iface.mainWindow() if hasattr(self, 'iface') else None)
        msg.setWindowTitle("About Map-X")
        msg.setIcon(QMSG_INFO)
        msg.setTextFormat(QT_RICH_TEXT)
        
        text = (
            "<div style='font-family: Arial, sans-serif;'>"
            "<h2 style='color: #2c3e50; margin-bottom: 5px;'>Map-X (Lite)</h2>"
            "<p style='color: #7f8c8d; margin-top: 0px; margin-bottom: 15px;'>Advanced spatial sync & compare tool with smart Z-ordering, and real-time statistical legend.</p>"
            "<table style='margin-bottom: 15px;' cellpadding='3'>"
            "<tr><td width='70'><b>Version:</b></td><td>1.0.2-lite</td></tr>"
            "<tr><td><b>Author:</b></td><td>Jujun Junaedi</td></tr>"
            "<tr><td><b>Contact:</b></td><td><a href='mailto:jujun.junaedi@outlook.com' style='color: #2980b9; text-decoration: none;'>jujun.junaedi@outlook.com</a></td></tr>"
            "</table>"
            "<hr style='border: 0; border-top: 1px solid #bdc3c7; margin-bottom: 15px;'>"
            "<p style='margin-bottom: 15px;'>Support the continuous development of this tool or upgrade to the Pro version for advanced features (Quad View, Export, Crosshair Tracking).</p>"
            "<div>"
            "<a href='https://paypal.me/junjunan81' style='text-decoration: none;'>"
            "<span style='background-color: #0070ba; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;'>Via PayPal</span></a>"
            "&nbsp;&nbsp;"
            "<a href='https://buymeacoffee.com/juneth' style='text-decoration: none;'>"
            "<span style='background-color: #f39c12; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;'>Via Buy me a coffee</span></a>"
            "&nbsp;&nbsp;"
            "<a href='https://saweria.co/juneth' style='text-decoration: none;'>"
            "<span style='background-color: #2ecc71; color: white; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 11px;'>Via Saweria (Local IDN)</span></a>"
            "</div>"
            "<br><p style='font-size: 10px; color: #95a5a6; margin-top: 10px;'>© 2024-2026 Jujun Junaedi. All Rights Reserved.</p>"
            "</div>"
        )
        msg.setText(text)
        msg.setStandardButtons(QMessageBox.Ok)
        
        if hasattr(msg, 'exec'):
            msg.exec()
        else:
            msg.exec_()

    def show_pro_message(self, feature_name):
        msg = QMessageBox(self.window)
        msg.setWindowTitle("Pro Feature Locked")
        msg.setIcon(QMSG_WARN)
        msg.setTextFormat(QT_RICH_TEXT)
        msg.setTextInteractionFlags(QT_TEXT_BROWSER_INTERACTION)

        html_text = f"""
        <div style='font-family: Arial, sans-serif; font-size: 12px;'>
            <h3 style='color: #d35400; margin-bottom: 5px;'>🔒 {feature_name} (Pro Version Only)</h3>
            <p style='margin-top:0;'>This feature is locked in the Lite version. Upgrade to unlock up to 4 synchronized views, crosshair tracking, and layout exporting!</p>
            <p><i>Fitur ini hanya tersedia di versi Pro. Upgrade untuk membuka hingga 4 tampilan map sinkron, crosshair tracking, dan export layout!</i></p>
            <hr style='border: 1px solid #ecf0f1; margin: 15px 0;'>
            <p style='margin-bottom: 5px;'><b>Get the Pro Version here / Dapatkan Versi Pro disini:</b></p>
            <ul style='margin-top: 0; padding-left: 20px;'>
                <li style='margin-bottom: 8px;'>🌐 <a href='https://jujunet.gumroad.com/l/mapxpro' style='color: #2980b9; text-decoration: none;'>Download via Gumroad (Global)</a></li>
                <li>🇮🇩 <a href='https://lynk.id/kangjun/l7glq3q1g6v8' style='color: #2980b9; text-decoration: none;'>Download via Lynk.id (Indonesia)</a></li>
            </ul>
        </div>
        """
        msg.setText(html_text)
        if hasattr(msg, 'exec'):
            msg.exec()
        else:
            msg.exec_()

    def run(self):
        if not self.window:
            self.window = QWidget() 
            self.window.setWindowFlags(QT_WINDOW)
            
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
            if os.path.exists(icon_path):
                self.window.setWindowIcon(QIcon(icon_path))
                
            self.window.setWindowTitle("Map-X v1.0.2 Lite | ©Jujun.J")
            self.window.setObjectName("MainWindow")
            self.window.resize(1200, 700)
            self.window.setStyleSheet(STYLE_QSS)
            
            self.layout_utama = QVBoxLayout(self.window)
            self.layout_utama.setContentsMargins(0, 0, 0, 0)
            self.layout_utama.setSpacing(0)
            
            self.view1 = self.create_map_view("Map 1", is_master=True)
            self.view2 = self.create_map_view("Map 2", is_master=False)
            self.views = [self.view1, self.view2]
            
            self.set_layout_mode()
            self.setup_connections()
        
        self.window.show()

    def set_layout_mode(self):
        if self.current_splitter:
            self.current_splitter.setParent(None)
            self.current_splitter.deleteLater()
        
        for view in self.views:
            view.setParent(None)
            view.setVisible(False)

        self.current_splitter = QSplitter(QT_HORIZONTAL)
        self.current_splitter.setHandleWidth(1) 
        self.current_splitter.addWidget(self.view1)
        self.current_splitter.addWidget(self.view2)
        self.view1.setVisible(True)
        self.view2.setVisible(True)
        self.current_splitter.setSizes([10000, 10000])

        self.layout_utama.addWidget(self.current_splitter)

    def create_map_view(self, title, is_master=False):
        container = QFrame()
        container.setObjectName("MapContainer")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QHBoxLayout()
        header.setContentsMargins(2, 1, 2, 1)
        header.setSpacing(2)
        header.addWidget(QLabel(title, objectName="Title"))
        
        if is_master:
            btn_layout = QPushButton("⊞", objectName="ToolBtn")
            btn_layout.setToolTip("Change Layout")
            layout_menu = QMenu(btn_layout)
            layout_menu.addAction("Dual View (2)").triggered.connect(self.set_layout_mode)
            layout_menu.addAction("Triple View (3) 🔒").triggered.connect(lambda: self.show_pro_message("Triple View Layout"))
            layout_menu.addAction("Quad View (4) 🔒").triggered.connect(lambda: self.show_pro_message("Quad View Layout"))
            btn_layout.setMenu(layout_menu)
            header.addWidget(btn_layout)
            
            btn_export = QPushButton("📸", objectName="ToolBtn")
            btn_export.setToolTip("Export Map-X Layout (Pro Version)")
            btn_export.clicked.connect(lambda: self.show_pro_message("Export to Image"))
            header.addWidget(btn_export)
        
        btn_layer = QPushButton("Layer", objectName="LayerBtn")
        btn_layer.clicked.connect(lambda: self.open_layer_menu(container))
        header.addWidget(btn_layer)
        
        btn_legend_toggle = QPushButton("L", objectName="ToolBtn")
        btn_legend_toggle.setCheckable(True) 
        btn_legend_toggle.setToolTip("Toggle Legend Mode")
        btn_legend_toggle.clicked.connect(self.refresh_all_legends) 
        header.addWidget(btn_legend_toggle)
        
        header.addStretch()
        
        btn_pan = QPushButton("✋", objectName="ToolBtn") 
        btn_in = QPushButton("+", objectName="ToolBtn")
        btn_out = QPushButton("-", objectName="ToolBtn")
        btn_zoom_lay = QPushButton("Z", objectName="ToolBtn")
        btn_zoom_lay.setToolTip("Zoom to Selected Data Layers")
        btn_zoom_lay.clicked.connect(lambda: self.zoom_to_selected_layers(container))
        
        header.addWidget(btn_pan)
        header.addWidget(btn_in)
        header.addWidget(btn_out)
        header.addWidget(btn_zoom_lay)
        
        if is_master:
            self.btn_crosshair = QPushButton("⌖", objectName="ToolBtn")
            self.btn_crosshair.setToolTip("Crosshair Tracking (Pro Version)")
            self.btn_crosshair.clicked.connect(lambda: self.show_pro_message("Crosshair Tracking"))
            header.addWidget(self.btn_crosshair)
            
            self.btn_synch = QPushButton("S", objectName="ToolBtn")
            self.btn_synch.setCheckable(True)
            self.btn_synch.setToolTip("Sync Map Extent")
            self.btn_synch.toggled.connect(self.toggle_sync)
            header.addWidget(self.btn_synch)
        
        btn_toggle = QPushButton("▢", objectName="ToolBtn")
        btn_toggle.setToolTip("Maximize View")
        btn_toggle.clicked.connect(lambda: self.toggle_maximize(container))
        header.addWidget(btn_toggle)
        
        canvas = QgsMapCanvas()
        canvas.setProject(QgsProject.instance()) 
        canvas.setCanvasColor(QColor("white"))
        canvas.setDestinationCrs(QgsProject.instance().crs())
        canvas.setMouseTracking(True)
        canvas.viewport().setMouseTracking(True)
        
        container.pan_tool = QgsMapToolPan(canvas)
        container.zoom_in_tool = QgsMapToolZoom(canvas, False)
        container.zoom_out_tool = QgsMapToolZoom(canvas, True)
        canvas.setMapTool(container.pan_tool)
        
        btn_pan.clicked.connect(lambda: canvas.setMapTool(container.pan_tool))
        btn_in.clicked.connect(lambda: canvas.setMapTool(container.zoom_in_tool))
        btn_out.clicked.connect(lambda: canvas.setMapTool(container.zoom_out_tool))

        legend_frame = QFrame(canvas)
        legend_frame.setObjectName("LegendFrame")
        legend_frame.move(5, 5)
        
        frame_layout = QVBoxLayout(legend_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setVerticalScrollBarPolicy(QT_SCROLL_AS_NEEDED)
        scroll.setHorizontalScrollBarPolicy(QT_SCROLL_ALWAYS_OFF)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        
        legend_items_layout = QVBoxLayout(scroll_content)
        legend_items_layout.setContentsMargins(4, 4, 4, 4)
        legend_items_layout.setSpacing(2)
        legend_items_layout.setAlignment(QT_ALIGN_TOP) 
        
        scroll.setWidget(scroll_content)
        frame_layout.addWidget(scroll)
        legend_frame.hide()
        
        layout.addLayout(header)
        layout.addWidget(canvas)
        
        container.canvas = canvas
        container.legend_frame = legend_frame
        container.legend_layout = legend_items_layout
        container.btn_legend_toggle = btn_legend_toggle 
        container.selected_layers = []
        return container

    def zoom_to_selected_layers(self, container):
        if not container.selected_layers:
            return
        
        extent = None
        
        canvas_crs = container.canvas.mapSettings().destinationCrs()
        transform_context = QgsProject.instance().transformContext()
        base_keys = ['google', 'satellite', 'osm', 'bing', 'street', 'hybrid', 'terang', 'gelap', 'map']
        
        for layer in container.selected_layers:
            lname = layer.name().lower()
            if any(k in lname for k in base_keys):
                continue
                
            try:
                lay_ext = layer.extent()
                if not lay_ext.isNull() and not lay_ext.isEmpty():
                    if layer.crs().isValid() and canvas_crs.isValid() and layer.crs() != canvas_crs:
                        xform = QgsCoordinateTransform(layer.crs(), canvas_crs, transform_context)
                        lay_ext = xform.transformBoundingBox(lay_ext)
                    
                    if extent is None:
                        extent = QgsRectangle(lay_ext)
                    else:
                        extent.combineExtentWith(lay_ext)
            except Exception:
                continue
            
        if extent is not None:
            extent.scale(1.1)
            container.canvas.setExtent(extent)
            container.canvas.refresh()

    def toggle_maximize(self, target_container):
        currently_maximized = False
        
        for view in self.views:
            if view != target_container and not view.isVisible() and view.property("was_visible"):
                currently_maximized = True
                break
        
        if currently_maximized:
            for view in self.views:
                if view.property("was_visible"):
                    view.setVisible(True)
        else:
            for view in self.views:
                if view.isVisible():
                    view.setProperty("was_visible", True)
                    if view != target_container:
                        view.setVisible(False)
                else:
                    view.setProperty("was_visible", False)

    def open_layer_menu(self, container):
        menu = QMenu(self.window) 
        unique_layers = {}
        
        for layer in QgsProject.instance().mapLayers().values():
            if layer.name() not in unique_layers:
                unique_layers[layer.name()] = layer
                
        sorted_layer_names = sorted(unique_layers.keys())
        
        for name in sorted_layer_names:
            layer = unique_layers[name]
            action = QAction(name, menu, checkable=True)
            action.setChecked(layer in container.selected_layers)
            action.triggered.connect(lambda checked, l=layer, c=container: self.update_layers(c, l, checked))
            menu.addAction(action)
            
        btn_layer = container.findChild(QPushButton, "LayerBtn")
        pos = container.mapToGlobal(btn_layer.pos()) if btn_layer else container.mapToGlobal(container.rect().topLeft())
        
        if hasattr(menu, 'exec'):
            menu.exec(pos)
        else:
            menu.exec_(pos)

    def _apply_z_order(self, container):
        base_keys = ['google', 'satellite', 'osm', 'bing', 'street', 'hybrid', 'terang', 'gelap', 'map']
        top_keys = ['gcell', 'site', 'tower', 'bts', 'node', 'enodeb']
        
        base_layers, top_layers, data_layers = [], [], []
        valid_layers = list(QgsProject.instance().mapLayers().values())
        
        container.selected_layers = [layer for layer in container.selected_layers if layer in valid_layers]
        
        for layer in container.selected_layers:
            try:
                lname = layer.name().lower()
                if any(k in lname for k in base_keys):
                    base_layers.append(layer)
                elif any(k in lname for k in top_keys):
                    top_layers.append(layer)
                else:
                    data_layers.append(layer) 
            except RuntimeError:
                continue
        
        sorted_layers = top_layers + data_layers + base_layers
        container.canvas.setLayers(sorted_layers)
        
        container.canvas.setDestinationCrs(QgsProject.instance().crs())
        try:
            container.canvas.mapSettings().setTransformContext(QgsProject.instance().transformContext())
        except AttributeError:
            pass
            
        container.canvas.refresh()

    def update_layers(self, container, layer, checked):
        lname = layer.name().lower()
        is_global_layer = any(k in lname for k in ['map', 'osm', 'google', 'satellite', 'bing', 'gcell', 'site'])
        
        def apply_to_container(tgt_container):
            if checked:
                if layer not in tgt_container.selected_layers: 
                    tgt_container.selected_layers.append(layer)
            else:
                if layer in tgt_container.selected_layers: 
                    tgt_container.selected_layers.remove(layer)
            self._apply_z_order(tgt_container)

        if container == self.view1 and is_global_layer:
            for view in self.views:
                apply_to_container(view)
        else:
            apply_to_container(container)
            
        self.refresh_all_legends()

    def calculate_stats(self, layer):
        renderer = layer.renderer()
        if not renderer:
            return None, 0
        
        counts = {}
        total = 0
        r_type = renderer.type()
        
        try:
            if r_type == "graduatedSymbol":
                ranges = renderer.ranges()
                field_idx = layer.fields().indexOf(renderer.classAttribute())
                for feat in layer.getFeatures():
                    val = feat.attributes()[field_idx]
                    if val is None:
                        continue 
                    for rng in ranges:
                        if rng.lowerValue() <= val <= rng.upperValue():
                            lbl = rng.label()
                            counts[lbl] = counts.get(lbl, 0) + 1
                            total += 1
                            break
                            
            elif r_type == "categorizedSymbol":
                cats = renderer.categories()
                field_idx = layer.fields().indexOf(renderer.classAttribute())
                for feat in layer.getFeatures():
                    val = feat.attributes()[field_idx]
                    for cat in cats:
                        if str(val) == str(cat.value()):
                            lbl = cat.label()
                            counts[lbl] = counts.get(lbl, 0) + 1
                            total += 1
                            break
        except Exception:
            return None, 0
            
        return counts, total

    def refresh_all_legends(self):
        for container in self.views:
            if not container.isVisible():
                continue
            
            layout = container.legend_layout
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            all_data_layers = [layer for layer in container.canvas.layers() if not any(k in layer.name().lower() for k in ['google', 'satellite', 'osm', 'bing'])]
            
            show_all_mode = container.btn_legend_toggle.isChecked()
            layers_to_show = []

            if all_data_layers:
                if show_all_mode:
                    layers_to_show = all_data_layers
                else:
                    priority_layer = None
                    for layer in all_data_layers:
                         if layer.renderer().type() == "graduatedSymbol":
                             priority_layer = layer
                             break
                    
                    if not priority_layer:
                        for layer in all_data_layers:
                            if layer.renderer().type() == "categorizedSymbol":
                                if not any(k in layer.name().lower() for k in ['gcell', 'site', 'tower', 'bts']):
                                    priority_layer = layer
                                    break
                    
                    if not priority_layer:
                        for layer in all_data_layers:
                            if layer.renderer().type() == "categorizedSymbol":
                                priority_layer = layer
                                break
                    
                    if not priority_layer and all_data_layers:
                        first = all_data_layers[0]
                        if not any(k in first.name().lower() for k in ['gcell', 'site']):
                            priority_layer = first
                        else:
                            priority_layer = first 

                    if priority_layer:
                        layers_to_show = [priority_layer]

            if layers_to_show:
                container.legend_frame.show()
                container.legend_frame.raise_() 
                
                max_w = 100 
                total_h = 10 
                
                for layer in layers_to_show:
                    header = QLabel(layer.name(), objectName="LegendHeader")
                    layout.addWidget(header)
                    
                    metrics = header.fontMetrics()
                    header_w = metrics.horizontalAdvance(layer.name()) + 20
                    max_w = max(max_w, header_w)
                    total_h += 18
                    
                    counts, total_feats = self.calculate_stats(layer)
                    renderer = layer.renderer()
                    
                    if renderer:
                        for item in renderer.legendSymbolItems():
                            row_w = QHBoxLayout()
                            row_w.setContentsMargins(0, 0, 0, 0)
                            row_w.setSpacing(3)
                            
                            symbol = item.symbol()
                            if symbol:
                                pixmap = QgsSymbolLayerUtils.symbolPreviewPixmap(symbol, QSize(10, 10))
                                icon_lbl = QLabel()
                                icon_lbl.setPixmap(pixmap)
                                row_w.addWidget(icon_lbl)
                            
                            label_txt = item.label()
                            if counts and total_feats > 0:
                                count = counts.get(label_txt, 0)
                                percent = (count / total_feats) * 100
                                display_txt = f"{label_txt} • {count} ({percent:.1f}%)"
                            else:
                                display_txt = label_txt
                                
                            txt_lbl = QLabel(display_txt, objectName="LegendLabel")
                            row_w.addWidget(txt_lbl)
                            row_w.addStretch()
                            
                            row_widget = QWidget()
                            row_widget.setLayout(row_w)
                            layout.addWidget(row_widget)
                            
                            text_w = txt_lbl.fontMetrics().horizontalAdvance(display_txt) + 30
                            max_w = max(max_w, text_w)
                            total_h += 16

                final_w = min(max_w, 200)
                final_h = min(total_h, 250)
                container.legend_frame.setFixedSize(final_w, final_h)
            else:
                container.legend_frame.hide()

    def toggle_sync(self, checked):
        self.is_synced = checked
        if checked:
            self.apply_sync(self.main_canvas.extent(), "main")

    def setup_connections(self):
        self.main_canvas.extentsChanged.connect(lambda: self.apply_sync(self.main_canvas.extent(), "main"))
        self.view1.canvas.extentsChanged.connect(lambda: self.apply_sync(self.view1.canvas.extent(), "v1"))
        self.view2.canvas.extentsChanged.connect(lambda: self.apply_sync(self.view2.canvas.extent(), "v2"))

    def apply_sync(self, extent, source_id):
        if not self.is_synced or self.is_refreshing:
            return
            
        self.is_refreshing = True
        
        canvases = {
            "main": self.main_canvas,
            "v1": self.view1.canvas,
            "v2": self.view2.canvas
        }
        
        for cid, canvas in canvases.items():
            if cid != source_id:
                canvas.blockSignals(True)
                canvas.setExtent(extent)
                canvas.refresh()
                canvas.blockSignals(False)
                
        self.is_refreshing = False