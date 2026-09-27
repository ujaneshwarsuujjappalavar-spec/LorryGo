from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "lorrygo_secret_2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "lorry_transport.db")


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():

    conn = get_db()

    # USERS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer'
        )
    """)

    # LORRIES
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lorries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_number TEXT UNIQUE NOT NULL,
            lorry_type TEXT NOT NULL,
            capacity TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available',
            price_per_km REAL NOT NULL DEFAULT 30,
            driver_id INTEGER
        )
    """)

    # BOOKINGS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            lorry_id INTEGER NOT NULL,
            pickup_location TEXT NOT NULL,
            drop_location TEXT NOT NULL,
            distance REAL NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Booked'
        )
    """)

    # DRIVER GPS
    conn.execute("""
        CREATE TABLE IF NOT EXISTS driver_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER UNIQUE NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    # SAMPLE LORRIES
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM lorries"
    ).fetchone()["c"]

    if count == 0:

        conn.executemany("""
            INSERT INTO lorries
            (vehicle_number, lorry_type, capacity, status, price_per_km)
            VALUES (?, ?, ?, 'Available', ?)
        """, [

            ("KA17AB1234", "Mini Lorry", "2 Ton", 30),

            ("KA17CD5678", "Medium Lorry", "5 Ton", 35),

            ("KA17EF9012", "Heavy Lorry", "10 Ton", 45)

        ])

        conn.commit()

    conn.close()


# =========================================================
# LOGIN HELPERS
# =========================================================

def customer_required():

    return (
        "user_id" in session
        and session.get("user_role") == "customer"
    )


def driver_required():

    return (
        "user_id" in session
        and session.get("user_role") == "driver"
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template("index.html")


# =========================================================
# CUSTOMER REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        if not all([name, email, phone, password]):

            return render_template(
                "register.html",
                error="Please fill all fields."
            )

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, phone, password, role)
                VALUES (?, ?, ?, ?, 'customer')
            """, (
                name,
                email,
                phone,
                password
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()

            return render_template(
                "register.html",
                error="This email is already registered. Please use another email or login."
            )

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# DRIVER REGISTER
# =========================================================

@app.route("/driver-register", methods=["GET", "POST"])
def driver_register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")

        vehicle_number = request.form.get(
            "vehicle_number", ""
        ).strip().upper()

        lorry_type = request.form.get(
            "lorry_type", ""
        ).strip()

        capacity = request.form.get(
            "capacity", ""
        ).strip()

        if not all([
            name,
            email,
            phone,
            password,
            vehicle_number,
            lorry_type,
            capacity
        ]):

            return render_template(
                "driver_register.html",
                error="Please fill all driver and lorry details."
            )

        conn = get_db()

        try:

            cursor = conn.execute("""
                INSERT INTO users
                (name, email, phone, password, role)
                VALUES (?, ?, ?, ?, 'driver')
            """, (
                name,
                email,
                phone,
                password
            ))

            driver_id = cursor.lastrowid

            conn.execute("""
                INSERT INTO lorries
                (
                    vehicle_number,
                    lorry_type,
                    capacity,
                    status,
                    price_per_km,
                    driver_id
                )
                VALUES (?, ?, ?, 'Available', ?, ?)
            """, (
                vehicle_number,
                lorry_type,
                capacity,
                30,
                driver_id
            ))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.rollback()
            conn.close()

            return render_template(
                "driver_register.html",
                error="Email or vehicle number is already registered."
            )

        conn.close()

        return redirect(
            url_for("login", registered="driver")
        )

    return render_template("driver_register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE email = ?
            AND password = ?
        """, (
            email,
            password
        )).fetchone()

        conn.close()

        if user:

            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]

            if user["role"] == "driver":

                return redirect(
                    url_for("driver_dashboard")
                )

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    message = None

    if request.args.get("registered") == "driver":

        message = (
            "Driver account created successfully. "
            "You can login now."
        )

    return render_template(
        "login.html",
        message=message
    )


# =========================================================
# CUSTOMER DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(url_for("login"))

    if session.get("user_role") == "driver":

        return redirect(
            url_for("driver_dashboard")
        )

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session["user_id"],
    )).fetchone()

    booking_count = conn.execute("""
        SELECT COUNT(*) AS c
        FROM bookings
        WHERE customer_id = ?
    """, (
        session["user_id"],
    )).fetchone()["c"]

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        booking_count=booking_count
    )


# =========================================================
# FIND LORRY
# =========================================================

