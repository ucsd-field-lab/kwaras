from openpyxl import load_workbook


class ExcelReader:

    def __init__(self, filename):

        wb = load_workbook(filename)
        self.worksheet = wb.get_active_sheet()
        self.fieldnames = next(self.worksheet.rows)

    def __next__(self):
        values = ['' if cell.value is None else cell.value for cell in next(self.worksheet.rows)]
        row = dict(list(zip(self.fieldnames, values)))
        return row

    def __iter__(self):
        return self
