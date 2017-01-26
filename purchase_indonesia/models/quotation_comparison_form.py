from openerp import models, fields, api, exceptions
from psycopg2 import OperationalError

from openerp import SUPERUSER_ID
import openerp
import openerp.addons.decimal_precision as dp
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, date,time
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar
from openerp import tools
import re
from lxml import etree
from openerp.tools.translate import _


class InheritPurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    comparison_id = fields.Many2one('quotation.comparison.form','QCF')

class InheritPurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    comparison_id = fields.Many2one('quotation.comparison.form','QCF')
    trigger_state = fields.Boolean('Trigger State')
    trigger_filter_cancel = fields.Boolean('Trigger Cancel',default=False,compute='_filter_cancel')

    @api.multi
    def button_confirm(self):
        self.write({'trigger_state':True})
        res = super(InheritPurchaseOrderLine,self).button_confirm()
        return res

    @api.multi
    def button_cancel(self):
        self.write({'trigger_state':False})
        res = super(InheritPurchaseOrderLine,self).button_cancel()
        return res

    @api.multi
    @api.depends('order_id')
    def _filter_cancel(self):
        for item in self:
            if item.order_id.state == 'cancel':
                item.trigger_filter_cancel = True


class QuotationComparisonForm(models.Model):

    def return_action_to_open(self, cr, uid, ids, context=None):
        """ This opens the xml view specified in xml_id for the current Purchase Tender """
        if context is None:
            context = {}
        if context.get('xml_id'):
            res = self.pool.get('ir.actions.act_window').for_xml_id(cr, uid ,'purchase', context['xml_id'], context=context)
            res['context'] = context
            res['context'].update({'default_comparison_id': ids[0]})
            res['domain'] = [('comparison_id','=',ids[0])]
            return res
        return False

    @api.multi
    def purchase_request_dpt_head(self):
        return 'Purchase Request Department Head'

    @api.multi
    def purchase_request_division_head(self):
        return 'Purchase Request Division Head'

    @api.multi
    def purchase_request_budget(self):
        return 'Purchase Request Budget'

    @api.multi
    def purchase_request_technical1(self):
        return 'Purchase Request Technical Dept Head'

    @api.multi
    def purchase_request_technical2(self):
        return 'Purchase Request Technical Div Head'

    @api.multi
    def purchase_request_technical3(self):
        return 'Purchase Request Technical ICT'

    @api.multi
    def purchase_request_technical4(self):
        return 'Purchase Request Technical Agronomy'

    @api.multi
    def purchase_request_technical5(self):
        return 'Purchase Request Technical IE'

    @api.multi
    def purchase_request_director(self):
        return 'Purchase Request Director'

    @api.multi
    def purchase_request_president_director(self):
        return 'Purchase Request President Director'

    @api.multi
    def purchase_ro_head(self):
        return 'Purchase Request RO Head'

    @api.multi
    def purchase_procurement_staff(self):
        return 'Purchase Request Procurment Staff'

    @api.multi
    def purchase_request_manager(self):
        return 'Purchase Request Manager'

    @api.multi
    def purchase_request_finance(self):
        return 'Purchase Request Finance Procurement'

    #Method Get user
    @api.multi
    def _get_user(self):
        #find User
        user= self.env['res.users'].browse(self.env.uid)

        return user

    @api.multi
    def _get_employee(self):
        #find User Employee

        employee = self.env['hr.employee'].search([('user_id','=',self._get_user().id)])

        return employee

    @api.multi
    def _get_user_ro_manager(self):
        #get List of Ro Manager from user.groups
        arrRO = []

        list_ro_manager = self.env['res.groups'].search([('name','like',self.purchase_ro_head())]).users

        for ro_manager_id in list_ro_manager:
                arrRO.append(ro_manager_id.id)
        try:
            ro_manager = self.env['res.users'].search([('id','in',arrRO)]).id
        except:
            raise exceptions.ValidationError('User get Role President Director Not Found in User Access')

        return ro_manager

    @api.multi
    def _get_president_director(self):
        #get List of president director from user.groups
        arrPresidentDirector = []

        #search User President director from user list
        list_president= self.env['res.groups'].search([('name','like',self.purchase_request_president_director())]).users

        for president_id in list_president:
            arrPresidentDirector.append(president_id.id)
        try:
            president = self.env['res.users'].search([('id','=',arrPresidentDirector[0])]).id
        except:
            raise exceptions.ValidationError('User get Role President Director Not Found in User Access')
        return president

    @api.multi
    def _get_director(self):
        #get List of director from user.groups
        arrDirector = []

        #search User Director from user list
        list_director= self.env['res.groups'].search([('name','like',self.purchase_request_director())]).users
        for director_id in list_director:
            arrDirector.append(director_id.id)
        try:
            director = self.env['res.users'].search([('id','=',arrDirector[0])]).id
        except:
            raise exceptions.ValidationError('User get Role Director Purchase Not Found in User Access')
        return director

    @api.multi
    def _get_division_finance(self):
        #get List of Finance from user.groups
        arrDivhead = []

        #search User Finance from user list
        listdivision= self.env['res.groups'].search([('name','like',self.purchase_request_division_head())]).users

        for divhead in listdivision:
            arrDivhead.append(divhead.id)
        try:
            division = self.env['res.users'].search([('id','=',arrDivhead[0])]).id
        except:
            raise exceptions.ValidationError('User get Role Division Head Not Found in User Access')

        return division

    @api.multi
    def _get_procurement_finance(self):
        #get List of Finance from user.groups
        arrFinancehead = []

        #search User Finance from user list
        listprocurement= self.env['res.groups'].search([('name','like',self.purchase_request_finance())]).users

        for financeproc in listprocurement:
            arrFinancehead.append(financeproc.id)
        try:
            fin_procur = self.env['res.users'].search([('id','=',arrFinancehead[0])]).id
        except:
            raise exceptions.ValidationError('User get Role Finance Procurement Not Found in User Access')

        return fin_procur



    _name = 'quotation.comparison.form'
    _description = 'Form Quotation Comparison'
    _order = 'complete_name desc'
    _inherit=['mail.thread']

    name = fields.Char('name')
    complete_name =fields.Char("Complete Name", compute="_complete_name", store=True)
    date_pp = fields.Date('Date')
    type_location = fields.Char('Location')
    pic_id = fields.Many2one('res.users','Created By')
    assign_to = fields.Many2one('res.users','Approver by')
    location = fields.Char('Location')
    origin = fields.Char('Source Purchase Request')
    partner_id = fields.Many2one('res.partner')
    company_id = fields.Many2one('res.company','Company')
    requisition_id = fields.Many2one('purchase.requisition','Purchase Requisition')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Send QCF'),
        ('confirm2','Send QCF RO'),
        ('approve','Approval Finance'),
        ('approve1', 'Approval GM Finance'),
        ('approve2','Approval Director'),
        ('approve3','Approval President Director'),
        ('approve4','Approval head of the representative office'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled')], string="State",store=True,track_visibility='onchange')
    remarks = fields.Text('Remarks')
    reject_reason = fields.Text('Reject Reason')
    line_remarks = fields.Integer(compute='_compute_line_remarks')
    tracking_approval_ids = fields.One2many('tracking.approval','owner_id','Tracking Approval List')
    purchase_line_ids = fields.One2many('purchase.order.line','comparison_id','Order Line')
    quotation_comparison_line_ids = fields.One2many('quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids2 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids3 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids4 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids5 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids6 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids7 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids8 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids9 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')
    v_quotation_comparison_line_ids10 = fields.One2many('v.quotation.comparison.form.line','qcf_id','Comparison Line')


    _defaults = {
        'state' : 'draft'
    }

    @api.multi
    def generated_po(self):
        po_lines = self.env['purchase.requisition'].search([('id','=',self.requisition_id.id)])
        po_lines.generate_po()

    @api.multi
    def create(self,vals, context=None):
        vals['name']=self.env['ir.sequence'].next_by_code('quotation.comparison.form')
        res=super(QuotationComparisonForm, self).create(vals)
        return res

    @api.multi
    def _get_purchase_request(self):
        #get Purchase.request model
        purchase_request = self.env['purchase.request'].search([('complete_name','like',self.origin)])
        return purchase_request
    
    @api.multi
    def _get_max_price(self):
        purchase_request_a = self.env['purchase.requisition'].search([('id','=',self.requisition_id.id)]).purchase_ids
        price = max(purchase.amount_total for purchase in purchase_request_a)
        return price

    @api.multi
    def _get_price_low(self):
        #get Minimal price from purchase params for Quotation comparison Form
        price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])
        price = min(price.value_params for price in price_standard)
        return float(price)

    @api.multi
    def _get_price_mid(self):
        #get middle price from purchase params for Quotation comparison Form
        arrMid = []
        price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])
        for price in price_standard:
            arrMid.append(price.value_params)
        price = arrMid[1]
        return float(price)
    
    @api.multi
    def _get_price_high(self):
        #get Maximal price from purchase params for Quotation comparison Form
        price_standard = self.env['purchase.params.setting'].search([('name','=',self._name)])
        price = max(price.value_params for price in price_standard)
        return float(price)

    @api.one
    @api.depends('name','date_pp','company_id','type_location')
    def _complete_name(self):
        """ Forms complete name of location from parent category to child category.
        """
        fmt = '%Y-%m-%d'

        if self.name and self.date_pp and self.company_id.code and self.type_location:
            date = self.date_pp
            conv_date = datetime.strptime(str(date), fmt)
            month = conv_date.month
            year = conv_date.year

            #change integer to roman
            if type(month) != type(1):
                raise TypeError, "expected integer, got %s" % type(month)
            if not 0 < month < 4000:
                raise ValueError, "Argument must be between 1 and 3999"
            ints = (1000, 900,  500, 400, 100,  90, 50,  40, 10,  9,   5,  4,   1)
            nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
            result = ""
            for i in range(len(ints)):
              count = int(month / ints[i])
              result += nums[i] * count
              month -= ints[i] * count
            month = result

            self.complete_name = self.name + '/' \
                                 + self.company_id.code+'-'\
                                 +'QCF'+'/'\
                                 +str(self.type_location)+'/'+str(month)+'/'+str(year)
        else:
            self.complete_name = self.name

        return True

    @api.multi
    @api.depends('line_remarks')
    def _compute_line_remarks(self):
        self.env.cr.execute('select count(partner_id) from(select partner_id from quotation_comparison_form_line where qcf_id = %d group by partner_id)a' %(self.id))
        line = self.env.cr.fetchone()[0]
        self.line_remarks = line

    @api.multi
    def print_qcf(self):
        return self.env['report'].get_action(self, 'purchase_indonesia.report_quotation_comparison_form_document')

    @api.multi
    def action_send(self):
        if self._get_purchase_request().code == 'KPST':
            self.write({'state' : 'confirm'})
        elif self._get_purchase_request().code in ['KOKB','KPWK']:
            self.write({'state' : 'confirm2'})
        return True

    @api.multi
    def button_draft(self):
        for rec in self:
            rec.state = 'draft'
        return True

    @api.multi
    def action_confirm(self):
        """ Confirms QCF.
        """
        self._get_value_purchase_order_line()
        self.write({'state' : 'approve','assign_to':self._get_procurement_finance()})



    @api.multi
    def action_confirm2(self):
        """ Confirms QCF.
        """
        if self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() < self._get_price_low():
            self.write({'state' : 'approve4','assign_to':self._get_user_ro_manager()})
        elif self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() >= self._get_price_low():
            self.write({'state' : 'approve4','assign_to':self._get_user_ro_manager()})
        return True

    @api.multi
    def action_approve(self):
        if self._get_purchase_request().code == 'KPST' and self._get_max_price() < self._get_price_low():
            self.write({'state' : 'done'})
            self.generated_po()
        elif self._get_purchase_request().code == 'KPST' and self._get_max_price() > self._get_price_low():
            self.write({'state' : 'approve1','assign_to':self._get_division_finance()})

    @api.multi
    def action_approve1(self):
        if self._get_purchase_request().code == 'KPST' and self._get_max_price() < self._get_price_mid() or self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() < self._get_price_mid():
            self.write({'state' : 'done'})
            self.generated_po()
        elif self._get_purchase_request().code == 'KPST' and self._get_max_price() >= self._get_price_mid() or self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() >= self._get_price_mid():
            self.write({'state' : 'approve2','assign_to':self._get_director()})

    @api.multi
    def action_approve2(self):
        if self._get_purchase_request().code == 'KPST' and self._get_max_price() >= self._get_price_mid() and self._get_max_price() < self._get_price_high() or self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() >= self._get_price_mid() and self._get_max_price() < self._get_price_high():
            self.write({'state' : 'done'})
            self.generated_po()
        elif self._get_purchase_request().code == 'KPST' and self._get_max_price() >= self._get_price_high() or self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() >= self._get_price_high():
            self.write({'state' : 'approve3','assign_to':self._get_president_director()})

    @api.multi
    def action_approve3(self):
        self.write({'state': 'done'})
        self.generated_po()
        return True

    @api.multi
    def action_approve4(self):
        if self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() < self._get_price_low():
            self.write({'state' : 'done'})
            self.generated_po()
        elif self._get_purchase_request().code in ['KOKB','KPWK'] and self._get_max_price() >= self._get_price_mid():
            self.write({'state' : 'approve1','assign_to':self._get_division_finance()})
        return True

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    @api.multi
    def action_reject(self,):
        self.write({'state': 'reject'})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def tracking_approval(self):
        user= self.env['res.users'].browse(self.env.uid)
        employee = self.env['hr.employee'].search([('user_id','=',user.id)]).name_related
        current_date=str(datetime.now().today())
        # datetimeval=datetime.strptime(current_date, "%Y-%m-%d %H:%M:%S")
        tracking_data = {
            'owner_id': self.id,
            'state' : self.state,
            'name_user' : employee,
            'datetime'  :current_date
        }
        self.env['tracking.approval'].create(tracking_data)

    @api.multi
    def open_product_line(self,ids,context=None):
        """ This opens product line view to view all lines from the different quotations, groupby default by product and partner to show comparaison
            between vendor price
            @return: the product line tree view
        """
        if context is None:
            context = {}
        res = self.env['ir.actions.act_window'].for_xml_id('purchase_requisition', 'purchase_line_tree', context=context)
        res['context'] = context
        po_lines = self.env['purchase.requisition'].search([('id','=',self.requisition_id.id)]).po_line_ids
        requistion_id = self.requisition_id.id
        res['context'] = {
            'search_default_groupby_product': True,
            'search_default_hide_cancelled': True,
            'tender_id' : requistion_id,
        }
        res['domain'] = [('id', 'in', [line.id for line in po_lines])]
        return res

    @api.multi
    def _get_value_purchase_order_line(self):
        arrOrderLine = []
        remarks = ''
        v_remarks = ''
        goods_name = ''
        vendor_name = ''
        payment_term = ''
        goods_price = ''
        delivery_term = ''
        incoterm = ''

        for item in self:

            order_line = item.env['purchase.order.line'].search([('comparison_id','=',item.id),('trigger_state','=',True)])

            for record in order_line:
                arrOrderLine.extend((record.product_id.name,record.product_qty,
                                     record.price_unit,record.partner_id.name))

                goods_name = record.product_id.name
                vendor_name = record.partner_id.name
                goods_price = str(record.price_unit)

                purchase = item.env['purchase.order'].search([('id','=',record.order_id.id)])
                for record in purchase:
                    arrOrderLine.extend((record.delivery_term,record.incoterm_id.name,
                                         record.payment_term_id.name))

                    delivery_term = record.delivery_term
                    incoterm = record.incoterm_id.name
                    payment_term = record.payment_term_id.name

                v_remarks =  '* Item dengan nama barang '+' '+ goods_name \
                             +' Vendor yang di pilih adalah '+' '+vendor_name \
                             +' karena Kondisi Barang '+delivery_term\
                             +' memberikan harga kompetitif dengan harga '+goods_price\
                             +' dengan klausul pembayaran '+payment_term\
                             +' incoterm bertipe ' + incoterm\
                             +'\n'+'\n'
                remarks = remarks + v_remarks

            item.remarks = remarks


