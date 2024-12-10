from flask import Flask, render_template
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)


@app.route('/')
def admin_page():
    return render_template('admin.html')  


@app.route('/guest')
def guest_page():
    connection = mysql.connector.connect(user="dbadmin", password="Q#604664456957uf", host="newyork.mysql.database.azure.com", port=3306, database="reservations", ssl_disabled=False)
    
    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM reservations.kentekens")
        rows = cursor.fetchall()
        connection.close()
        return render_template('guest.html', rows=rows)  

        

if __name__ == '__main__':  
    app.run(debug=True, port=5000)  
