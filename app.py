from flask import Flask, render_template, request, jsonify, session
import sqlite3
import requests
import os
import hmac
from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# CONFIGURAÇÃO DO FLASK
# =========================================================

app = Flask(__name__)


# =========================================================
# CONFIGURAÇÕES DO SISTEMA
# =========================================================

DATABASE = "database.db"

HOLIDAYS_API = (
    "https://date.nager.at/api/v3/"
    "PublicHolidays/2026/BR"
)


# Chave utilizada para proteger a sessão do Flask.
# Em produção deve ser configurada por variável de ambiente.
app.secret_key = os.getenv(
    "SECRET_KEY",
    "chave-local-clinica-saude-2026"
)


# Senha padrão da área do funcionário.
# Para o teste local:
# clinica2026
#
# Em produção também deveria vir de variável de ambiente.
EMPLOYEE_PASSWORD = os.getenv(
    "EMPLOYEE_PASSWORD",
    "clinica2026"
)


# Configurações do cookie da sessão
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# =========================================================
# HORÁRIOS DA CLÍNICA
# =========================================================

ALLOWED_TIMES = [
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00"
]


# =========================================================
# BANCO DE DADOS
# =========================================================

def get_connection():
    """
    Cria e retorna uma conexão com o SQLite.
    """

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def create_database():
    """
    Cria a tabela de agendamentos caso ela ainda não exista.
    """

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            patient_name TEXT NOT NULL,

            phone TEXT NOT NULL,

            date TEXT NOT NULL,

            time TEXT NOT NULL,

            created_at TEXT NOT NULL,

            UNIQUE(date, time)
        )
    """)

    connection.commit()

    connection.close()


# =========================================================
# PÁGINA PRINCIPAL
# =========================================================

@app.route("/")
def index():
    """
    Renderiza a página principal do sistema.
    """

    return render_template("index.html")


# =========================================================
# LOGIN DO FUNCIONÁRIO
# =========================================================

@app.route("/employee/login", methods=["POST"])
def employee_login():
    """
    Recebe a senha enviada pelo frontend
    e cria uma sessão caso esteja correta.
    """

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Senha não informada."
        }), 400


    password = data.get("password", "")


    # compare_digest faz uma comparação mais apropriada
    # para informações sensíveis.
    password_is_correct = hmac.compare_digest(
        str(password),
        str(EMPLOYEE_PASSWORD)
    )


    if not password_is_correct:

        return jsonify({
            "error": "Senha incorreta."
        }), 401


    session["employee_authenticated"] = True


    return jsonify({
        "message": "Login realizado com sucesso."
    })


# =========================================================
# LOGOUT DO FUNCIONÁRIO
# =========================================================

@app.route("/employee/logout", methods=["POST"])
def employee_logout():
    """
    Remove a autenticação do funcionário.
    """

    session.pop(
        "employee_authenticated",
        None
    )


    return jsonify({
        "message": "Logout realizado com sucesso."
    })


# =========================================================
# STATUS DO FUNCIONÁRIO
# =========================================================

@app.route("/employee/status", methods=["GET"])
def employee_status():
    """
    Informa ao frontend se existe
    funcionário autenticado na sessão.
    """

    authenticated = session.get(
        "employee_authenticated",
        False
    )


    return jsonify({
        "authenticated": authenticated
    })


# =========================================================
# VERIFICAR AUTENTICAÇÃO
# =========================================================

def employee_is_authenticated():
    """
    Retorna True caso exista funcionário autenticado.
    """

    return session.get(
        "employee_authenticated",
        False
    )


# =========================================================
# API DE FERIADOS
# =========================================================

def get_holidays():
    """
    Consulta a API Nager.Date e retorna
    uma lista com as datas dos feriados brasileiros.

    Retorna None caso a API esteja indisponível.
    """

    try:

        response = requests.get(
            HOLIDAYS_API,
            timeout=10
        )

        response.raise_for_status()

        holidays = response.json()


        holiday_dates = [
            holiday["date"]
            for holiday in holidays
        ]


        return holiday_dates


    except (
        requests.RequestException,
        ValueError,
        KeyError
    ) as error:

        print(
            "Erro ao consultar API de feriados:",
            error
        )

        return None


# =========================================================
# VALIDAR DATA
# =========================================================

def is_valid_business_day(date_string):
    """
    Verifica se a data:

    - possui formato válido;
    - pertence ao ano de 2026;
    - não é sábado;
    - não é domingo;
    - não é feriado.
    """

    try:

        selected_date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).date()


    except (
        ValueError,
        TypeError
    ):

        return False, "Data inválida.", 400


    # Como a API obrigatória solicitada pela empresa
    # é especificamente do ano de 2026.
    if selected_date.year != 2026:

        return (
            False,
            "O sistema aceita agendamentos apenas para 2026.",
            400
        )


    # weekday:
    #
    # Segunda = 0
    # Terça   = 1
    # Quarta  = 2
    # Quinta  = 3
    # Sexta   = 4
    # Sábado  = 5
    # Domingo = 6

    if selected_date.weekday() >= 5:

        return (
            False,
            "Não realizamos agendamentos aos finais de semana.",
            400
        )


    holidays = get_holidays()


    # Se a API estiver fora do ar,
    # não liberamos o agendamento sem validar.
    if holidays is None:

        return (
            False,
            "Não foi possível consultar os feriados. "
            "Tente novamente em alguns instantes.",
            503
        )


    if date_string in holidays:

        return (
            False,
            "Não realizamos agendamentos em feriados.",
            400
        )


    return True, None, 200


# =========================================================
# HORÁRIOS DISPONÍVEIS
# =========================================================

@app.route("/available", methods=["GET"])
def available():
    """
    Exemplo:

    GET /available?date=2026-10-13

    Retorna os horários livres daquela data.
    """

    date = request.args.get("date")


    if not date:

        return jsonify({
            "error": "Informe uma data."
        }), 400


    valid_day, message, status_code = (
        is_valid_business_day(date)
    )


    if not valid_day:

        return jsonify({

            "date": date,

            "available": [],

            "message": message

        }), status_code


    connection = get_connection()


    # -----------------------------------------------------
    # Reagendamento
    # -----------------------------------------------------
    #
    # Se um funcionário estiver reagendando uma consulta,
    # poderá informar:
    #
    # /available?date=2026-10-14&exclude_id=1
    #
    # Assim o próprio horário atual do agendamento
    # não será considerado ocupado.
    # -----------------------------------------------------

    exclude_id = request.args.get(
        "exclude_id",
        type=int
    )


    if (
        exclude_id is not None
        and employee_is_authenticated()
    ):

        appointments = connection.execute(
            """
            SELECT time
            FROM appointments
            WHERE date = ?
            AND id != ?
            """,
            (
                date,
                exclude_id
            )
        ).fetchall()


    else:

        appointments = connection.execute(
            """
            SELECT time
            FROM appointments
            WHERE date = ?
            """,
            (date,)
        ).fetchall()


    connection.close()


    occupied_times = [
        appointment["time"]
        for appointment in appointments
    ]


    available_times = [
        appointment_time
        for appointment_time in ALLOWED_TIMES
        if appointment_time not in occupied_times
    ]


    return jsonify({

        "date": date,

        "timezone":
            "America/Sao_Paulo",

        "available":
            available_times

    })


# =========================================================
# CRIAR AGENDAMENTO
# =========================================================

@app.route("/appointments", methods=["POST"])
def create_appointment():
    """
    Cria um novo agendamento.

    Exemplo JSON:

    {
        "patient_name": "Nadia",
        "phone": "(19) 99999-9999",
        "date": "2026-10-13",
        "time": "08:00"
    }
    """

    data = request.get_json()


    if not data:

        return jsonify({
            "error":
                "Dados do agendamento não informados."
        }), 400


    patient_name = str(
        data.get(
            "patient_name",
            ""
        )
    ).strip()


    phone = str(
        data.get(
            "phone",
            ""
        )
    ).strip()


    date = data.get("date")

    appointment_time = data.get("time")


    # =====================================================
    # VALIDAR CAMPOS
    # =====================================================

    if (
        not patient_name
        or not phone
        or not date
        or not appointment_time
    ):

        return jsonify({
            "error": "Preencha todos os campos."
        }), 400


    # =====================================================
    # VALIDAR DATA
    # =====================================================

    valid_day, message, status_code = (
        is_valid_business_day(date)
    )


    if not valid_day:

        return jsonify({
            "error": message
        }), status_code


    # =====================================================
    # VALIDAR HORÁRIO
    # =====================================================

    if appointment_time not in ALLOWED_TIMES:

        return jsonify({
            "error": "Horário inválido."
        }), 400


    # =====================================================
    # DATA/HORA DA CRIAÇÃO
    # =====================================================

    brazil_timezone = ZoneInfo(
        "America/Sao_Paulo"
    )


    created_at = datetime.now(
        brazil_timezone
    ).isoformat()


    # =====================================================
    # SALVAR
    # =====================================================

    connection = get_connection()


    try:

        cursor = connection.execute(
            """
            INSERT INTO appointments
            (
                patient_name,
                phone,
                date,
                time,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                patient_name,
                phone,
                date,
                appointment_time,
                created_at
            )
        )


        connection.commit()


        appointment_id = (
            cursor.lastrowid
        )


    except sqlite3.IntegrityError:

        connection.close()


        return jsonify({
            "error":
                "Este horário já foi agendado."
        }), 409


    connection.close()


    return jsonify({

        "message":
            "Agendamento realizado com sucesso.",

        "appointment": {

            "id":
                appointment_id,

            "patient_name":
                patient_name,

            "phone":
                phone,

            "date":
                date,

            "time":
                appointment_time,

            "timezone":
                "America/Sao_Paulo",

            "created_at":
                created_at
        }

    }), 201


