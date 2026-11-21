"""Waste Detection & Classification System - Tkinter GUI entry point.

Usage:
    python main.py                      # webcam (camera index 0)
    python main.py --source conveyor.mp4  # video file
    python main.py --source image.jpg   # single image
    python main.py --source 1           # camera index 1
    python main.py --model waste.pt     # custom waste model

Environment:
    WASTE_MODEL_PATH  Path to a YOLOv8 model trained on waste classes
                      (plastic, paper, metal, glass, organic, etc.).
                      Falls back to yolov8n.pt (COCO) if not set.
"""

import argparse
import os

import cv2
import tkinter as tk
from PIL import Image, ImageTk

import config
from waste_monitor import WasteMonitor


def parse_args():
    parser = argparse.ArgumentParser(description="Waste Detection & Classification System")
    parser.add_argument("--source", default="0",
                        help="Video source: camera index (0,1,...), video file, or image file")
    parser.add_argument("--model", default=None,
                        help="Path to YOLOv8 waste model (.pt). Overrides WASTE_MODEL_PATH env.")
    parser.add_argument("--conf", type=float, default=None,
                        help="Confidence threshold (default: %.2f)" % config.CONFIDENCE_THRESHOLD)
    parser.add_argument("--output", default=None,
                        help="Save annotated output to this path (video/image)")
    parser.add_argument("--no-display", action="store_true",
                        help="Run without GUI (headless, for video/image processing)")
    return parser.parse_args()


def resolve_source(source_str):
    if source_str.isdigit():
        return int(source_str)
    return source_str


def run_headless(monitor, source, output):
    if isinstance(source, str) and os.path.isfile(source):
        ext = os.path.splitext(source)[1].lower()
        if ext in (".jpg", ".jpeg", ".png", ".bmp"):
            out = output or "output_" + os.path.basename(source)
            monitor.run_on_image(source, out)
            return
    monitor.run_on_video(source, output_path=output, display=False)


class WasteMonitorGUI:
    def __init__(self, monitor, source, output=None):
        self.monitor = monitor
        self.source = source
        self.output = output
        self.cap = self._open_source(source)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open source: {source}")

        self.writer = None
        self.running = True
        self.stats_text = tk.StringVar(value="Starting...")

        self.root = tk.Tk()
        self.root.title("Waste Detection & Classification System")
        self.root.configure(bg="#1e1e1e")

        header = tk.Label(self.root, text="WASTE DETECTION & CLASSIFICATION",
                          font=("Helvetica", 16, "bold"), fg="white", bg="#1e1e1e")
        header.pack(pady=5)

        self.video_label = tk.Label(self.root, bg="#1e1e1e")
        self.video_label.pack()

        info_frame = tk.Frame(self.root, bg="#1e1e1e")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        self.stats_label = tk.Label(info_frame, textvariable=self.stats_text,
                                    font=("Consolas", 11), fg="#00ff00", bg="#1e1e1e",
                                    justify=tk.LEFT)
        self.stats_label.pack(side=tk.LEFT)

        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Quit", command=self.close,
                  font=("Helvetica", 11), bg="#d9534f", fg="white",
                  padx=20).pack(side=tk.LEFT, padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(10, self.update_frame)

    def _open_source(self, source):
        if isinstance(source, int):
            return cv2.VideoCapture(source, cv2.CAP_DSHOW)
        return cv2.VideoCapture(source)

    def update_frame(self):
        if not self.running:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.stats_text.set("End of stream.")
            self.root.after(1000, self.close)
            return

        annotated, detections = self.monitor.process_frame(frame)

        if self.writer:
            self.writer.write(annotated)

        frame_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(frame_rgb))
        self.video_label.imgtk = img
        self.video_label.configure(image=img)

        s = self.monitor.stats
        lines = [
            f"Total: {s.total} | Recyclable: {s.recyclable_count} | Non-recyclable: {s.non_recyclable_count}",
            f"Plastic: {s.counts.get('plastic', 0)} | Paper: {s.counts.get('paper', 0)} | Metal: {s.counts.get('metal', 0)} | Glass: {s.counts.get('glass', 0)}",
            f"Recyclable rate: {s.recyclable_rate*100:.1f}%",
        ]
        self.stats_text.set("\n".join(lines))

        self.root.after(10, self.update_frame)

    def close(self):
        self.running = False
        if self.cap:
            self.cap.release()
        if self.writer:
            self.writer.release()
        self.monitor.stats.print_report()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    args = parse_args()
    source = resolve_source(args.source)
    print("=" * 55)
    print("  WASTE DETECTION & CLASSIFICATION SYSTEM")
    print("=" * 55)
    monitor = WasteMonitor(model_path=args.model, conf=args.conf)

    if args.no_display or (isinstance(source, str) and os.path.isfile(source)
                           and os.path.splitext(source)[1].lower() in (".jpg", ".jpeg", ".png", ".bmp")):
        run_headless(monitor, source, args.output)
    else:
        try:
            gui = WasteMonitorGUI(monitor, source, args.output)
            gui.run()
        except RuntimeError as e:
            print(f"[Error] {e}")
            print("[Info] Falling back to headless mode.")
            run_headless(monitor, source, args.output)


if __name__ == "__main__":
    main()