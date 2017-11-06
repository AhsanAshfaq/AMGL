# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OrderHistory(models.Model):
    _name = 'amgl.order.history'
    _description = 'Order History'

    name = fields.Char()
    date_create = fields.Datetime()
    fields_updated = fields.Char()
    remaining_quantity = fields.Float()
    received_quantity = fields.Float()
    order_id = fields.Many2one('amgl.order',string="Orders")
    updated_by = fields.Many2one('res.users')
