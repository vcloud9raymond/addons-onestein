# -*- coding: utf-8 -*-
# Copyright 2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import datetime
from odoo.tests import common
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF
from odoo.exceptions import Warning, ValidationError


class TestLeaveHours(common.TransactionCase):
    def setUp(self):
        super(TestLeaveHours, self).setUp()

        self.leave_obj = self.env['hr.holidays']
        self.status_obj = self.env['hr.holidays.status']
        self.calendar_obj = self.env['resource.calendar']
        self.workday_obj = self.env['resource.calendar.attendance']
        self.contract_obj = self.env['hr.contract']
        self.employee_obj = self.env['hr.employee']

        self.today_start = datetime.today().replace(
            hour=8, minute=0, second=0, microsecond=0)
        self.today_end = datetime.today().replace(
            hour=18, minute=0, second=0, microsecond=0)

        today_start = self.today_start.strftime(DF)
        today_end = self.today_end.strftime(DF)

        self.calendar = self.calendar_obj.create({
            'name': 'Calendar 1',
        })

        for i in range(0, 7):
            self.workday_obj.create({
                'name': 'Day ' + str(i),
                'dayofweek': str(i),
                'hour_from': 8.0,
                'hour_to': 16.0,
                'calendar_id': self.calendar.id,
            })

        self.employee_1 = self.employee_obj.create({
            'name': 'Employee 1',
            'calendar_id': self.calendar.id,
        })
        self.employee_2 = self.employee_obj.create({
            'name': 'Employee 2',
            'calendar_id': self.calendar.id,
        })
        self.employee_3 = self.employee_obj.create({
            'name': 'Employee 3',
        })
        self.employee_4 = self.employee_obj.create({
            'name': 'Failing Employee',
            'calendar_id': self.calendar.id,
        })

        self.contract_1 = self.contract_obj.create({
            'name': 'Contract 1',
            'employee_id': self.employee_3.id,
            'wage': 2000.0,
            'working_hours': self.calendar.id,
        })

        self.status_1 = self.status_obj.create({
            'name': 'Status 1',
            'limit': True,
        })
        self.status_2 = self.status_obj.create({
            'name': 'Status 2',
            'limit': False,
        })

        self.leave_allocation_1 = self.leave_obj.create({
            'name': 'Allocation Request 1',
            'holiday_status_id': self.status_1.id,
            'holiday_type': 'employee',
            'employee_id': self.employee_1.id,
            'number_of_days_temp': 10,
            'number_of_hours_temp': 80,
            'type': 'add',
        })

        self.leave_1 = self.leave_obj.create({
            'holiday_status_id': self.status_1.id,
            'holiday_type': 'employee',
            'type': 'remove',
            'date_from': today_start,
            'date_to': today_end,
            'employee_id': self.employee_1.id,
            'number_of_hours_temp': 8,
        })

        self.leave_allocation_2 = self.leave_obj.create({
            'name': 'Allocation Request 2',
            'holiday_status_id': self.status_1.id,
            'holiday_type': 'employee',
            'employee_id': self.employee_2.id,
            'number_of_days_temp': 10,
            'type': 'add',
        })

        self.leave_2 = self.leave_obj.create({
            'holiday_status_id': self.status_1.id,
            'holiday_type': 'employee',
            'type': 'remove',
            'date_from': today_start,
            'date_to': today_end,
            'employee_id': self.employee_2.id,
        })

        self.leave_allocation_3 = self.leave_obj.create({
            'name': 'Allocation Request 3',
            'holiday_status_id': self.status_1.id,
            'holiday_type': 'employee',
            'employee_id': self.employee_3.id,
            'number_of_days_temp': 10,
            'type': 'add',
        })

        self.leave_3 = self.leave_obj.create({
            'holiday_status_id': self.status_1.id,
            'holiday_type': 'employee',
            'type': 'remove',
            'date_from': today_start,
            'date_to': today_end,
            'employee_id': self.employee_3.id,
        })

    def test_01_onchange(self):

        def test_onchange(leave, employee, allocation):
            field_onchange = leave._onchange_spec()
            self.assertEqual(field_onchange.get('employee_id'), '1')
            self.assertEqual(field_onchange.get('date_from'), '1')
            self.assertEqual(field_onchange.get('date_to'), '1')

            values = {
                'employee_id': employee.id,
                'date_from': self.today_start.strftime(DF),
                'date_to': self.today_end.strftime(DF),
            }
            if allocation:
                leave.with_context(default_type='add').onchange(
                    values, 'employee_id', field_onchange)
                leave.with_context(default_type='add').onchange(
                    values, 'date_from', field_onchange)
                leave.with_context(default_type='add').onchange(
                    values, 'date_to', field_onchange)
            else:
                leave.onchange(values, 'employee_id', field_onchange)
                leave.onchange(values, 'date_from', field_onchange)
                leave.onchange(values, 'date_to', field_onchange)

        test_list = [
            {
                'leave': self.leave_1,
                'employee': self.employee_1,
                'allocation': False,
            },
            {
                'leave': self.leave_2,
                'employee': self.employee_2,
                'allocation': False,
            },
            {
                'leave': self.leave_3,
                'employee': self.employee_3,
                'allocation': False,
            },
            {
                'leave': self.leave_allocation_1,
                'employee': self.employee_1,
                'allocation': True,
            },
            {
                'leave': self.leave_allocation_2,
                'employee': self.employee_2,
                'allocation': True,
            },
            {
                'leave': self.leave_allocation_3,
                'employee': self.employee_3,
                'allocation': True,
            },
        ]

        for test in test_list:
            test_onchange(test['leave'], test['employee'], test['allocation'])

    def test_02_onchange_fail(self):
        field_onchange = self.leave_1._onchange_spec()
        values = {
            'date_from': self.today_end.strftime(DF),
            'date_to': self.today_start.strftime(DF),
        }

        with self.assertRaises(Warning):
            self.leave_1.onchange(values, 'date_from', field_onchange)
        with self.assertRaises(Warning):
            self.leave_1.onchange(values, 'date_to', field_onchange)

        values.update({
            'employee_id': None,
            'date_from': self.today_start.strftime(DF),
            'date_to': self.today_end.strftime(DF),
        })

        self.leave_1.onchange(values, 'employee_id', field_onchange)

        with self.assertRaises(Warning):
            self.leave_1.onchange(values, 'date_from', field_onchange)
        with self.assertRaises(Warning):
            self.leave_1.onchange(values, 'date_to', field_onchange)

    def test_03_creation_fail(self):
        with self.assertRaises(ValidationError):
            self.leave_obj.create({
                'holiday_status_id': self.status_2.id,
                'holiday_type': 'employee',
                'type': 'remove',
                'date_from': self.today_start.strftime(DF),
                'date_to': self.today_end.strftime(DF),
                'employee_id': self.employee_4.id,
                'number_of_hours_temp': 8.0
            })

    def test_04_get_work_limits(self):

        start_dt, work_limits = self.calendar_obj._get_work_limits(
            self.today_end, self.today_start)
        self.assertEqual(start_dt, self.today_start)
        self.assertEqual(work_limits, [
            (
                self.today_start.replace(
                    hour=0, minute=0, second=0, microsecond=0),
                self.today_start
            ),
            (
                self.today_end,
                self.today_end.replace(
                    hour=23, minute=59, second=59, microsecond=999999)
            ),
        ])

        start_dt, work_limits = self.calendar_obj._get_work_limits(
            self.today_end, None)
        self.assertEqual(start_dt, self.today_end.replace(
            hour=0, minute=0, second=0, microsecond=0))
        self.assertEqual(work_limits, [
            (
                self.today_end,
                self.today_end.replace(
                    hour=23, minute=59, second=59, microsecond=999999)
            ),
        ])

        start_dt, work_limits = self.calendar_obj._get_work_limits(
            None, self.today_start)
        self.assertEqual(start_dt, self.today_start)
        self.assertEqual(work_limits, [
            (
                self.today_start.replace(
                    hour=0, minute=0, second=0, microsecond=0),
                self.today_start
            ),
        ])

        start_dt, work_limits = self.calendar_obj._get_work_limits(None, None)
        self.assertEqual(start_dt, datetime.today().replace(
            hour=0, minute=0, second=0, microsecond=0))
        self.assertEqual(work_limits, [])

    def test_05_get_working_intervals_of_day(self):
        default_interval = (
            self.today_start.hour,
            self.today_end.hour
        )
        interval = self.calendar_obj.get_working_intervals_of_day(
            self.today_start,
            self.today_end,
            default_interval=default_interval
        )

        self.assertEqual(interval, [(
            self.today_start,
            self.today_end
        )])

    def test_06_compute_leaves_count(self):
        employee_list = self.employee_1 + \
            self.employee_2 + \
            self.employee_3 + \
            self.employee_4
        employee_list._compute_leaves_count()

    def test_07_get_hours(self):
        self.leave_allocation_1.action_approve()
        self.leave_1.action_approve()
        hours = self.status_1.get_hours(self.employee_1)

        self.assertEqual(hours['virtual_remaining_hours'], 72.0)
        self.assertEqual(hours['remaining_hours'], 72.0)
        self.assertEqual(hours['hours_taken'], 8.0)
        self.assertEqual(hours['max_hours'], 80.0)

        self.assertEqual(self.status_1.with_context(
            employee_id=self.employee_1.id).virtual_remaining_hours, 72.0)
        self.assertEqual(self.status_1.with_context(
            employee_id=self.employee_1.id).remaining_hours, 72.0)
        self.assertEqual(self.status_1.with_context(
            employee_id=self.employee_1.id).hours_taken, 8.0)
        self.assertEqual(self.status_1.with_context(
            employee_id=self.employee_1.id).max_hours, 80.0)

        self.assertEqual(self.status_1.max_hours, 0.0)

        self.assertEqual(
            self.status_1.with_context(
                employee_id=self.employee_1.id).name_get(),
            [(self.status_1.id, 'Status 1')])

        self.assertEqual(
            self.status_2.with_context(
                employee_id=self.employee_1.id).name_get(),
            [(self.status_2.id, 'Status 2  (0.0 Left)')])

        self.assertEqual(
            self.status_1.name_get(),
            [(self.status_1.id, 'Status 1')])
