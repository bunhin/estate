from openerp import models, fields, api, exceptions
from datetime import datetime, date
from openerp.exceptions import ValidationError
from dateutil.relativedelta import *
import calendar




class NurseryVehicle(models.Model):

    _inherit="fleet.vehicle"

    no_vehicle=fields.Char('')
    vehicle_type=fields.Selection([('1','Vehicle Internal'), ('2','Vehicle External')])







