from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QScrollArea,
    QSplitter,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

# For plotting
import matplotlib.pyplot as plt
import io

# Import the analysis function
from mrcnn import model
from rcc_non_linear import Model


class DDAPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left Side: Input Form ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        form_container = QWidget()
        self.form_layout = QFormLayout(form_container)
        self.form_layout.setLabelAlignment(Qt.AlignLeft)

        # --- Section: Column Properties ---
        self.form_layout.addRow(QLabel("<h3>Column Properties (kips, in)</h3>"))
        self.column_type_combo = QComboBox()
        self.column_type_combo.addItems(["Circular", "Rectangular"])
        self.form_layout.addRow("Column Type:", self.column_type_combo)

        # --- Dynamic fields for column shape ---
        self.diameter_label = QLabel("Diameter (in):")
        self.diameter_input = QLineEdit("36")
        self.form_layout.addRow(self.diameter_label, self.diameter_input)

        self.width_label = QLabel("Width (in):")
        self.width_input = QLineEdit("24")
        self.form_layout.addRow(self.width_label, self.width_input)

        self.height_label = QLabel("Height (in):")
        self.height_input = QLineEdit("36")
        self.form_layout.addRow(self.height_label, self.height_input)

        self.length_input = QLineEdit("240")
        self.cover_input = QLineEdit("1.5")
        self.form_layout.addRow("Length (in):", self.length_input)
        self.form_layout.addRow("Cover (in):", self.cover_input)

        # --- Section: Concrete Properties ---
        self.form_layout.addRow(QLabel("<h3>Concrete Strength</h3>"))
        self.fc_input = QLineEdit("4")
        self.form_layout.addRow("fc' (ksi):", self.fc_input)

        # --- Section: Longitudinal Reinforcement ---
        self.form_layout.addRow(QLabel("<h3>Longitudinal Reinforcement</h3>"))

        # Circular Reinforcement Fields
        self.long_num_bars_label = QLabel("Number of Bars:")
        self.long_num_bars_input = QLineEdit("16")
        self.long_bar_dia_label = QLabel("Bar Diameter (in):")
        self.long_bar_dia_input = QLineEdit("1.0")
        self.form_layout.addRow(self.long_num_bars_label, self.long_num_bars_input)
        self.form_layout.addRow(self.long_bar_dia_label, self.long_bar_dia_input)

        # Rectangular Reinforcement Fields
        self.top_bars_label = QLabel("<b>Top Bars</b>")
        self.top_num_bars_input = QLineEdit("4")
        self.top_bar_dia_input = QLineEdit("1.0")
        self.form_layout.addRow(self.top_bars_label)
        self.form_layout.addRow("Number:", self.top_num_bars_input)
        self.form_layout.addRow("Diameter (in):", self.top_bar_dia_input)

        self.int_bars_label = QLabel("<b>Intermediate Bars</b>")
        self.int_num_bars_input = QLineEdit("2")
        self.int_bar_dia_input = QLineEdit("1.0")
        self.form_layout.addRow(self.int_bars_label)
        self.form_layout.addRow("Number (per side):", self.int_num_bars_input)
        self.form_layout.addRow("Diameter (in):", self.int_bar_dia_input)

        self.bot_bars_label = QLabel("<b>Bottom Bars</b>")
        self.bot_num_bars_input = QLineEdit("4")
        self.bot_bar_dia_input = QLineEdit("1.0")
        self.form_layout.addRow(self.bot_bars_label)
        self.form_layout.addRow("Number:", self.bot_num_bars_input)
        self.form_layout.addRow("Diameter (in):", self.bot_bar_dia_input)

        # Common Reinforcement Fields
        self.long_fy_input = QLineEdit("60")
        self.long_fu_input = QLineEdit("90")
        self.long_eps_ult_input = QLineEdit("0.09")
        self.form_layout.addRow("fy (ksi):", self.long_fy_input)
        self.form_layout.addRow("fu (ksi):", self.long_fu_input)
        self.form_layout.addRow("Ultimate Strain:", self.long_eps_ult_input)

        # --- Section: Transverse Reinforcement ---
        self.form_layout.addRow(QLabel("<h3>Transverse Reinforcement</h3>"))
        self.trans_bar_dia_input = QLineEdit("0.5")
        self.trans_spacing_input = QLineEdit("5")
        self.trans_fyh_input = QLineEdit("60")
        self.trans_fuh_input = QLineEdit("90")
        self.trans_epsh_ult_input = QLineEdit("0.09")
        self.form_layout.addRow("Bar Diameter (in):", self.trans_bar_dia_input)
        self.form_layout.addRow("Spacing (in):", self.trans_spacing_input)
        self.form_layout.addRow("fyh (ksi):", self.trans_fyh_input)
        self.form_layout.addRow("fuh (ksi):", self.trans_fuh_input)
        self.form_layout.addRow("Ultimate Strain:", self.trans_epsh_ult_input)

        # --- Section: Loading ---
        self.form_layout.addRow(QLabel("<h3>Loading</h3>"))
        self.axial_load_input = QLineEdit("400")
        self.form_layout.addRow("Axial Load (kips):", self.axial_load_input)

        # --- Action Buttons ---
        self.submit_btn = QPushButton("Submit")
        self.clear_btn = QPushButton("Clear")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.clear_btn)
        self.form_layout.addRow(button_layout)

        scroll_area.setWidget(form_container)

        # --- Right Side: Output Panel (with Plot) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        output_splitter = QSplitter(Qt.Vertical)

        self.plot_label = QLabel("Pushover curve will be displayed here.")
        self.plot_label.setAlignment(Qt.AlignCenter)
        self.plot_label.setMinimumHeight(300)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Pushover analysis results will appear here...")

        output_splitter.addWidget(self.plot_label)
        output_splitter.addWidget(self.output)
        output_splitter.setSizes([400, 200])  # Initial size ratio

        right_layout.addWidget(output_splitter)

        splitter.addWidget(scroll_area)
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 550])

        # --- Connect Signals to Slots ---
        self.submit_btn.clicked.connect(self._run_analysis)
        self.clear_btn.clicked.connect(self._clear_form)
        self.column_type_combo.currentIndexChanged.connect(self._update_column_fields)

        self._update_column_fields()

    def _update_column_fields(self):
        is_circular = self.column_type_combo.currentText() == "Circular"

        self.diameter_label.setVisible(is_circular)
        self.diameter_input.setVisible(is_circular)
        self.width_label.setVisible(not is_circular)
        self.width_input.setVisible(not is_circular)
        self.height_label.setVisible(not is_circular)
        self.height_input.setVisible(not is_circular)

        self.long_num_bars_label.setVisible(is_circular)
        self.long_num_bars_input.setVisible(is_circular)
        self.long_bar_dia_label.setVisible(is_circular)
        self.long_bar_dia_input.setVisible(is_circular)

        self.top_bars_label.setVisible(not is_circular)
        self.top_num_bars_input.setVisible(not is_circular)
        self.top_bar_dia_input.setVisible(not is_circular)
        self.form_layout.labelForField(self.top_num_bars_input).setVisible(
            not is_circular
        )
        self.form_layout.labelForField(self.top_bar_dia_input).setVisible(
            not is_circular
        )

        self.int_bars_label.setVisible(not is_circular)
        self.int_num_bars_input.setVisible(not is_circular)
        self.int_bar_dia_input.setVisible(not is_circular)
        self.form_layout.labelForField(self.int_num_bars_input).setVisible(
            not is_circular
        )
        self.form_layout.labelForField(self.int_bar_dia_input).setVisible(
            not is_circular
        )

        self.bot_bars_label.setVisible(not is_circular)
        self.bot_num_bars_input.setVisible(not is_circular)
        self.bot_bar_dia_input.setVisible(not is_circular)
        self.form_layout.labelForField(self.bot_num_bars_input).setVisible(
            not is_circular
        )
        self.form_layout.labelForField(self.bot_bar_dia_input).setVisible(
            not is_circular
        )

    def _run_analysis(self):
        try:
            self.output.clear()
            self.plot_label.setText("Generating plot...")

            # --- Gather Inputs ---
            analysis_inputs = {
                "column_type": self.column_type_combo.currentText(),
                "length": float(self.length_input.text()),
                "cover": float(self.cover_input.text()),
                "fc": float(self.fc_input.text()),
                "fy": float(self.long_fy_input.text()),
                "fu": float(self.long_fu_input.text()),
                "eps_ult": float(self.long_eps_ult_input.text()),
                "trans_bar_dia": float(self.trans_bar_dia_input.text()),
                "trans_spacing": float(self.trans_spacing_input.text()),
                "fyh": float(self.trans_fyh_input.text()),
                "fuh": float(self.trans_fuh_input.text()),
                "epsh_ult": float(self.trans_epsh_ult_input.text()),
                "axial_load": float(self.axial_load_input.text()),
            }

            col_props = {
                "fc": analysis_inputs["fc"],
                "L": analysis_inputs["length"],
                "cover": analysis_inputs["cover"],
                "fy": analysis_inputs["fy"],
                "fu": analysis_inputs["fu"],
                "e_ult": analysis_inputs["eps_ult"],
                "dh": analysis_inputs["trans_bar_dia"],
                "sh": analysis_inputs["trans_spacing"],
                "fyh": analysis_inputs["fyh"],
                "fuh": analysis_inputs["fuh"],
                "esm": analysis_inputs["epsh_ult"],
                "P_axial": analysis_inputs["axial_load"],
            }

            if analysis_inputs["column_type"] == "Circular":
                analysis_inputs["diameter"] = float(self.diameter_input.text())
                analysis_inputs["long_num_bars"] = int(self.long_num_bars_input.text())
                analysis_inputs["long_bar_dia"] = float(self.long_bar_dia_input.text())
                col_props["D"] = analysis_inputs["diameter"]
                col_props["nBars"] = analysis_inputs["long_num_bars"]
                col_props["db"] = analysis_inputs["long_bar_dia"]
            else:  # Rectangular
                analysis_inputs["width"] = float(self.width_input.text())
                analysis_inputs["height"] = float(self.height_input.text())
                analysis_inputs["top_num_bars"] = int(self.top_num_bars_input.text())
                analysis_inputs["top_bar_dia"] = float(self.top_bar_dia_input.text())
                analysis_inputs["int_num_bars"] = int(self.int_num_bars_input.text())
                analysis_inputs["int_bar_dia"] = float(self.int_bar_dia_input.text())
                analysis_inputs["bot_num_bars"] = int(self.bot_num_bars_input.text())
                analysis_inputs["bot_bar_dia"] = float(self.bot_bar_dia_input.text())
                col_props["B"] = analysis_inputs["width"]
                col_props["H"] = analysis_inputs["height"]
                col_props["nBarsTop"] = analysis_inputs["top_num_bars"]
                col_props["dbTop"] = analysis_inputs["top_bar_dia"]
                col_props["nBarsInt"] = analysis_inputs["int_num_bars"]
                col_props["dbInt"] = analysis_inputs["int_bar_dia"]
                col_props["nBarsBot"] = analysis_inputs["bot_num_bars"]
                col_props["dbBot"] = analysis_inputs["bot_bar_dia"]

            # --- Run Analysis ---
            model = Model(col_props)
            results_df, bilinear_df, yield_step = model.run_pushover_analysis(dU=0.1)
            results_text = bilinear_df.to_string(index=False, float_format="{:.3f}".format)
            # --- Display Text Results ---
            self.output.setText(results_text)

            # --- Parse and Plot Results ---
            drifts = []
            forces = []
            lines = results_text.strip().split("\n")
            if len(lines) > 1:
                for line in lines[1:]:  # Skip header
                    parts = line.split()
                    if len(parts) == 3:
                        forces.append(float(parts[1]))
                        drifts.append(float(parts[2]))

            fig, ax = plt.subplots()
            ax.plot(drifts, forces, marker="o", linestyle="-")
            ax.set_title("Pushover Curve")
            ax.set_xlabel("Drift (%)")
            ax.set_ylabel("Force (kips)")
            ax.grid(True)
            fig.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(buf.read())
            self.plot_label.setPixmap(pixmap)

            plt.close(fig)

        except ValueError as e:
            self.output.append(
                f"\nError: Invalid input. Please ensure all fields have valid numbers. Details: {e}"
            )
        except Exception as e:
            self.output.append(f"\nAn unexpected error occurred: {e}")

    def _clear_form(self):
        self.column_type_combo.setCurrentIndex(0)
        self.diameter_input.setText("36")
        self.width_input.setText("24")
        self.height_input.setText("36")
        self.length_input.setText("240")
        self.cover_input.setText("1.5")
        self.fc_input.setText("4")
        self.long_num_bars_input.setText("16")
        self.long_bar_dia_input.setText("1.0")
        self.top_num_bars_input.setText("4")
        self.top_bar_dia_input.setText("1.0")
        self.int_num_bars_input.setText("2")
        self.int_bar_dia_input.setText("1.0")
        self.bot_num_bars_input.setText("4")
        self.bot_bar_dia_input.setText("1.0")
        self.long_fy_input.setText("60")
        self.long_fu_input.setText("90")
        self.long_eps_ult_input.setText("0.09")
        self.trans_bar_dia_input.setText("0.5")
        self.trans_spacing_input.setText("5")
        self.trans_fyh_input.setText("60")
        self.trans_fuh_input.setText("90")
        self.trans_epsh_ult_input.setText("0.09")
        self.axial_load_input.setText("400")
        self.output.clear()
        self.plot_label.setText("Pushover curve will be displayed here.")
