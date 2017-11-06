# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Custodian(models.Model):
    _name = 'amgl.custodian'
    _description = 'Custodian'

    name = fields.Char()
    customers = fields.One2many('amgl.customer', 'custodian_id', string='Custodians')
