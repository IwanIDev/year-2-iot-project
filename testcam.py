from ultralytics import YOLO
import cv2

#after training the model there will be a folder called runs, open detect folder and pick most recent train
#go into the wieghts folder and put the best.pt file in the model function

model = YOLO("best2.pt")

cap = cv2.VideoCapture(0)  # 0 = laptop webcam

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=0.5)

    annotated = results[0].plot()

    cv2.imshow("YOLO Webcam", annotated)

    if cv2.waitKey(1) == ord('q'):
        break

#run the script and it should work

cap.release()
cv2.destroyAllWindows()
