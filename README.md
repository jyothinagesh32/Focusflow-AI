# FocusFlow AI — XAMPP MySQL Connected

## 1. Start XAMPP
Open XAMPP Control Panel and start **MySQL**. Apache is not required for this Flask app.

## 2. Create/import the database
1. Open `http://localhost/phpmyadmin`.
2. Select **Import**.
3. Choose `database/focusflow_ai.sql` from this project folder.
4. Click **Import** / **Go**.
The SQL file creates the `focusflow_ai` database and the core tables. On startup, SQLAlchemy `db.create_all()` creates any additional tables used by this version of the app.

## 3. Configure the MySQL password
Default config assumes XAMPP MySQL username `root` and an empty password.
If your root account has a password, open `config.py` and change:
`mysql+pymysql://root:@127.0.0.1:3306/focusflow_ai`
to:
`mysql+pymysql://root:YOUR_PASSWORD@127.0.0.1:3306/focusflow_ai`
If the password contains characters such as @, #, /, or :, URL-encode those characters or set `DATABASE_URL` to a properly encoded URI.

## 4. Install and run in Windows CMD
Open CMD in the extracted project folder and run:

```cmd
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. Keep the CMD window open.

## 5. Confirm the database connection
When MySQL is not running or the credentials/database are incorrect, the app will show a SQLAlchemy/MySQL connection error in CMD at startup. Make sure XAMPP MySQL is green/running and the database name is exactly `focusflow_ai`.

## Existing data warning
This ZIP uses MySQL by default. Your old SQLite data in `focusflow_ai.db` will not be copied automatically into MySQL. Keep a backup of your existing database. If you already have student records in SQLite, they must be migrated separately; don't delete the old database.
