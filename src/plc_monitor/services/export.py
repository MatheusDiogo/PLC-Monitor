import csv


def export_readings(database, path, plc_id=None):
    rows = database.fetch_all_readings(plc_id)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["CLP", "Aluno", "Tag", "Valor", "Timestamp"])
        writer.writerows(rows)
