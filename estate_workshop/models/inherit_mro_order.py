from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
import time
import datetime
from openerp import tools


class InheritMroOrder(models.Model):

    _inherit = 'mro.order'

    mecanictimesheet_ids = fields.One2many('estate.mecanic.timesheet','owner_id')
    employeeline_ids = fields.One2many('estate.workshop.employeeline','mro_id')
    serviceexternal_ids = fields.One2many('estate.workshop.external.service','owner_id')
    code_id = fields.Many2one('estate.workshop.causepriority.code','Priority',domain=[('type', '=', '2')])
    reconcil_id = fields.Many2one('estate.workshop.causepriority.code',domain=[('type', '=', '3')],
                                  states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
    actualtools_ids= fields.One2many('estate.workshop.actualequipment','mro_id')
    plannedtools_ids = fields.One2many('estate.workshop.plannedequipment','mro_id')
    cost_ids = fields.One2many('v.summary.cost.workshop.detail','mo_id')
    plannedtask_ids = fields.One2many('estate.workshop.plannedtask','mro_id')
    actualtask_ids = fields.One2many('estate.workshop.actualtask','mro_id')
    actualpart_ids = fields.One2many('estate.workshop.actual.sparepart','owner_id')
    plannedpart_ids = fields.One2many('estate.workshop.planned.sparepart','owner_id')
    typetask_id = fields.Many2one('estate.master.type.task','Type Task',domain=[('parent_id','=',False)])
    type_service = fields.Selection([('1','Vehicle'),
                                     ('2','Building'),('3','Machine'),('4','Computing'),('5','Tools'),('6','ALL')],
                                    )

    # Group code constraint
    @api.multi
    @api.constrains('plannedtask_ids')
    def _constrains_plannedmastertask_id(self):
        self.ensure_one()
        if self.plannedtask_ids:
            temp={}
            for task in self.plannedtask_ids:
                task_value_name = task.mastertask_id.name
                if task_value_name in temp.values():
                    error_msg = "Task \"%s\" is set more than once " % task_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[task.id] = task_value_name
            return temp

    @api.multi
    @api.constrains('actualtask_ids')
    def _constrains_actualmastertask_id(self):
        self.ensure_one()
        if self.actualtask_ids:
            temp={}
            for task in self.actualtask_ids:
                task_value_name = task.mastertask_id.name
                if task_value_name in temp.values():
                    error_msg = "Task \"%s\" is set more than once " % task_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[task.id] = task_value_name
            return temp

    @api.multi
    @api.constrains('plannedpart_ids')
    def _constrains_plannedsparepart_id(self):
        self.ensure_one()
        if self.plannedpart_ids:
            temp={}
            for part in self.plannedpart_ids:
                part_value_name = part.product_id.name
                if part_value_name in temp.values():
                    error_msg = "Product Part \"%s\" is set more than once " % part_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[part.id] = part_value_name
            return temp

    @api.multi
    @api.constrains('actualpart_ids')
    def _constrains_actualsparepart_id(self):
        self.ensure_one()
        if self.actualpart_ids:
            temp={}
            for part in self.actualpart_ids:
                part_value_name = part.product_id.name
                if part_value_name in temp.values():
                    error_msg = "Product Part \"%s\" is set more than once " % part_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[part.id] = part_value_name
            return temp

    @api.multi
    @api.constrains('plannedtools_ids')
    def _constrains_plannedtools_id(self):
        self.ensure_one()
        if self.plannedtools_ids:
            temp={}
            for tools in self.plannedtools_ids:
                tools_value_name = tools.asset_id.name
                if tools_value_name in temp.values():
                    error_msg = "Tools or Equipment \"%s\" is set more than once " % tools_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[tools.id] = tools_value_name
            return temp

    @api.multi
    @api.constrains('actualtools_ids')
    def _constrains_actualtools_id(self):
        self.ensure_one()
        if self.actualtools_ids:
            temp={}
            for tools in self.actualtools_ids:
                tools_value_name = tools.asset_id.name
                if tools_value_name in temp.values():
                    error_msg = "Tools or Equipment \"%s\" is set more than once " % tools_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[tools.id] = tools_value_name
            return temp

    @api.multi
    @api.constrains('employeeline_ids')
    def _constrains_employee_id(self):
        self.ensure_one()
        if self.employeeline_ids:
            temp={}
            for employee in self.employeeline_ids:
                employee_value_name = employee.employee_id.name
                if employee_value_name in temp.values():
                    error_msg = "Employee \"%s\" is set more than once " % employee_value_name
                    raise exceptions.ValidationError(error_msg)
                temp[employee.id] = employee_value_name
            return temp


    #---------------------------------------------------------------------------------------------


    #new API
    @api.multi
    def test_if_parts(self):
        #constraint for Maintenance type and priority
        for order in self:
            if order.typetask_id.id == False:
                error_msg = "Maintenance Type Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if order.code_id.id == False:
                error_msg = "Priority Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if order.type_service_handling == "1":
                countLineEmployee = 0
                countLinePlannedpart = 0
                countLinePlannedtask = 0
                countLinePlannedtools = 0
                for itemline in self:
                    countLineEmployee += len(itemline.employeeline_ids)
                    countLinePlannedpart += len(itemline.plannedpart_ids)
                    countLinePlannedtask += len(itemline.plannedtask_ids)
                    countLinePlannedtools += len(itemline.plannedtools_ids)
                if countLinePlannedtask == 0:
                    error_msg = "Tab Planned Operations Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLineEmployee == 0:
                    error_msg = "Tab Planned Labor's Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLinePlannedpart == 0:
                    error_msg = "Tab Planned Sparepart Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLinePlannedtools == 0:
                    error_msg = "Tab Planned Tools Must be Filled"
                    raise exceptions.ValidationError(error_msg)
            if order.type_service_handling == "2":
                countLineExternal = 0
                for itemexternalline in self:
                    countLineExternal += len(itemexternalline.serviceexternal_ids)
                if countLineExternal == 0:
                    error_msg = "Tab Service External Must be Filled"
                    raise exceptions.ValidationError(error_msg)
            super(InheritMroOrder,self).test_if_parts()

    @api.multi
    def action_done(self):
        for order in self:
            if order.reconcil_id.id == False:
                error_msg = "Reconcil Field Must be Filled"
                raise exceptions.ValidationError(error_msg)
            if order.type_service_handling == "1":
                countLineEmployee = 0
                countLineActualpart = 0
                countLineActualtask = 0
                countLineActualtools = 0
                for itemLine in self:
                    countLineActualtools += len(itemLine.actualtools_ids)
                    countLineActualpart += len(itemLine.actualtask_ids)
                    countLineActualtask += len(itemLine.actualpart_ids)
                    countLineEmployee += len(itemLine.mecanictimesheet_ids)
                if countLineActualtask == 0:
                    error_msg = "Tab Actual Operations Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLineActualpart == 0:
                    error_msg = "Tab Actual Sparepart Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLineEmployee == 0:
                    error_msg = "Tab Labor's Must be Filled"
                    raise exceptions.ValidationError(error_msg)
                if countLineActualtools == 0:
                    error_msg = "Tab Actual Tools Must be Filled"
                    raise exceptions.ValidationError(error_msg)
            super(InheritMroOrder,self).action_done()

    @api.multi
    @api.onchange('plannedtask_ids','actualtask_ids')
    def _onchange_owner_id(self):
        if self.state == 'draft':
            for owner in self.plannedtask_ids:
                owner.owner_id = self.owner_id
        if self.state == 'ready':
            for owner in self.actualtask_ids:
                owner.owner_id = self.owner_id

    @api.multi
    @api.onchange('owner_id','asset_id')
    def _onchange_owner_id(self):
        if self.asset_id :
            self.owner_id = self.asset_id.id

    #onchange
    @api.multi
    @api.onchange('asset_id','type_service')
    def _onchange_type_service(self):
        if self.asset_id == True:
            self.type_service = self.asset_id.type_asset















