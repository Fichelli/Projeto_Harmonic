import os
from datetime import timedelta

from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import func   # <- para ORDER BY NEWID() no SQL Server

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")

# ---- SQL Server (ajuste .env se precisar) ----
MSSQL_USER = os.getenv("MSSQL_USER", "SA")
MSSQL_PASSWORD = os.getenv("MSSQL_PASSWORD", "")
MSSQL_HOST = os.getenv("MSSQL_HOST", "localhost")
MSSQL_PORT = os.getenv("MSSQL_PORT", "1433")
MSSQL_DB = os.getenv("MSSQL_DB", "harmonic_db")
ODBC_DRIVER = os.getenv("ODBC_DRIVER", "ODBC Driver 17 for SQL Server")  # ou 18


def ensure_mssql_database():
    """Cria o banco se não existir (requer permissão)."""
    # Para rodar na escola
    # server_uri = (
    #     f"mssql+pyodbc://{MSSQL_USER}:{MSSQL_PASSWORD}"
    #     f"@{MSSQL_HOST},{MSSQL_PORT}/master?driver={ODBC_DRIVER.replace(' ', '+')}"
    # )
    # Para rodar em casa
    server_uri = (
        f"mssql+pyodbc://@{MSSQL_HOST},{MSSQL_PORT}/master"
        f"?driver={ODBC_DRIVER.replace(' ', '+')}&trusted_connection=yes"
    )
    engine = create_engine(server_uri, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        conn.execute(text(
            f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{MSSQL_DB}') "
            f"BEGIN CREATE DATABASE [{MSSQL_DB}] COLLATE Latin1_General_100_CI_AI_SC END"
        ))


# garante DB
ensure_mssql_database()

# aponta SQLAlchemy para o DB
# Para rodar na escola
# app.config["SQLALCHEMY_DATABASE_URI"] = (
#     f"mssql+pyodbc://{MSSQL_USER}:{MSSQL_PASSWORD}"
#     f"@{MSSQL_HOST},{MSSQL_PORT}/{MSSQL_DB}?driver={ODBC_DRIVER.replace(' ', '+')}"
# )

# Para rodar em casa
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mssql+pyodbc://@{MSSQL_HOST},{MSSQL_PORT}/{MSSQL_DB}"
    f"?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# sessão
app.permanent_session_lifetime = timedelta(days=1)

db = SQLAlchemy(app)


# -----------------------------
# Modelos
# -----------------------------
class User(db.Model):
    __tablename__ = "users"

    id           = db.Column(db.Integer, primary_key=True)
    first_name   = db.Column(db.String(80), nullable=False)
    last_name    = db.Column(db.String(80), nullable=False)
    cpf          = db.Column(db.String(14), unique=True, nullable=False)
    email        = db.Column(db.String(180), unique=True, nullable=False)
    nickname     = db.Column(db.String(80), unique=True, nullable=False)
    role         = db.Column(
        db.Enum("listener", "artist", "admin", name="user_roles"),
        default="listener",
        nullable=False
    )
    password_hash = db.Column(db.String(255), nullable=False)

    musics = db.relationship("Music", backref="artist", lazy=True)
    favorites = db.relationship("Favorite", backref="user", lazy=True)

    def set_password(self, raw_password: str):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class Music(db.Model):
    __tablename__ = "musics"

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(160), nullable=False)
    genre       = db.Column(db.String(80))
    cover_url   = db.Column(db.String(4096))
    artist_name = db.Column(db.String(120))
    artist_id   = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    favorited_by = db.relationship("Favorite", backref="music", lazy=True)


