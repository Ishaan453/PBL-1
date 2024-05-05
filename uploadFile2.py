from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
import os
from botocore.exceptions import NoCredentialsError

app = Flask(__name__)
app.secret_key = os.urandom(24)

# AWS Cognito configuration
# You don't need any specific library for this, just AWS SDK (boto3)
# Fill in your AWS Cognito user pool details here
USER_POOL_ID = 'us-east-1_86cNP2ufr'
CLIENT_ID = '14s0g4qcnah3ta9relp24p3l2n'
REGION = 'us-east-1'

@app.route('/')
def login_page():
    return render_template('login.html', alert_message='Please Login')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # You need to validate the username and password against AWS Cognito
    # You can use boto3 to interact with AWS Cognito to authenticate users
    # Here's a simplified example:
    try:
        client = boto3.client('cognito-idp', region_name=REGION)
        response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            },
            ClientId=CLIENT_ID
        )
        return redirect(url_for('upload_page'))  # Redirect to the upload page after successful login
    
    except client.exceptions.NotAuthorizedException:
        return render_template('login.html', alert_message='Incorrect Credentials'), 401
        #return 'Invalid username or password.', 401  # Return error message and 401 status code if authentication fails
    except NoCredentialsError:
        return render_template('login.html', alert_message='Credentials Not Found'), 500
        #return 'AWS credentials not found. Please configure AWS credentials.', 500
    except Exception as e:
        error_message = str(e)
        return render_template('login.html', alert_message=error_message), 500
        #return str(e), 500  # Return error message and 500 status code for any other errors

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    """Check if the filename has an allowed file extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        try:
            
            s3 = boto3.resource('s3')
            image_file = request.files['image']
            full_name = request.form['fullName']

            if ' ' in image_file.filename:
                return render_template('upload.html', message='Image file name should not contain spaces')
            
            if not allowed_file(image_file.filename):
                return render_template('upload.html', message='Invalid file format. Only PNG, JPG and JPEG files are allowed.')
            
            # Upload image to S3
            object_key = 'index/' + image_file.filename
            s3.Object('mess-student-face', object_key).put(Body=image_file, Metadata={'FullName': full_name})
            
            #return 'Image uploaded successfully!'
            return render_template('upload.html', message='Image uploaded Successfully!')
        except NoCredentialsError:
            return 'AWS credentials not found. Please configure AWS credentials.', 500
    
    return render_template('upload.html')

@app.route('/manage', methods=['GET', 'POST'])
def manage():
    if request.method == 'POST':

        dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
        table = dynamodb.Table('mess_students')
        student_name = request.form['student_name']

        try:
            # Query DynamoDB table for the student's name
            response = table.get_item(Key={'name': student_name})
            student = response.get('Item')

            if student:
                # Student found, render manage.html with student details
                return render_template('manage.html', student=student)
            else:
                # Student not found, render manage.html with error message
                flash(f"No student found with the name '{student_name}'.", 'error')
                return redirect(url_for('manage'))

        except Exception as e:
            # Handle DynamoDB query error
            flash(f"Error searching for student: {str(e)}", 'error')
            return redirect(url_for('manage'))

    # Render manage.html without student details on initial load
    return render_template('manage.html')


if __name__ == '__main__':
    app.run(debug=True)
