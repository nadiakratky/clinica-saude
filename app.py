from flask import Flask, render_template, request, jsonify, session
import sqlite3
import requests
import os
import hmac
from datetime import datetime
from zoneinfo import ZoneInfo


app = Flask(__name__)


# =========================================================
# CONFIGURAÇÕES
# =========================================================

DATABASE = "database.db"

HOLIDAYS_API = (
    "https://date.nager.at/api/v3/"
    "PublicHolidays/2026/BR"
)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "chave-local-clinica-saude-2026"
)

EMPLOYEE_PASSWORD = os.getenv(
    "EMPLOYEE_PASSWORD",
    "clinica2026"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# =========================================================
# HORÁRIOS
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
# ESPECIALIDADES
# =========================================================

SPECIALTIES = [
    "Clínica Geral",
    "Pediatria",
    "Cardiologia",
    "Ginecologia",
    "Ortopedia",
    "Dermatologia"
]


# =========================================================
# BANCO
# =========================================================

def get_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def create_new_appointments_table(connection):

    connection.execute("""
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            specialty TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at TEXT NOT NULL,

            UNIQUE(date, time, specialty)
        )
    """)


def create_database():

    connection = get_connection()

    existing_table = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'appointments'
    """).fetchone()


    # Banco novo
    if existing_table is None:

        create_new_appointments_table(
            connection
        )

        connection.commit()
        connection.close()

        return


    # Verifica estrutura do banco antigo
    columns = connection.execute(
        "PRAGMA table_info(appointments)"
    ).fetchall()

    column_names = [
        column["name"]
        for column in columns
    ]


    # Se ainda não existe especialidade,
    # migramos a tabela antiga.
    if "specialty" not in column_names:

        connection.execute("""
            ALTER TABLE appointments
            RENAME TO appointments_old
        """)

        create_new_appointments_table(
            connection
        )

        connection.execute("""
            INSERT INTO appointments
            (
                id,
                patient_name,
                phone,
                specialty,
                date,
                time,
                created_at
            )

            SELECT
                id,
                patient_name,
                phone,
                'Clínica Geral',
                date,
                time,
                created_at

            FROM appointments_old
        """)

        connection.execute("""
            DROP TABLE appointments_old
        """)

        connection.commit()


    connection.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# LOGIN FUNCIONÁRIO
# =========================================================

@app.route(
    "/employee/login",
    methods=["POST"]
)
def employee_login():

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Senha não informada."
        }), 400


    password = str(
        data.get(
            "password",
            ""
        )
    )


    if not hmac.compare_digest(
        password,
        EMPLOYEE_PASSWORD
    ):

        return jsonify({
            "error": "Senha incorreta."
        }), 401


    session[
        "employee_authenticated"
    ] = True


    return jsonify({
        "message":
            "Login realizado com sucesso."
    })


# =========================================================
# LOGOUT
# =========================================================

@app.route(
    "/employee/logout",
    methods=["POST"]
)
def employee_logout():

    session.pop(
        "employee_authenticated",
        None
    )


    return jsonify({
        "message":
            "Logout realizado com sucesso."
    })


# =========================================================
# STATUS
# =========================================================

@app.route(
    "/employee/status",
    methods=["GET"]
)
def employee_status():

    return jsonify({

        "authenticated":
            session.get(
                "employee_authenticated",
                False
            )

    })


def employee_is_authenticated():

    return session.get(
        "employee_authenticated",
        False
    )


# =========================================================
# FERIADOS
# =========================================================

def get_holidays():

    try:

        response = requests.get(
            HOLIDAYS_API,
            timeout=10
        )

        response.raise_for_status()

        holidays = response.json()


        return [
            holiday["date"]
            for holiday in holidays
        ]


    except (
        requests.RequestException,
        ValueError,
        KeyError
    ) as error:

        print(
            "Erro ao consultar feriados:",
            error
        )

        return None


# =========================================================
# VALIDAR DATA
# =========================================================

def is_valid_business_day(
    date_string
):

    try:

        selected_date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).date()


    except (
        ValueError,
        TypeError
    ):

        return (
            False,
            "Data inválida.",
            400
        )


    if selected_date.year != 2026:

        return (
            False,
            "O sistema aceita agendamentos apenas para 2026.",
            400
        )


    if selected_date.weekday() >= 5:

        return (
            False,
            "Não realizamos agendamentos aos finais de semana.",
            400
        )


    holidays = get_holidays()


    if holidays is None:

        return (
            False,
            "Não foi possível consultar os feriados. Tente novamente.",
            503
        )


    if date_string in holidays:

        return (
            False,
            "Não realizamos agendamentos em feriados.",
            400
        )


    return (
        True,
        None,
        200
    )


# =========================================================
# HORÁRIOS DISPONÍVEIS
# =========================================================

@app.route(
    "/available",
    methods=["GET"]
)
def available():

    date = request.args.get(
        "date"
    )

    specialty = request.args.get(
        "specialty"
    )

    exclude_id = request.args.get(
        "exclude_id",
        type=int
    )


    if not date:

        return jsonify({
            "error":
                "Informe uma data."
        }), 400


    if specialty:

        if specialty not in SPECIALTIES:

            return jsonify({
                "error":
                    "Especialidade inválida."
            }), 400


    valid_day, message, status_code = (
        is_valid_business_day(
            date
        )
    )


    if not valid_day:

        return jsonify({

            "date":
                date,

            "available":
                [],

            "message":
                message

        }), status_code


    connection = get_connection()


    # Se a especialidade foi informada,
    # verificamos ocupação apenas nela.
    if specialty:

        if (
            exclude_id is not None
            and employee_is_authenticated()
        ):

            appointments = (
                connection.execute(
                    """
                    SELECT time
                    FROM appointments

                    WHERE date = ?
                    AND specialty = ?
                    AND id != ?
                    """,
                    (
                        date,
                        specialty,
                        exclude_id
                    )
                ).fetchall()
            )

        else:

            appointments = (
                connection.execute(
                    """
                    SELECT time
                    FROM appointments

                    WHERE date = ?
                    AND specialty = ?
                    """,
                    (
                        date,
                        specialty
                    )
                ).fetchall()
            )


    # Compatibilidade com o endpoint
    # original do desafio.
    else:

        appointments = (
            connection.execute(
                """
                SELECT time
                FROM appointments

                WHERE date = ?
                """,
                (date,)
            ).fetchall()
        )


    connection.close()


    occupied_times = [
        appointment["time"]
        for appointment in appointments
    ]


    available_times = [

        appointment_time

        for appointment_time
        in ALLOWED_TIMES

        if appointment_time
        not in occupied_times

    ]


    return jsonify({

        "date":
            date,

        "specialty":
            specialty,

        "timezone":
            "America/Sao_Paulo",

        "available":
            available_times

    })


# =========================================================
# CRIAR AGENDAMENTO
# =========================================================

@app.route(
    "/appointments",
    methods=["POST"]
)
def create_appointment():

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


    specialty = str(
        data.get(
            "specialty",
            ""
        )
    ).strip()


    date = data.get(
        "date"
    )

    appointment_time = data.get(
        "time"
    )


    if (
        not patient_name
        or not phone
        or not specialty
        or not date
        or not appointment_time
    ):

        return jsonify({
            "error":
                "Preencha todos os campos."
        }), 400


    if specialty not in SPECIALTIES:

        return jsonify({
            "error":
                "Especialidade inválida."
        }), 400


    valid_day, message, status_code = (
        is_valid_business_day(
            date
        )
    )


    if not valid_day:

        return jsonify({
            "error":
                message
        }), status_code


    if appointment_time not in ALLOWED_TIMES:

        return jsonify({
            "error":
                "Horário inválido."
        }), 400


    brazil_timezone = ZoneInfo(
        "America/Sao_Paulo"
    )


    created_at = datetime.now(
        brazil_timezone
    ).isoformat()


    connection = get_connection()


    try:

        cursor = connection.execute(
            """
            INSERT INTO appointments
            (
                patient_name,
                phone,
                specialty,
                date,
                time,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                patient_name,
                phone,
                specialty,
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
                "Este horário já está ocupado para esta especialidade."
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

            "specialty":
                specialty,

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
# =========================================================

@app.route(
    "/appointments",
    methods=["GET"]
)
def get_appointments():

    if not employee_is_authenticated():

        return jsonify({
            "error":
                "Acesso restrito a funcionários."
        }), 401


    connection = get_connection()


    appointments = (
        connection.execute(
            """
            SELECT
                id,
                patient_name,
                phone,
                specialty,
                date,
                time,
                created_at

            FROM appointments

            ORDER BY
                date ASC,
                time ASC
            """
        ).fetchall()
    )


    connection.close()


    result = []


    for appointment in appointments:

        result.append({

            "id":
                appointment["id"],

            "patient_name":
                appointment[
                    "patient_name"
                ],

            "phone":
                appointment["phone"],

            "specialty":
                appointment[
                    "specialty"
                ],

            "date":
                appointment["date"],

            "time":
                appointment["time"],

            "created_at":
                appointment[
                    "created_at"
                ]

        })


    return jsonify(
        result
    )


# =========================================================
# REAGENDAR
# =========================================================

@app.route(
    "/appointments/<int:appointment_id>",
    methods=["PUT"]
)
def update_appointment(
    appointment_id
):

    if not employee_is_authenticated():

        return jsonify({
            "error":
                "Acesso restrito a funcionários."
        }), 401


    data = request.get_json()


    if not data:

        return jsonify({
            "error":
                "Dados não informados."
        }), 400


    new_date = data.get(
        "date"
    )

    new_time = data.get(
        "time"
    )


    connection = get_connection()


    appointment = (
        connection.execute(
            """
            SELECT *
            FROM appointments
            WHERE id = ?
            """,
            (appointment_id,)
        ).fetchone()
    )


    if appointment is None:

        connection.close()

        return jsonify({
            "error":
                "Agendamento não encontrado."
        }), 404


    new_specialty = data.get(
        "specialty",
        appointment["specialty"]
    )


    if new_specialty not in SPECIALTIES:

        connection.close()

        return jsonify({
            "error":
                "Especialidade inválida."
        }), 400


    if not new_date or not new_time:

        connection.close()

        return jsonify({
            "error":
                "Informe a nova data e horário."
        }), 400


    valid_day, message, status_code = (
        is_valid_business_day(
            new_date
        )
    )


    if not valid_day:

        connection.close()

        return jsonify({
            "error":
                message
        }), status_code


    if new_time not in ALLOWED_TIMES:

        connection.close()

        return jsonify({
            "error":
                "Horário inválido."
        }), 400


    occupied = connection.execute(
        """
        SELECT id

        FROM appointments

        WHERE date = ?
        AND time = ?
        AND specialty = ?
        AND id != ?
        """,
        (
            new_date,
            new_time,
            new_specialty,
            appointment_id
        )
    ).fetchone()


    if occupied:

        connection.close()

        return jsonify({
            "error":
                "Este horário já está ocupado para esta especialidade."
        }), 409


    try:

        connection.execute(
            """
            UPDATE appointments

            SET
                specialty = ?,
                date = ?,
                time = ?

            WHERE id = ?
            """,
            (
                new_specialty,
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
                appointment[
                    "patient_name"
                ],

            "phone":
                appointment["phone"],

            "specialty":
                new_specialty,

            "date":
                new_date,

            "time":
                new_time
        }

    })


# =========================================================
# CANCELAR
# =========================================================

@app.route(
    "/appointments/<int:appointment_id>",
    methods=["DELETE"]
)
def delete_appointment(
    appointment_id
):

    if not employee_is_authenticated():

        return jsonify({
            "error":
                "Acesso restrito a funcionários."
        }), 401


    connection = get_connection()


    appointment = (
        connection.execute(
            """
            SELECT *
            FROM appointments
            WHERE id = ?
            """,
            (appointment_id,)
        ).fetchone()
    )


    if appointment is None:

        connection.close()

        return jsonify({
            "error":
                "Agendamento não encontrado."
        }), 404


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
            "Agendamento cancelado com sucesso."

    })


# =========================================================
# INICIAR
# =========================================================

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True
    )