@app.route("/find-lorry")
def find_lorry():

    pickup = request.args.get(
        "pickup", ""
    ).strip()

    destination = request.args.get(
        "destination", ""
    ).strip()

    distance = request.args.get(
        "distance", ""
    ).strip()

    conn = get_db()

    lorries = conn.execute("""
        SELECT *
        FROM lorries
        WHERE status = 'Available'
        ORDER BY id
    """).fetchall()

    conn.close()

    return render_template(
        "find_lorry.html",
        lorries=lorries,
        pickup=pickup,
        destination=destination,
        distance=distance
    )


# =========================================================
# BOOK LORRY
# =========================================================

@app.route("/book-lorry", methods=["POST"])
def book_lorry():

    if not customer_required():

        return redirect(
            url_for("login")
        )

    lorry_id = request.form.get(
        "lorry_id"
    )

    pickup = request.form.get(
        "pickup_location", ""
    ).strip()

    destination = request.form.get(
        "drop_location", ""
    ).strip()

    try:

        distance = float(
            request.form.get(
                "distance", "0"
            )
        )

    except ValueError:

        distance = 0

    if (
        not lorry_id
        or not pickup
        or not destination
        or distance <= 0
    ):

        return (
            "Please provide valid booking details.",
            400
        )

    conn = get_db()

    lorry = conn.execute("""
        SELECT *
        FROM lorries
        WHERE id = ?
        AND status = 'Available'
    """, (
        lorry_id,
    )).fetchone()

    if lorry is None:

        conn.close()

        return (
            "This lorry is no longer available."
        )

    price = round(
        distance *
        float(lorry["price_per_km"]),
        2
    )

    conn.execute("""
        INSERT INTO bookings
        (
            customer_id,
            lorry_id,
            pickup_location,
            drop_location,
            distance,
            price,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, 'Booked')
    """, (
        session["user_id"],
        lorry_id,
        pickup,
        destination,
        distance,
        price
    ))

    conn.execute("""
        UPDATE lorries
        SET status = 'Booked'
        WHERE id = ?
    """, (
        lorry_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for("my_bookings")
    )


# =========================================================
# MY BOOKINGS
# =========================================================

@app.route("/my-bookings")
def my_bookings():

    if not customer_required():

        return redirect(
            url_for("login")
        )

    conn = get_db()

    bookings = conn.execute("""
        SELECT
            bookings.*,
            lorries.vehicle_number,
            lorries.lorry_type,
            lorries.capacity,
            users.name AS driver_name,
            users.phone AS driver_phone
        FROM bookings
        JOIN lorries
            ON bookings.lorry_id = lorries.id
        LEFT JOIN users
            ON lorries.driver_id = users.id
        WHERE bookings.customer_id = ?
        ORDER BY bookings.id DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "my_bookings.html",
        bookings=bookings
    )


# =========================================================
# TRACK DELIVERY
# =========================================================

@app.route("/track-delivery")
def track_delivery():

    if not customer_required():

        return redirect(
            url_for("login")
        )

    conn = get_db()

    bookings = conn.execute("""
        SELECT
            bookings.*,
            lorries.vehicle_number,
            lorries.driver_id,
            users.name AS driver_name
        FROM bookings
        JOIN lorries
            ON bookings.lorry_id = lorries.id
        LEFT JOIN users
            ON lorries.driver_id = users.id
        WHERE bookings.customer_id = ?
        ORDER BY bookings.id DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "track_delivery.html",
        bookings=bookings
    )


# =========================================================
# CUSTOMER LIVE MAP
# =========================================================

@app.route("/live-map")
def live_map():

    if not customer_required():

        return redirect(
            url_for("login")
        )

    driver_id = request.args.get(
        "driver_id", ""
    )

    return render_template(
        "live_map.html",
        driver_id=driver_id
    )


# =========================================================
# DRIVER DASHBOARD
# =========================================================

@app.route("/driver-dashboard")
def driver_dashboard():

    if not driver_required():

        return redirect(
            url_for("login")
        )

    conn = get_db()

    driver = conn.execute("""
        SELECT
            users.id,
            users.name,
            users.email,
            users.phone,
            lorries.id AS lorry_id,
            lorries.vehicle_number,
            lorries.lorry_type,
            lorries.capacity,
            lorries.status,
            lorries.price_per_km
        FROM users
        LEFT JOIN lorries
            ON users.id = lorries.driver_id
        WHERE users.id = ?
    """, (
        session["user_id"],
    )).fetchone()

    bookings = conn.execute("""
        SELECT
            bookings.*,
            users.name AS customer_name,
            users.phone AS customer_phone,
            lorries.vehicle_number,
            lorries.lorry_type
        FROM bookings
        JOIN lorries
            ON bookings.lorry_id = lorries.id
        JOIN users
            ON bookings.customer_id = users.id
        WHERE lorries.driver_id = ?
        ORDER BY bookings.id DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "driver_dashboard.html",
        driver=driver,
        bookings=bookings
    )


# =========================================================
# ACCEPT BOOKING
# =========================================================

@app.route("/accept-booking", methods=["POST"])
def accept_booking():

    if not driver_required():

        return redirect(
            url_for("login")
        )

    booking_id = request.form.get(
        "booking_id"
    )

    conn = get_db()

    booking = conn.execute("""
        SELECT
            bookings.*,
            lorries.driver_id
        FROM bookings
        JOIN lorries
            ON bookings.lorry_id = lorries.id
        WHERE bookings.id = ?
        AND lorries.driver_id = ?
    """, (
        booking_id,
        session["user_id"]
    )).fetchone()

    if booking is None:

        conn.close()

        return "Booking not found."

    if booking["status"] != "Booked":

        conn.close()

        return (
            "This booking has already been processed."
        )

    conn.execute("""
        UPDATE bookings
        SET status = 'Accepted'
        WHERE id = ?
    """, (
        booking_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for("driver_dashboard")
    )


# =========================================================
# DRIVER GPS PAGE
# =========================================================

@app.route("/driver-live-map")
def driver_live_map():

    if not driver_required():

        return redirect(
            url_for("login")
        )

    return render_template(
        "driver_live_map.html"
    )


# =========================================================
# UPDATE DRIVER GPS
# =========================================================

@app.route("/update-location", methods=["POST"])
def update_location():

    if not driver_required():

        return jsonify({
            "success": False,
            "message": "Driver login required."
        }), 403

    try:

        data = request.get_json()

        latitude = float(
            data["latitude"]
        )

        longitude = float(
            data["longitude"]
        )

    except Exception:

        return jsonify({
            "success": False,
            "message": "Invalid GPS data."
        }), 400

    conn = get_db()

    existing = conn.execute("""
        SELECT id
        FROM driver_locations
        WHERE driver_id = ?
    """, (
        session["user_id"],
    )).fetchone()

    if existing:

        conn.execute("""
            UPDATE driver_locations
            SET latitude = ?,
                longitude = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE driver_id = ?
        """, (
            latitude,
            longitude,
            session["user_id"]
        ))

    else:

        conn.execute("""
            INSERT INTO driver_locations
            (
                driver_id,
                latitude,
                longitude
            )
            VALUES (?, ?, ?)
        """, (
            session["user_id"],
            latitude,
            longitude
        ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


# =========================================================
# GET DRIVER GPS
# =========================================================

@app.route("/driver-location")
def driver_location():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Login required."
        }), 401

    driver_id = request.args.get(
        "driver_id"
    )

    conn = get_db()

    if driver_id:

        location = conn.execute("""
            SELECT
                driver_locations.*,
                users.name AS driver_name,
                lorries.vehicle_number
            FROM driver_locations
            JOIN users
                ON driver_locations.driver_id = users.id
            LEFT JOIN lorries
                ON driver_locations.driver_id =
                   lorries.driver_id
            WHERE driver_locations.driver_id = ?
        """, (
            driver_id,
        )).fetchone()

    else:

        location = conn.execute("""
            SELECT
                driver_locations.*,
                users.name AS driver_name,
                lorries.vehicle_number
            FROM driver_locations
            JOIN users
                ON driver_locations.driver_id = users.id
            LEFT JOIN lorries
                ON driver_locations.driver_id =
                   lorries.driver_id
            ORDER BY driver_locations.updated_at DESC
            LIMIT 1
        """).fetchone()

    conn.close()

    if location is None:

        return jsonify({
            "success": False,
            "message": "Driver location is not available yet."
        })

    return jsonify({

        "success": True,

        "driver_id":
            location["driver_id"],

        "driver_name":
            location["driver_name"],

        "vehicle_number":
            location["vehicle_number"],

        "latitude":
            location["latitude"],

        "longitude":
            location["longitude"],

        "updated_at":
            location["updated_at"]
    })


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    create_database()

    print("----------------------------------------")
    print("       LORRYGO TRANSPORT SYSTEM")
    print("----------------------------------------")
    print("http://127.0.0.1:5000")
    print("----------------------------------------")

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )