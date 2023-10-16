from odoo import api, fields, models

class AccountKhqr(models.Model):
    _name = 'account.khqr'

    name = fields.Char(string="Account KHQR")
    khqr_img = fields.Binary(string="KHQR Image")

