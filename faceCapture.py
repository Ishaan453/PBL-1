import cv2
import os
import time
import boto3
import io
from PIL import Image

# Directory to save captured images
output_directory = 'C:\AWS\PBL-Project\StudentImages'

# Create the output directory if it does not exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Initialize the camera
cap = cv2.VideoCapture(0)

# Initialize variables
start_time = None
stare_duration_threshold = 3  # 3 seconds

# Load Haar cascade for face and eye detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # Display the captured frame
    cv2.imshow('Camera', frame)

    # Convert frame to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces in the frame
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    # Check if a face is detected
    if len(faces) > 0:
        # If this is the first time someone is staring
        if start_time is None:
            start_time = time.time()
        else:
            # Check if someone has been staring for more than the threshold duration
            if time.time() - start_time >= stare_duration_threshold:
                # Check if eyes are open
                for (x, y, w, h) in faces:
                    roi_gray = gray[y:y+h, x:x+w]
                    eyes = eye_cascade.detectMultiScale(roi_gray)
                    if len(eyes) > 0:
                        # Save the image to the output directory
                        image_path = os.path.join(output_directory, f"stared_{time.strftime('%Y%m%d%H%M%S')}.jpg")
                        cv2.imwrite(image_path, frame)
                        #print(f"Image captured: {image_path}")

                        rekognition = boto3.client('rekognition', region_name='ap-south-1')
                        dynamodb = boto3.client('dynamodb', region_name='ap-south-1')
                        
                        image = Image.open(image_path)
                        stream = io.BytesIO()
                        image.save(stream,format="JPEG")
                        image_binary = stream.getvalue()

                        response = rekognition.search_faces_by_image(
                            CollectionId='mess',
                            Image={'Bytes':image_binary}                                       
                            )
                        
                        found = False
                        for match in response['FaceMatches']:
                                
                            face = dynamodb.get_item(
                                TableName='mess_students',  
                                Key={'RekognitionId': {'S': match['Face']['FaceId']}}
                                )
                            
                            if 'Item' in face:
                                print("Welcome ", face['Item']['FullName']['S'], ", have a good meal!")
                                found = True

                        if not found:
                            print("Person cannot be recognized")

                        os.remove(image_path)
                        
                        choice = input("Enter any key to continue: ")

                        break  # Break out of the loop once an image is captured

                # Reset start time
                start_time = None

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close all OpenCV windows
cap.release()
cv2.destroyAllWindows()