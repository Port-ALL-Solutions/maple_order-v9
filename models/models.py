# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime


# modifier le contact (partner) de Odoo pour inclure sa région et son numéro FPAQ
class Contact(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'
	region = fields.Char(string="Region")
	fpaqNum = fields.Char(string="FPAQ num")
	siteNum = fields.Char(string="Site num")

# On modifie l'employé, spécifiquement pour l'inspecteur.  Chaque inspecteur a un numéro.  Chaque 
# inspecteur doit garder un 
# décompte de barils inspectés dans l'année.  Lorsqu'on change d'année, il faudrait remettre
# le décompte à 000...
class Inspecteur(models.Model):
	_name = 'hr.employee'
	_inherit = 'hr.employee'
	barrelCnt = fields.Integer(string="Barrel Count", default=1)
	inspectNb = fields.Integer(string="Inspector No", default=0)
		# Lorsqu'on accède l'Inspecteur, si l'année courante est différente de barrelCntYear
		# on remet le barrelCnt à 1, et on met l'année courante dans barrelCntYear
	barrelCntYear = fields.Integer(string="Barrel Count Year", default=999999)



# Purchase Order spécifique à Sirop de l'est
class Commande(models.Model):
	_name = 'mapleorder.order'
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	# on a un produit (défini dans Odoo)
	article = fields.Many2one('product.product', string="Product", required=True)
	quantity = fields.Integer(string="Quantity", required=True, default=50)
	productor = fields.Many2one('res.partner', string="Producer", required=True)
	productorName = fields.Char(compute='_get_prod_name', store=True)
	active = fields.Boolean(default=True)
	pickid = fields.Many2one('mapleorder.maplepick') # un pickup order peut pointer vers plusieurs maple order
	barrellist = fields.One2many('mapleorder.barrel', 'purchorder', string="Barrel List") # tous les barils reçus à partir de cette commande
	closed = fields.Boolean(default=False) # si la commande est maintenant refermée (complétée)
	address = fields.Char(related='productor.street', store=True)
	city  = fields.Char(related='productor.city', store=True)
	phone = fields.Char(related='productor.phone', store=True)
	buyer = fields.Selection([('Sirop de l\'Est', 'Sirop de l\'Est'), ('L.B. Maple Treat', 'L.B. Maple Treat'), ('Autre', 'Autre')], required=True, default='Sirop de l\'Est')
	customer = fields.Many2one('res.partner', string="Customer")

	pick_schedule = fields.Date(related='pickid.schedule', store=True, string="Scheduled")
	pick_driver = fields.Char(related='pickid.driverName', store=True)
	pick_barrelQty = fields.Integer(related='pickid.barrelQty', store=True)
	receivedAt = fields.Date(related='pickid.receivedAt', store=True)

	siteNum = fields.Char(related="productor.siteNum")


	@api.depends('productor')
	@api.multi
	def _init_region_val(self):
		for rec in self:
			if rec.productor != False:
				rec.region = rec.productor.region

	region = fields.Char(default=_init_region_val, compute='_init_region_val', store=True)

	notes = fields.Text()

	barrelQtyRegistered = fields.Integer(compute='compute_barrel_qty', store=True)

	warehouse = fields.Many2one('stock.warehouse')
	row = fields.Char()

	@api.onchange('row')
	@api.multi
	def  _uppercase_row(self):
		for rec in self:
			rec.row = (rec.row or "").upper()

	@api.depends('pickid')
	@api.one
	def compute_barrel_qty(self):
		count = self.env['mapleorder.barrel'].search_count([('purchorder','=',self.id)]) 
		self.barrelQtyRegistered = count

	@api.depends('productor')
	@api.one
	def _get_prod_name(self):
		if self.productor != False:
			self.productorName = self.productor.name

	@api.depends('productor')
	@api.one
	def retrieve_phone_from_partner(self):
		self.phone = self.productor.phone

	# Lorsqu'on change la quantité de barils, mettre le total à jour
	# dans l'ordre de cueillette correspondant (maplepick).  Maplepick devrait calculer
	# automatiquement, mais Odoo ne semble pas le permettre; on va l'aider
	@api.depends('quantity')
	@api.multi
	def _update_barrel_qty(self):
		for rec in self:
			if rec.pickid:	# seulement si un pickid est défini...
				pickid._compute_total_barrel()
				toto = 1

# ordre de cueillette / pick order, peut être relié à plusieurs purchase orders, avec un indicateur si reçu
class maplepick(models.Model):
	_name = 'mapleorder.maplepick'
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	active = fields.Boolean(default=True)
	driver = fields.Many2one('hr.employee')
	driverName = fields.Char(compute='_get_driver_name', store=True)
	schedule = fields.Date(default=datetime.date.today(), string="Scheduled")
	order = fields.One2many('mapleorder.order', 'pickid')
	note = fields.Text()
	completed = fields.Boolean(default=False)
	barrelQty = fields.Integer(compute='_compute_total_barrel', string="Ordered Barrel Quantity", store=True)

	# pour la réception
	warehouse = fields.Many2one('stock.warehouse')
	row = fields.Char(size=2)
	receivedBy = fields.Many2one('hr.employee', string="Received by")
	barrelReceived = fields.Integer(compute='_compute_received_barrels', string="Received Barrel Quantity", store=True)
	receivedAt = fields.Date(default=datetime.date.today(), string="Received At")
	closed = fields.Boolean(default=False) # si la commande est maintenant refermée (complétée)

	# la liste des noms des producteurs, utilisée pour le calendrier
	prods = fields.Char(compute='_compute_prod_list', store=True)

	# permettre de faire le décompte des barils lorsqu'on modifie la liste des commandes
	@api.depends('order')
	@api.one
	def _compute_total_barrel(self):
		self.barrelQty = 0
		for record in self.order:
			self.barrelQty += record.quantity

	# à partir d'un employé, trouver le nom
	@api.depends('driver')
	@api.one
	def _get_driver_name(self):
		if self.driver != False:
			self.driverName = self.driver.name

	# produire la liste des noms des producteurs (champs prods), utile pour le calendrier
	@api.depends('order')
	@api.one
	def _compute_prod_list(self):
		self.prods = ''
		for record in self.order:
			if record.productorName :
				self.prods += record.productorName
				self.prods += ','

	# fait le total des barils reçus, (bouton Calc)
	@api.one
	def eval_barrel_received(self):
		self.barrelReceived = 0
		for orders in self.order:
			orders.compute_barrel_qty()
			self.barrelReceived += orders.barrelQtyRegistered




# chacun des barils brut (non classifié) enregistrés lors de la réception
class registeredBarrel(models.Model):
	_name = 'mapleorder.barrel' 
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	active = fields.Boolean(default=True)
	tote = fields.Boolean(default=False, string="Tote?")
	processStatus = fields.Selection([('received', 'received'), ('weighted', 'weighted'), ('rated', 'rated'), ('revised', 'revised'), ('rejected', 'rejected'), ('empty', 'empty'), ('transformed', 'transformed'), ('produced', 'produced')], default='received')
	delivery = fields.Many2one('mapleorder.delivery')
	shipped = fields.Boolean(default=False)

	nameproducer = fields.Char(related='purchorder.productorName', string="Producer Name", store=True)
	purchorder = fields.Many2one('mapleorder.order', string="Purchase Orders")
	warehouse = fields.Many2one('stock.warehouse', required=True)
	article = fields.Many2one(related="purchorder.article")

	row = fields.Char(size=2)
	producerAddr = fields.Char(related='purchorder.address', store=True, string="Producer Address")
	producerCity = fields.Char(related='purchorder.city', store=True, string="Producer City")
	buyer = fields.Selection(related='purchorder.buyer', store=True)

	dateReceived = fields.Date(default=datetime.date.today(), string="Received At")
	containerState = fields.Selection([('ok', 'ok'), ('broken', 'broken'), ('replaced', 'replaced'), ('leased', 'leased')], default='ok')
	tempnumber = fields.Char()
	barrelNumber = fields.Char()
	full = fields.Boolean(default=True)

	# Règle SQL pour que les tempnumbers soient uniques
	_sql_constraints = [('tempnumb_uniq', 'unique(tempnumber)', 'Error : temporary number must be unique'),
						('sealnumb_uniq', 'unique(seal)', 'Error : seal must be unique'),
						('barrel_uniq', 'unique(barrelNumber)', 'Error : barrel number must be unique')]

	# pour s'assurer que la rangée soit toujours en majuscule 
	# pour faciliter la recherche, le classement, etc
	@api.onchange('row')
	@api.multi
	def  _uppercase_row(self):
		self.row = (self.row or "").upper()

	# recopier l'entrepot et la rangée de la commande vers le baril, lorsqu'on crée le baril
	@api.onchange('tempnumber')
	@api.one
	def eval_buyer(self):
		for rec in self.purchorder:
			if rec.warehouse != False:
				self.warehouse = rec.warehouse
				self.row = rec.row
				break


	####################################################################
	# STATUT= weighted
	grossweight = fields.Integer(default=0)
	netweight = fields.Integer(default=0)
	tare = fields.Char()	# sélection possible ?
	propriete = fields.Selection([('A','A'), ('P','P')], default="P")
	valve = fields.Boolean(string="Valve")
	site = fields.Char(related="purchorder.siteNum")
	type = fields.Char(related="article.name")
	barrelState = fields.Selection([('OK','OK'), ('leg.bosse', 'leg.bosse'), ('bosse','bosse'), ('tres bosse', 'tres bosse')], default='OK')
	genre = fields.Selection([('Galvanized', 'Galvanized'), ('Stainless', 'Stainless'), ('One-time', 'One-time'), ('Plastic', 'Plastic'), ('Other', 'Other')],default="Stainless")

	# Le statut du baril 'reçu' change (devient weighted) aussitôt qu'un poids brut est défini
	@api.onchange('grossweight')
	@api.one
	def eval_producer_name(self):
		if self.grossweight > 0 and self.processStatus == 'received' and not self.transform:
			self.processStatus = 'weighted'
		toto = 1


	##########################################################
	# STATUT = rated ou revised
	seal = fields.Char()
	flavor = fields.Char(default='1')
	default = fields.Selection([('NC', 'NC'), ('CROCHET', 'CROCHET'), ('VR', 'VR')])
	grade = fields.Selection([('DO', 'DO'), ('AM', 'AM'), ('FO', 'FO'), ('TF', 'TF')])
	brix = fields.Float(group_operator="avg")	# pour produire le valeur moyenne dans les vues, pas sur que c'est nécessaire
	lumiere = fields.Integer(group_operator="avg")
	ratedBy = fields.Many2one('hr.employee')
	ratedAt = fields.Date(default=datetime.date.today(), string="Rated At")

	# Pour qu'on puisse gérer le # de scellé, bâti a partir de l'info dans table Employé
	inspectCnt = fields.Integer(related='ratedBy.barrelCnt', store=True)
	inspectCntYear = fields.Integer(related='ratedBy.barrelCntYear', store=True)

	# Le statut du baril change (devient rated) aussitôt qu'un scellé est défini
	@api.onchange('seal')
	@api.multi
	def eval_processStatus_rated(self):
		for rec in self:
			if rec.processStatus == 'weighted' and not self.transform:
				rec.processStatus = 'rated'

	# générer le numéro de scellé
	@api.onchange('ratedBy')
	@api.one
	def def_seal_number(self):
		if self and self.ratedBy and not self.transform:
			# On va chercher la date reçue du baril; on vérifie l'année
			date = self.dateReceived
			annee = int( date[:4] )  # on prend les 4 premiers caractères, transformés en chiffres
			annee = annee % 100		# 0 à 99
			# Changement d'année, on recommence à compter à 1
			if self.inspectCntYear != annee:
				self.inspectCntYear = annee
				self.inspectCnt = 1
			prefix = self.ratedBy.inspectNb * 100 + annee
			suffixe = '%05d' % (self.ratedBy.barrelCnt)
			self.inspectCnt += 1
			self.seal = str(prefix)+'-'+suffixe

	# Le grade est calculé automatiquement à partir de la lumière
	@api.onchange('lumiere')
	@api.one
	def _def_eval_grade(self):
		if self.lumiere > 75:
			self.grade = 'DO'
		elif self.lumiere > 50:
			self.grade = 'AM'
		elif self.lumiere > 25:
			self.grade = 'FO'
		else:
			self.grade = 'TF'

	###################################################
	# STATUT = transformed pour barils source, produced pour barils 'tote'

	transform = fields.Many2one('mapleorder.transform')
	sourceBarrels = fields.Many2one('mapleorder.transform')
	inspector = fields.Many2one('hr.employee')
	inspectOn = fields.Date(default=datetime.date.today())

	# helper fields : pour permettre d'accéder aux champs de la table employé à travers inspector
	trans_inspectCnt = fields.Integer(related='inspector.barrelCnt', store=True)
	trans_inspectCntYear = fields.Integer(related='inspector.barrelCntYear', store=True)

	# Lorsqu'on rentre le nouveau poids du baril (tote) et qu'on a déjà
	# un lien vers 'transform' (mais que le seal est encore null) alors c'est qu'il faut initialiser le contenu
	@api.onchange('grossweight')
	@api.one
	def _def_init_tote(self):
		if self.transform and not self.seal :
			self.processStatus = 'produced'
			self.inspector = self.transform.transformedBy
			self.inspectOn = self.transform.transformedOn
			self.tote = True
			self.full = True
			self.lumiere = self.transform.lumieres	# valeur par défaut
			self.dateReceived = self.transform.transformedOn
			self.tempnumber = "0000"
			self.barrelNumber = "Tote"

	@api.onchange('transform', 'inspector', 'inspectOn')
	@api.one
	def createSeal(self):
			# On peut générer uniquement un numéro de scellé si on a défini un 
			# employé producteur (on a besoin de son numéro d'inspecteur)

			if self.inspector and self.inspectOn and not self.seal:

				# Générer un numéro de scellé spécial
				# On va chercher la date de transformation
				date = self.inspectOn
				annee = int( date[:4] )  # on prend les 4 premiers caractères, transformés en chiffres
				annee = annee % 100		# 0 à 99

				# On se base sur le décompte de barils du TransformedBy
				CntYear = self.inspector.barrelCntYear
				if CntYear != annee:
					# Changement d'année, on recommence à compter à 1
					# Attention bug de l'année 2100 : on ne garde que les 2 derniers chiffres de l'année
					self.trans_inspectCntYear = annee
					self.trans_inspectCnt = 1

				prefix = self.inspector.inspectNb * 100 + annee
				suffixe = '%05d' % (self.trans_inspectCnt)
				self.trans_inspectCnt += 1
				self.seal = str(prefix)+'-'+suffixe




class transformation(models.Model):
	_name = 'mapleorder.transform'

	active = fields.Boolean(default=True)
	transformedBy = fields.Many2one('hr.employee', required=True)
	transformedOn = fields.Date(default=datetime.date.today(), string="Transformed on")
	barrelList = fields.One2many('mapleorder.barrel', 'transform', string="Totes produced")
	sourceList = fields.One2many('mapleorder.barrel', 'sourceBarrels', string="Source barrels")

	brixs			= fields.Integer()
	lumieres		= fields.Float()
	grossweights	= fields.Integer()
	grades			= fields.Selection([('DO', 'DO'), ('AM', 'AM'), ('FO', 'FO'), ('TF', 'TF')])


	# Au fur et à mesure qu'on modifie la liste des barils source, on doit recalculer
	# la lumière, le Brix, etc
	@api.onchange('sourceList')
	@api.one
	def _recalc_tote_param(self):
		count = 0		# je ne sais pas comment compter le nombre d'éléments dans un One2Many
		for rec in self.sourceList:
			count+=1
			rec.transform = self
			toto = 1

		if count > 0:
			self.brixs = 0
			self.lumieres = 0
			self.grossweights = 0
			count = 0
			for rec in self.sourceList:
				count += 1
				# S'assurer que chaque baril source sache qu'il produit un/des totes
				# et indiquer qu'il est maintenant vide
				rec.sourceBarrels = self
				rec.processStatus = 'transformed'
				rec.full = False
				self.brixs += rec.brix
				self.lumieres += rec.lumiere
				self.grossweights += rec.grossweight

			self.brixs = self.brixs / count
			self.lumieres = self.lumieres / count
			if self.lumieres > 75:
				self.grades = 'DO'
			elif self.lumieres > 50:
				self.grades = 'AM'
			elif self.lumieres > 25:
				self.grades = 'FO'
			else:
				self.grades = 'TF'


	# il faut pouvoir ajouter des barils destination (totes)
	# et les initialiser avec les paramètres
	# Cette fonction est appelée par Odoo après que le tote ait été inséré
	@api.onchange('barrelList')
	@api.one
	def  _init_tote(self):
		for rec in self.barrelList:
			rec.inspector = self.transformedBy
			rec.inspectOn = self.transformedOn
			rec.createSeal()



class mapledelivery(models.Model):
	_name = 'mapleorder.delivery'
	_inherit = ['mail.thread', 'ir.needaction_mixin']

	active = fields.Boolean(default=True)

	scheduled = fields.Date(default=datetime.date.today())
	destination = fields.Many2one('res.partner')
	transport = fields.Char()
	notes = fields.Text()
	barrelList = fields.One2many('mapleorder.barrel', 'delivery')

	# Au fur et à mesure que les barils sont ajoutés dans la liste
	# les marquer d'un nouveau status
	@api.onchange('barrelList')
	@api.one
	def _mark_barrel_as_shipped(self):
		for rec in self.barrelList:
			rec.shipped = True
			rec.active = False	# Il est désormais archivé, et ne devrait plus paraitre dans les listes
			toto = 1
