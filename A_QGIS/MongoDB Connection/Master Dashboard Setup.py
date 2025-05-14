# Import libraries - install respective modules when prompt
import os
import sys
import pymongo
import glob
import shutil
import subprocess
from PyQt5.QtGui import *
from qgis.PyQt.QtWidgets import (
    QFileDialog,
    QDockWidget,
    QVBoxLayout,
    QGridLayout,
    QWidget,
    QTabWidget,
    QComboBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QSizePolicy,
    QHeaderView,
    QMessageBox,
)
from qgis.PyQt.QtCore import Qt, QUrl, QSize, QRectF
from PyQt5.QtWebEngineWidgets import QWebEngineView
from qgis.gui import QgsVertexMarker
from qgis.core import (
    QgsProject,
    QgsLayerTreeGroup,
    QgsRectangle,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsPointXY,
)
from qgis.utils import iface
from pymongo import MongoClient
import pandas as pd
import gzip
import base64
import json


# ---------------------
# DashboardWidget Class
# ---------------------
class DashboardWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Naming window
        self.setWindowTitle("Road Inspection Analytics System")

        # Initialising
        self.db = self.connect_to_database() # Connect to mongodb
        self.current_defect_index = 0  # Keep track of the current defect
        self.bboxes = []  # Initialize the bboxes list
        self.defect_info_label = QLabel()  # Label to show defect info

        # Tab widget
        self.tab_widget = QTabWidget()

        # region <Tab 1>
        # Tab 1, General Dashboard
        self.web_view_1 = QWebEngineView()

        # Set base path dynamically
        script_path = os.path.abspath(sys.argv[0])
        folder_path = os.path.dirname(script_path)
        base_path = os.path.join(
            folder_path, "A_QGIS", "MongoDB Connection", "dashboard"
        )

        # Paths to HTML, CSS, JS, and JSON files
        html_file_path = os.path.join(base_path, "dashboard.html")
        css_file_path = os.path.join(base_path, "dashboard.css")
        js_file_path = os.path.join(base_path, "dashboard.js")
        json_file_path = os.path.join(base_path, "data.json")

        # Export df_inspection_dates to JSON
        df_inspection_dates.to_json(json_file_path, orient="records")

        # Read and base64 encode the CSS content
        with open(css_file_path, "r") as css_file:
            css_content = css_file.read()
        css_base64 = base64.b64encode(css_content.encode("utf-8")).decode("utf-8")

        # Read the JavaScript content
        with open(js_file_path, "r") as js_file:
            js_content = js_file.read()

        # Convert the DataFrame to JSON
        json_data = df_inspection_dates.to_json(orient="records")

        # Compress the JSON data
        compressed_data = gzip.compress(json_data.encode("utf-8"))

        # Encode the compressed data in base64
        compressed_base64_data = base64.b64encode(compressed_data).decode("utf-8")

        # Read and modify HTML content
        with open(html_file_path, "r") as file:
            html_content_1 = file.read()
            # Embed the base64 encoded CSS directly in the HTML
            html_content_1 = html_content_1.replace(
                'href="dashboard.css"', f'href="data:text/css;base64,{css_base64}"'
            )
            # Embed the JavaScript directly in the HTML
            html_content_1 = html_content_1.replace(
                '<script src="dashboard.js"></script>', f"<script>{js_content}</script>"
            )
            # Embed the compressed and base64 encoded JSON data directly in the HTML
            html_content_1 = html_content_1.replace(
                "</head>",
                f'<script>const compressedJsonData = "{compressed_base64_data}";</script></head>',
            )
            # Inject batch status and defect count into HTML
            html_content_1 = html_content_1.replace(
                "</head>",
                f"<script>const batchStatus = {json.dumps(batch_status)}; const totalDefectCount = {total_defect_count};</script></head>",
            )

        self.web_view_1.setHtml(html_content_1)

        # Create export button for the General tab
        self.export_button = QPushButton("Export to PDF")
        self.export_button.clicked.connect(self.export_data)
        self.export_button.setMinimumSize(150, 50)

        # Create a vertical layout for the General tab
        self.general_tab_layout = QVBoxLayout()
        self.general_tab_layout.addWidget(self.web_view_1)
        self.general_tab_layout.addWidget(self.export_button)
        self.general_tab_layout.setContentsMargins(
            0, 0, 0, 0
        )  # Remove margins if needed

        # Create container for the General tab
        self.general_tab_container = QWidget()
        self.general_tab_container.setLayout(self.general_tab_layout)
        self.tab_widget.addTab(self.general_tab_container, "General")

        # endregion

        # region <Tab 2>
        # Tab 2, Defect Analysis
        self.web_view_2 = QWebEngineView()

        # Filter dropdowns
        self.batch_filter = [QComboBox()]
        self.batch_set = ["Nil"]

        self.year_filter = [QComboBox()]
        self.year_set = ["Nil"]

        self.month_filter = [QComboBox()]
        self.month_set = ["Nil"]

        self.day_filter = [QComboBox()]
        self.day_set = ["Nil"]

        self.area_filter = [QComboBox()]
        self.area_set = ["Nil"]

        self.defect_filter = [QComboBox()]
        self.defect_set = ["Nil"]

        self.defecttype_filter = [QComboBox()]
        self.defecttype_set = ["Nil"]

        self.severity_filter = [QComboBox()]
        self.severity_set = ["Nil"]

        self.filter_list = [
            self.batch_filter,
            self.year_filter,
            self.month_filter,
            self.day_filter,
            self.area_filter,
            self.defect_filter,
            self.defecttype_filter,
            self.severity_filter,
        ]
        self.set_list = [
            self.batch_set,
            self.year_set,
            self.month_set,
            self.day_set,
            self.area_set,
            self.defect_set,
            self.defecttype_set,
            self.severity_set,
        ]

        for filter_item in self.filter_list:
            filter_item[0].addItem("Nil")

        self.reconnect_dropdown()

        # Labels for filters
        self.label_batch = QLabel("Batch Filter:")
        self.label_year = QLabel("Year Filter:")
        self.label_month = QLabel("Month Filter:")
        self.label_day = QLabel("Day Filter:")
        self.label_area = QLabel("Area Filter:")
        self.label_defect = QLabel("Defect Filter:")
        self.label_defecttype = QLabel("Defect Type Filter:")
        self.label_severity = QLabel("Severity Filter:")
        self.label_list = [
            self.label_batch,
            self.label_year,
            self.label_month,
            self.label_day,
            self.label_area,
            self.label_defect,
            self.label_defecttype,
            self.label_severity,
        ]

        # Table
        self.label_instructions = QLabel(
            'Click on <b>"Inspect"</b> button to zoom into selected defect(s) on map canvas.<br>'
            'Click on <b>"View"</b> button to view image and/or change severity levels.'
        )
        self.label_instructions.setAlignment(Qt.AlignCenter)  # Align center

        # Create a QTableWidget for displaying data
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels(
            [
                "IMAGE NAME",
                "LOCATION",
                "DEFECT(S)",
                "SEVERITY",
                "ZOOM",
                "VIEW IMAGE",
                "BATCH",
            ]
        )

        # Set minimum size for the table widget
        self.table_widget.setMinimumSize(
            600, 400
        )  # Adjust the size according to your needs

        # Populate table with some data and buttons
        self.populate_table()

        self.dashboard_2_layout = QGridLayout()

        # Add labels and filters
        for i in range(len(self.filter_list)):
            self.dashboard_2_layout.addWidget(self.label_list[i], i, 0)
            self.dashboard_2_layout.addWidget(self.filter_list[i][0], i, 1)
            
        # Add export to excel button
        self.export_to_excel_button = QPushButton("Export to Excel")
        self.export_to_excel_button.clicked.connect(self.export_to_excel)
        self.dashboard_2_layout.addWidget(self.export_to_excel_button, 8, 0, 1, 1)

        # Add the button beneath all of the filters
        self.clear_button = QPushButton("Clear Filters")
        self.clear_button.clicked.connect(self.clear_filters)
        self.dashboard_2_layout.addWidget(self.clear_button, 8, 1, 1, 1)

        # Add a spacer to create some space between filters and table
        self.dashboard_2_layout.addWidget(QWidget(), 9, 0, 1, 2)

        # Other widgets
        self.dashboard_2_layout.addWidget(self.label_instructions, 10, 0, 1, 2)
        self.dashboard_2_layout.addWidget(self.table_widget, 11, 0, 1, 2)
        self.dashboard_2_layout.addWidget(self.web_view_2, 12, 0, 1, 2)

        # Container
        self.dashboard_2_container = QWidget()
        self.dashboard_2_container.setLayout(self.dashboard_2_layout)

        self.tab_widget.addTab(self.dashboard_2_container, "Defect Analysis")
        # endregion

        # region <Tab 3>
        # Tab 3, Image Viewer
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        self.defect_label = QLabel()
        self.defect_label.setAlignment(Qt.AlignLeft)
        self.defect_combo_box = QComboBox()

        # Severity options
        self.severity_list = ["1", "2", "3"]

        # Add items to the defect combo box
        self.defect_combo_box.addItems(self.severity_list)

        # Current severity label
        self.current_severity_label = QLabel(
            f"---------------------------------------------------------Note: To change severity level and/or view of defects, hover over to 'Defect Analysis' dashboard and click on 'View Image'---------------------------------------------------------"
        )
        self.current_severity_label.setAlignment(Qt.AlignCenter)

        # Create navigation buttons
        self.left_button = QPushButton("Previous Defect ID")
        self.right_button = QPushButton("Next Defect ID")
        self.save_button = QPushButton("Save")

        # Initially hide the severity dropdown and save button
        self.defect_combo_box.setVisible(False)
        self.save_button.setVisible(False)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)  # Center align the image

        # Create a grid layout for the Image Viewer tab
        self.image_viewer_layout = QGridLayout()
        self.image_viewer_layout.addWidget(self.current_severity_label, 0, 4, 1, 2)

        self.image_viewer_container = QWidget()
        self.image_viewer_container.setLayout(self.image_viewer_layout)
        self.tab_widget.addTab(self.image_viewer_container, "Image Viewer")
        self.to_export_to_excel = self.df_inspection_copy

        # Initially hide the elements
        self.hide_image_viewer_elements()

        # Showing the dashboard
        layout = QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        container = QWidget()
        container.setLayout(layout)
        self.setWidget(container)

        # Ensure the layout updates
        self.general_tab_container.adjustSize()
        self.general_tab_container.update()

        self.marker = None

    # endregion
    
    def export_to_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "document1", "Excel Files (*.xlsx)"
        )
        
        # Drop D M Y columns
        self.to_export_to_excel.drop(columns=["D", "M", "Y"], inplace=True)
        
        if file_path:
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                # Write the data to Excel
                self.to_export_to_excel.to_excel(writer, sheet_name="Sheet1", index=False)
                
                # Access the workbook and worksheet
                workbook = writer.book
                worksheet = workbook["Sheet1"]
                
                # Set column widths
                for column in self.to_export_to_excel:
                    column_width = max(
                        self.to_export_to_excel[column].astype(str).str.len().max(), len(column)
                    )
                    col_idx = self.to_export_to_excel.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = column_width

    def toggle_layer_visibility(self, filtered_data):
        # Get the root of the layer tree
        inspection_dates_folder = (
            QgsProject.instance().layerTreeRoot().findGroup("Inspection Dates")
        )
        date_folders = [
            child
            for child in inspection_dates_folder.children()
            if isinstance(child, QgsLayerTreeGroup)
        ]

        # Loop through each date folder and fetch layers
        for date_folder in date_folders:
            date_folder_name = date_folder.name()
            for layer in date_folder.findLayers():
                layer_name = layer.name()
                layer_id = layer.layerId()
                qgis_layer = layer.layer()

                if (
                    filtered_data["LayerID"].str.contains(layer_id).any()
                    and layer_name != date_folder_name
                ):
                    layer.setItemVisibilityChecked(True)
                    date_folder.setItemVisibilityChecked(True)

                    # Get the list of field names
                    field_names = [field.name() for field in qgis_layer.fields()]
                    print(field_names)

                    # Get the list of Image IDs to be visible
                    feature_ids = filtered_data["ImageID"].astype(str).tolist()

                    # Create a filter expression for visible features
                    filter_expression = f'"ImageID" IN ({",".join(feature_ids)})'

                    # Apply the filter to the layer
                    qgis_layer.setSubsetString(filter_expression)
                else:
                    layer.setItemVisibilityChecked(False)
                    # Clear the filter
                    qgis_layer.setSubsetString("")

            # Refresh the layer to apply the changes
            qgis_layer.triggerRepaint()

        # Do the same for the all defects layer
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if child.name() == "All Defects":
                all_defects_layer = child
        qgis_layer_ad = all_defects_layer.layer()

        # Get the list of Image IDs to be visible
        feature_ids_ad = filtered_data["ImageID"].astype(str).tolist()

        # Create a filter expression for visible features
        filter_expression_ad = f'"ImageID" IN ({",".join(feature_ids_ad)})'

        # Apply the filter to the layer
        qgis_layer_ad.setSubsetString(filter_expression_ad)

    # Export html as pdf
    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "document1", "PDF Files (*.pdf)"
        )
        if file_path:
            self.web_view_1.page().printToPdf(file_path)

    def clear_filters(self):
        for filter_item in self.filter_list:
            filter_item[0].setCurrentText("Nil")

        self.filter_table()

    # region <fetch_defect_ids functions>
    def fetch_defect_ids(self, image_id):
        db = self.get_database()  # Assuming this connects to your MongoDB
        defects = db["defect"].find({"imageID": image_id})

        defect_severity_map = {}

        for defect in defects:
            defect_id = str(defect.get("defectID", "NULL")).strip()
            severity = str(defect.get("severity", "NULL")).strip()

            # Debugging output
            print(f"Fetched from MongoDB - defectID: {defect_id}, severity: {severity}")

            if (
                defect_id not in defect_severity_map
            ):  # Ensure only unique defect IDs are stored
                defect_severity_map[defect_id] = severity

        # Debugging outputs
        print(f"Final defect_severity_map: {defect_severity_map}")

        return list(defect_severity_map.keys()), list(defect_severity_map.values())

    # endregion

    # region <populate_table>
    def populate_table(self):
        df_inspection_copy = df_inspection_dates.copy()
        self.df_inspection_copy = (
            df_inspection_copy.groupby("ImageID").agg(combine_values).reset_index()
        )
        self.df_inspection_copy["Layer Name"] = self.df_inspection_copy[
            "Layer Name"
        ].apply(lambda x: x.split(", ")[0])

        self.populate_filters(filtered_data=self.df_inspection_copy)

        # Fetch defect IDs and update the table
        self.update_table(self.df_inspection_copy)
    # endregion


    # region <update_table>
    def update_table(self, df):
        self.table_widget.clearContents()

        # Setting number of rows based on the data
        self.table_widget.setRowCount(len(df))

        for index, row in df.iterrows():
            item_defect = QTableWidgetItem(row["Type"])
            item_road = QTableWidgetItem(row["Road"])
            item_severity = QTableWidgetItem(row["Severity"])
            item_batch = QTableWidgetItem(str(row["BatchID"]))
            item_imagename = QTableWidgetItem(str(row["OImagePath"].split("\\")[-1]))

            # Zoom btn
            zoomBtn = QPushButton("Inspect")
            zoomBtn.clicked.connect(
                lambda checked, lon=row["Longitude"], lat=row[
                    "Latitude"
                ]: self.handle_zoom_btn_click(lon=lon, lat=lat)
            )
            zoomBtn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

            # View btn
            viewBtn = QPushButton("View")
            defects = row["Type"].split(",")
            defect_ids = row["DefectID"].split(",")  # Ensure defect IDs are available
            severities = row["Severity"].split(",")

            viewBtn.clicked.connect(
                lambda checked, oImagePath=row[
                    "OImagePath"
                ], defects=defects, defect_ids=defect_ids, severities=severities: self.handle_view_btn_click(
                    oImagePath=oImagePath,
                    defects=defects,
                    defect_ids=defect_ids,
                    severities=severities,
                )
            )
            viewBtn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

            self.table_widget.setItem(index, 0, item_imagename)
            self.table_widget.setItem(index, 1, item_road)
            self.table_widget.setItem(index, 2, item_defect)
            self.table_widget.setItem(index, 3, item_severity)
            self.table_widget.setCellWidget(index, 4, zoomBtn)
            self.table_widget.setCellWidget(index, 5, viewBtn)
            self.table_widget.setItem(index, 6, item_batch)

        # Adjust column widths to fit content
        self.table_widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
    # endregion

    def clear_dropdown(self):
        # Clear all items from each dropdown
        for filter_item in self.filter_list:
            filter_item[0].clear()

        # Add "Nil" item to each dropdown
        for filter_item in self.filter_list:
            filter_item[0].addItem("Nil")

    def reconnect_dropdown(self):
        self.set_dropdown_index()

        for filter_item in self.filter_list:
            filter_item[0].currentIndexChanged.connect(self.filter_table)

    def disconnect_dropdown(self):
        for filter_item in self.filter_list:
            filter_item[0].currentIndexChanged.disconnect(self.filter_table)

    def set_dropdown_index(self):
        for i in range(len(self.filter_list)):
            self.filter_list[i][0].setCurrentText(self.set_list[i][0])

    # region <populate_filters>
    def populate_filters(self, filtered_data):
        self.disconnect_dropdown()
        self.clear_dropdown()

        ubatch_numeric = sorted([int(batch) for batch in filtered_data["BatchID"].unique()])

        # Convert back to strings after sorting
        ubatch = [str(batch) for batch in ubatch_numeric]
        self.batch_filter[0].addItems(ubatch)

        uyear = sorted(filtered_data["Y"].unique())
        self.year_filter[0].addItems(uyear)

        umonth = sorted(filtered_data["M"].unique())
        self.month_filter[0].addItems(umonth)

        uday = sorted(filtered_data["D"].unique())
        self.day_filter[0].addItems(uday)

        uarea = sorted(filtered_data["Town"].unique())
        # uregion = sorted(filtered_data["Region"].unique())
        # self.area_filter[0].addItems(uregion)
        self.area_filter[0].addItems(uarea)

        udefect = sorted(filtered_data["Layer Name"].unique())
        self.defect_filter[0].addItems(udefect)

        udefecttype = []
        for row in filtered_data["Type"]:
            udefecttype.extend(row.split(", "))
        udefecttype = sorted(list(set(udefecttype)))
        # Putting NULL at the start and take it out from inside the list if exists
        if "NULL" in udefecttype:
            udefecttype.remove("NULL")
            udefecttype.insert(0, "NULL")

        self.defecttype_filter[0].addItems(udefecttype)

        useverity = []
        for row in filtered_data["Severity"]:
            useverity.extend(row.split(", "))
        useverity = sorted(list(set(useverity)))

        self.severity_filter[0].addItems(useverity)

        self.reconnect_dropdown()

    # endregion

    # region <filter_table>
    def filter_table(self):
        for i in range(len(self.filter_list)):
            self.set_list[i][0] = self.filter_list[i][0].currentText()

        def safe_reset_index(df):
            if "level_0" in df.columns:
                df = df.drop(columns=["level_0"])
            return df.reset_index(drop=True)

        filtered_df = self.df_inspection_copy.copy()

        # Apply the filters
        if self.batch_set[0] != "Nil":
            filtered_df = filtered_df[filtered_df["BatchID"] == self.batch_set[0]]
            filtered_df = safe_reset_index(filtered_df)

        if self.year_set[0] != "Nil":
            filtered_df = filtered_df[filtered_df["Y"] == self.year_set[0]]
            filtered_df = safe_reset_index(filtered_df)

        if self.month_set[0] != "Nil":
            filtered_df = filtered_df[filtered_df["M"] == self.month_set[0]]
            filtered_df = safe_reset_index(filtered_df)

        if self.day_set[0] != "Nil":
            filtered_df = filtered_df[filtered_df["D"] == self.day_set[0]]
            filtered_df = safe_reset_index(filtered_df)

        if self.defect_set[0] != "Nil":
            filtered_df = filtered_df[filtered_df["Layer Name"] == self.defect_set[0]]
            filtered_df = safe_reset_index(filtered_df)

        # Filter for defect type if defecttype is in the list
        if self.defecttype_set[0] != "Nil":
            filtered_df = filtered_df[
                filtered_df["Type"].str.contains(self.defecttype_set[0])
            ]
            filtered_df = safe_reset_index(filtered_df)

        if self.severity_set[0] != "Nil":
            filtered_df = filtered_df[filtered_df["Severity"].str.contains(self.severity_set[0])]
            filtered_df = safe_reset_index(filtered_df)

        if self.area_set[0] != "Nil":
            # if self.area_set[0] in regions:
            #     filtered_df = filtered_df[filtered_df["Region"] == self.area_set[0]]
            # else:
            filtered_df = filtered_df[filtered_df["Town"] == self.area_set[0]]
            filtered_df = safe_reset_index(filtered_df)

        self.to_export_to_excel = filtered_df
        self.populate_filters(filtered_data=filtered_df)
        self.update_table(filtered_df)

        self.toggle_layer_visibility(filtered_df)

    # endregion

    def handle_zoom_btn_click(self, lon, lat):
        self.latitude_input = lat
        self.longitude_input = lon
        self.zoom_to_coordinate()

    # region <zoom_to_coordinate>
    def zoom_to_coordinate(self):
        try:
            latitude = float(self.latitude_input.text())
            longitude = float(self.longitude_input.text())
        except:
            latitude = float(self.latitude_input)
            longitude = float(self.longitude_input)
        try:
            # Define a buffer distance around the point (in degrees)
            buffer_distance = 0.005  # Adjust this value as needed

            # Create a QgsRectangle from the point with a buffer
            rect = QgsRectangle(
                longitude - buffer_distance,
                latitude - buffer_distance,
                longitude + buffer_distance,
                latitude + buffer_distance,
            )

            # Transform the extent from WGS84 (EPSG:4326) to the project CRS
            project_crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)  # EPSG:4326
            wgs84_crs = QgsCoordinateReferenceSystem(4326)  # EPSG:4326
            transform = QgsCoordinateTransform(
                wgs84_crs, project_crs, QgsProject.instance()
            )
            rect_transformed = transform.transformBoundingBox(rect)

            # Set the extent of the map canvas to the transformed rectangle
            iface.mapCanvas().setExtent(rect_transformed)
            iface.mapCanvas().refresh()

            # Remove previous marker if exists
            if self.marker:
                self.remove_marker()

            # Create a new marker at the specified coordinates
            self.marker = QgsVertexMarker(iface.mapCanvas())
            self.marker.setCenter(QgsPointXY(longitude, latitude))
            self.marker.setColor(QColor(0, 0, 0))  # Black '+' marker
            self.marker.setIconType(QgsVertexMarker.ICON_CROSS)
            self.marker.setIconSize(12)  # Adjust the size as needed
            self.marker.setPenWidth(2)
            self.marker.show()

        except ValueError:
            print("Please enter valid numerical coordinates.")

    # endregion

    # Method to remove the marker from the map canvas
    def remove_marker(self):
        if self.marker:
            self.marker.hide()
            del self.marker
            self.marker = None

    def add_defect_to_filename(self, file_path):
        # Find position of last dot before file extension
        dot_position = file_path.rfind(".")
        # Add "_defect" before file extension
        new_file_path = file_path[:dot_position] + "_defect" + file_path[dot_position:]
        return new_file_path

    def handle_view_btn_click(self, oImagePath, defects, defect_ids, severities):
        if os.path.exists(oImagePath):
            url = QUrl.fromLocalFile(oImagePath)
            self.display_image(url, defects, defect_ids, severities)
        else:
            QMessageBox.warning(
                self, "File Not Found", f"The file '{oImagePath}' does not exist."
            )

    # hide image viewer elements
    def hide_image_viewer_elements(self):
        self.left_button.setVisible(False)
        self.right_button.setVisible(False)
        self.save_button.setVisible(False)
        self.defect_combo_box.setVisible(False)

    # show image viewer elements
    def show_image_viewer_elements(self):
        self.left_button.setVisible(True)
        self.right_button.setVisible(True)
        self.save_button.setVisible(True)
        self.defect_combo_box.setVisible(True)

    def move_left(self):
        if self.defect_widgets:
            self.current_defect_index = (self.current_defect_index - 1) % len(
                self.defect_widgets
            )
            self.zoom_to_current_defect()

    def move_right(self):
        if self.defect_widgets:
            self.current_defect_index = (self.current_defect_index + 1) % len(
                self.defect_widgets
            )
            self.zoom_to_current_defect()

    def zoom_to_current_defect(self):
        if not self.defect_widgets or self.current_defect_index < 0:
            return

        bbox = self.bboxes[self.current_defect_index]

        if bbox:
            self.draw_bbox_on_image(bbox)  # Draw the bounding box on the image
            self.prev_defect_index = self.current_defect_index

        defect_id = (
            self.defect_widgets[self.current_defect_index][0]
            .text()
            .split("(")[-1]
            .strip(")")
        )
        self.defect_info_label.setText(f"Red bounding box at Defect ID: {defect_id}")

    def draw_bbox_on_image(self, bbox):
        if not bbox:
            return

        # Extract original bbox coordinates
        x_min, y_min, x_max, y_max = bbox
        print(f"Original bbox: {bbox}")

        # Calculate scaling factors based on original and scaled image sizes
        scale_x = self.scaled_size.width() / self.original_size.width()
        scale_y = self.scaled_size.height() / self.original_size.height()

        print(f"Scaling factors - X: {scale_x}, Y: {scale_y}")

        # Scale bbox coordinates
        x_min_scaled = x_min * scale_x
        y_min_scaled = y_min * scale_y
        x_max_scaled = x_max * scale_x
        y_max_scaled = y_max * scale_y

        rect = QRectF(
            x_min_scaled,
            y_min_scaled,
            x_max_scaled - x_min_scaled,
            y_max_scaled - y_min_scaled,
        )
        print(f"Scaled bbox: {rect}")

        # Draw the bounding box
        self.image_label.setPixmap(self.original_pixmap)

        pixmap = self.image_label.pixmap()
        painter = QPainter(pixmap)
        painter.setPen(
            QPen(Qt.red, 2)
        )  # Set the color and thickness of the bounding box

        # Draw the actual bounding box
        painter.drawRect(rect)

        painter.end()  # Finish painting

        # Update the QLabel with the modified pixmap
        self.image_label.setPixmap(pixmap)

    # region <severity tab functions>
    def display_image(
        self, url, defects, defect_ids, severities, target_size=QSize(800, 600)
    ):
        # Load the image using QImage to get its original size
        image_path = url.toLocalFile()
        image = QImage(image_path)

        # Get the original size of the image
        original_width = image.width()
        original_height = image.height()
        print(f"Original image size: {original_width}x{original_height}")

        # Scale the image to fit the target size while maintaining aspect ratio
        pixmap = QPixmap.fromImage(image)
        pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.original_pixmap = pixmap.copy()

        # Set the pixmap to the QLabel
        self.image_label.setPixmap(pixmap)

        # Store the original and scaled image sizes
        self.original_size = QSize(original_width, original_height)
        self.scaled_size = pixmap.size()

        # GLYNIS STUFF

        self.defect_label.setText("Defect(s) Detected:")
        self.bboxes.clear()
        self.defect_widgets = []

        # Clear previous layout items
        for i in reversed(range(self.image_viewer_layout.count())):
            widget = self.image_viewer_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Set headers
        headers = [
            "Defect Name (Defect ID)",
            "Severity Level (1 - Low, 3 - High)",
            "Modified Severity Level (1 - Low, 3 - High)",
            "Click 'Save' Button to Update",
        ]
        for col, header in enumerate(headers):
            header_label = QLabel(header)
            header_label.setFixedHeight(20)
            header_label.setAlignment(Qt.AlignBottom)
            self.image_viewer_layout.addWidget(header_label, 0, col)

        # Ensure defect_ids and severities have the same length
        max_len = max(len(defect_ids), len(severities))
        if len(defect_ids) < max_len:
            defect_ids.extend(["NULL"] * (max_len - len(defect_ids)))
        if len(severities) < max_len:
            severities.extend(["NULL"] * (max_len - len(severities)))

        # Clear previous bboxes
        self.bboxes.clear()

        # Process and display each defect
        self.defect_widgets = []
        for i, (defect_id, severity) in enumerate(zip(defect_ids, severities)):
            defect_name = "NULL"
            bbox = None
            if defect_id.strip() != "NULL":
                try:
                    # Debug: Get the correct defect name and severity from the database
                    print(
                        f"Fetching details for defect_id {defect_id.strip()} from database."
                    )
                    db = self.get_database()
                    defect = db["defect"].find_one({"defectID": int(defect_id.strip())})

                    if defect:
                        severity = str(defect.get("severity", "NULL")).strip()
                        defect_name = str(defect.get("outputLabel", "Unknown")).strip()
                        bbox = eval(
                            defect.get("bbox", "[]")
                        )  # Convert bbox string to list
                        # Debug
                        print(
                            f"Details for defect_id {defect_id.strip()}: {defect_name}, Severity: {severity}"
                        )
                    else:
                        # Debug
                        print(f"No details found for defect_id {defect_id.strip()}.")
                except ValueError:
                    # Debug
                    print(
                        f"Invalid defect_id: {defect_id.strip()}. Unable to fetch details from database."
                    )
                    severity = "NULL"

            defect_label_text = f"{defect_name} ({defect_id.strip()})"
            print(f"Displaying: {defect_label_text}")

            defect_label = QLabel(defect_label_text)
            severity_label = QLabel(severity.strip())
            severity_combo_box = QComboBox()
            severity_combo_box.addItems(self.severity_list)
            severity_combo_box.setCurrentText(severity.strip())
            save_button = QPushButton("Save")

            if defect_id.strip() == "NULL":
                severity_combo_box.setEnabled(False)
                save_button.setEnabled(False)
            else:
                save_button.clicked.connect(
                    lambda checked, defect_id=defect_id, combo=severity_combo_box: self.save_severity(
                        defect_id, combo.currentText()
                    )
                )

            # Add widget to layout
            self.image_viewer_layout.addWidget(defect_label, i + 1, 0)
            self.image_viewer_layout.addWidget(severity_label, i + 1, 1)
            self.image_viewer_layout.addWidget(severity_combo_box, i + 1, 2)
            self.image_viewer_layout.addWidget(save_button, i + 1, 3)

            self.defect_widgets.append(
                (defect_label, severity_label, severity_combo_box, save_button)
            )

            # Store the bbox for this defect
            self.bboxes.append(bbox)

        # Create and connect navigation buttons
        self.left_button = QPushButton("Previous Defect ID")
        self.right_button = QPushButton("Next Defect ID")

        if all(defect_id.strip() == "NULL" for defect_id in defect_ids):
            self.left_button.setEnabled(False)
            self.right_button.setEnabled(False)
        else:
            self.left_button.clicked.connect(self.move_left)
            self.right_button.clicked.connect(self.move_right)

        # Add navigation buttons to layout
        self.image_viewer_layout.addWidget(self.left_button, len(defect_ids) + 1, 0)
        self.image_viewer_layout.addWidget(self.right_button, len(defect_ids) + 1, 1)

        # Add the defect info label
        self.image_viewer_layout.addWidget(
            self.defect_info_label, len(defect_ids) + 1, 2, 1, 2
        )

        # Add the "Export Image" button in the next row, spanning 2 columns
        save_image_button = QPushButton("Export Image")
        save_image_button.clicked.connect(self.save_image)
        self.image_viewer_layout.addWidget(
            save_image_button, len(defect_ids) + 2, 0, 1, 2
        )

        # Add the "Return to Defect Analysis" button in the same row, spanning the remaining columns
        back_button = QPushButton("Return to 'Defect Analysis'")
        back_button.clicked.connect(self.go_back_to_dashboard)
        self.image_viewer_layout.addWidget(back_button, len(defect_ids) + 2, 2, 1, 2)

        # Add the web view below all buttons
        self.image_viewer_layout.addWidget(
            self.image_label, len(defect_ids) + 3, 0, 1, 4
        )

        # Show the image viewer elements only when needed
        self.show_image_viewer_elements()
        self.tab_widget.setCurrentWidget(self.image_viewer_container)

        # Initialize the defect info label with default text
        self.defect_info_label.setText("Click 'Previous Defect ID' or 'Next Defect ID' to view the red bounding box on a defect ID.")
        

    # endregion

    def show_image_viewer_elements(self):
        for _, _, combo, button in self.defect_widgets:
            combo.setVisible(True)
            button.setVisible(True)

    def connect_to_database(self):
        # Replace with your MongoDB connection string
        client = MongoClient("mongodb://localhost:27017/")
        # db = client["FYP"]  # Ensure the database name matches your MongoDB setup
        db=client["newdb"]
        return db

    def get_database(self):
        # Return the database connection
        return self.db

    def save_image(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "Save Image", "defect1", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.image_label.grab().save(file_path)

    # endregion
    
    def go_back_to_dashboard(self):
        self.tab_widget.setCurrentWidget(self.dashboard_2_container)

    def save_severity(self, defect_id, new_severity):
        # Get the database connection
        db = self.get_database()
        defect_collection = db["defect"]
        image_collection = db["image"]

        try:
            defect_id = int(defect_id)
        except ValueError:
            print(f"Invalid defect_id: {defect_id}.")
            return

        # Update severity in MongoDB for the defect_id
        query = {"defectID": defect_id}
        update = {"$set": {"severity": int(new_severity)}}
        result = defect_collection.update_one(query, update)

        if result.matched_count > 0:
            defect = defect_collection.find_one({"defectID": defect_id})
            if defect:
                # Debugging: Print the entire defect document
                print("\nDefect info:", defect)  
                
                # Access defect type and handle case if missing
                defect_type = defect.get("outputLabel", "").strip().lower()
                # Debugging: Print the defect type
                print(f"Retrieved defect_type: '{defect_type}'")  

                image_id = defect.get("imageID", "")
                if not defect_type or "kerb" in defect_type:
                    QMessageBox.warning(
                        self,
                        "Update Successful",
                        f"Severity level for defect ID {defect_id} has been updated.\n\nNote: For all kerb defects, moving image file to s1, s2, or s3 severity folders for active-training is not allowed.",
                    )
                    return

                # Find the corresponding image record
                image_record = image_collection.find_one({"imageID": image_id})
                if image_record:
                    image_path = image_record.get("imagePath", "")
                    if image_path:
                        base_name = os.path.basename(image_path).split(".")[0]
                        base_name_with_defect_id = f"{base_name}_{defect_id}"

                        # Get the base path
                        base_path = os.getenv("FYP_BASE_PATH", "")
                        if not base_path:
                            print(
                                "Base path not set. Set FYP_BASE_PATH environment variable in run_qgis_setup.bat."
                            )
                            return

                        # Construct the correct paths
                        unedited_folder = os.path.join(
                            base_path, "active_learning", "unedited"
                        )
                        classified_folder = os.path.join(
                            base_path,
                            "active_learning",
                            "classified",
                            "train",
                        )
                        severity_folder = os.path.join(
                            classified_folder, f"s{new_severity}"
                        )

                        # Check if the unedited folder exists
                        if not os.path.exists(unedited_folder):
                            print(
                                f"The unedited folder path does not exist: {unedited_folder}"
                            )
                            return

                        # Look for the file in the unedited folder
                        files = [
                            f
                            for f in os.listdir(unedited_folder)
                            if f.startswith(base_name_with_defect_id)
                            and f.endswith(".jpg")
                        ]

                        if not files:
                            QMessageBox.warning(
                                self,
                                "File Not Found",
                                f"Severity for defect ID {defect_id} has been updated, but image path file for defect ID {defect_id} could not be found in the unedited folder.",
                            )
                            return

                        # Move the file if everything is fine
                        file_to_move = os.path.join(unedited_folder, files[0])
                        new_file_path = os.path.join(
                            severity_folder, os.path.basename(file_to_move)
                        )

                        shutil.move(file_to_move, new_file_path)
                        print(f"Moved '{file_to_move}' to '{new_file_path}'")

                        QMessageBox.information(
                            self,
                            "Save Successful",
                            f"Severity for defect ID {defect_id} has been updated.\n\nThe image '{base_name_with_defect_id}' has been moved to '{severity_folder}'",
                        )
                    else:
                        print(f"Image path for image ID {image_id} not found.")
                        QMessageBox.warning(
                            self,
                            "File Not Found",
                            f"Severity for defect ID {defect_id} has been updated, but image path file for defect ID {defect_id} could not be found in the unedited folder.",
                        )
                else:
                    print(f"Image record with ID {image_id} not found.")
                    QMessageBox.warning(
                        self,
                        "File Not Found",
                        f"Severity for defect ID {defect_id} has been updated, but the image record could not be found.",
                    )
            else:
                print(f"Defect with ID {defect_id} not found in the database.")
                QMessageBox.warning(
                    self,
                    "Update Failed",
                    f"Failed to update severity for defect ID {defect_id}. Defect not found in the database.",
                )
        else:
            QMessageBox.warning(
                self,
                "Update Failed",
                f"Failed to update severity for defect ID {defect_id}.",
            )





# -------------------------------
# Ian Functions to do stuff
# -------------------------------
def combine_values(series):
    unique_values = series.astype(str).unique()
    if len(unique_values) == 1:
        return unique_values[0]
    else:
        return ", ".join(map(str, unique_values))


# -------------------------
# fetch_layer_data function
# -------------------------
def fetch_layer_data(layer_index_or_name, road_field_name):
    # Get layer by index or name
    if isinstance(layer_index_or_name, int):
        layer = QgsProject.instance().mapLayers()[layer_index_or_name]
    elif isinstance(layer_index_or_name, str):
        layers = QgsProject.instance().mapLayersByName(layer_index_or_name)
        if not layers:
            return []
        layer = layers[0]
    else:
        print("Invalid layer index or name provided.")
        return []

    # Fetch data from layer
    features = layer.getFeatures()
    data = []
    for feature in features:
        road = feature[road_field_name]
        geom = feature.geometry()
        if geom:
            coords = geom.asPoint()
            data.append((road, coords.x(), coords.y()))
    return data


# -----------------------------------
# fetch_inspection_date_data function
# -----------------------------------
def fetch_inspection_date_data(folder_name):
    # Fetch the subfolders under the Inspection Dates folder
    inspection_dates_folder = (
        QgsProject.instance().layerTreeRoot().findGroup(folder_name)
    )
    date_folders = [
        child
        for child in inspection_dates_folder.children()
        if isinstance(child, QgsLayerTreeGroup)
    ]

    # Loop through each date folder and fetch layers
    inspection_data = []
    for date_folder in date_folders:
        date_folder_name = date_folder.name()
        layers = date_folder.findLayers()

        for layer in layers:
            layer_name = layer.name()
            layer_id = layer.layerId()
            if layer_name == date_folder_name:
                layer_name = "AllDefect"
                layer.setItemVisibilityChecked(False)
            else:
                layer.setItemVisibilityChecked(True)
                date_folder.setItemVisibilityChecked(True)
            if (
                layer_name.endswith("Defect")
                or layer_name.endswith("NonDefect")
                or layer_name == "AllDefect"
            ):
                qgis_layer = layer.layer()
                features = qgis_layer.getFeatures()
                for feature in features:
                    road = feature["Road"]
                    road_type = feature["RoadType"]
                    datetime = feature["DateTime"]
                    defect_type = feature["Type"]
                    severity = feature["Severity"]
                    town = feature["Town"]
                    batch = feature["BatchID"]
                    oimagepath = feature["OImagePath"]
                    imageID = feature["ImageID"]
                    geom = feature.geometry()
                    defect_id = feature["DefectID"]
                    if geom:
                        coords = geom.asPoint()
                        inspection_data.append(
                            (
                                date_folder_name,
                                layer_name,
                                road,
                                town,
                                road_type,
                                datetime,
                                defect_type,
                                severity,
                                coords.x(),
                                coords.y(),
                                batch,
                                oimagepath,
                                imageID,
                                layer_id,
                                defect_id,
                            )
                        )
    return inspection_data


# -------------------------
# fetch_batch_times function
# -------------------------
def fetch_batch_times(layer_index_or_name, start_time_field, end_time_field):
    # Get layer by index or name
    if isinstance(layer_index_or_name, int):
        layer = QgsProject.instance().mapLayers()[layer_index_or_name]
    elif isinstance(layer_index_or_name, str):
        layers = QgsProject.instance().mapLayersByName(layer_index_or_name)
        if not layers:
            return None, None
        layer = layers[0]
    else:
        print("Invalid layer index or name provided.")
        return None, None

    # Fetch data from layer
    features = layer.getFeatures()
    for feature in features:
        start_time = feature[start_time_field]
        end_time = feature[end_time_field]

        # Check if start_time and end_time are valid
        if start_time == "-" or end_time == "-" or not start_time or not end_time:
            print(f"Invalid start or end time: {start_time}, {end_time}")
            return None, None, start_time

        return start_time, end_time, None

    return None, None


# -------------------------
# get_batch_status function
# -------------------------
def get_batch_status(batch_layer_data):
    if batch_layer_data and batch_layer_data[0]:
        # Get latest batch status field
        batchStatus = batch_layer_data[0][0]
        if batchStatus.lower() in ["completed", "complete"]:
            print("Batch Status: " + batchStatus)
            return True
    return False


# -------------------------
# get_batch_defect_count function
# -------------------------
layer_name = "Latest Batch Defects"
layer_field_name = "Road"
layer_field_batch_name = "Status"

# Fetch layer data
layer_data = fetch_layer_data(layer_name, layer_field_name)
layer_batch_data = fetch_layer_data(layer_name, layer_field_batch_name)


def get_batch_defect_count():
    if layer_data:
        # Calculate the total defect count detected in the batch
        total_defect_count = len(layer_data)
        return total_defect_count
    return 0


# -------------------------
# Determine/Fetch the batch status and defect count
# -------------------------
batch_layer_data = fetch_batch_times("layer_name", "start_time_field", "end_time_field")
batch_status = get_batch_status(layer_batch_data)
total_defect_count = get_batch_defect_count()

# -------------------
# DATA
# -------------------
inspection_dates_folder = "Inspection Dates"
road_field_name = "Road"
town_field_name = "Town"
type_field_name = "Type"
severity_field_name = "Severity"
roadtype_field_name = "RoadType"

inspection_data = fetch_inspection_date_data(inspection_dates_folder)
df_inspection = pd.DataFrame(
    inspection_data,
    columns=[
        "Date",
        "Layer Name",
        "Road",
        "Town",
        "RoadType",
        "DateTime",
        "Type",
        "Severity",
        "Longitude",
        "Latitude",
        "BatchID",
        "OImagePath",
        "ImageID",
        "LayerID",
        "DefectID",
    ],
)

# Go through the data in Type, verifying if the last index after splt(" ") is a float or integer
def check_last_index(value):
    temp = value.split(" ")
    if temp[-1].replace(".", "").isdigit():
        return " ".join(temp[:-1])
    if ")" in temp[-1] and "(" in temp[-2]:
        return " ".join(temp[:-2])
    return value


df_inspection["Type"] = df_inspection["Type"].apply(check_last_index)


# -------------------
# Sorting for regions
# -------------------
central_region = [
    "ANG MO KIO",
    "CHENG SAN",
    "JALAN KAYU",
    "FERNVALE",
    "TECK GHEE",
    "BISHAN",
    "TOA PAYOH",
    "KAMPONG GLAM",
    "KOLAM AYER",
    "KRETA AYER",
    "WHAMPOA",
    "BOUNA VISTA",
    "HENDERSON",
    "MOULMEIN",
    "QUEENSTOWN",
    "TANJONG PAGAR",
    "TIONG BAHRU",
    "NOVENA",
    "KALLANG",
]
north_east_region = [
    "BEDOK",
    "EUNOS",
    "KAKI BUKIT",
    "PAYA LEBAR",
    "SERANGOON",
    "PASIR RIS",
    "PUNGGOL",
    "BUANGKOK",
    "ANCHORVALE",
    "COMPASSVALE",
    "RIVERVALE",
    "TAMPINES",
    "HOUGANG",
]
north_west_region = [
    "CHOA CHU KANG",
    "SUNGEI KADUT",
    "KEAT HONG",
    "BUKIT TIMAH",
    "CASHEW",
    "ULU PANDAN",
    "ZHENGHUA",
    "LIMBANG",
    "MARSILING",
    "WOODGROVE",
    "YEW TEE",
    "CHONG PANG",
    "NEE SOON",
    "ADMIRALTY",
    "WOODLANDS",
    "CANBERRA",
    "SEMBAWANG",
]
south_east_region = [
    "BEDOK",
    "CHANGI",
    "FENGSHAN",
    "KAMPONG CHAI CHEE",
    "SIGLAP",
    "BRADDELL",
    "GEYLANG",
    "JOO CHIAT",
    "KEMBANGAN",
    "MARINE PARADE",
]
south_west_region = [
    "BRICKLAND",
    "BUKIT GOMBAK",
    "JURONG EAST",
    "CLEMENTI",
    "BUKIT BATOK",
    "AYER RAJAH",
    "BOON LAY",
    "NANYANG",
    "TELOK BLANGAH",
    "WEST COAST",
]

# ------------------
# Inspection dates
# ------------------
day_list = []
month_list = []
year_list = []
for date in df_inspection["Date"]:
    temp = date.split(" ")
    day_list.append(temp[0])
    month_list.append(temp[1])
    year_list.append(temp[2])

temp = {"Day": day_list, "Month": month_list, "Year": year_list}

df_inspection_dates = df_inspection.copy()
df_inspection_dates["D"] = day_list
df_inspection_dates["M"] = month_list
df_inspection_dates["Y"] = year_list

# ----------------------
# Display Widget in QGIS
# ----------------------
# Instantiate DashboardWidget to QGIS interface
dashboard = DashboardWidget()
iface.addDockWidget(Qt.RightDockWidgetArea, dashboard)
