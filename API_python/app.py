from flask import Flask, render_template

app = Flask(__name__)

@app.route('/guest', methods=['GET'])
def guest_page():
    return render_template('guest.html')

@app.route('/admin', methods=['GET'])
def admin_page():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

