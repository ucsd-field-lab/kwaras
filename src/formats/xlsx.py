from openpyxl import load_workbook


class ExcelReader:

    def __init__(self, filename):

        wb = load_workbook(filename)
        self.worksheet = wb.get_active_sheet()
        self.fieldnames = self.worksheet.rows.next()

    def next(self):
        values = ['' if cell.value is None else cell.value for cell in self.worksheet.rows.next()]
        row = dict(zip(self.fieldnames, values))
        return row

    def __iter__(self):
        return self
