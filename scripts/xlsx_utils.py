from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def _load_shared_strings(workbook_zip: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in workbook_zip.namelist():
        return []

    root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
    return [
        "".join(text_node.text or "" for text_node in item.iter(f"{{{NS['a']}}}t"))
        for item in root
    ]


def _worksheet_path(workbook_zip: zipfile.ZipFile) -> str:
    workbook = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
    relations = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
    relation_map = {relation.attrib["Id"]: relation.attrib["Target"] for relation in relations}
    first_sheet = workbook.find("a:sheets", NS)[0]
    sheet_path = relation_map[first_sheet.attrib[f"{{{NS['r']}}}id"]]
    return sheet_path if sheet_path.startswith("xl/") else f"xl/{sheet_path}"


def iter_xlsx_rows(path: Path):
    with zipfile.ZipFile(path) as workbook_zip:
        shared_strings = _load_shared_strings(workbook_zip)
        worksheet = ET.fromstring(workbook_zip.read(_worksheet_path(workbook_zip)))
        sheet_data = worksheet.find("a:sheetData", NS)

        for row in sheet_data:
            values = []
            for cell in row:
                value_node = cell.find("a:v", NS)
                value = value_node.text if value_node is not None else ""
                if cell.attrib.get("t") == "s" and value != "":
                    value = shared_strings[int(value)]
                values.append(value)
            yield values
