# menu.py
import flet as ft
import sqlite3
import hashlib
import threading
import datetime
import re
import unicodedata
import random

# Consumo médio por dispositivo

CONSUMO_PADRAO = {
    "ar condicionado": 1.2,   # kWh por hora
    "lâmpada": 0.06,          # kWh por hora
    "câmera": 0.02,           # kWh por hora
    "outros": 0.1
}

# Tela de Outros dispositivos

def tela_outros(page: ft.Page):
    init_dispositivos_session(page)
    page.clean()
    page.title = "Outros Dispositivos"
    dispositivos = page.session.get("dispositivos") or {}
    outros = dispositivos.get("outros", {})
    lista = []

    for chave, estado in outros.items():
        def toggle(e, nome=chave):
            dispositivos = page.session.get("dispositivos")
            dispositivos["outros"][nome] = e.control.value
            page.session.set("dispositivos", dispositivos)
            registrar_uso(page, "outros", nome, e.control.value)
            page.snack_msg(f"{nome.capitalize()}: {'Ligado' if e.control.value else 'Desligado'}")

        lista.append(
            ft.Row(
                [
                    ft.Text(chave.capitalize(), size=18, color="white", expand=True),
                    ft.Switch(value=estado, on_change=toggle),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )

    if not lista:
        lista = [ft.Text("Nenhum dispositivo adicionado ainda.", color="white")]

    page.add(
        ft.Column(
            [
                ft.Text("Controle de Outros Dispositivos", size=22, weight="bold", color="white"),
                ft.Divider(color="white"),
                *lista,
                ft.TextButton("⬅ Voltar", on_click=lambda e: carregar_dashboard(page), style=ft.ButtonStyle(color="white")),
            ],
            spacing=12,
            expand=True
        )
    )

# Adicionar dispositivo

def adicionar_dispositivo_dialog(page: ft.Page):
    tipos = ["alexa", "aquecedor", "smart tv", "fechadura inteligente", "interruptor inteligente"]
    comodos = ["sala de estar", "quarto do amom", "quarto do victor", "quarto do fernando"]

    tipo_dd = ft.Dropdown(label="Tipo de dispositivo", options=[ft.dropdown.Option(t) for t in tipos])
    comodo_dd = ft.Dropdown(label="Cômodo", options=[ft.dropdown.Option(c) for c in comodos])

    def confirmar(ev):
        tipo = tipo_dd.value
        comodo = comodo_dd.value
        if not tipo or not comodo:
            page.snack_msg("Selecione tipo e cômodo antes de adicionar!")
            return
        chave = f"{tipo} ({comodo})"
        dispositivos = page.session.get("dispositivos") or {}
        outros = dispositivos.get("outros", {})
        outros[chave] = False
        dispositivos["outros"] = outros
        page.session.set("dispositivos", dispositivos)
        page.snack_msg(f"Dispositivo '{chave}' adicionado em Outros.")
        dlg.open = False
        page.update()

    def cancelar(ev):
        dlg.open = False
        page.update()

    dlg = ft.AlertDialog(
        title=ft.Text("Adicionar Dispositivo"),
        content=ft.Column([tipo_dd, comodo_dd], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar),
            ft.TextButton("Adicionar", on_click=confirmar),
        ],
        modal=True,
    )
    page.dialog = dlg
    dlg.open = True
    page.update()

# Dashboard principal

def carregar_dashboard(page: ft.Page):
    init_dispositivos_session(page)
    page.clean()
    page.title = "SmartLight Solar - Dashboard"

    header = ft.Row(
        [
            ft.Text("🌞 SmartLight Solar", size=22, weight="bold", color="white"),
            ft.Row(
                [
                    ft.ElevatedButton("Relatório", on_click=lambda e: tela_relatorio(page)),
                    ft.ElevatedButton("Adicionar Dispositivo", on_click=lambda e: adicionar_dispositivo_dialog(page)),
                    ft.ElevatedButton("Sair", bgcolor="red", color="white", on_click=lambda e: page.go("/")),
                ],
                spacing=8,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    estilo = ft.ButtonStyle(
        padding=50,
        text_style=ft.TextStyle(size=20),
        bgcolor="#1E2A3A",
        color="white",
    )

    dispositivos_grid = ft.Column(
        [
            ft.Row(
                [
                    ft.ElevatedButton("Ar Condicionado", expand=True, style=estilo, on_click=lambda e: tela_ar_condicionado(page)),
                    ft.ElevatedButton("Lâmpada", expand=True, style=estilo, on_click=lambda e: tela_lampada(page)),
                ],
                expand=True,
                spacing=20,
            ),
            ft.Row(
                [
                    ft.ElevatedButton("Câmera", expand=True, style=estilo, on_click=lambda e: tela_camera(page)),
                    ft.ElevatedButton("Outros", expand=True, style=estilo, on_click=lambda e: tela_outros(page)),
                ],
                expand=True,
                spacing=20,
            ),
        ],
        spacing=20,
        expand=True,
    )

    botoes_inferiores = ft.Row(
        [
            ft.TextButton("Suporte", on_click=lambda e: tela_suporte(page), style=ft.ButtonStyle(color="white")),
            ft.TextButton("Assistente Virtual", on_click=lambda e: tela_assistente(page), style=ft.ButtonStyle(color="white")),
            ft.TextButton("Conta", on_click=lambda e: tela_conta(page), style=ft.ButtonStyle(color="white")),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        spacing=20,
    )

    def snack_msg(msg):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor="blue", open=True)
        page.update()

    page.snack_msg = snack_msg

    page.add(
        ft.Column(
            [
                header,
                ft.Divider(color="white"),
                ft.Text("Dispositivos", size=20, weight="bold", color="white"),
                dispositivos_grid,
                ft.Divider(color="white"),
                botoes_inferiores,
            ],
            spacing=18,
            expand=True,
        )
    )

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r'[^a-z0-9\s]', '', s)
    return s

def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

# sqlite: buscar e atualizar usuário

DB = "usuarios.db"

def buscar_usuario(email):
    with sqlite3.connect(DB, timeout=5, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, email FROM usuarios WHERE email = ?", (email,))
        return cursor.fetchone()

def atualizar_usuario(email, novo_nome=None, nova_senha_hashed=None):
    with sqlite3.connect(DB, timeout=5, check_same_thread=False) as conn:
        cursor = conn.cursor()
        if novo_nome and nova_senha_hashed:
            cursor.execute("UPDATE usuarios SET nome=?, senha=? WHERE email=?", (novo_nome, nova_senha_hashed, email))
        elif novo_nome:
            cursor.execute("UPDATE usuarios SET nome=? WHERE email=?", (novo_nome, email))
        elif nova_senha_hashed:
            cursor.execute("UPDATE usuarios SET senha=? WHERE email=?", (nova_senha_hashed, email))
        conn.commit()

# Inicio de sessão

def init_dispositivos_session(page: ft.Page):
    if page.session.get("dispositivos") is None:
        page.session.set("dispositivos", {
            "ar condicionado": {
                "sala de estar": False,
                "quarto do amom": False,
                "quarto do victor": False,
                "quarto do fernando": False
            },
            "lâmpada": {
                "sala de estar": False,
                "quarto do amom": False,
                "quarto do victor": False,
                "quarto do fernando": False
            },
            "câmera": {
                "quintal": False,
                "garagem": False,
                "lavanderia": False,
                "sala de estar": False
            },
            "outros": {}
        })
    if page.session.get("schedules") is None:
        page.session.set("schedules", [])
    if page.session.get("uso") is None:
        page.session.set("uso", {})

# Agendamento

def schedule_action(page: ft.Page, dispositivo: str, comodo: str, acao: bool, target_dt: datetime.datetime):
    now = datetime.datetime.now()
    delay = (target_dt - now).total_seconds()
    if delay < 0:
        # agenda para o próximo dia se o horário ja passou
        delay += 24 * 3600

    def task():
        dispositivos = page.session.get("dispositivos")
        if not dispositivos:
            return
        # aplica ação
        dispositivos[dispositivo][comodo] = acao
        page.session.set("dispositivos", dispositivos)
        # registra uso (se for ligar ou desligar)
        registrar_uso(page, dispositivo, comodo, acao)
        # notifica (se der kkk)
        try:
            page.snack_msg(f"Agendamento executado: {dispositivo.capitalize()} do {comodo.capitalize()} {'ligado' if acao else 'desligado'}.")
            page.update()
        except Exception:
            pass
        # remove schedule da lista
        schedules = page.session.get("schedules")
        if schedules is None:
            schedules = []
        for i, s in enumerate(schedules):
            if s.get("device") == dispositivo and s.get("comodo") == comodo and s.get("time") == target_dt.isoformat():
                schedules.pop(i)
                break
        page.session.set("schedules", schedules)

    t = threading.Timer(delay, task)
    t.daemon = True
    t.start()

    schedules = page.session.get("schedules")
    if schedules is None:
        schedules = []
    schedules.append({
        "device": dispositivo,
        "comodo": comodo,
        "action": acao,
        "time": target_dt.isoformat()
    })
    page.session.set("schedules", schedules)
    # Atualizar UI
    try:
        page.update()
    except Exception:
        pass


time_pattern = re.compile(
    r'(\d{1,2})[:h](\d{2})(?:\s*(am|pm|da manhã|da tarde|da noite|manhã|tarde|noite))?',
    flags=re.IGNORECASE
)

def parse_time_from_text(text: str):
    m = time_pattern.search(text)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2))
    suffix = (m.group(3) or "").lower()
    if any(x in suffix for x in ["pm", "tarde", "noite", "da tarde", "da noite"]) and hour < 12:
        hour += 12
    if any(x in suffix for x in ["am", "manhã", "da manhã"]) and hour == 12:
        hour = 0
    now = datetime.datetime.now()
    try:
        return datetime.datetime(now.year, now.month, now.day, hour, minute)
    except ValueError:
        return None

# Registro de uso (para relatório)

def registrar_uso(page: ft.Page, dispositivo: str, comodo: str, ligado: bool):
    uso = page.session.get("uso")
    if uso is None:
        uso = {}
    key = f"{dispositivo}::{comodo}"
    if ligado:
        # inicia contado de tempo
        uso.setdefault(key, {})
        uso[key]["inicio"] = datetime.datetime.now().isoformat()
        uso[key]["horas"] = uso[key].get("horas", 0)
    else:
        # finaliza e junta horas
        if key in uso and "inicio" in uso[key]:
            inicio = datetime.datetime.fromisoformat(uso[key]["inicio"])
            dur = (datetime.datetime.now() - inicio).total_seconds() / 3600
            uso[key]["horas"] = uso[key].get("horas", 0) + dur
            uso[key].pop("inicio", None)
    page.session.set("uso", uso)

# Telas de dispositivos

def tela_ar_condicionado(page: ft.Page):
    init_dispositivos_session(page)
    page.clean()
    page.title = "Ar Condicionado"
    dispositivos = page.session.get("dispositivos") or {}
    lista = []
    for c in dispositivos.get("ar condicionado", {}).keys():
        def toggle(e, nome=c):
            dispositivos = page.session.get("dispositivos")
            dispositivos["ar condicionado"][nome] = e.control.value
            page.session.set("dispositivos", dispositivos)
            registrar_uso(page, "ar condicionado", nome, e.control.value)
            page.snack_msg(f"{nome.capitalize()}: {'Ligado' if e.control.value else 'Desligado'}")
        lista.append(
            ft.Row(
                [
                    ft.Text(c.capitalize(), size=18, color="white", expand=True),
                    ft.Switch(value=dispositivos["ar condicionado"][c], on_change=toggle),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )
    page.add(
        ft.Column(
            [
                ft.Text("Controle de Ar Condicionado", size=22, weight="bold", color="white"),
                ft.Divider(color="white"),
                *lista,
                ft.TextButton("⬅ Voltar", on_click=lambda e: carregar_dashboard(page), style=ft.ButtonStyle(color="white"))
            ],
            spacing=12,
            expand=True
        )
    )

def tela_lampada(page: ft.Page):
    init_dispositivos_session(page)
    page.clean()
    page.title = "Lâmpadas"
    dispositivos = page.session.get("dispositivos") or {}
    lista = []
    for c in dispositivos.get("lâmpada", {}).keys():
        def toggle(e, nome=c):
            dispositivos = page.session.get("dispositivos")
            dispositivos["lâmpada"][nome] = e.control.value
            page.session.set("dispositivos", dispositivos)
            registrar_uso(page, "lâmpada", nome, e.control.value)
            page.snack_msg(f"{nome.capitalize()}: {'Ligada' if e.control.value else 'Desligada'}")
        lista.append(
            ft.Row(
                [
                    ft.Text(c.capitalize(), size=18, color="white", expand=True),
                    ft.Switch(value=dispositivos["lâmpada"][c], on_change=toggle),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )
    page.add(
        ft.Column(
            [
                ft.Text("Controle de Lâmpadas", size=22, weight="bold", color="white"),
                ft.Divider(color="white"),
                *lista,
                ft.TextButton("⬅ Voltar", on_click=lambda e: carregar_dashboard(page), style=ft.ButtonStyle(color="white"))
            ],
            spacing=12,
            expand=True
        )
    )

def tela_camera(page: ft.Page):
    init_dispositivos_session(page)
    page.clean()
    page.title = "Câmeras"
    dispositivos = page.session.get("dispositivos") or {}
    lista = []
    for l in dispositivos.get("câmera", {}).keys():
        def toggle(e, nome=l):
            dispositivos = page.session.get("dispositivos")
            dispositivos["câmera"][nome] = e.control.value
            page.session.set("dispositivos", dispositivos)
            registrar_uso(page, "câmera", nome, e.control.value)
            page.snack_msg(f"Câmera {nome.capitalize()}: {'Ativa' if e.control.value else 'Inativa'}")
        lista.append(
            ft.Row(
                [
                    ft.Text(l.capitalize(), size=18, color="white", expand=True),
                    ft.Switch(value=dispositivos["câmera"][l], on_change=toggle),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        )
    page.add(
        ft.Column(
            [
                ft.Text("Monitoramento de Câmeras", size=22, weight="bold", color="white"),
                ft.Divider(color="white"),
                *lista,
                ft.TextButton("⬅ Voltar", on_click=lambda e: carregar_dashboard(page), style=ft.ButtonStyle(color="white"))
            ],
            spacing=12,
            expand=True
        )
    )

# Relatório de energia

def tela_relatorio(page: ft.Page):
    init_dispositivos_session(page)
    page.clean()
    page.title = "Relatório de Energia"
    uso = page.session.get("uso") or {}
    lines = []
    total_kwh = 0.0
    for chave, dados in uso.items():
        try:
            disp, comodo = chave.split("::")
        except ValueError:
            continue
        horas = dados.get("horas", 0.0)
        if "inicio" in dados:
            inicio = datetime.datetime.fromisoformat(dados["inicio"])
            horas += (datetime.datetime.now() - inicio).total_seconds() / 3600
        consumo = horas * CONSUMO_PADRAO.get(disp, CONSUMO_PADRAO["outros"])
        total_kwh += consumo
        lines.append(ft.Text(f"{disp.capitalize()} - {comodo.capitalize()}: {consumo:.2f} kWh", color="white"))
    co2_ev = total_kwh * 0.084  # 84 g CO2 per kWh => 0.084 kg
    if not lines:
        lines = [ft.Text("Nenhum consumo registrado ainda.", color="white")]
    page.add(
        ft.Column(
            [
                ft.Text("Relatório de Consumo de Energia", size=22, weight="bold", color="white"),
                ft.Divider(color="white"),
                *lines,
                ft.Divider(color="white"),
                ft.Text(f"Total: {total_kwh:.2f} kWh", size=18, color="yellow"),
                ft.Text(f"Estimativa de CO₂ evitada: {co2_ev:.2f} kg", size=16, color="green"),
                ft.TextButton("⬅ Voltar", on_click=lambda e: carregar_dashboard(page), style=ft.ButtonStyle(color="white"))
            ],
            spacing=12
        )
    )

# Assistente Virtual chat e agendamento

def tela_assistente(page: ft.Page):
    init_dispositivos_session(page)
    page.clean()
    page.title = "Assistente Virtual"

    mensagens = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    entrada = ft.TextField(hint_text="Digite sua mensagem...", expand=True)

    respostas_ligar = [
        "Pronto, já liguei {disp} do {comodo} ✅",
        "O {disp} do {comodo} foi ativado 🚀",
        "Pode deixar! {disp} do {comodo} está ligado agora 😉"
    ]
    respostas_desligar = [
        "Certo, desliguei {disp} do {comodo} ❌",
        "{disp} do {comodo} foi desativado 🔌",
        "Tudo bem, {disp} do {comodo} está desligado 👍"
    ]
    respostas_agendado = [
        "Feito — agendei para {hora}: {acao} {disp} do {comodo}.",
        "Agendado: às {hora} eu vou {acao} o {disp} do {comodo}.",
        "Anotado! Às {hora} eu {acao}rei o {disp} do {comodo}."
    ]

    def processar_comando(texto):
        texto_lower = texto.lower()
        dispositivos = page.session.get("dispositivos") or {}

        # ação
        if any(p in texto_lower for p in ["ligue", "acenda", "ative", "ligar", "ativar", "acender"]):
            acao_bool = True
            acao_text = "ligar"
        elif any(p in texto_lower for p in ["desligue", "apague", "desative", "desligar", "desativar", "apagar"]):
            acao_bool = False
            acao_text = "desligar"
        else:
            return "Não entendi se devo ligar ou desligar 🤔"

        norm_text = normalize_text(texto_lower)

        # dispositivo
        dispositivo = None
        for d in dispositivos.keys():
            if normalize_text(d) in norm_text:
                dispositivo = d
                break
        if not dispositivo:
            return "Não entendi qual dispositivo você quer controlar 🤔"

        # comodo
        comodo = None
        for c in dispositivos[dispositivo].keys():
            if normalize_text(c) in norm_text:
                comodo = c
                break
        if not comodo:
            return f"Não encontrei o cômodo para o {dispositivo} 🔍"

        # horário?
        target = parse_time_from_text(texto_lower)
        if target:
            schedule_action(page, dispositivo, comodo, acao_bool, target)
            hora_str = target.strftime("%Y-%m-%d %H:%M")
            resposta = random.choice(respostas_agendado).format(hora=hora_str, acao=acao_text, disp=dispositivo.capitalize(), comodo=comodo.capitalize())
            return resposta

        # ação imediata
        dispositivos[dispositivo][comodo] = acao_bool
        page.session.set("dispositivos", dispositivos)
        registrar_uso(page, dispositivo, comodo, acao_bool)
        if acao_bool:
            return random.choice(respostas_ligar).format(disp=dispositivo.capitalize(), comodo=comodo.capitalize())
        else:
            return random.choice(respostas_desligar).format(disp=dispositivo.capitalize(), comodo=comodo.capitalize())

    def enviar_msg(e):
        if entrada.value.strip() == "":
            return
        user_msg = entrada.value.strip()
        mensagens.controls.append(ft.Text(f"Você: {user_msg}", color="white"))
        resp = processar_comando(user_msg)
        mensagens.controls.append(ft.Text(f"Assistente: {resp}", color="cyan"))
        entrada.value = ""
        page.update()

    # Listar agendamentos
    def listar_agendamentos_control():
        schedules = page.session.get("schedules")
        if schedules is None or len(schedules) == 0:
            return ft.Text("Sem agendamentos", color="white")
        textos = []
        for s in schedules:
            dt = s.get("time")
            textos.append(f"{s.get('device').capitalize()} - {s.get('comodo').capitalize()} @ {dt} -> {'ligar' if s.get('action') else 'desligar'}")
        return ft.Column([ft.Text("Agendamentos:", color="white")] + [ft.Text(t, color="white") for t in textos])

    enviar_btn = ft.ElevatedButton("Enviar", on_click=enviar_msg)

    page.add(
        ft.Column(
            [
                ft.Text("Chat com Assistente Virtual", size=22, weight="bold", color="white"),
                ft.Divider(color="white"),
                mensagens,
                ft.Row([entrada, enviar_btn]),
                ft.Divider(color="white"),
                listar_agendamentos_control(),
                ft.TextButton("⬅ Voltar", on_click=lambda e: carregar_dashboard(page), style=ft.ButtonStyle(color="white"))
            ],
            spacing=12,
            expand=True
        )
    )

# Conta

def tela_conta(page: ft.Page):
    page.clean()
    page.title = "Conta"
    usuario_email = page.session.get("usuario_email")
    if not usuario_email:
        page.add(ft.Text("Usuário não identificado. Faça login novamente.", color="white"))
        page.add(ft.TextButton("Voltar ao login", on_click=lambda e: page.go("/"), style=ft.ButtonStyle(color="white")))
        return
    usuario = buscar_usuario(usuario_email)
    nome_atual = usuario[0] if usuario else ""
    email_atual = usuario[1] if usuario else usuario_email

    nome = ft.TextField(label="Nome", value=nome_atual, width=300)
    email = ft.TextField(label="E-mail", value=email_atual, disabled=True, width=300)
    senha = ft.TextField(label="Nova Senha (deixe vazio para manter)", password=True, can_reveal_password=True, width=300)

    def salvar(e):
        novo_nome = nome.value.strip()
        nova_senha_val = senha.value.strip()
        nova_hash = hash_senha(nova_senha_val) if nova_senha_val else None
        atualizar_usuario(email_atual, novo_nome if novo_nome else None, nova_hash)
        page.snack_msg("Alterações salvas com sucesso!")
        page.update()

    page.add(
        ft.Column(
            [
                ft.Text("Configurações da Conta", size=22, weight="bold", color="white"),
                ft.Divider(color="white"),
                nome,
                email,
                senha,
                ft.ElevatedButton("Salvar Alterações", on_click=salvar),
                ft.ElevatedButton("Sair da Conta", bgcolor="red", color="white", on_click=lambda e: page.go("/")),
                ft.TextButton("⬅ Voltar", on_click=lambda e: carregar_dashboard(page), style=ft.ButtonStyle(color="white")),
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

# Suporte

def tela_suporte(page: ft.Page):
    page.clean()
    page.title = "Suporte"

    page.add(
        ft.Column(
            [
                ft.Text("Suporte", size=22, weight="bold", color="white"),
                ft.Text("Qualquer problema, entre em contato conosco pelo e-mail:", color="white"),
                ft.Text("📧 smartlightsolar@gmail.com", color="yellow"),
                ft.Divider(color="white"),
                ft.Text(
                    "Se preferir, descreva o problema aqui e pressione ENVIAR (em breve podemos adicionar um formulário).",
                    color="white",
                ),
                ft.Row(
                    [
                        ft.TextButton("⬅ Voltar", on_click=lambda e: carregar_dashboard(page), style=ft.ButtonStyle(color="white"))
                    ],
                    alignment=ft.MainAxisAlignment.START
                )
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
    )

# Dashboard principal

def carregar_dashboard(page: ft.Page):
    init_dispositivos_session(page)
    page.clean()
    page.title = "SmartLight Solar - Dashboard"

    def abrir_adicionar(e):
        nome_field = ft.TextField(label="Nome do dispositivo", width=300)

        def adicionar_ev(ev):
            nome_val = nome_field.value.strip()
            if nome_val:
                adicionar_dispositivo(page, nome_val)
            dlg.open = False
            page.update()

        def cancelar_ev(ev):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Adicionar Dispositivo"),
            content=nome_field,
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_ev),
                ft.TextButton("Adicionar", on_click=adicionar_ev)
            ],
            modal=True
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    header = ft.Row(
        [
            ft.Text("🌞 SmartLight Solar", size=22, weight="bold", color="white"),
            ft.Row(
                [
                    ft.ElevatedButton("Relatório", on_click=lambda e: tela_relatorio(page)),
                    ft.ElevatedButton("Adicionar Dispositivo", on_click=abrir_adicionar),
                    ft.ElevatedButton("Sair", bgcolor="red", color="white", on_click=lambda e: page.go("/")),
                ],
                spacing=8
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    estilo = ft.ButtonStyle(padding=50, text_style=ft.TextStyle(size=20), bgcolor="#1E2A3A", color="white")

    dispositivos_grid = ft.Column(
        [
            ft.Row(
                [
                    ft.ElevatedButton("Ar Condicionado", expand=True, style=estilo, on_click=lambda e: tela_ar_condicionado(page)),
                    ft.ElevatedButton("Lâmpada", expand=True, style=estilo, on_click=lambda e: tela_lampada(page)),
                ],
                expand=True,
                spacing=20
            ),
            ft.Row(
                [
                    ft.ElevatedButton("Câmera", expand=True, style=estilo, on_click=lambda e: tela_camera(page)),
                    ft.ElevatedButton("Outros", expand=True, style=estilo, on_click=lambda e: page.snack_msg("Outros dispositivos")),
                ],
                expand=True,
                spacing=20
            )
        ],
        spacing=20,
        expand=True
    )

    botoes_inferiores = ft.Row(
        [
            ft.TextButton("Suporte", on_click=lambda e: tela_suporte(page), style=ft.ButtonStyle(color="white")),
            ft.TextButton("Assistente Virtual", on_click=lambda e: tela_assistente(page), style=ft.ButtonStyle(color="white")),
            ft.TextButton("Conta", on_click=lambda e: tela_conta(page), style=ft.ButtonStyle(color="white")),
        ],
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        spacing=20
    )

    def snack_msg(msg):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor="blue", open=True)
        page.update()

    page.snack_msg = snack_msg

    page.add(
        ft.Column(
            [
                header,
                ft.Divider(color="white"),
                ft.Text("Dispositivos", size=20, weight="bold", color="white"),
                dispositivos_grid,
                ft.Divider(color="white"),
                botoes_inferiores
            ],
            spacing=18,
            expand=True
        )
    )

def adicionar_dispositivo(page: ft.Page, nome: str):
    if not nome.strip():
        return
    dispositivos = page.session.get("dispositivos") or {}
    outros = dispositivos.get("outros", {})
    outros[nome.strip().lower()] = False
    dispositivos["outros"] = outros
    page.session.set("dispositivos", dispositivos)
    page.snack_msg(f"Dispositivo '{nome}' adicionado em Outros.")
    page.update()