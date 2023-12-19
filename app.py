from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    jsonify,
    flash,

)
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from pymongo import MongoClient
import os
import hashlib
from datetime import datetime, timedelta
from bson import ObjectId
import jwt
from os.path import join, dirname
from functools import wraps


app = Flask(__name__)
# Atur folder untuk menyimpan file di direktori 'static'
app.config["UPLOAD_FOLDER"] = "static/uploads"

dotenv_path = join(dirname(__file__), '.env')

MONGODB_CONNECTION_STRING = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_CONNECTION_STRING)
db = client[DB_NAME]

SECRET_KEY = "SPARTA"
# # Memberikan SECRET_KEY
app.config["SECRET_KEY"] = "SPARTA"

# Setup Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login_user"


# HOME
@app.route("/")
def index_page():
    return render_template("index_page.html")


# AUTH
# Define User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["nama"]
        self.email = user_data["email"]
        self.role = user_data["role"]


@login_manager.user_loader
def load_user(user_id):
    user_data = db.user.find_one({"_id": ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None


# PENDAFTAR
# Login Pendaftar
@app.route("/login/user", methods=["GET", "POST"])
def login_pendaftar():
    # Jika methods POST
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username_receive = request.form.get("username_give")
        password_receive = request.form.get("password_give")

        password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()

        user_data = db.user.find_one(
            {
                "username": username_receive,
                "password": password_hash,
            }
        )

        if user_data is not None:
            user = User(user_data)
            login_user(user)

            payload = {
                "username": username_receive,
                "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
            return jsonify(
                {"result": "success", "token": token, "role": user_data["role"]}
            )
        else:
            return jsonify(
                {
                    "result": "fail",
                    "msg": "Terdapat kesalahan pada username atau Password anda!",
                }
            )

    # GET
    msg = request.args.get("msg")
    return render_template("login_pendaftar.html", msg=msg)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login_pendaftar"))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Silakan login terlebih dahulu untuk mengakses halaman ini.", "error")
            return redirect(url_for("login_pendaftar"))
        return f(*args, **kwargs)

    return decorated_function


# artikel
@app.route("/artikel")
def artikel():
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))
    return render_template("artikel.html")


@login_required
@app.route("/dashboard")
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))

    print(
        "\n\nloaded user",
        current_user.id,
        current_user.username,
        current_user.email,
        "\n",
    )
    return render_template("dashboard.html")


@app.route("/pendaftaran")
@login_required
def halamanan_pendaftaran():
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))

    return render_template("pendaftaran.html")


@app.route("/register/user", methods=["GET", "POST"])
def register_user():
    # Jika methods POST
    if request.method == "POST":
        username_receive = request.form.get("username_give")
        email_receive = request.form.get("email_give")
        password_receive = request.form.get("password_give")

        # Hashing password
        password_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()

        # Data yang akan disimpan
        doc = {
            "username": username_receive,
            "email": email_receive,
            "password": password_hash,
            "nama": username_receive,
            "role": 'user'
        }

        # Masukkan data ke database
        db.user.insert_one(doc)

        return jsonify({"result": "success"})

    # Jika methods GET
    msg = request.args.get("msg")
    return render_template("registrasi.html", msg=msg)


# Pendaftaran pesantren
@login_required
@app.route("/pendaftaran", methods=["POST"])
def pendaftaran():
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))

    nama = request.form["nama"]
    jenisKelamin = request.form["jenisKelamin"]
    alamat = request.form["alamat"]
    no = request.form["no"]
    asal = request.form["asal"]
    ijazah = request.files["ijazah"]
    kk = request.files["kk"]

    today = datetime.now()
    mytime = today.strftime("%Y-%m-%d-%H-%M-%S")

    ijazah_save = f'static/file/ijazah-{mytime}.{ijazah.filename.split(".")[-1]}'
    kk_save = f'static/file/kk-{mytime}.{kk.filename.split(".")[-1]}'

    ijazah.save(ijazah_save)
    kk.save(kk_save)

    time = today.strftime("%Y-%m-%d")

    doc = {
        "nama": nama,
        "jenisKelamin": jenisKelamin,
        "alamat": alamat,
        "no": no,
        "asal": asal,
        "ijazah": ijazah_save,
        "kk": kk_save,
        "time": time,
    }
    db.pendaftaran.insert_one(doc)
    return render_template("pendaftaran.html")


@login_required
@app.route("/profile")
def profile():
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))

    return render_template("profile.html")


@login_required
@app.route("/status_pendaftaran")
def status_pendaftaran():
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))

    return render_template("status_pendaftaran.html")


@app.route("/kontak")
def kontak_kami():
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))
    return render_template("kontak_kami.html")


# ADMIN
@app.route("/admin")
def admin():
    # proteksi route admin
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))

    if current_user.role != "admin":
        return redirect(url_for("login_pendaftar"))

    data = db.pendaftaran.find()
    return render_template("dashboard_admin.html", data=data)


@app.route("/update/<id>", methods=["GET", "POST"])
def update(id):
    data = db.pendaftaran.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        updated_data = {
            "nama": request.form["nama"],
            "asal": request.form["asal"],
            "status": request.form["status"],
            # ... (tambahkan bidang lainnya sesuai kebutuhan)
        }

        db.pendaftaran.update_one({"_id": ObjectId(id)}, {"$set": updated_data})

        return redirect(url_for("admin"))

    return render_template("update.html", data=data)


@app.route("/hapus/<id>")
def hapus(id):
    # Mendapatkan data pendaftaran yang akan dihapus
    data = db.pendaftaran.find_one({"_id": ObjectId(id)})

    # Menghapus file Ijazah dan Kartu Keluarga dari direktori
    if data:
        os.remove(data["ijazah"])
        os.remove(data["kk"])

    # Menghapus data dari database
    db.pendaftaran.delete_one({"_id": ObjectId(id)})

    return redirect(url_for("admin"))


@app.route("/profile_admin")
def profile_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("login_pendaftar"))
    if current_user.role != "admin":
        return redirect(url_for("login_pendaftar"))
    
    return render_template("profile_admin.html")


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
