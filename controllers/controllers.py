# -*- coding: utf-8 -*-
# from odoo import http


# class HrHospital(http.Controller):
#     @http.route('/hr_hospital/hr_hospital', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_hospital/hr_hospital/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_hospital.listing', {
#             'root': '/hr_hospital/hr_hospital',
#             'objects': http.request.env['hr_hospital.hr_hospital'].search([]),
#         })

#     @http.route('/hr_hospital/hr_hospital/objects/<model("hr_hospital.hr_hospital"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_hospital.object', {
#             'object': obj
#         })
