# -*- coding: utf-8 -*-
from openerp import http

# class Commbaril(http.Controller):
#     @http.route('/commbaril/commbaril/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/commbaril/commbaril/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('commbaril.listing', {
#             'root': '/commbaril/commbaril',
#             'objects': http.request.env['commbaril.commbaril'].search([]),
#         })

#     @http.route('/commbaril/commbaril/objects/<model("commbaril.commbaril"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('commbaril.object', {
#             'object': obj
#         })