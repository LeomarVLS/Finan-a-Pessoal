import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
from datetime import datetime


# CONEXÃO COM GOOGLE SHEETS

def connect_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"], scope
    )

    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["sheet_id"])


sheet = connect_sheet()

# GARANTIR ESTRUTURA DAS ABAS

def ensure_headers():
    required_tabs = {
        "users": ["name"],
        "categories": ["name"],

        # Templates fixos que se repetem todo mês
        "fixed_templates": ["id", "nome", "valor", "categoria", "usuario"],
        "income_templates": ["id", "nome", "valor"],

        # Lançamentos mensais gerados a partir dos templates
        "fixed_expenses": ["id", "nome", "valor", "categoria", "usuario", "data", "hora"],
        "incomes": ["id", "nome", "valor", "data", "hora"],

        "personal_expenses": ["id", "nome", "valor", "categoria", "usuario", "data", "hora"],

        # Controle interno de meses já processados
        "processed_months": ["month", "generated_at"]
    }

    for tab, headers in required_tabs.items():
        try:
            ws = sheet.worksheet(tab)
        except gspread.exceptions.WorksheetNotFound:
            ws = sheet.add_worksheet(title=tab, rows=1000, cols=20)
            ws.append_row(headers)
            continue

        rows = ws.get_all_values()
        if not rows:
            ws.append_row(headers)
            continue

        current_header = rows[0]
        if current_header != headers:
            ws.clear()
            ws.append_row(headers)

ensure_headers()

# AUXILIARES DE LEITURA/ESCRITA

def load_table(name):
    try:
        ws = sheet.worksheet(name)
        rows = ws.get_all_values()

        if not rows or len(rows) < 2:
            return []

        header = rows[0]
        data = []

        for row in rows[1:]:
            if len(row) < len(header):
                row += [""] * (len(header) - len(row))

            data.append({header[i]: row[i] for i in range(len(header))})

        return data

    except Exception as e:
        print(f"[ERRO] load_table('{name}'): {e}")
        return []


def append_row(name, data):
    try:
        ws = sheet.worksheet(name)
        if isinstance(data, dict):
            header = ws.get_all_values()[0]
            data = [data.get(col, "") for col in header]
        ws.append_row(data)
    except Exception as e:
        print(f"[ERRO] append_row('{name}'): {e}")


def overwrite_table(name, items):
    try:
        ws = sheet.worksheet(name)
        ws.clear()

        if not items:
            return

        headers = list(items[0].keys())
        ws.append_row(headers)

        for row in items:
            ws.append_row([row.get(h, "") for h in headers])

    except Exception as e:
        print(f"[ERRO] overwrite_table('{name}'): {e}")