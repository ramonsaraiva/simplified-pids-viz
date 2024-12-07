from orangebox import Parser
import tkinter as tk
from tkinter import ttk
import tkinterdnd2
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class SimplifiedParamsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Simplified Parameters")

        self.root.drop_target_register(tkinterdnd2.DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.handle_drop)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.placeholder = ttk.Label(
            self.root,
            text="Drag and drop a blackbox log here",
            font=("Arial", 24),
            padding=40,
        )
        self.placeholder.pack(expand=True)

    def handle_drop(self, event):
        file_path = event.data
        try:
            self.placeholder.pack_forget()
            for child in self.notebook.winfo_children():
                child.destroy()

            parser = Parser.load(file_path)

            simplified_pids_mode = parser.headers.get("simplified_pids_mode", 0)
            if simplified_pids_mode not in (0, 1, 2):
                raise ValueError(
                    f"Invalid simplified_pids_mode: {simplified_pids_mode}. Must be 0, 1, or 2."
                )

            logging.debug(f"Simplified PID Mode: {simplified_pids_mode}")

            if simplified_pids_mode in (0, 1):
                logging.debug("Raw PID values from log:")
                logging.debug(f"Roll PID: {parser.headers.get('rollPID', 'Not found')}")
                logging.debug(
                    f"Pitch PID: {parser.headers.get('pitchPID', 'Not found')}"
                )
                logging.debug(f"Yaw PID: {parser.headers.get('yawPID', 'Not found')}")
                logging.debug(
                    f"FF Weight: {parser.headers.get('ff_weight', 'Not found')}"
                )

            if simplified_pids_mode == 2:
                simplified_params = {
                    k: v
                    for k, v in parser.headers.items()
                    if k.startswith("simplified_")
                }
            else:
                simplified_params = predict_slider_values(parser.headers)

            logging.debug("Simplified parameters:")
            logging.debug(simplified_params)

            self.setup_ui(simplified_params)

        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to load file: {str(e)}")

    def setup_ui(self, params):
        tuning_frame = ttk.Frame(self.notebook)
        filter_frame = ttk.Frame(self.notebook)

        self.notebook.add(tuning_frame, text="Tuning")
        self.notebook.add(filter_frame, text="Filters")

        if "simplified_pids_mode" in params:
            mode_frame = ttk.Frame(tuning_frame)
            mode_frame.pack(fill=tk.X, pady=5, padx=10)
            ttk.Label(
                mode_frame, text=f"PID Mode: {params['simplified_pids_mode']}"
            ).pack()

        filter_params = {k: v for k, v in params.items() if "filter" in k.lower()}
        tuning_params = {
            k: v
            for k, v in params.items()
            if "filter" not in k.lower() and k != "simplified_pids_mode"
        }

        tuning_order = [
            ("simplified_d_gain", "Damping (D Gains)"),
            ("simplified_pi_gain", "Tracking (P&I Gains)"),
            ("simplified_feedforward_gain", "Stick Response (FF Gains)"),
            ("simplified_dmax_gain", "Dynamic Damping (D Max)"),
            ("simplified_i_gain", "Drift - Wobble (I Gains)"),
            ("simplified_pitch_d_gain", "Pitch Damping (Pitch:Roll D)"),
            ("simplified_pitch_pi_gain", "Pitch Tracking (Pitch:Roll P, I & FF)"),
            ("simplified_master_multiplier", "Master Multiplier"),
        ]

        ordered_tuning_params = {
            k: tuning_params[k] for k, _ in tuning_order if k in tuning_params
        }
        self._create_sliders(tuning_frame, ordered_tuning_params, dict(tuning_order))
        self._create_sliders(filter_frame, filter_params)

    def _create_sliders(self, parent_frame, params, labels_map=None):
        for key, value in params.items():
            frame = ttk.Frame(parent_frame)
            frame.pack(fill=tk.X, pady=5, padx=10)

            label_text = labels_map[key] if labels_map and key in labels_map else key
            ttk.Label(frame, text=label_text).pack(side=tk.LEFT, padx=5)

            slider = ttk.Scale(
                frame,
                from_=0,
                to=2,
                orient=tk.HORIZONTAL,
                value=value / 100,
                length=400,
            )
            slider.pack(side=tk.RIGHT, padx=5)

            value_label = ttk.Label(frame, text=f"{value/100:.2f}")
            value_label.pack(side=tk.RIGHT, padx=5)

            def update_label(val, label=value_label):
                label.config(text=f"{float(val):.2f}")

            slider.configure(command=update_label)