class Favorite(db.Model):
    __tablename__ = "favorites"

    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    music_id = db.Column(db.Integer, db.ForeignKey("musics.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "music_id", name="uq_favorite_user_music"),
    )

# -----------------------------
# Músicas padrão (seed)
# -----------------------------
SEED_TRACKS = [
    # ---------------- BRASIL ----------------
    {"title": "Envolver",                "genre": "Reggaeton",     "artist_name": "Anitta",                    "cover_url": "https://upload.wikimedia.org/wikipedia/pt/c/c7/Envolver_-_Anitta.png"},
    {"title": "Idiota",                  "genre": "Pop",           "artist_name": "Jão",                       "cover_url": "https://i.scdn.co/image/ab67616d0000b27376086200d394250d6eef8adf"},
    {"title": "Me Lambe",                "genre": "Pop",           "artist_name": "Jão",                       "cover_url": "https://static.wikia.nocookie.net/jao/images/2/22/SUPER_Capa_do_%C3%81lbum.png/revision/latest?cb=20231207144616&path-prefix=pt-br"},
    {"title": "Coringa",                 "genre": "Pop",           "artist_name": "Jão",                       "cover_url": "https://upload.wikimedia.org/wikipedia/pt/4/4f/Coringa_-_J%C3%A3o.png"},
    {"title": "Love Love",               "genre": "Pop",           "artist_name": "Luísa Sonza",              "cover_url": "https://s2-g1.glbimg.com/PdfwBwbI2SO9O3f8ZyKjZKFPUp8=/0x0:2048x2048/1008x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_59edd422c0c84a879bd37670ae4f538a/internal_photos/bs/2023/q/q/A40hpHRceiB3Ewik8t2w/luisasonzaescandalointimocapa.jpg"},

    {"title": "Penhasco",                "genre": "Pop",           "artist_name": "Luísa Sonza",              "cover_url": "https://s2-g1.glbimg.com/PdfwBwbI2SO9O3f8ZyKjZKFPUp8=/0x0:2048x2048/1008x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_59edd422c0c84a879bd37670ae4f538a/internal_photos/bs/2023/q/q/A40hpHRceiB3Ewik8t2w/luisasonzaescandalointimocapa.jpg"},
    {"title": "Chico",                   "genre": "MPB Pop",       "artist_name": "Luísa Sonza",              "cover_url": "https://s2-g1.glbimg.com/PdfwBwbI2SO9O3f8ZyKjZKFPUp8=/0x0:2048x2048/1008x0/smart/filters:strip_icc()/i.s3.glbimg.com/v1/AUTH_59edd422c0c84a879bd37670ae4f538a/internal_photos/bs/2023/q/q/A40hpHRceiB3Ewik8t2w/luisasonzaescandalointimocapa.jpg"},
    {"title": "Cachorrinhas",            "genre": "Pop",           "artist_name": "Luísa Sonza",              "cover_url": "https://upload.wikimedia.org/wikipedia/pt/0/08/Capa_de_Cachorrinhas_%28Single%29_por_Lu%C3%ADsa_Sonza.jpeg"},
    {"title": "A Queda",                 "genre": "Pop",           "artist_name": "Gloria Groove",            "cover_url": "https://upload.wikimedia.org/wikipedia/pt/d/d8/A_Queda_-_Gloria_Groove.png"},
    {"title": "Bonekinha",               "genre": "Pop",           "artist_name": "Gloria Groove",            "cover_url": "https://upload.wikimedia.org/wikipedia/pt/2/26/Bonekinha_-_Gloria_Groove.png"},

    {"title": "Vermelho",                "genre": "Funk Melody",   "artist_name": "Gloria Groove",            "cover_url": "https://i1.sndcdn.com/artworks-nVymX5g1gmqDspcF-0LzxWg-t500x500.jpg"},
    {"title": "Malvadão 3",              "genre": "Trap",          "artist_name": "Xamã",                     "cover_url": "https://i1.sndcdn.com/artworks-JF6pznmLkcZv6BUj-13K27A-t500x500.jpg"},
    {"title": "Sereia",                  "genre": "R&B",           "artist_name": "L7NNON & Biel do Furduncinho","cover_url": "https://i.scdn.co/image/ab67616d0000b27350dd8571c2fd2af11e35d8fe"},
    {"title": "Desenrola, Bate e Joga",  "genre": "Funk",          "artist_name": "L7NNON & Os Hawaianos",    "cover_url": "https://cdn-images.dzcdn.net/images/cover/e8549155e888b77086f9642a357d0ef7/0x1900-000000-80-0-0.jpg"},
    {"title": "Ai Preto",                "genre": "Funk",     "artist_name": "L7NNON, Bianca, Biel",     "cover_url": "https://cdn-images.dzcdn.net/images/cover/daa38f2cb1e80191011b98c517b9b1eb/500x500.jpg"},

    {"title": "Favela Vive 5",           "genre": "Rap",           "artist_name": "ADL, Major RD, MC Hariel", "cover_url": "https://i1.sndcdn.com/artworks-9XO1GZ9c4hSkKVH7-1w1hew-t500x500.jpg"},
    {"title": "Vivendo no Auge",         "genre": "Trap",          "artist_name": "Filipe Ret",               "cover_url": "https://i1.sndcdn.com/artworks-6DpYtWUndBiRFSNY-9db7Jw-t1080x1080.jpg"},
    {"title": "Amor",                    "genre": "Funk",          "artist_name": "MC Pedrinho",              "cover_url": "https://images.suamusica.com.br/ymcg6mXavT48MwCRsE9o2sSkc7U=/500x500/filters:format(webp)/29523760/2180412/cd_cover.png"},
    {"title": "Nosso Quadro",            "genre": "Sertanejo",     "artist_name": "Ana Castela",              "cover_url": "https://i1.sndcdn.com/artworks-FeouDUnfzuwC3xjL-dqcrCA-t1080x1080.jpg"},
    {"title": "Pipoco",                  "genre": "Sertanejo Pop", "artist_name": "Ana Castela & Melody",     "cover_url": "https://upload.wikimedia.org/wikipedia/pt/0/0d/Ana_Castela%2C_Melody_e_DJ_Chris_no_Beat_-_Pipoco.png"},

    {"title": "Seu Brilho Sumiu",        "genre": "Sertanejo",     "artist_name": "Israel & Rodolffo",        "cover_url": "https://i.scdn.co/image/ab67616d0000b27399de1add582e2730cd763249"},
    {"title": "Erro Gostoso",            "genre": "Sertanejo",     "artist_name": "Simone Mendes",            "cover_url": "https://image-cdn-ak.spotifycdn.com/image/ab67706c0000da84808d9c9be0f0d976019859ac"},
    {"title": "Leão",                    "genre": "R&B",           "artist_name": "Marília Mendonça & Xamã",  "cover_url": "https://i.scdn.co/image/ab67616d0000b2731ad875ebbdd67f6bb50514b5"},
    {"title": "Faixa Amarel",            "genre": "Trap",          "artist_name": "2ZDinizz",                 "cover_url": "https://cdn-images.dzcdn.net/images/cover/c77e5c5fd4586f3ef42b6492fbf7de76/0x1900-000000-80-0-0.jpg"},
    {"title": "Deixa Acontecer",         "genre": "Pagode",        "artist_name": "Grupo Revelação",          "cover_url": "https://i1.sndcdn.com/artworks-IzeeG5dgohv1mIyC-RJyRQw-t500x500.jpg"},

        # ---------------- INTERNACIONAL ----------------
    {"title": "As It Was",               "genre": "Pop",           "artist_name": "Harry Styles",             "cover_url": "https://rollingstone.com.br/wp-content/uploads/harry_house_amazon.jpg"},
    {"title": "Flowers",                 "genre": "Pop",           "artist_name": "Miley Cyrus",              "cover_url": "https://m.media-amazon.com/images/M/MV5BYzU3ZTFkZDctYmNlNi00ZjMxLTgwNGItYTI1YjdmOWJiNTQzXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg"},
    {"title": "Anti-Hero",               "genre": "Pop",           "artist_name": "Taylor Swift",             "cover_url": "https://akamai.sscdn.co/tb/letras-blog/wp-content/uploads/2022/10/d057787-Midnights.jpg"},
    {"title": "Cruel Summer",            "genre": "Pop",           "artist_name": "Taylor Swift",             "cover_url": "https://upload.wikimedia.org/wikipedia/pt/1/19/Capa_de_Lover_por_Taylor_Swift_%282019%29.png"},
    {"title": "Unholy",                  "genre": "Pop",           "artist_name": "Sam Smith & Kim Petras",   "cover_url": "https://upload.wikimedia.org/wikipedia/pt/d/da/Sam_Smith_e_Kim_Petras_-_Unholy.png"},

    {"title": "Kill Bill",               "genre": "R&B",           "artist_name": "SZA",                      "cover_url": "https://www.97fm.com.br/noticias/imagens/9628/1671031279.jpg"},
    {"title": "Good Days",               "genre": "R&B",           "artist_name": "SZA",                      "cover_url": "https://upload.wikimedia.org/wikipedia/pt/4/42/SZA_Good_Days.png"},
    {"title": "Save Your Tears",         "genre": "Pop",           "artist_name": "The Weeknd",               "cover_url": "https://cdn-images.dzcdn.net/images/cover/f520bf0be2e3cfc476824e75d20a164a/1900x1900-000000-80-0-0.jpg"},
    {"title": "Die for You",             "genre": "R&B",           "artist_name": "The Weeknd",               "cover_url": "https://upload.wikimedia.org/wikipedia/pt/3/39/The_Weeknd_-_Starboy.png"},
    {"title": "Eyes Closed",             "genre": "Pop",           "artist_name": "Imagine Dragons",          "cover_url": "https://upload.wikimedia.org/wikipedia/pt/3/3f/Night_Visions_Album_Cover.jpeg"},

    {"title": "Open Arms",               "genre": "Trap/R&B",      "artist_name": "SZA ft. Travis Scott",     "cover_url": "https://cdn-images.dzcdn.net/images/cover/59bc09c9de157574278546857c0bd33d/500x500.jpg"},
    {"title": "INDUSTRY BABY",           "genre": "Rap",           "artist_name": "Lil Nas X & Jack Harlow",  "cover_url": "https://upload.wikimedia.org/wikipedia/pt/b/b9/Industry_Baby_-_Lil_Nas_X_%26_Jack_Harlow.png"},
    {"title": "Montero (Call Me By Your Name)", "genre": "Pop",   "artist_name": "Lil Nas X",                "cover_url": "https://upload.wikimedia.org/wikipedia/pt/thumb/9/9f/Montero_-_Lil_Nas_X.png/250px-Montero_-_Lil_Nas_X.png"},
    {"title": "First Class",             "genre": "Rap",           "artist_name": "Jack Harlow",              "cover_url": "https://upload.wikimedia.org/wikipedia/pt/thumb/9/9f/Montero_-_Lil_Nas_X.png/250px-Montero_-_Lil_Nas_X.png"},
    {"title": "Super Freaky Girl",       "genre": "Rap",           "artist_name": "Nicki Minaj",              "cover_url": "https://upload.wikimedia.org/wikipedia/pt/thumb/e/e4/Nicki_Minaj_-_Super_Freaky_Girl_%28Roman_Remix%29.png/250px-Nicki_Minaj_-_Super_Freaky_Girl_%28Roman_Remix%29.png"},

    {"title": "Golden Hour",             "genre": "Pop",           "artist_name": "JVKE",                     "cover_url": "https://cdn-images.dzcdn.net/images/cover/e697f14e5e05fcc159ce7df2d175245f/0x1900-000000-80-0-0.jpg"},
    {"title": "Calm Down",               "genre": "Afropop",       "artist_name": "Rema",                     "cover_url": "https://lastfm.freetls.fastly.net/i/u/500x500/553ecf9c0b810188e9cd9b4dc5ce00ce.jpg"},
    {"title": "Peaches & Eggplants",     "genre": "Rap",           "artist_name": "Young Nudy",               "cover_url": "https://upload.wikimedia.org/wikipedia/en/c/c5/Young_Nudy_Peaches_and_Eggplants_Remix.png"},
    {"title": "vampire",                 "genre": "Pop",           "artist_name": "Olivia Rodrigo",           "cover_url": "https://musicainstantanea.com.br/wp-content/uploads/2023/06/Olivia-Rodrigo-Guts.jpg"},
    {"title": "Paint the Town Red",      "genre": "Rap",           "artist_name": "Doja Cat",                 "cover_url": "https://lastfm.freetls.fastly.net/i/u/ar0/62ec57b826d21856fa65ec1d09cedd08.jpg"},

    {"title": "One Right Now",           "genre": "Pop",           "artist_name": "Post Malone & The Weeknd", "cover_url": "https://i.discogs.com/Gdr853Hn2bA_6DyStxny3xdxTYkoxcXfJK1zErqA7Rw/rs:fit/g:sm/q:40/h:300/w:300/czM6Ly9kaXNjb2dz/LWRhdGFiYXNlLWlt/YWdlcy9SLTIxMzYx/MDM2LTE2Mzk1OTU0/ODktNzg4MC5qcGVn.jpeg"},
    {"title": "I'm Good (Blue)",         "genre": "Eletrônica",    "artist_name": "David Guetta & Bebe Rexha","cover_url": "https://upload.wikimedia.org/wikipedia/pt/4/46/David_Guetta_-_I%27m_Good_%28Blue%29.jpg"},
    {"title": "Shivers",                 "genre": "Pop",           "artist_name": "Ed Sheeran",               "cover_url": "https://upload.wikimedia.org/wikipedia/pt/8/8b/Shivers_-_Ed_Sheeran.png"},
    {"title": "Break My Soul",           "genre": "Pop/Dance",     "artist_name": "Beyoncé",                  "cover_url": "https://upload.wikimedia.org/wikipedia/pt/9/92/Break_My_Soul_-_Beyonc%C3%A9.png"},
    {"title": "Greedy",                  "genre": "Pop",           "artist_name": "Tate McRae",               "cover_url": "https://upload.wikimedia.org/wikipedia/pt/9/9b/Greedy_-_Tate_McRae.webp"},
]

def get_or_create_seed_artist():
    """Garante um usuário 'técnico' para as músicas padrão."""
    # Usamos um e-mail/nickname fixos para identificar esse usuário
    artist = User.query.filter_by(email="harmonic.seed@system.local").first()
    if not artist:
        artist = User(
            first_name="Harmonic",
            last_name="Seeds",
            cpf="00000000000",  # 14 caracteres, só pra satisfazer o campo
            email="harmonic.seed@system.local",
            nickname="harmonic_seeds",
            role="artist",
        )
        # Senha qualquer (não será usada na prática)
        artist.set_password("seed1234")
        db.session.add(artist)
        db.session.commit()
    return artist

def seed_default_musics():
    """
    Garante que as músicas padrão existam no banco.
    Se alguma já existir (mesmo título para esse artista técnico), não duplica.
    """
    artist = get_or_create_seed_artist()

    for track in SEED_TRACKS:
        title       = track["title"]
        genre       = track.get("genre")
        cover_url   = track.get("cover_url")
        artist_name = track.get("artist_name")

        # Verifica se essa música já existe para esse artista técnico
        existing = Music.query.filter_by(
            title=title,
            artist_name=artist_name
        ).first()

        if existing:
            continue

        m = Music(
            title       = title,
            genre       = genre,
            cover_url   = track.get("cover_url") or None,
            artist_name = track.get("artist_name") or None,
            artist_id   = artist.id
        )
        db.session.add(m)

    db.session.commit()

def get_or_create_admin_user():
    """Cria o usuário admin padrão se ele não existir."""
    admin = User.query.filter_by(email="admin@harmonic.com").first()
    if not admin:
        admin = User(
            first_name="Administrador",
            last_name="Harmonic",
            cpf="00000000000001",  # só pra satisfazer o campo
            email="admin@harmonic.com",
            nickname="admin",
            role="admin"
        )
        admin.set_password("admin123")   # você pode trocar depois
        db.session.add(admin)
        db.session.commit()
    return admin


# -----------------------------
# Contexto global para templates
# -----------------------------
@app.context_processor
def inject_user():
    return {
        "user_name": session.get("user_name", "Convidado"),
        "user_role": session.get("user_role", "listener")
    }


# -----------------------------
# Rotas de páginas
# -----------------------------
@app.route("/")
def splash():
    # mostra a animação/logo
    return render_template("logo.html")


@app.route("/logo")
def logo():
    return render_template("logo.html")


@app.route("/inicio")
def inicio():
    return render_template("inicio.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email_or_user = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.email == email_or_user) | (User.nickname == email_or_user)
        ).first()

        if not user or not user.check_password(password):
            flash("Credenciais inválidas.", "error")
            return redirect(url_for("login"))

        session.permanent = True
        session["user_id"] = user.id
        session["user_name"] = user.nickname
        session["user_role"] = user.role
        flash("Login efetuado com sucesso!", "success")
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta.", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("firstName", "").strip()
        last_name  = request.form.get("lastName", "").strip()
        cpf        = request.form.get("cpf", "").strip()
        email      = request.form.get("email", "").strip().lower()
        user_type  = request.form.get("userType", "listener").strip()
        nickname   = request.form.get("nickname", "").strip()
        password   = request.form.get("password", "")
        password2  = request.form.get("confirmPassword", "")

        if not all([first_name, last_name, cpf, email, nickname, password, password2]):
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("register"))

        if password != password2:
            flash("As senhas não conferem.", "error")
            return redirect(url_for("register"))

        if user_type not in ("listener", "artist", "admin"):
            user_type = "listener"

        if User.query.filter_by(email=email).first():
            flash("E-mail já cadastrado.", "error")
            return redirect(url_for("register"))
        if User.query.filter_by(cpf=cpf).first():
            flash("CPF já cadastrado.", "error")
            return redirect(url_for("register"))
        if User.query.filter_by(nickname=nickname).first():
            flash("Nickname já em uso.", "error")
            return redirect(url_for("register"))

        u = User(
            first_name=first_name,
            last_name=last_name,
            cpf=cpf,
            email=email,
            nickname=nickname,
            role=user_type
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

        flash("Cadastro realizado! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# -----------------------------
# Recuperar senha
# -----------------------------
@app.route("/recover", methods=["GET", "POST"])
def recover():
    if request.method == "POST":
        email      = request.form.get("email", "").strip().lower()
        password   = request.form.get("password", "")
        password2  = request.form.get("confirm_password", "")

        if not all([email, password, password2]):
            flash("Preencha todos os campos.", "error")
            return redirect(url_for("recover"))

        if password != password2:
            flash("As senhas não conferem.", "error")
            return redirect(url_for("recover"))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("E-mail não encontrado.", "error")
            return redirect(url_for("recover"))

        user.set_password(password)
        db.session.commit()

        flash("Senha atualizada com sucesso! Faça login.", "success")
        return redirect(url_for("login"))

    return render_template("recover.html")


# -----------------------------
# CRUD de músicas (artista/admin)
# -----------------------------
@app.route("/crud_msc", methods=["GET", "POST"])
def crud_msc():
    user_id = session.get("user_id")
    user_role = session.get("user_role")

    if not user_id:
        flash("Faça login para acessar essa página.", "error")
        return redirect(url_for("login"))

    if user_role not in ("artist", "admin"):
        flash("Acesso restrito a artistas e administradores.", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        title       = request.form.get("title", "").strip()
        artist_name = request.form.get("artist_name", "").strip()
        genre       = request.form.get("genre", "").strip()
        cover_url   = request.form.get("cover_url", "").strip()

        if not title:
            flash("O nome da música é obrigatório.", "error")
            return redirect(url_for("crud_msc"))

        # se não informar nome de artista, usa o nickname
        if not artist_name:
            u = User.query.get(user_id)
            artist_name = u.nickname if u else ""

        music = Music(
            title=title,
            artist_id=user_id,
            artist_name=artist_name or None,
            genre=genre or None,
            cover_url=cover_url or None
        )
        db.session.add(music)
        db.session.commit()

        flash("Música cadastrada com sucesso!", "success")
        return redirect(url_for("home"))

    return render_template("crud_msc.html")

# -----------------------------
# Perfil do usuário (editar dados)
# -----------------------------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("Faça login para acessar o perfil.", "error")
        return redirect(url_for("login"))

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name  = request.form.get("last_name", "").strip()
        email      = request.form.get("email", "").strip().lower()
        nickname   = request.form.get("nickname", "").strip()
        password   = request.form.get("password", "")

        if not all([first_name, last_name, email, nickname]):
            flash("Preencha todos os campos obrigatórios.", "error")
            return redirect(url_for("profile"))

        # Verificar se e-mail já está em uso por outro usuário
        existing_email = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()
        if existing_email:
            flash("Este e-mail já está em uso por outro usuário.", "error")
            return redirect(url_for("profile"))

        # Verificar se nickname já está em uso por outro usuário
        existing_nick = User.query.filter(
            User.nickname == nickname,
            User.id != user.id
        ).first()
        if existing_nick:
            flash("Este nickname já está em uso.", "error")
            return redirect(url_for("profile"))

        # Atualiza dados
        user.first_name = first_name
        user.last_name  = last_name
        user.email      = email
        user.nickname   = nickname

        # Atualiza senha só se o campo vier preenchido
        if password:
            user.set_password(password)

        db.session.commit()

        # Atualiza o nome mostrado na home/menu
        session["user_name"] = user.nickname

        flash("Perfil atualizado com sucesso!", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)

# -----------------------------
# HOME: descobre, suas músicas e favoritos
# -----------------------------
@app.route("/home")
def home():
    user_id  = session.get("user_id")
    user_role = session.get("user_role", "listener")

    # 10 músicas "aleatórias" — NEWID() no SQL Server
    discover_tracks = (
        Music.query
        .order_by(func.newid())
        .limit(10)
        .all()
    )

    artist_tracks = []
    favorite_tracks = []
    favorite_ids = set()

    if user_id:
        # músicas desse artista
        if user_role in ("artist", "admin"):
            artist_tracks = Music.query.filter_by(artist_id=user_id).all()

        # músicas favoritas do usuário logado
        favorite_tracks = (
            Music.query
            .join(Favorite, Favorite.music_id == Music.id)
            .filter(Favorite.user_id == user_id)
            .all()
        )
        favorite_ids = {m.id for m in favorite_tracks}

    admin_users = None
    admin_uploads = None
    admin_stats = None

    if session.get("user_role") == "admin":
        admin_users = User.query.all()
        admin_uploads = Music.query.all()
        admin_stats = {
            "total_users": User.query.count(),
            "total_musics": Music.query.count(),
            "total_favorites": Favorite.query.count(),
        }

    return render_template(
        "home.html",
        discover_tracks=discover_tracks,
        artist_tracks=artist_tracks,
        favorite_tracks=favorite_tracks,
        favorite_ids=favorite_ids,

        # dados do admin
        admin_users=admin_users,
        admin_uploads=admin_uploads,
        admin_stats=admin_stats
    )

@app.route("/admin/update_user", methods=["POST"])
def admin_update_user():
    if session.get("user_role") != "admin":
        return redirect(url_for("home"))

    user_id = request.form.get("id")
    user = User.query.get_or_404(user_id)

    # impedir alterar seed
    if user.email == "seed@harmonic.com":
        flash("O usuário seed não pode ser alterado.", "error")
        return redirect(url_for("home"))

    user.first_name = request.form.get("first_name")
    user.last_name = request.form.get("last_name")
    user.nickname = request.form.get("nickname")
    user.role = request.form.get("role")

    db.session.commit()

    flash("Usuário atualizado!", "success")
    return redirect(url_for("home"))


@app.route("/admin/delete_user", methods=["POST"])
def admin_delete_user():
    if session.get("user_role") != "admin":
        return redirect(url_for("home"))

    user_id = request.form.get("id")
    user = User.query.get_or_404(user_id)

    # proteções
    if user.email == "seed@harmonic.com":
        flash("O usuário seed não pode ser removido!", "error")
        return redirect(url_for("home"))

    if user.id == session.get("user_id"):
        flash("Você não pode excluir a própria conta!", "error")
        return redirect(url_for("home"))

    Favorite.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()

    flash("Usuário removido com sucesso!", "success")
    return redirect(url_for("home"))


# -----------------------------
# Favoritar / desfavoritar
# -----------------------------
@app.route("/favorite/<int:music_id>", methods=["POST"])
def toggle_favorite(music_id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Você precisa estar logado para favoritar músicas.", "error")
        return redirect(url_for("login"))

    music = Music.query.get_or_404(music_id)

    fav = Favorite.query.filter_by(user_id=user_id, music_id=music.id).first()
    if fav:
        db.session.delete(fav)
        flash("Música removida dos favoritos.", "info")
    else:
        fav = Favorite(user_id=user_id, music_id=music.id)
        db.session.add(fav)
        flash("Música adicionada aos favoritos.", "success")

    db.session.commit()
    return redirect(url_for("home"))


# -----------------------------
# Inicialização do banco
# -----------------------------
@app.cli.command("init-db")
def init_db():
    """Cria as tabelas no banco SQL Server."""
    db.create_all()
    print("Banco criado com sucesso!")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        get_or_create_admin_user()
        seed_default_musics()
    app.run(debug=True)
