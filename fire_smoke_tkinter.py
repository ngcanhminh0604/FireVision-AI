# -*- coding: utf-8 -*-
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "runs" / "train" / "yolov8_custom_64epoch" / "weights" / "best.pt"

FIRE_CLASS_ID = 0
SMOKE_CLASS_ID = 1
FIRE_CONFIDENCE = 0.35
SMOKE_CONFIDENCE = 0.08
PREDICT_IMAGE_SIZE = 1280
DETECTION_TTL_SECONDS = 0.8
CAMERA_INDEX = 0


def detect_faint_smoke(frame):
    h, w = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_gray_white = (0, 0, 85)
    upper_gray_white = (180, 80, 255)
    mask = cv2.inRange(hsv, lower_gray_white, upper_gray_white)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.GaussianBlur(mask, (15, 15), 0)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    min_area = max(900, int(w * h * 0.012))
    max_area = int(w * h * 0.65)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area or area > max_area:
            continue

        x, y, bw, bh = cv2.boundingRect(contour)
        aspect_ratio = bw / max(bh, 1)
        if aspect_ratio < 0.18 or aspect_ratio > 5.5:
            continue

        roi = mask[y : y + bh, x : x + bw]
        density = cv2.countNonZero(roi) / max(bw * bh, 1)
        if density < 0.18:
            continue

        candidates.append(
            {
                "class_id": SMOKE_CLASS_ID,
                "name": "smoke",
                "confidence": min(0.99, 0.35 + density),
                "xyxy": (x, y, x + bw, y + bh),
            }
        )

    candidates.sort(key=lambda item: item["confidence"], reverse=True)
    return candidates[:3]


def draw_box(frame, item, color, label):
    x1, y1, x2, y2 = item["xyxy"]
    text = f"{label} {item['confidence']:.2f}"

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        frame,
        text,
        (x1, max(24, y1 - 8)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        color,
        2,
        cv2.LINE_AA,
    )


class DetectionWorker(threading.Thread):
    def __init__(self, name, class_id, confidence, input_queue, result_callback, use_smoke_fallback=False):
        super().__init__(daemon=True)
        self.name = name
        self.class_id = class_id
        self.confidence = confidence
        self.input_queue = input_queue
        self.result_callback = result_callback
        self.use_smoke_fallback = use_smoke_fallback
        self.model = YOLO(str(MODEL_PATH))

    def run(self):
        while True:
            frame = self.input_queue.get()
            if frame is None:
                break

            boxes = predict_class(self.model, frame, self.class_id, self.name, self.confidence)
            if self.use_smoke_fallback and not boxes:
                boxes = detect_faint_smoke(frame)

            self.result_callback(self.name, boxes)


def predict_class(model, frame, class_id, name, confidence):
    results = model.predict(
        frame,
        conf=confidence,
        imgsz=PREDICT_IMAGE_SIZE,
        classes=[class_id],
        verbose=False,
    )

    boxes = []
    for box in results[0].boxes:
        score = float(box.conf[0])
        if score < confidence:
            continue

        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        boxes.append(
            {
                "class_id": class_id,
                "name": name,
                "confidence": score,
                "xyxy": (x1, y1, x2, y2),
            }
        )

    return boxes


class FireSmokeApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Fire and Smoke Detection")
        self.window.geometry("900x700")
        self.window.configure(bg="#101418")
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        if not MODEL_PATH.exists():
            messagebox.showerror("Lỗi", f"Không tìm thấy model:\n{MODEL_PATH}")
            self.window.destroy()
            return

        self.upload_model = YOLO(str(MODEL_PATH))
        self.camera = None
        self.running = False
        self.fire_queue = None
        self.smoke_queue = None
        self.workers = []
        self.result_lock = threading.Lock()
        self.latest_results = {
            "fire": {"boxes": [], "time": 0.0},
            "smoke": {"boxes": [], "time": 0.0},
        }

        self.video_label = tk.Label(window, bg="#101418")
        self.video_label.pack(padx=16, pady=(16, 8))

        self.status_label = tk.Label(
            window,
            text="KHÔNG PHÁT HIỆN",
            font=("Arial", 30, "bold"),
            fg="white",
            bg="#2f3338",
            width=24,
            pady=12,
        )
        self.status_label.pack(pady=8)

        self.detail_label = tk.Label(
            window,
            text=(
                f"Camera 2 luồng + upload ảnh | "
                f"Lửa >= {FIRE_CONFIDENCE} | Khói >= {SMOKE_CONFIDENCE}"
            ),
            font=("Arial", 11),
            fg="#b8c0cc",
            bg="#101418",
        )
        self.detail_label.pack(pady=(0, 10))

        button_frame = tk.Frame(window, bg="#101418")
        button_frame.pack(pady=8)

        self.start_button = tk.Button(
            button_frame,
            text="Bắt đầu camera",
            font=("Arial", 13, "bold"),
            command=self.start_camera,
            width=16,
        )
        self.start_button.grid(row=0, column=0, padx=8)

        self.stop_button = tk.Button(
            button_frame,
            text="Dừng",
            font=("Arial", 13, "bold"),
            command=self.stop_camera,
            width=10,
            state=tk.DISABLED,
        )
        self.stop_button.grid(row=0, column=1, padx=8)

        self.upload_button = tk.Button(
            button_frame,
            text="Upload ảnh",
            font=("Arial", 13, "bold"),
            command=self.upload_image,
            width=12,
        )
        self.upload_button.grid(row=0, column=2, padx=8)

        self.close_button = tk.Button(
            button_frame,
            text="Thoát",
            font=("Arial", 13, "bold"),
            command=self.close,
            width=10,
        )
        self.close_button.grid(row=0, column=3, padx=8)

    def start_camera(self):
        if self.running:
            return

        self.camera = cv2.VideoCapture(CAMERA_INDEX)
        if not self.camera.isOpened():
            messagebox.showerror("Lỗi", "Không mở được camera. Hãy kiểm tra webcam.")
            self.camera = None
            return

        self.fire_queue = queue.Queue(maxsize=1)
        self.smoke_queue = queue.Queue(maxsize=1)
        self.workers = [
            DetectionWorker("fire", FIRE_CLASS_ID, FIRE_CONFIDENCE, self.fire_queue, self.update_result),
            DetectionWorker(
                "smoke",
                SMOKE_CLASS_ID,
                SMOKE_CONFIDENCE,
                self.smoke_queue,
                self.update_result,
                use_smoke_fallback=True,
            ),
        ]

        for worker in self.workers:
            worker.start()

        with self.result_lock:
            self.latest_results = {
                "fire": {"boxes": [], "time": 0.0},
                "smoke": {"boxes": [], "time": 0.0},
            }

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_frame()

    def stop_camera(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        for worker_queue in (self.fire_queue, self.smoke_queue):
            if worker_queue is not None:
                self.put_latest_frame(worker_queue, None)

        self.fire_queue = None
        self.smoke_queue = None
        self.workers = []
        self.set_status("KHÔNG PHÁT HIỆN", "#2f3338")

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh để nhận diện",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"),
                ("All files", "*.*"),
            ],
        )
        if not file_path:
            return

        self.stop_camera()

        image = cv2.imread(file_path)
        if image is None:
            messagebox.showerror("Lỗi", "Không đọc được file ảnh đã chọn.")
            return

        fire_boxes = predict_class(
            self.upload_model,
            image,
            FIRE_CLASS_ID,
            "fire",
            FIRE_CONFIDENCE,
        )
        smoke_boxes = predict_class(
            self.upload_model,
            image,
            SMOKE_CLASS_ID,
            "smoke",
            SMOKE_CONFIDENCE,
        )
        if not smoke_boxes:
            smoke_boxes = detect_faint_smoke(image)

        display_image = image.copy()
        for item in smoke_boxes:
            draw_box(display_image, item, (150, 150, 150), "KHÓI")
        for item in fire_boxes:
            draw_box(display_image, item, (0, 0, 220), "LỬA")

        self.show_frame(display_image)
        status, color = self.get_status_from_boxes(fire_boxes, smoke_boxes)
        self.set_status(status, color)

    def update_frame(self):
        if not self.running or self.camera is None:
            return

        ok, frame = self.camera.read()
        if not ok:
            self.stop_camera()
            messagebox.showerror("Lỗi", "Không đọc được hình ảnh từ camera.")
            return

        self.put_latest_frame(self.fire_queue, frame.copy())
        self.put_latest_frame(self.smoke_queue, frame.copy())

        display_frame = self.draw_latest_results(frame)
        status, color = self.get_status()
        self.set_status(status, color)
        self.show_frame(display_frame)

        self.window.after(30, self.update_frame)

    def put_latest_frame(self, worker_queue, frame):
        if worker_queue is None:
            return

        try:
            worker_queue.put_nowait(frame)
        except queue.Full:
            try:
                worker_queue.get_nowait()
            except queue.Empty:
                pass
            worker_queue.put_nowait(frame)

    def update_result(self, name, boxes):
        with self.result_lock:
            self.latest_results[name] = {"boxes": boxes, "time": time.time()}

    def get_fresh_results(self):
        now = time.time()
        with self.result_lock:
            fire = self.latest_results["fire"].copy()
            smoke = self.latest_results["smoke"].copy()

        if now - fire["time"] > DETECTION_TTL_SECONDS:
            fire["boxes"] = []
        if now - smoke["time"] > DETECTION_TTL_SECONDS:
            smoke["boxes"] = []

        return fire["boxes"], smoke["boxes"]

    def draw_latest_results(self, frame):
        fire_boxes, smoke_boxes = self.get_fresh_results()

        for item in smoke_boxes:
            draw_box(frame, item, (150, 150, 150), "KHÓI")

        for item in fire_boxes:
            draw_box(frame, item, (0, 0, 220), "LỬA")

        return frame

    def show_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame = resize_to_fit(rgb_frame, 820, 520)
        image = Image.fromarray(rgb_frame)
        photo = ImageTk.PhotoImage(image=image)

        self.video_label.configure(image=photo)
        self.video_label.image = photo

    def get_status(self):
        fire_boxes, smoke_boxes = self.get_fresh_results()
        return self.get_status_from_boxes(fire_boxes, smoke_boxes)

    def get_status_from_boxes(self, fire_boxes, smoke_boxes):
        if fire_boxes:
            return "LỬA", "#d62828"

        if smoke_boxes:
            return "KHÓI", "#6c757d"

        return "KHÔNG PHÁT HIỆN", "#2f3338"

    def set_status(self, text, color):
        self.status_label.config(text=text, bg=color)

    def close(self):
        self.stop_camera()
        self.window.destroy()


def resize_to_fit(frame, max_width, max_height):
    h, w = frame.shape[:2]
    scale = min(max_width / w, max_height / h)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)


if __name__ == "__main__":
    root = tk.Tk()
    app = FireSmokeApp(root)
    root.mainloop()
