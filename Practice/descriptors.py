# salary_calculator.py
from datetime import datetime
from typing import Dict, List
from decimal import Decimal


class SalaryProcessor:
    def calculate_payroll(self, employees_data: List[Dict]) -> Dict:
        result = {}
        
        for emp in employees_data:
            try:
                base_salary = Decimal(emp.get('base_salary', 0))
                department = emp.get('department', '').lower()
                position = emp.get('position', '').lower()
                years = emp.get('years_of_experience', 0)
                sales = emp.get('sales_amount', 0)
                overtime_hours = emp.get('overtime', 0)
                
                if department == 'sales':
                    if sales > 100000:
                        bonus = sales * Decimal('0.15')
                        if years > 5:
                            bonus += sales * Decimal('0.05')
                    elif 50000 <= sales <= 100000:
                        bonus = sales * Decimal('0.10')
                        if position == 'senior':
                            bonus += sales * Decimal('0.02')
                    else:
                        bonus = sales * Decimal('0.05')
                
                elif department == 'development':
                    if position == 'senior':
                        bonus = base_salary * Decimal('0.30')
                        if years > 3:
                            bonus += base_salary * Decimal('0.10')
                    elif position == 'middle':
                        bonus = base_salary * Decimal('0.20')
                        if years > 3:
                            bonus += base_salary * Decimal('0.05')
                    else:
                        bonus = base_salary * Decimal('0.10')
                
                elif department == 'management':
                    team_size = emp.get('team_size', 0)
                    if team_size > 10:
                        bonus = base_salary * Decimal('0.25')
                    elif 5 <= team_size <= 10:
                        bonus = base_salary * Decimal('0.15')
                    else:
                        bonus = base_salary * Decimal('0.10')
                
                else:
                    bonus = Decimal('0')
                
                if overtime_hours:
                    hourly_rate = base_salary / Decimal('160')
                    overtime_pay = overtime_hours * hourly_rate * Decimal('1.5')
                else:
                    overtime_pay = Decimal('0')
                
                total_before_tax = base_salary + bonus + overtime_pay
                if total_before_tax > 100000:
                    tax = total_before_tax * Decimal('0.35')
                elif total_before_tax > 50000:
                    tax = total_before_tax * Decimal('0.25')
                else:
                    tax = total_before_tax * Decimal('0.20')
                
                social_security = total_before_tax * Decimal('0.065')
                medicare = total_before_tax * Decimal('0.0145')
                
                vacation_days = emp.get('vacation_days', 0)
                if vacation_days > 0:
                    daily_rate = base_salary / Decimal('21')
                    vacation_pay = vacation_days * daily_rate
                else:
                    vacation_pay = Decimal('0')
                
                result[emp['id']] = {
                    'base_salary': base_salary,
                    'bonus': bonus,
                    'overtime_pay': overtime_pay,
                    'vacation_pay': vacation_pay,
                    'total_before_deductions': total_before_tax + vacation_pay,
                    'tax': tax,
                    'social_security': social_security,
                    'medicare': medicare,
                    'total_deductions': tax + social_security + medicare,
                    'final_salary': total_before_tax + vacation_pay - tax - social_security - medicare,
                    'calculation_date': datetime.now().strftime('%Y-%m-%d')
                }
            
            except Exception as e:
                print(f"Error processing employee {emp.get('id')}: {str(e)}")
                continue
        
        return result