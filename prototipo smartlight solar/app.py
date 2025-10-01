import flet as ft
import sqlite3
import hashlib
from menu import carregar_dashboard


# ==============================
# Funções auxiliares do Banco
# ==============================
def criar_banco():
    with sqlite3.connect("usuarios.db", timeout=5, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL
            )
        """)
        # garante que a coluna 'nome' existe
        try:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN nome TEXT")
        except sqlite3.OperationalError:
            pass  # já existe
        conn.commit()


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def cadastrar_usuario(email, senha, nome="Usuário"):
    try:
        with sqlite3.connect("usuarios.db", timeout=5, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (nome, email, hash_senha(senha))
            )
            conn.commit()
        return True, "Usuário cadastrado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "E-mail já cadastrado."
    except sqlite3.OperationalError as e:
        return False, f"Erro no banco: {e}"


def verificar_credenciais(email, senha):
    with sqlite3.connect("usuarios.db", timeout=5, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT senha FROM usuarios WHERE email = ?", (email,))
        row = cursor.fetchone()
    return row and row[0] == hash_senha(senha)


# ==============================
# Páginas do App
# ==============================
def tela_login(page: ft.Page):
    page.clean()
    page.title = "SmartLight Solar - Login"

    email = ft.TextField(label="E-mail", width=300, border_radius=10)
    senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, width=300, border_radius=10)

    def login(e):
        if verificar_credenciais(email.value, senha.value):
            # guarda e-mail do usuário logado
            page.session.set("usuario_email", email.value)
            carregar_dashboard(page)
        else:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Cadastro não encontrado ou senha incorreta.", color="white"),
                bgcolor="red",
                open=True,
            )
            page.update()

    entrar_btn = ft.ElevatedButton(
        text="Entrar",
        width=300,
        style=ft.ButtonStyle(bgcolor="#FFFFFF", color="#000000", shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=login
    )

    cadastro_btn = ft.TextButton(
        text="Cadastre Aqui",
        style=ft.ButtonStyle(color="#FFFFFF"),
        on_click=lambda e: tela_cadastro(page)
    )

    layout = ft.Column(
        controls=[
            ft.Image(src="imagens/Logo.png", width=150, height=150),
            email,
            senha,
            entrar_btn,
            cadastro_btn
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
    page.add(layout)


def tela_cadastro(page: ft.Page):
    page.clean()
    page.title = "SmartLight Solar - Cadastro"

    cad_nome = ft.TextField(label="Nome", width=300, border_radius=10)
    cad_email = ft.TextField(label="E-mail", width=300, border_radius=10)
    cad_senha = ft.TextField(label="Senha", password=True, width=300, border_radius=10)

    def salvar(e):
        ok, msg = cadastrar_usuario(cad_email.value, cad_senha.value, cad_nome.value if cad_nome.value else "Usuário")
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color="white"),
            bgcolor="green" if ok else "red",
            open=True,
        )
        page.update()
        if ok:
            tela_login(page)

    salvar_btn = ft.ElevatedButton(
        text="Cadastrar",
        width=300,
        style=ft.ButtonStyle(bgcolor="#FFFFFF", color="#000000", shape=ft.RoundedRectangleBorder(radius=10)),
        on_click=salvar
    )

    voltar_btn = ft.TextButton(
        text="Voltar ao Login",
        style=ft.ButtonStyle(color="#FFFFFF"),
        on_click=lambda e: tela_login(page)
    )

    layout = ft.Column(
        controls=[
            ft.Image(src="imagens/Logo.png", width=120, height=120),
            cad_nome,
            cad_email,
            cad_senha,
            salvar_btn,
            voltar_btn
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
    page.add(layout)


# ==============================
# Inicialização
# ==============================
def main(page: ft.Page):
    page.bgcolor = "#0F1B2D"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    criar_banco()
    tela_login(page)


ft.app(target=main)
