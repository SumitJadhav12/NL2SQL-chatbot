import re

DANGEROUS_KEYWORDS = [
    r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b', r'\bALTER\b',
    r'\bCREATE\b', r'\bEXEC\b', r'\bGRANT\b', r'\bREVOKE\b', r'\bTRUNCATE\b'
]
SYSTEM_TABLES = [r'sqlite_master', r'sqlite_temp_master', r'sqlite_sequence']

def validate_sql(sql: str):
    if not sql:
        return False, "Empty SQL"
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT'):
        return False, "Only SELECT allowed"
    for kw in DANGEROUS_KEYWORDS:
        if re.search(kw, sql_upper):
            return False, f"Dangerous keyword {kw} not allowed"
    for tbl in SYSTEM_TABLES:
        if re.search(tbl, sql, re.IGNORECASE):
            return False, f"System table {tbl} not allowed"
    return True, ""