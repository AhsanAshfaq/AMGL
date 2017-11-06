# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class MetalMovement(models.Model):
    _name = 'amgl.metal_movement'
    _description = 'Metal Movement'

    @api.model
    def create(self, vals):
        record = super(MetalMovement, self).create(vals)
        domain = [('customer_id', '=', record['customer'].id), ('state', '=', 'completed')]
        searched_orders = self.env['amgl.order'].search(domain)
        bol = False
        total_items_to_move = 0
        total_items_in_stock = 0
        for order in searched_orders:
            for ol in order.order_line:
                for temp_order_line in record['order_lines']:
                    if temp_order_line.products == ol.products:
                        total_items_to_move += temp_order_line.quantity
                        total_items_in_stock += ol.quantity
                    else:
                        bol = True
        if bol is not True:
            raise ValidationError("Selected product is in process. Please select another one.")
        if total_items_in_stock < total_items_to_move:
            raise ValidationError("Quantity of product should be less then stock.")

        template = self.env.ref('amgl.create_mmr_email', raise_if_not_found=True)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        temp_mmr_link =  base_url+"/web#id="+str(record['id'])+"&view_type=form&model=metal.movement&action=81&menu_id=70"
        temp_mmr_name = "Metal Move Request - "+str(record['customer'].full_name)
        record['states'] = 'created'
        user_ids = [record['first_approve'].id, record['second_approve'].id]
        for id in user_ids:
            template.with_context(mmr_link=temp_mmr_link,
                                  date=str(record['date_create']),
                                  ref=str(record['reference']),
                                  fapprove=str(record['first_approve'].name),
                                  sapprove=str(record['second_approve'].name),
                                  customer=str(record['customer'].full_name),
                                  custodian=str(record['custodian'].name),
                                  mmt=str(record['metal_movement_type']),
                                  mmf_name=str(record['mmf_name']),
                                  mmf_accountnumber=str(record['mmf_account_number']),
                                  mmf_accounttype=str(record['mmf_account_type']),
                                  mmt_name=str(record['mmt_name']),
                                  mmt_address=str(record['mmt_address']),
                                  mmt_account=str(record['mmt_account_number']),
                                  mmr_name=temp_mmr_name).send_mail(
                id, force_send=True, raise_exception=True
            )
        return record

    def update_approve(self):
        if self.env.user.id == self.first_approve.id:
            self.update({
                'is_first_approve': True
            })
        if self.env.user.id == self.second_approve.id:
            self.update({
                'is_second_approve': True
            })
        if self.is_first_approve == True and self.is_second_approve == True:
            self.update({
                'is_complete': True
            })

        return True

    def update_reject(self):
        if self.env.user.id == self.first_approve.id:
            self.update({
                'is_first_approve': False
            })
            template = self.env.ref('amgl.reject_mmr_email', raise_if_not_found=True)
            mail_id = template.with_context(rejected_by=self.first_approve.name).send_mail(
                self.create_uid.id, force_send=True, raise_exception=True
            )
        if self.env.user.id == self.second_approve.id:
            self.update({
                'is_second_approve': False
            })
            template = self.env.ref('amgl.reject_mmr_email', raise_if_not_found=True)
            mail_id = template.with_context(rejected_by=self.second_approve.name).send_mail(
                self.create_uid.id, force_send=True, raise_exception=True
            )
        return True

    def _get_current_user(self):
        if self.first_approve == self.env.user:
            if self.is_first_approve:
                self.update({'current_user': False})
            else:
                self.update({'current_user': True}) #sending false because we need to show in True case
        elif self.second_approve == self.env.user:
            if self.is_second_approve:
                self.update({'current_user': False})
            else:
                self.update({'current_user': True})
        else:
            self.update({'current_user': False})
        return True

    def on_change_customer(self,customer):
        if not customer:
            customer = 0

        self.env.cr.execute("select p.* from amgl_order_line as ol inner join amgl_order as o on o.id = ol.order_id inner join amgl_products as p on p.id = ol.products where o.customer_id = "+str(customer))
        list = self.env.cr.fetchall()
        for order in self.order_lines:
            order.update({
                'products':list
            })

    name = fields.Char()
    date_create = fields.Datetime(string="Date", required=True)
    reference = fields.Char(string="Reference", required=True)
    is_first_approve = fields.Boolean()
    is_second_approve = fields.Boolean()
    is_complete = fields.Boolean()
    current_user = fields.Boolean(compute='_get_current_user')
    states = fields.Char(default="created")
    first_approve = fields.Many2one("res.users",string="First Approve By", required=True)
    second_approve = fields.Many2one("res.users", string="Second Approve By", required=True)
    sepcial_instruction = fields.Html(string="Special Instruction")
    metal_movement_type = fields.Selection(selection=[('IT','Internal Transfer'),('USPSPM','USPS Priority Mail')
        ,('USPSDA','USPS 2nd Day Air'),('USPSND','USPS Next Day'),('O','Other'),('AC','Armored Carrier')
        ,('IPPU','InPerson Pickup')],default="IT")
    custodian = fields.Many2one("res.users",string="Custodian", required=True, domain=[('groups_id','in',[12])])
    customer = fields.Many2one("amgl.customer", string="Customer", required=True)
    mmf_name = fields.Char(string="Name")
    mmf_account_number = fields.Char(string="Account Number")
    mmf_account_type = fields.Selection(selection=[('Commingled','Commingled'),('Segregated','Segregated')]
                                        ,string="Account Type")
    mmt_name = fields.Char(string="Name")
    mmt_address = fields.Char(string="Address")
    mmt_account_number = fields.Char(string="Account # (if applicable)")
    mmt_company = fields.Char(string="Company")
    pickup_date = fields.Datetime(string="Pickup Datetime")
    order_lines = fields.One2many('amgl.order_line','metal_movement_id',string="Metals To Be Moved")