class QuotationComparisonFormLine(models.Model):

    _name = 'quotation.comparison.form.line'
    _description = 'Quotation Comparison Line'
    _auto = False
    _order = 'req_id'

    id = fields.Integer()
    rownum = fields.Integer()
    cheapest = fields.Integer()
    req_id = fields.Many2one('purchase.requisition')
    qcf_id = fields.Many2one('quotation.comparison.form')
    company_id = fields.Many2one('res.company','Company')
    product_id = fields.Many2one('product.product','Product')
    qty_request = fields.Float('Quantity Request')
    product_uom = fields.Many2one('product.uom','Unit Of Measurement')
    partner_id = fields.Many2one('res.partner','Vendor')
    price_unit = fields.Float('Price Unit')
    price_subtotal = fields.Float('Price Subtotal')
    amount_untaxed = fields.Float('Amount Untaxed')
    price_tax = fields.Float('Price Tax')
    amount_total = fields.Float('Amount Total')
    payment_term_id = fields.Many2one('account.payment.term','Payment Term')
    date_planned = fields.Datetime('Planned Date')
    incoterm_id = fields.Many2one('stock.incoterms','Incoterms')
    delivery_term = fields.Char('Delivery Term')
    po_des_all_name = fields.Text('Description')


    def init(self, cr):
        cr.execute("""create or replace view quotation_comparison_form_line as
                        select row_number() over() id,qcf_id,
                            com_id company_id,req_id,
                            po_pol_all.product_id,
                            row_number() over (partition by req_id,po_pol_all.product_id order by po_pol_all.product_id asc) rownum,
                            qty_request,
                            product_uom,
                            part_id partner_id,
                            price_unit,
                            price_subtotal,
                            amount_untaxed,
                            price_tax,
                            amount_total,
                            payment_term_id,date_planned,incoterm_id,delivery_term,
                            po_pol_min.cheapest,po_des_all_name from
                    (
                    select pol_des_name po_des_all_name,qcf.id qcf_id,qcf.requisition_id req_id,* from quotation_comparison_form qcf
                    inner join (
                        select row_number() over() id,po.company_id com_id,po.partner_id part_id,pol.pol_name pol_des_name,*
                            from purchase_order po inner join (
                                select name pol_name,* from purchase_order_line
                                    )pol on po.id = pol.order_id and po.requisition_id is not null
                                    )qcf_po on qcf.requisition_id = qcf_po.requisition_id
                            )po_pol_all
                        inner join
                        (
                            select requisition_id, product_id, min(price_subtotal) cheapest
                            from (
                                select * from purchase_order po inner join (
                                    select * from purchase_order_line
                                )pol on po.id = pol.order_id and po.requisition_id is not null
                            )po_pol group by po_pol.requisition_id, product_id
                        ) po_pol_min
                        on po_pol_all.req_id = po_pol_min.requisition_id and po_pol_all.product_id = po_pol_min.product_id
                        """)


class ViewQuotationComparison(models.Model):

    _name = 'v.quotation.comparison.form.line'
    _description = 'Quotation Comparison Line'
    _auto = False
    _order = 'isheader asc'


    id = fields.Integer()
    isheader = fields.Integer()
    grand_total_label = fields.Char(compute='_is_grand_total_label')
    qcf_id = fields.Many2one('quotation.comparison.form')
    req_id = fields.Many2one('purchase.requisition')
    product_id = fields.Many2one('product.product','Product')
    last_price = fields.Float('Last Price')
    last_price_char = fields.Char('Last Price')
    write_date = fields.Datetime('Last Date PO')
    qty_request = fields.Char('Quantity Request')
    product_uom = fields.Many2one('product.uom','Unit Of Measurement')
    vendor1 = fields.Char('Vendor')
    vendor2 = fields.Char('Vendor')
    vendor3 = fields.Char('Vendor')
    vendor4 = fields.Char('Vendor')
    vendor5 = fields.Char('Vendor')
    vendor6 = fields.Char('Vendor')
    vendor7 = fields.Char('Vendor')
    vendor8 = fields.Char('Vendor')
    vendor9 = fields.Char('Vendor')
    vendor10 = fields.Char('Vendor')
    po_des_all_name = fields.Text('Description')
    hide = fields.Boolean()

    def init(self, cr):
        cr.execute("""create or replace view v_quotation_comparison_form_line as
select qcf_line.*, last_price.last_price, last_price.write_date, '' last_price_char from (
                        select row_number() over() id,vqcf.*,qcf.id qcf_id from (
                                                            select * from (
                                        select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,max(vendor3) vendor3,max(vendor4) vendor4,max(vendor5) vendor5,max(vendor6) vendor6,max(vendor7) vendor7,max(vendor8) vendor8,max(vendor9) vendor9,max(vendor10) vendor10,cast('' as varchar) po_des_all_name,2 isheader from (
                                            SELECT r.req_id,r.product_id,qty_request,product_uom,
                                                     MAX(CASE WHEN r.rownum = 1 THEN r.name ELSE NULL END) AS "vendor1",
                                                     MAX(CASE WHEN r.rownum = 2 THEN r.name ELSE NULL END) AS "vendor2",
                                                     MAX(CASE WHEN r.rownum = 3 THEN r.name ELSE NULL END) AS "vendor3",
                                                     MAX(CASE WHEN r.rownum = 4 THEN r.name ELSE NULL END) AS "vendor4",
                                                     MAX(CASE WHEN r.rownum = 5 THEN r.name ELSE NULL END) AS "vendor5",
                                                     MAX(CASE WHEN r.rownum = 6 THEN r.name ELSE NULL END) AS "vendor6",
                                                     MAX(CASE WHEN r.rownum = 7 THEN r.name ELSE NULL END) AS "vendor7",
                                                     MAX(CASE WHEN r.rownum = 8 THEN r.name ELSE NULL END) AS "vendor8",
                                                     MAX(CASE WHEN r.rownum = 9 THEN r.name ELSE NULL END) AS "vendor9",
                                                     MAX(CASE WHEN r.rownum = 10 THEN r.name ELSE NULL END) AS "vendor10"
                                                FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
                                                  select qcfl_rn.id rownum,company_id,po_des_all_name,
                                                    qcfl_rn.req_id,qcfl_rn.partner_id,
                                                    product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from quotation_comparison_form_line qcfl inner join (
                                                                select row_number() over(PARTITION BY req_id
                                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
                                                                            from  quotation_comparison_form_line
                                                                            group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
                                                )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
                                            GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
                                        )h group by req_id)header
                                           union all
                                         select * from (
                                           SELECT r.req_id,r.product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast(qty_request as varchar) qty_request,product_uom,
                                                 MAX(CASE WHEN r.rownum = 1 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor1",
                                                 MAX(CASE WHEN r.rownum = 2 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor2",
                                                 MAX(CASE WHEN r.rownum = 3 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor3",
                                                 MAX(CASE WHEN r.rownum = 4 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor4",
                                                 MAX(CASE WHEN r.rownum = 5 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor5",
                                                 MAX(CASE WHEN r.rownum = 6 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor6",
                                                 MAX(CASE WHEN r.rownum = 7 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor7",
                                                 MAX(CASE WHEN r.rownum = 8 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor8",
                                                 MAX(CASE WHEN r.rownum = 9 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor9",
                                                 MAX(CASE WHEN r.rownum = 10 THEN CAST(r.price_unit as varchar) ELSE NULL END) AS "vendor10",cast(max(po_des_all_name)as varchar) po_des_all_name,3 isheader
                                            FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
                                              select qcfl_rn.id rownum,company_id,po_des_all_name,
                                                qcfl_rn.req_id,qcfl_rn.partner_id,
                                                product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from quotation_comparison_form_line qcfl inner join (
                                                            select row_number() over(PARTITION BY req_id
                                                                        ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
                                                                        from  quotation_comparison_form_line
                                                                        group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
                                            )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
                                        GROUP BY r.product_id,r.req_id,qty_request,product_uom,po_des_all_name  order by req_id asc )content
                                        union all
                                        select * from (
                                        select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,cast(sum(vendor1) as varchar) vendor1,cast(sum(vendor2) as varchar) vendor2,cast(sum(vendor3) as varchar) vendor3,cast(sum(vendor4) as varchar) vendor4,cast(sum(vendor5) as varchar) vendor5,cast(sum(vendor6) as varchar) vendor6,cast(sum(vendor7) as varchar) vendor7,cast(sum(vendor8) as varchar) vendor8,cast(sum(vendor9) as varchar) vendor9,cast(sum(vendor10) as varchar) vendor10,cast('' as varchar) po_des_all_name,4 isheader from (
                                            SELECT r.req_id,r.product_id,qty_request,product_uom,
                                                     MAX(CASE WHEN r.rownum = 1 THEN r.price_subtotal ELSE NULL END) AS "vendor1",
                                                     MAX(CASE WHEN r.rownum = 2 THEN r.price_subtotal ELSE NULL END) AS "vendor2",
                                                     MAX(CASE WHEN r.rownum = 3 THEN r.price_subtotal ELSE NULL END) AS "vendor3",
                                                     MAX(CASE WHEN r.rownum = 4 THEN r.price_subtotal ELSE NULL END) AS "vendor4",
                                                     MAX(CASE WHEN r.rownum = 5 THEN r.price_subtotal ELSE NULL END) AS "vendor5",
                                                     MAX(CASE WHEN r.rownum = 6 THEN r.price_subtotal ELSE NULL END) AS "vendor6",
	                                                 MAX(CASE WHEN r.rownum = 7 THEN r.price_subtotal ELSE NULL END) AS "vendor7",
	                                                 MAX(CASE WHEN r.rownum = 8 THEN r.price_subtotal ELSE NULL END) AS "vendor8",
	                                                 MAX(CASE WHEN r.rownum = 9 THEN r.price_subtotal ELSE NULL END) AS "vendor9",
	                                                 MAX(CASE WHEN r.rownum = 10 THEN r.price_subtotal ELSE NULL END) AS "vendor10"
                                                FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
                                                  select qcfl_rn.id rownum,company_id,
                                                    qcfl_rn.req_id,qcfl_rn.partner_id,po_des_all_name,
                                                    product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from quotation_comparison_form_line qcfl inner join (
                                                                select row_number() over(PARTITION BY req_id
                                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
                                                                            from  quotation_comparison_form_line
                                                                            group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
                                                )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
                                            GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
                                        )h group by req_id)footer1
                                        union all
                                        select * from (
                                        select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,cast(sum(vendor1) as varchar) vendor1,cast(sum(vendor2) as varchar) vendor2,cast(sum(vendor3) as varchar) vendor3,cast(sum(vendor4) as varchar) vendor4,cast(sum(vendor5) as varchar) vendor5,
                                        cast(sum(vendor6) as varchar) vendor6,cast(sum(vendor7) as varchar) vendor7,
                                        cast(sum(vendor8) as varchar) vendor8,cast(sum(vendor9) as varchar) vendor9,
                                        cast(sum(vendor10) as varchar) vendor10,cast('' as varchar) po_des_all_name,5 isheader from (
                                            SELECT r.req_id,r.product_id,qty_request,product_uom,
                                                     MAX(CASE WHEN r.rownum = 1 THEN r.price_tax ELSE NULL END) AS "vendor1",
                                                     MAX(CASE WHEN r.rownum = 2 THEN r.price_tax ELSE NULL END) AS "vendor2",
                                                     MAX(CASE WHEN r.rownum = 3 THEN r.price_tax ELSE NULL END) AS "vendor3",
                                                     MAX(CASE WHEN r.rownum = 4 THEN r.price_tax ELSE NULL END) AS "vendor4",
                                                     MAX(CASE WHEN r.rownum = 5 THEN r.price_tax ELSE NULL END) AS "vendor5",
                                                     MAX(CASE WHEN r.rownum = 6 THEN r.price_tax ELSE NULL END) AS "vendor6",
                                                     MAX(CASE WHEN r.rownum = 7 THEN r.price_tax ELSE NULL END) AS "vendor7",
                                                     MAX(CASE WHEN r.rownum = 8 THEN r.price_tax ELSE NULL END) AS "vendor8",
                                                     MAX(CASE WHEN r.rownum = 9 THEN r.price_tax ELSE NULL END) AS "vendor9",
                                                     MAX(CASE WHEN r.rownum = 10 THEN r.price_tax ELSE NULL END) AS "vendor10"
                                                FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
                                                  select qcfl_rn.id rownum,company_id,po_des_all_name,
                                                    qcfl_rn.req_id,qcfl_rn.partner_id,
                                                    product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from quotation_comparison_form_line qcfl inner join (
                                                                select row_number() over(PARTITION BY req_id
                                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
                                                                            from  quotation_comparison_form_line
                                                                            group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
                                                )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
                                            GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
                                        )h group by req_id)footer2
                                        union all
                                        select * from (
                                        select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,
                                        cast(max(vendor1) as varchar) vendor1,cast(max(vendor2) as varchar) vendor2,
                                        cast(max(vendor3) as varchar) vendor3,cast(max(vendor4) as varchar) vendor4,
                                        cast(max(vendor5) as varchar) vendor5,cast(max(vendor6) as varchar) vendor6,
                                        cast(max(vendor7) as varchar) vendor7,cast(max(vendor8) as varchar) vendor8,
                                        cast(max(vendor9) as varchar) vendor9,cast(max(vendor10) as varchar) vendor10,
                                        cast('' as varchar) po_des_all_name,6 isheader from (
                                            SELECT r.req_id,r.product_id,qty_request,product_uom,
                                                     MAX(CASE WHEN r.rownum = 1 THEN r.amount_total ELSE NULL END) AS "vendor1",
                                                     MAX(CASE WHEN r.rownum = 2 THEN r.amount_total ELSE NULL END) AS "vendor2",
                                                     MAX(CASE WHEN r.rownum = 3 THEN r.amount_total ELSE NULL END) AS "vendor3",
                                                     MAX(CASE WHEN r.rownum = 4 THEN r.amount_total ELSE NULL END) AS "vendor4",
                                                     MAX(CASE WHEN r.rownum = 5 THEN r.amount_total ELSE NULL END) AS "vendor5",
                                                     MAX(CASE WHEN r.rownum = 6 THEN r.amount_total ELSE NULL END) AS "vendor6",
                                                     MAX(CASE WHEN r.rownum = 7 THEN r.amount_total ELSE NULL END) AS "vendor7",
                                                     MAX(CASE WHEN r.rownum = 8 THEN r.amount_total ELSE NULL END) AS "vendor8",
                                                     MAX(CASE WHEN r.rownum = 9 THEN r.amount_total ELSE NULL END) AS "vendor9",
                                                     MAX(CASE WHEN r.rownum = 10 THEN r.amount_total ELSE NULL END) AS "vendor10"
                                                FROM  (select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,amount_total,price_tax,payment_term_id,incoterm_id,delivery_term,po_des_all_name from (
                                                  select qcfl_rn.id rownum,company_id,po_des_all_name,
                                                    qcfl_rn.req_id,qcfl_rn.partner_id,
                                                    product_id,price_unit,qty_request,product_uom,amount_total,price_tax,payment_term_id,incoterm_id,delivery_term from quotation_comparison_form_line qcfl inner join (
                                                                select row_number() over(PARTITION BY req_id
                                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
                                                                            from  quotation_comparison_form_line
                                                                            group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
                                                )con_qcfl_rn inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id) r
                                            GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
                                        )h group by req_id)footer
                                        union all
                                        select * from (
                                        select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,max(vendor3) vendor3,
                                        max(vendor4) vendor4,max(vendor5) vendor5,
                                        max(vendor6) vendor6,max(vendor7) vendor7,
                                        max(vendor8) vendor8,max(vendor9) vendor9,
                                        max(vendor10) vendor10,cast('' as varchar) po_des_all_name,7 isheader from (
                                            SELECT r.req_id,r.product_id,qty_request,product_uom,
                                                     MAX(CASE WHEN r.rownum = 1 THEN r.name_term ELSE NULL END) AS "vendor1",
                                                     MAX(CASE WHEN r.rownum = 2 THEN r.name_term ELSE NULL END) AS "vendor2",
                                                     MAX(CASE WHEN r.rownum = 3 THEN r.name_term ELSE NULL END) AS "vendor3",
                                                     MAX(CASE WHEN r.rownum = 4 THEN r.name_term ELSE NULL END) AS "vendor4",
                                                     MAX(CASE WHEN r.rownum = 5 THEN r.name_term ELSE NULL END) AS "vendor5",
                                                     MAX(CASE WHEN r.rownum = 6 THEN r.name_term ELSE NULL END) AS "vendor6",
                                                     MAX(CASE WHEN r.rownum = 7 THEN r.name_term ELSE NULL END) AS "vendor7",
                                                     MAX(CASE WHEN r.rownum = 8 THEN r.name_term ELSE NULL END) AS "vendor8",
                                                     MAX(CASE WHEN r.rownum = 9 THEN r.name_term ELSE NULL END) AS "vendor9",
                                                     MAX(CASE WHEN r.rownum = 10 THEN r.name_term ELSE NULL END) AS "vendor10"
                                                FROM  (
                                                select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,name_term,name_inco,delivery_term,po_des_all_name from (
                                                  select qcfl_rn.id rownum,company_id,po_des_all_name,
                                                    qcfl_rn.req_id,qcfl_rn.partner_id,
                                                    product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from quotation_comparison_form_line qcfl inner join (
                                                                select row_number() over(PARTITION BY req_id
                                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
                                                                            from  quotation_comparison_form_line
                                                                            group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
                                                )con_qcfl_rn
                                                			 inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id
                                                			 left join (select apt.id apt_id,name name_term from account_payment_term apt)payterm on con_qcfl_rn.payment_term_id = payterm.apt_id
                                                			 left join (select id si_id , name name_inco from stock_incoterms si)incoterm on con_qcfl_rn.incoterm_id = incoterm.si_id
                                                			 ) r
                                            GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
                                        )h group by req_id)paymentterm
                                        union all
                                        select * from (
                                        select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,
                                        max(vendor3) vendor3,max(vendor4) vendor4,max(vendor5) vendor5,  max(vendor6) vendor6,max(vendor7) vendor7,
                                        max(vendor8) vendor8,max(vendor9) vendor9,
                                        max(vendor10) vendor10,cast('' as varchar) po_des_all_name,8 isheader from (
                                            SELECT r.req_id,r.product_id,qty_request,product_uom,
                                                     MAX(CASE WHEN r.rownum = 1 THEN r.delivery_term ELSE NULL END) AS "vendor1",
                                                     MAX(CASE WHEN r.rownum = 2 THEN r.delivery_term ELSE NULL END) AS "vendor2",
                                                     MAX(CASE WHEN r.rownum = 3 THEN r.delivery_term ELSE NULL END) AS "vendor3",
                                                     MAX(CASE WHEN r.rownum = 4 THEN r.delivery_term ELSE NULL END) AS "vendor4",
                                                     MAX(CASE WHEN r.rownum = 5 THEN r.delivery_term ELSE NULL END) AS "vendor5",
                                                     MAX(CASE WHEN r.rownum = 6 THEN r.delivery_term ELSE NULL END) AS "vendor6",
                                                     MAX(CASE WHEN r.rownum = 7 THEN r.delivery_term ELSE NULL END) AS "vendor7",
                                                     MAX(CASE WHEN r.rownum = 8 THEN r.delivery_term ELSE NULL END) AS "vendor8",
                                                     MAX(CASE WHEN r.rownum = 9 THEN r.delivery_term ELSE NULL END) AS "vendor9",
                                                     MAX(CASE WHEN r.rownum = 10 THEN r.delivery_term ELSE NULL END) AS "vendor10"
                                                FROM  (
                                                select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,name_term,name_inco,delivery_term,po_des_all_name from (
                                                  select qcfl_rn.id rownum,company_id,po_des_all_name,
                                                    qcfl_rn.req_id,qcfl_rn.partner_id,
                                                    product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from quotation_comparison_form_line qcfl inner join (
                                                                select row_number() over(PARTITION BY req_id
                                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
                                                                            from  quotation_comparison_form_line
                                                                            group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
                                                )con_qcfl_rn
                                                			 inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id
                                                			 left join (select apt.id apt_id,name name_term from account_payment_term apt)payterm on con_qcfl_rn.payment_term_id = payterm.apt_id
                                                			 left join (select id si_id , name name_inco from stock_incoterms si)incoterm on con_qcfl_rn.incoterm_id = incoterm.si_id
                                                ) r
                                            GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
                                        )h group by req_id)deliverydate
                                        union all
                                        select * from (
                                        select req_id,0 product_id,cast(0 as boolean) hide,cast('' as varchar) grand_total_label,cast('' as varchar) qty_request,0 product_uom,max(vendor1) vendor1,max(vendor2) vendor2,
                                        max(vendor3) vendor3,max(vendor4) vendor4,max(vendor5) vendor5, max(vendor6) vendor6,max(vendor7) vendor7,
                                        max(vendor8) vendor8,max(vendor9) vendor9,
                                        max(vendor10) vendor10,cast('' as varchar) po_des_all_name,9 isheader from (
                                            SELECT r.req_id,r.product_id,qty_request,product_uom,
                                                     MAX(CASE WHEN r.rownum = 1 THEN r.name_inco ELSE NULL END) AS "vendor1",
                                                     MAX(CASE WHEN r.rownum = 2 THEN r.name_inco ELSE NULL END) AS "vendor2",
                                                     MAX(CASE WHEN r.rownum = 3 THEN r.name_inco ELSE NULL END) AS "vendor3",
                                                     MAX(CASE WHEN r.rownum = 4 THEN r.name_inco ELSE NULL END) AS "vendor4",
                                                     MAX(CASE WHEN r.rownum = 5 THEN r.name_inco ELSE NULL END) AS "vendor5",
                                                     MAX(CASE WHEN r.rownum = 6 THEN r.name_inco ELSE NULL END) AS "vendor6",
                                                     MAX(CASE WHEN r.rownum = 7 THEN r.name_inco ELSE NULL END) AS "vendor7",
                                                     MAX(CASE WHEN r.rownum = 8 THEN r.name_inco ELSE NULL END) AS "vendor8",
                                                     MAX(CASE WHEN r.rownum = 9 THEN r.name_inco ELSE NULL END) AS "vendor9",
                                                     MAX(CASE WHEN r.rownum = 10 THEN r.name_inco ELSE NULL END) AS "vendor10"
                                                FROM  (
                                                select rownum,name,req_id,product_id,qty_request,product_uom,price_unit,price_subtotal,price_tax,name_term,name_inco,delivery_term,po_des_all_name from (
                                                  select qcfl_rn.id rownum,company_id,po_des_all_name,
                                                    qcfl_rn.req_id,qcfl_rn.partner_id,
                                                    product_id,price_unit,qty_request,product_uom,price_subtotal,price_tax,payment_term_id,incoterm_id,delivery_term from quotation_comparison_form_line qcfl inner join (
                                                                select row_number() over(PARTITION BY req_id
                                                                            ORDER BY partner_id DESC NULLS LAST) id,partner_id,req_id
                                                                            from  quotation_comparison_form_line
                                                                            group by partner_id,req_id order by req_id desc)qcfl_rn on qcfl.partner_id = qcfl_rn.partner_id and qcfl.req_id = qcfl_rn.req_id
                                                )con_qcfl_rn
                                                			 inner join (select id,name from res_partner)partner on con_qcfl_rn.partner_id = partner.id
                                                			 left join (select apt.id apt_id,name name_term from account_payment_term apt)payterm on con_qcfl_rn.payment_term_id = payterm.apt_id
                                                			 left join (select id si_id , name name_inco from stock_incoterms si)incoterm on con_qcfl_rn.incoterm_id = incoterm.si_id
                                                			 ) r
                                            GROUP BY r.product_id,r.req_id,qty_request,product_uom  order by req_id
                                        )h group by req_id)franco
                                        )vqcf inner join quotation_comparison_form qcf on vqcf.req_id = qcf.requisition_id)qcf_line
                                        left join
                                        (select rank_id,product_id,last_price,write_date from(
        								select row_number() over(PARTITION BY po_id
                                                                            ORDER BY write_date DESC NULLS LAST) rank_id,* from (
        								select po.id po_id,order_id,product_id,price_unit last_price,state,write_date  from purchase_order po left join (
        									select id,order_id,product_id,price_total,price_unit,product_qty from purchase_order_line)pol on po.id = pol.order_id
        									where state = 'done' group by po.id,order_id,product_id,price_total,price_unit,product_qty )a )b where b.rank_id = 1
        									)last_price on qcf_line.product_id = last_price.product_id""")


    @api.multi
    @api.depends('qty_request')
    def _is_grand_total_label(self):
        for rec in self :
            if rec.isheader == 1:
                rec.po_des_all_name = ''
                rec.last_price = ''
                rec.write_date = ''
            elif rec.isheader == 2:
                rec.qty_request = 'xxx'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 3:
                rec.po_des_all_name = ''+rec.po_des_all_name
                rec.grand_total_label = ''
                rec.qty_request = str(rec.qty_request)
                rec.last_price_char = str(rec.last_price)
            elif rec.isheader == 4:
                rec.qty_request = 'Sub Total'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 5:
                rec.qty_request = 'Tax %'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 6:
                rec.qty_request = 'Grand Total'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 7:
                rec.qty_request = 'TOP'
                rec.po_des_all_name = ''
                rec.last_price = ''
                rec.write_date = ''
            elif rec.isheader == 8:
                rec.qty_request = 'Delivery'
                rec.po_des_all_name = ''
                rec.write_date = ''
            elif rec.isheader == 9:
                rec.qty_request = 'Incoterm/FRANCO'
                rec.po_des_all_name = ''
                rec.write_date = ''

