# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api, exceptions


# class openacademy(models.Model):
#     _name = 'openacademy.openacademy'
#     _description = 'openacademy.openacademy'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

class Course(models.Model):
    _name='openacademy.course'
    _description='OpenAcademy Courses'

    name=fields.Char(string="Title", required=True)
    description = fields.Text()

    responsible_id = fields.Many2one('res.users', ondelete='set null', string="Responsible", index=True)

    session_ids=fields.One2many('openacademy.session', 'course_id', string="Sessions")

    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    _sql_constraints = [
        ('name_description_check',
         'CHECK(name!=description)',
         "El titulo no debe coincidir con la descripcion"),
        ('unique_name',
         'UNIQUE(name)',
         "El nombre del curso no puede reptirse"),
    ]


class Sessions(models.Model):
    _name='openacademy.session'
    _description = 'OpenAcademy Sessions'

    name=fields.Char(string="Nombre de la sesion", required=True)
    start_date=fields.Date(default=fields.Date.today)
    duration=fields.Float(digits=(6, 2), help="Duracion en dias de la sesion")
    seats=fields.Integer(string="Numero de asientos")
    active = fields.Boolean(default=True)
    color=fields.Integer()




    instructor_id = fields.Many2one('res.partner', string="Instructor",
                                    domain=['|', ('instructor', '=', True),
                                            ('category_id.name', 'ilike', "Teacher")])

    course_id = fields.Many2one('openacademy.course',ondelete='cascade', string="Course", required=True)

    attendee_ids=fields.Many2many('res.partner',string="Asistentes")
    taken_seats=fields.Integer(string="Asientos ocupados", compute='_taken_seats')

    end_date=fields.Date(string="Fecha de fin de la sesion",compute='_end_date',inverse='set_end_date')

    attendees_count=fields.Integer(string="Numero de asistentes", compute='_attendees_count', store=True)

    @api.depends('attendee_ids')
    def _attendees_count(self):
        for r in self
        r.attendees_count=len(r.attendee_ids)



    @api.depends('seats','taken_seats')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats=0.0
            else:
                r.taken_seats=((len(r.attendee_ids) / r.seats)*100)

    @api.depends('start_date', 'duration')
    def _end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.duration = (r.end_date - r.start_date).days + 1

    @api.onchange('seats','taken_seats')
    def _verify_valid_seats(self):
        if r.seats < 0.0:
            return {
                'warning':
                {
                'title': "Numero incorrecto de asientos",
                'message':"El numero de asientos no puede ser negativo"
                },
            }
        if r.seats < len(r.attendee_ids):
            return {
                'warning':
                {
                'title': "Muchos atendedores",
                'message': "El numero de asientos no cubre con la cantidad de asistentes"
                },
            }

    @api.constrains('attendee_ids','instructor_id')
    def _check_ifinstructor(self):
        for r in self:
            if r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError("El instructor se encuentra entre los asistentes")