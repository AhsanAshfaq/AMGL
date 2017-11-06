# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Inventory(models.Model):
    _name = 'amgl.inventory'

    name = fields.Char()
    products = fields.Many2one('amgl.products', string='Product')
    quantity = fields.Float(string='Quantity')
    weight = fields.Float(string='Weight')
    total_weight = fields.Float(string='Total Weight')
    commodity = fields.Selection(selection=[('Gold', 'Gold'), ('Silver', 'Silver'),
                                 ('Platinum', 'Platinum'), ('Palladium', 'Palladium')],
                                 string="Commodity", required=True)
    customer_id = fields.Many2one('amgl.customer', string='Customer')
    order_id = fields.Many2one('amgl.order', string='Order')
    deposit_date = fields.Datetime(string='Deposit Date')