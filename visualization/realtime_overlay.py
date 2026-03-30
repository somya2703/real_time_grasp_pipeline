import cv2
from ultralytics import YOLO

model = YOLO("models/yolov8n.engine", task="detect")
frame = cv2.imread("/workspace/test_data/test.jpg")
results = model(frame)
annotated = results[0].plot()
cv2.imwrite("/workspace/test_data/output.jpg", annotated)
print("Saved to /workspace/test_data/output.jpg")