class StateProcurementProcess(models.Model):

    _name = 'state.procurement.process'
    _description = 'Tracking State From Purchase Request'
    _auto = False
    _order = 'pr_complete_name desc'


    id = fields.Char('id')
    pr_id = fields.Integer('purchase request')
    date_pr = fields.Date('Purchase Request Date')
    state = fields.Char('Purchase Request state')
    pr_complete_name = fields.Char('Purchase Request Complete Name')
    tender_complete_name = fields.Char('Tender Complete Name')
    tender_state = fields.Char('Tender State')
    qcf_complete_name = fields.Char('Qcf Complete Name')
    qcf_state = fields.Char('Qcf State')
    po_complete_name = fields.Char('Purchase Order Complete Name')
    po_state = fields.Char('Purchase Order State')
    complete_name_picking = fields.Char('GRN Complete Name')
    grn_state = fields.Char('GRN State')

    def init(self, cr):
        cr.execute(""" create or replace view state_procurement_process as
            select
                row_number() over() id,
                pr.id pr_id,pr.date_start date_pr,
                pr.state state,
                pr.complete_name pr_complete_name,
                tender.complete_name tender_complete_name,
                tender.state tender_state,qcf.complete_name qcf_complete_name,
                qcf.state qcf_state,
                po.complete_name po_complete_name,
                po.state po_state,grn.complete_name_picking,grn.state grn_state from purchase_request pr
            left join (
                select id tender_id,complete_name,origin,state from purchase_requisition
                )tender on pr.complete_name = tender.origin
            left join(
                select id,complete_name,state,origin from quotation_comparison_form
            )qcf on pr.complete_name = qcf.origin
            left join(
                select id,complete_name,state,source_purchase_request from purchase_order
            )po on pr.complete_name = po.source_purchase_request
            left join(
                select id,complete_name_picking,state,pr_source from stock_picking
                    )grn on pr.complete_name = grn.pr_source
                        """)