# =========================================================
# LISTAR AGENDAMENTOS
# SOMENTE FUNCIONÁRIOS
# =========================================================

@app.route("/appointments", methods=["GET"])
def get_appointments():
    """
    Lista todos os agendamentos.

    Esta rota só pode ser acessada
    por funcionário autenticado.
    """

    if not employee_is_authenticated():

        return jsonify({
            "error":
                "Acesso restrito a funcionários."
        }), 401


    connection = get_connection()


    appointments = connection.execute(
        """
        SELECT
            id,
            patient_name,
            phone,
            date,
            time,
            created_at

        FROM appointments

        ORDER BY
            date ASC,
            time ASC
        """
    ).fetchall()


    connection.close()


    appointments_list = []


    for appointment in appointments:

        appointments_list.append({

            "id":
                appointment["id"],

            "patient_name":
                appointment[
                    "patient_name"
                ],

            "phone":
                appointment["phone"],

            "date":
                appointment["date"],

            "time":
                appointment["time"],

            "created_at":
                appointment["created_at"]

        })


    return jsonify(
        appointments_list
    )


# =========================================================
# REAGENDAR / ALTERAR CONSULTA
# SOMENTE FUNCIONÁRIOS
# =========================================================

@app.route(
    "/appointments/<int:appointment_id>",
    methods=["PUT"]
)
def update_appointment(appointment_id):
    """
    Altera a data e o horário de uma consulta.

    Exemplo:

    PUT /appointments/1

    {
        "date": "2026-10-14",
        "time": "15:00"
    }
    """

    # =====================================================
    # AUTENTICAÇÃO
    # =====================================================

    if not employee_is_authenticated():

        return jsonify({
            "error":
                "Acesso restrito a funcionários."
        }), 401


    data = request.get_json()


    if not data:

        return jsonify({
            "error":
                "Dados do reagendamento não informados."
        }), 400


    new_date = data.get("date")

    new_time = data.get("time")


    if not new_date or not new_time:

        return jsonify({
            "error":
                "Informe a nova data e o novo horário."
        }), 400


    # =====================================================
    # VALIDAR DATA
    # =====================================================

    valid_day, message, status_code = (
        is_valid_business_day(
            new_date
        )
    )


    if not valid_day:

        return jsonify({
            "error": message
        }), status_code


    # =====================================================
    # VALIDAR HORÁRIO
    # =====================================================

    if new_time not in ALLOWED_TIMES:

        return jsonify({
            "error":
                "Horário inválido."
        }), 400


    connection = get_connection()


    # =====================================================
    # VERIFICAR SE O AGENDAMENTO EXISTE
    # =====================================================

    appointment = connection.execute(
        """
        SELECT
            id,
            patient_name,
            phone,
            date,
            time,
            created_at

        FROM appointments

        WHERE id = ?
        """,
        (appointment_id,)
    ).fetchone()


    if appointment is None:

        connection.close()


        return jsonify({
            "error":
                "Agendamento não encontrado."
        }), 404


    # =====================================================
    # VERIFICAR SE NOVO HORÁRIO ESTÁ OCUPADO
    # =====================================================

    occupied = connection.execute(
        """
        SELECT id

        FROM appointments

        WHERE date = ?
        AND time = ?
        AND id != ?
        """,
        (
            new_date,
            new_time,
            appointment_id
        )
    ).fetchone()


    if occupied:

        connection.close()


        return jsonify({
            "error":
                "Este horário já está ocupado."
        }), 409


    # =====================================================
    # ALTERAR
    # =====================================================

    try:

        connection.execute(
            """
            UPDATE appointments

            SET
                date = ?,
                time = ?

            WHERE id = ?
            """,
            (
                new_date,
                new_time,
                appointment_id
            )
        )


        connection.commit()


    except sqlite3.IntegrityError:

        connection.close()


        return jsonify({
            "error":
                "Este horário já está ocupado."
        }), 409


    connection.close()


    return jsonify({

        "message":
            "Agendamento alterado com sucesso.",

        "appointment": {

            "id":
                appointment_id,

            "patient_name":
                appointment["patient_name"],

            "phone":
                appointment["phone"],

            "date":
                new_date,

            "time":
                new_time

        }

    })


