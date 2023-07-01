from flask import Flask, render_template, request, redirect, url_for, session
from user import User
from plyer import notification
import mysql.connector
import json
import os
import sounddevice as sd
import soundfile as sf
import librosa
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

app = Flask(__name__)
app.secret_key = 'Shri@#$%2143'
sample_duration = 4  # Duration of the recording in seconds
sample_rate = 22050  # Sample rate of the audio
dataset_directory = 'C:/test/dataset'
model = ""
features = ""
labels = ""

# MySQL database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'test',
}

def record_voice_sample(sample_duration=3, sample_rate=22050):
    print("Recording voice sample...")
    recording = sd.rec(int(sample_duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    return recording.flatten()

def generate_login_form():
    login_form = '''
    <style>
        .login-form {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }

        .login-form label {
            margin-bottom: 10px;
        }

        .login-form input[type="text"],
        .login-form input[type="password"] {
            padding: 5px;
            margin-bottom: 15px;
            width: 200px;
            border-radius: 10px;
        }

        .login-form input[type="submit"] {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        
        .login-form input[type="submit"] {
        padding: 10px 20px;
        background-color: #4CAF50;
        color: white;
        border: none;
        cursor: pointer;
        }

        .login-form input[type="submit"]:hover {
            background-color: #45a049;
        }

        .login-form input[type="submit"]:active {
            background-color: #398439;
        }
    </style>

    <form action="/login" method="post" class="login-form">
        <label for="username">Username:</label>
        <input type="text" id="username" name="username" required>
        <br><br>
        
        <label for="password">Password:</label>
        <input type="password" id="password" name="password" required>
        <br><br>
        
        <input type="submit" value="Login">
    </form>
    '''
    return login_form

def generate_registration_form():
    registration_form = '''

    <style>
        .registration-form {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }

        .registration-form label {
            margin-bottom: 10px;
        }

        .registration-form input[type="text"] {
            padding: 5px;
            margin-bottom: 15px;
            width: 200px;
            border-radius: 10px;
        }

        .registration-form input[type="password"] {
            padding: 5px;
            margin-bottom: 15px;
            width: 200px;
            border-radius: 10px;
        }

        .registration-form input[type="email"] {
            padding: 5px;
            margin-bottom: 15px;
            width: 200px;
            border-radius: 10px;
        }

        .registration-form input[type="submit"] {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        
        .registration-form input[type="submit"] {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }

        .registration-form input[type="submit"]:hover {
            background-color: #45a049;
        }

        .registration-form input[type="submit"]:active {
            background-color: #398439;
        }
    </style>

    <form action="/register" method="post" class="registration-form">
        <label for="username">Username:</label>
        <input type="text" id="username" name="username" required><br><br>
        
        <label for="password">Password:</label>
        <input type="password" id="password" name="password" required><br><br>
        
        <label for="email">Email:</label>
        <input type="email" id="email" name="email" required><br><br>
        
        <input type="submit" value="Register">
    </form>
    '''
    return registration_form

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Process the login form data
        username = request.form['username']
        password = request.form['password']
        # Perform login authentication logic using the database connection
        
        # Example: Authenticate user against users table
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        
        if user:
            # Successful login
            query = "SELECT * FROM users WHERE user_name = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            user_json = json.dumps(user)

            # Save the user JSON string in a dictionary
            localStorage = {}
            localStorage['user'] = user_json

            # Save the dictionary to a file (optional)
            with open('localStorage.json', 'w') as file:
                json.dump(localStorage, file)

            show_toastr("Success", "Login successful!")
            return redirect(url_for('dashboard', userId=user[0]))
        else:
            # Failed login
            cursor.close()
            conn.close()
            return "Invalid username or password"
    
    # Render the login form
    login_form = generate_login_form()
    return render_template('login.html', form=login_form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Process the registration form data
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # Perform registration logic using the database connection
        
        # Check if the email already exists
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email_id = %s", (email,))
        existing_email = cursor.fetchone()
        
        if existing_email:
            cursor.close()
            conn.close()
            return "Email already exists. Please choose a different email."
        
        # Check if the username already exists
        cursor.execute("SELECT * FROM users WHERE user_name = %s", (username,))
        existing_username = cursor.fetchone()
        
        if existing_username:
            cursor.close()
            conn.close()
            return "Username already exists. Please choose a different username."
        
        # If email and username are unique, insert the user into the database
        cursor.execute("INSERT INTO users (user_name, password, email_id) VALUES (%s, %s, %s)", (username, password, email))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE user_name = %s", (username,))
        newUserObj = cursor.fetchone()

        cursor.close()
        conn.close()
        user_json = json.dumps(newUserObj)

        # Save the user JSON string in a dictionary
        localStorage = {}
        localStorage['user'] = user_json

        # Save the dictionary to a file (optional)
        with open('localStorage.json', 'w') as file:
            json.dump(localStorage, file)

        
        # return redirect(url_for('record_voice', user=user))
        return redirect(url_for('dashboard', userId=newUserObj[0]));

    
    # Render the registration form
    registration_form = generate_registration_form()
    return render_template('register.html', form=registration_form)

@app.route('/dashboard')
def dashboard():
    user = request.args.get('user')
    with open('localStorage.json', 'r') as file:
        localStorage = json.load(file)

    # Retrieve the user JSON string from the dictionary
    user_json = localStorage.get('user')

    # Convert the user JSON string back to an object
    user1 = json.loads(user_json)    
    print(user1)
    return render_template('dashboard.html', user=user)

@app.route('/voice_sample')
def voice_sample():
    user = request.args.get('user')
    with open('localStorage.json', 'r') as file:
        localStorage = json.load(file)

    # Retrieve the user JSON string from the dictionary
    user_json = localStorage.get('user')

    # Convert the user JSON string back to an object
    user1 = json.loads(user_json)
    return render_template('voice_sample.html', user_name=user1[1], user_id=user1[0])    
    
@app.route('/redirect_dashboard', methods=['GET', 'POST'])
def redirectingDashboard():   
    if request.method == 'POST':
        print("Hey Buddy Im here")
    return redirect(url_for('dashboard', user=19));    


@app.route('/record_voice', methods=['GET', 'POST'])
def start_recording():
    if request.method == 'POST':
        data = request.get_json()
        userId = data.get('userId')
        username = data.get('user_name')
        print(userId)
        print(username)
        # user = request.args.get('user')
        # sample_duration = 40  # Duration of the recording in seconds
        # sample_rate = 22050  # Sample rate of the audio
        # dataset_directory = 'C:/test/dataset'
        # Get the current user's name (you may need to adjust this depending on your authentication system)
        # username = user.username

                # Collect voice sample from the user
        num_classes = 13;
        for i in range(num_classes):
            print(f"Collecting voice sample for user: {username}")
            sample = record_voice_sample(sample_duration, sample_rate)
            os.makedirs(os.path.join(dataset_directory, username), exist_ok=True)
            file_path = os.path.join(dataset_directory, username, f"sample{i+1}.wav")
            sf.write(file_path, sample, sample_rate)
            print("Voice sample collected successfully.")
        # return redirect(url_for('dashboard', user=userId))
        show_toastr("Success", "voice sample collected Successfully")
        features, labels = load_data(dataset_directory)

        # Step 3: Train a voice recognition model
        if len(set(labels)) < 2:
            print("Error: Insufficient number of classes in the dataset. Please ensure there are at least two classes.")
        else:
            model = train_model(features, labels)
        return "Success"
    # return redirect(url_for('dashboard', user=userId))

    return render_template('record_voice.html')

def show_toastr(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=5
    )

def recognize_voice(model):
    # print("Recording audio for recognition...")
    recording = sd.rec(int(sample_duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    features = extract_features(recording.flatten(), sample_rate)
    prediction = model.predict([features])
    return prediction[0]

def train_model(features, labels):
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    model = SVC()
    model.fit(X_train, y_train)
    accuracy = model.score(X_test, y_test)
    print("Accuracy:", accuracy)
    return model

def load_data(directory):
    features = []
    labels = []
    for label in os.listdir(directory):
        subdir = os.path.join(directory, label)
        if os.path.isdir(subdir):
            for filename in os.listdir(subdir):
                file_path = os.path.join(subdir, filename)
                audio, sample_rate = librosa.load(file_path, res_type='kaiser_fast')
                features.append(extract_features(audio, sample_rate))
                labels.append(label)
    return features, labels

def extract_features(audio, sample_rate):
    mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=40)
    return mfccs.flatten()
    
@app.route('/start_quiz', methods=['GET', 'POST'])
def startQuiz():   
    if request.method == 'POST':
        quiz_type = request.form.get('quiz_type')

        # data = request.get_json()
        # quiz_type = data.get('quizType')
    
        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Fetch 5 random questions of the selected quiz type
        print(quiz_type)
        query = "SELECT * FROM questions WHERE subject = %s ORDER BY RAND() LIMIT 5"
        cursor.execute(query, (quiz_type,))
        questions = cursor.fetchall()

        with open('localStorage.json', 'r') as file:
            localStorage = json.load(file)

        # Retrieve the user JSON string from the dictionary
        user_json = localStorage.get('user')

        # Convert the user JSON string back to an object
        user1 = json.loads(user_json) 

        cursor.execute("DELETE FROM user_answers WHERE user_id = %s", (user1[0],))
        conn.commit()

        cursor.close()
        conn.close()

        # print(user1)
        # return "QUiz Has been started successfully"
        print(questions)
        return render_template('quiz.html', questions=questions)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    show_toastr("Success", "Quiz  submitted successfully!")
    with open('localStorage.json', 'r') as file:
        localStorage = json.load(file)

    # Retrieve the user JSON string from the dictionary
    user_json = localStorage.get('user')

    # Convert the user JSON string back to an object
    user1 = json.loads(user_json) 
    
    return redirect(url_for('dashboard', userId=user1[0]));

@app.route('/record_voice', methods=['POST'])
def record_voice():
    data = request.get_json()
    userId = data.get('userId')
    print(userId)

    return "It's working Fine"

@app.route('/save_answer', methods=['POST'])
def save_answer():
    with open('localStorage.json', 'r') as file:
        localStorage = json.load(file)

    # Retrieve the user JSON string from the dictionary
    user_json = localStorage.get('user')

    # Convert the user JSON string back to an object
    user1 = json.loads(user_json) 

    data = request.get_json()
    question_id = data.get('questionId')
    answer = data.get('answer')
    userId = user1[0]

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    query = "SELECT * FROM questions WHERE id = %s"
    cursor.execute(query, (question_id,))
    question = cursor.fetchone()
    print("Answe :",question[1])
    actualAnswer = question[1]
    print(question[1])
    if answer.lower() in question[1].lower():
        show_toastr("Correct", "Correct Answer")
    else:
        show_toastr("Incorrect", "Wrong answer! Answer: "+question[1])

# cursor.execute("INSERT INTO users (user_name, password, email_id) VALUES (%s, %s, %s)", (username, password, email))
#         conn.commit()
    query = "INSERT INTO user_answers (question_id, user_answer, actual_answer, user_id) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (question_id, answer, question[1], userId))
    conn.commit()

    # Save the answer to the database using your database logic

    return "Success"

@app.route('/show_results')
def showResult():

    with open('localStorage.json', 'r') as file:
        localStorage = json.load(file)

    # Retrieve the user JSON string from the dictionary
    user_json = localStorage.get('user')

    # Convert the user JSON string back to an object
    user1 = json.loads(user_json)

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    query = "SELECT * FROM user_answers WHERE user_id = %s"
    cursor.execute(query, (user1[0],))
    answers = cursor.fetchall()
    score = 0;
    total = len(answers);
    for answer in answers:
        user_answer = answer[2]
        actual_answer = answer[3]

        if user_answer == actual_answer:
            score = score + 1;
    if total != 0 :
        score = (score/total)*100;
    return render_template('answers.html', answers=answers, score=score)


    return "Show Results successfully";  
    
if __name__ == '__main__':
    app.run()