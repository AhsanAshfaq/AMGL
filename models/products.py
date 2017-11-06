# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression

class Products(models.Model):
    _name = 'amgl.products'
    _description = 'Product'

    @staticmethod
    def insert_char(my_string, position, char_to_insert):
        return my_string[:position] + char_to_insert + my_string[position:]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name.find(' ') != -1:
            name = '%' + name + '%'
            name = self.insert_char(name,name.find(' '),' %')
            name = name.replace(" ", "")
            domain = [('name', operator, name)]
        products = self.search(domain + args, limit=limit)
        return products.name_get()

    name = fields.Char('Product Name', required=True)
    type = fields.Selection(
        selection=[('Gold', 'Gold'), ('Silver', 'Silver')
            , ('Platinum', 'Platinum'), ('Palladium', 'Palladium')]
        , string="Commodity", required=True)
    weight_per_piece = fields.Float(string="Weight Per Piece", required=True)
    weight_unit = fields.Selection(string="Weight Unit", selection=[('oz', 'Ounce'), ('gram', 'Gram')
            , ('kg', 'Kilogram'), ('pounds', 'Pounds')], required=True, default="oz")
    customer_ids = fields.Many2many('amgl.customer', string='Customers')