# =========================================================
# CANCELAR AGENDAMENTO
# SOMENTE FUNCIONÁRIOS
# =========================================================

@app.route(
    "/appointments/<int:appointment_id>",
    methods=["DELETE"]
)
def delete_appointment(appointment_id):
    """
    Cancela e remove um agendamento.

    Exemplo:

    DELETE /appointments/1
    """

    # =====================================================
    # AUTENTICAÇÃO
    # =====================================================

    if not employee_is_authenticated():

        return jsonify({
            "error":
                "Acesso restrito a funcionários."
        }), 401


    connection = get_connection()


    # =====================================================
    # VERIFICAR SE EXISTE
    # =====================================================

    appointment = connection.execute(
        """
        SELECT
            id,
            patient_name,
            phone,
            date,
            time

        FROM appointments

        WHERE id = ?
        """,
        (appointment_id,)
    ).fetchone()


    if appointment is None:

        connection.close()


        return jsonify({
            "error":
                "Agendamento não encontrado."
        }), 404


    # =====================================================
    # EXCLUIR
    # =====================================================

    connection.execute(
        """
        DELETE FROM appointments

        WHERE id = ?
        """,
        (appointment_id,)
    )


    connection.commit()

    connection.close()


    return jsonify({

        "message":
            "Agendamento cancelado com sucesso.",

        "appointment": {

            "id":
                appointment_id,

            "patient_name":
                appointment["patient_name"],

            "date":
                appointment["date"],

            "time":
                appointment["time"]
        }

    })


# =========================================================
# INICIAR SISTEMA
# =========================================================

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True
    )