def predict_slider_values(headers):
    """
    This is most likely not accurate, but a starting point for proper values -> slider process.
    """
    DEFAULT_ROLL = [45, 80, 30]
    DEFAULT_PITCH = [47, 84, 34]
    DEFAULT_YAW = [45, 80, 0]
    DEFAULT_FF = [120, 125, 120]

    roll = headers.get("rollPID", DEFAULT_ROLL)
    pitch = headers.get("pitchPID", DEFAULT_PITCH)
    _yaw = headers.get("yawPID", DEFAULT_YAW)
    ff = headers.get("ff_weight", DEFAULT_FF)

    # Calculate ratios compared to defaults
    predicted_values = {}

    # D Gains (based on roll[2] and pitch[2])
    d_gain_roll = roll[2] / DEFAULT_ROLL[2] if DEFAULT_ROLL[2] != 0 else 1.0
    predicted_values["simplified_d_gain"] = d_gain_roll * 100

    # P&I Gains (based on roll[0] and roll[1])
    pi_gain_roll = ((roll[0] / DEFAULT_ROLL[0]) + (roll[1] / DEFAULT_ROLL[1])) / 2
    predicted_values["simplified_pi_gain"] = pi_gain_roll * 100

    # Stick Response (FF Gains)
    ff_gain = sum([a / b for a, b in zip(ff, DEFAULT_FF)]) / 3
    predicted_values["simplified_feedforward_gain"] = ff_gain * 100

    # I Gains (affects roll[1] and pitch[1])
    i_gain = (roll[1] / DEFAULT_ROLL[1]) * 100
    predicted_values["simplified_i_gain"] = i_gain

    # Pitch D ratio (compared to roll)
    pitch_d_ratio = (
        (pitch[2] / DEFAULT_PITCH[2]) / (roll[2] / DEFAULT_ROLL[2])
        if roll[2] != 0 and DEFAULT_ROLL[2] != 0
        else 1.0
    )
    predicted_values["simplified_pitch_d_gain"] = pitch_d_ratio * 100

    # Pitch P&I ratio (compared to roll)
    pitch_pi_ratio = (
        (pitch[0] / DEFAULT_PITCH[0]) / (roll[0] / DEFAULT_ROLL[0])
        + (pitch[1] / DEFAULT_PITCH[1]) / (roll[1] / DEFAULT_ROLL[1])
    ) / 2
    predicted_values["simplified_pitch_pi_gain"] = pitch_pi_ratio * 100

    # Master multiplier (average of all ratios)
    all_ratios = [
        roll[0] / DEFAULT_ROLL[0],
        roll[1] / DEFAULT_ROLL[1],
        roll[2] / DEFAULT_ROLL[2] if DEFAULT_ROLL[2] != 0 else 1.0,
        pitch[0] / DEFAULT_PITCH[0],
        pitch[1] / DEFAULT_PITCH[1],
        pitch[2] / DEFAULT_PITCH[2] if DEFAULT_PITCH[2] != 0 else 1.0,
    ]
    master_multiplier = sum(all_ratios) / len(all_ratios)
    predicted_values["simplified_master_multiplier"] = master_multiplier * 100

    return predicted_values


if __name__ == "__main__":
    root = tkinterdnd2.TkinterDnD.Tk()
    app = SimplifiedParamsGUI(root)
    root.mainloop()
