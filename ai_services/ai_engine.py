"""
AI Services for Employee Management System

This module contains the AI logic for:
1. Attendance Prediction
2. Employee Mood Analysis
3. Smart Leave Recommendations
"""

# import pandas as pd
# import numpy as np
from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from django.db.models import Q, Avg, Count
from attendance.models import AttendanceRecord, EmployeeSchedule
from leave.models import LeaveApplication, LeaveBalance
from employees.models import EmployeeProfile
from .models import AttendancePrediction, MoodAnalysis, LeaveRecommendation
import logging
from typing import Dict, List, Tuple, Optional
import json

logger = logging.getLogger(__name__)


class AttendancePredictionService:
    """AI service for predicting employee attendance patterns"""
    
    def __init__(self):
        self.model_confidence_threshold = 0.6
        
    def predict_attendance(self, employee: User, prediction_date: date = None) -> Dict:
        """
        Predict attendance probability for an employee on a specific date
        """
        if prediction_date is None:
            prediction_date = date.today() + timedelta(days=1)
        
        try:
            # Get historical attendance data
            historical_data = self._get_historical_attendance_data(employee)
            
            if len(historical_data) < 30:  # Need minimum data for predictions
                return self._generate_default_prediction(employee, prediction_date)
            
            # Calculate various prediction factors
            factors = self._calculate_prediction_factors(employee, historical_data, prediction_date)
            
            # Generate prediction
            prediction = self._generate_attendance_prediction(factors)
            
            # Save to database
            self._save_attendance_prediction(employee, prediction_date, prediction, factors)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting attendance for {employee.username}: {str(e)}")
            return self._generate_default_prediction(employee, prediction_date)
    
    def _get_historical_attendance_data(self, employee: User) -> List[Dict]:
        """Get historical attendance data for analysis"""
        cutoff_date = date.today() - timedelta(days=90)
        
        records = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=cutoff_date
        ).order_by('date')
        
        data = []
        for record in records:
            data.append({
                'date': record.date,
                'status': record.status,
                'is_late': record.is_late,
                'check_in_time': record.check_in_time,
                'actual_hours': float(record.actual_hours),
                'day_of_week': record.date.weekday(),
                'month': record.date.month
            })
        
        return data
    
    def _calculate_prediction_factors(self, employee: User, historical_data: List[Dict], prediction_date: date) -> Dict:
        """Calculate factors that influence attendance prediction"""
        # df = pd.DataFrame(historical_data)  # Temporarily commented out
        
        factors = {
            'historical_attendance_rate': 0.9,
            'recent_trend': 0.0,
            'day_of_week_pattern': 0.0,
            'seasonal_pattern': 0.0,
            'leave_proximity': 0.0,
            'workload_factor': 0.0
        }
        
        if len(historical_data) > 0:
            # Overall attendance rate using list comprehension instead of pandas
            present_count = len([d for d in historical_data if d.get('status') in ['PRESENT', 'LATE']])
            factors['historical_attendance_rate'] = present_count / len(historical_data)
            
            # Recent trend (last 2 weeks)
            recent_df = df.tail(14)
            if len(recent_df) > 0:
                recent_present = len(recent_df[recent_df['status'].isin(['PRESENT', 'LATE'])])
                factors['recent_trend'] = recent_present / len(recent_df)
            
            # Day of week pattern
            dow = prediction_date.weekday()
            dow_df = df[df['day_of_week'] == dow]
            if len(dow_df) > 0:
                dow_present = len(dow_df[dow_df['status'].isin(['PRESENT', 'LATE'])])
                factors['day_of_week_pattern'] = dow_present / len(dow_df)
            
            # Seasonal pattern
            month_df = df[df['month'] == prediction_date.month]
            if len(month_df) > 0:
                month_present = len(month_df[month_df['status'].isin(['PRESENT', 'LATE'])])
                factors['seasonal_pattern'] = month_present / len(month_df)
        
        # Check for nearby leave applications
        factors['leave_proximity'] = self._check_leave_proximity(employee, prediction_date)
        
        # Workload factor (simplified)
        factors['workload_factor'] = self._estimate_workload_factor(employee)
        
        return factors
    
    def _generate_attendance_prediction(self, factors: Dict) -> Dict:
        """Generate attendance prediction based on calculated factors"""
        # Simple weighted average model (can be replaced with ML model)
        weights = {
            'historical_attendance_rate': 0.3,
            'recent_trend': 0.25,
            'day_of_week_pattern': 0.2,
            'seasonal_pattern': 0.1,
            'leave_proximity': -0.1,  # Negative weight
            'workload_factor': 0.15
        }
        
        attendance_probability = 0.0
        for factor, value in factors.items():
            if factor in weights:
                attendance_probability += weights[factor] * value
        
        # Clamp between 0 and 1
        attendance_probability = max(0.0, min(1.0, attendance_probability))
        
        # Calculate lateness probability (inverse relationship with attendance)
        lateness_probability = max(0.0, (1.0 - attendance_probability) * 0.3)
        
        # Determine risk level
        if attendance_probability < 0.5:
            risk_level = 'HIGH'
        elif attendance_probability < 0.7:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        # Model confidence based on data quality
        confidence = min(0.9, 0.6 + (len(factors) * 0.05))
        
        return {
            'attendance_probability': attendance_probability,
            'lateness_probability': lateness_probability,
            'absence_risk': risk_level,
            'model_confidence': confidence,
            'contributing_factors': factors
        }
    
    def _check_leave_proximity(self, employee: User, prediction_date: date) -> float:
        """Check if prediction date is near approved leave"""
        nearby_leaves = LeaveApplication.objects.filter(
            employee=employee,
            status='APPROVED',
            start_date__lte=prediction_date + timedelta(days=3),
            end_date__gte=prediction_date - timedelta(days=3)
        )
        
        return 1.0 if nearby_leaves.exists() else 0.0
    
    def _estimate_workload_factor(self, employee: User) -> float:
        """Estimate current workload factor (simplified)"""
        # This is a simplified estimation - in real implementation,
        # this would integrate with project management systems
        return 0.5  # Default medium workload
    
    def _generate_default_prediction(self, employee: User, prediction_date: date) -> Dict:
        """Generate default prediction when insufficient data"""
        return {
            'attendance_probability': 0.85,  # Assume good attendance by default
            'lateness_probability': 0.1,
            'absence_risk': 'LOW',
            'model_confidence': 0.5,
            'contributing_factors': {'insufficient_data': True}
        }
    
    def _save_attendance_prediction(self, employee: User, prediction_date: date, prediction: Dict, factors: Dict):
        """Save prediction to database"""
        AttendancePrediction.objects.update_or_create(
            employee=employee,
            prediction_type='DAILY',
            prediction_date=prediction_date,
            defaults={
                'attendance_probability': prediction['attendance_probability'],
                'lateness_probability': prediction['lateness_probability'],
                'absence_risk': prediction['absence_risk'],
                'model_confidence': prediction['model_confidence'],
                'contributing_factors': factors
            }
        )


class MoodAnalysisService:
    """AI service for analyzing employee mood and well-being"""
    
    def __init__(self):
        self.attention_threshold = -0.3  # Mood score threshold for HR attention
    
    def analyze_employee_mood(self, employee: User, analysis_date: date = None) -> Dict:
        """
        Analyze employee mood based on various data points
        """
        if analysis_date is None:
            analysis_date = date.today()
        
        try:
            # Gather data sources
            data_sources = self._gather_mood_data_sources(employee, analysis_date)
            
            # Calculate mood metrics
            mood_metrics = self._calculate_mood_metrics(employee, data_sources, analysis_date)
            
            # Generate recommendations
            recommendations = self._generate_mood_recommendations(mood_metrics)
            
            # Check if requires HR attention
            requires_attention, attention_reason = self._check_hr_attention_required(mood_metrics)
            
            # Save to database
            self._save_mood_analysis(employee, analysis_date, mood_metrics, data_sources, 
                                   recommendations, requires_attention, attention_reason)
            
            return {
                'mood_score': mood_metrics['mood_score'],
                'mood_category': mood_metrics['mood_category'],
                'stress_level': mood_metrics['stress_level'],
                'engagement_level': mood_metrics['engagement_level'],
                'satisfaction_level': mood_metrics['satisfaction_level'],
                'recommendations': recommendations,
                'requires_attention': requires_attention,
                'attention_reason': attention_reason
            }
            
        except Exception as e:
            logger.error(f"Error analyzing mood for {employee.username}: {str(e)}")
            return self._generate_default_mood_analysis()
    
    def _gather_mood_data_sources(self, employee: User, analysis_date: date) -> Dict:
        """Gather data from various sources for mood analysis"""
        cutoff_date = analysis_date - timedelta(days=30)
        
        # Attendance patterns
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=cutoff_date,
            date__lte=analysis_date
        )
        
        # Leave usage patterns
        leave_applications = LeaveApplication.objects.filter(
            employee=employee,
            created_at__date__gte=cutoff_date,
            created_at__date__lte=analysis_date
        )
        
        # Recent performance indicators (simplified)
        recent_overtime = attendance_records.filter(overtime_hours__gt=0).count()
        recent_late_arrivals = attendance_records.filter(is_late=True).count()
        total_records = attendance_records.count()
        
        data_sources = {
            'attendance_consistency': 1.0 - (recent_late_arrivals / max(total_records, 1)),
            'overtime_frequency': recent_overtime / max(total_records, 1),
            'leave_frequency': leave_applications.count(),
            'recent_absences': attendance_records.filter(status='ABSENT').count(),
            'total_attendance_records': total_records
        }
        
        return data_sources
    
    def _calculate_mood_metrics(self, employee: User, data_sources: Dict, analysis_date: date) -> Dict:
        """Calculate mood metrics based on data sources"""
        
        # Base mood score calculation
        mood_score = 0.0
        
        # Attendance factor (positive impact)
        attendance_factor = data_sources['attendance_consistency'] * 0.3
        mood_score += (attendance_factor - 0.15)  # Normalize around 0
        
        # Overtime factor (negative impact if excessive)
        overtime_factor = min(data_sources['overtime_frequency'], 0.5)
        mood_score -= overtime_factor * 0.4
        
        # Leave usage factor
        leave_factor = min(data_sources['leave_frequency'] / 10.0, 0.2)  # Normalize
        # Moderate leave usage is positive, excessive might indicate issues
        if leave_factor < 0.1:
            mood_score += 0.1  # Good work-life balance
        else:
            mood_score -= leave_factor * 0.5
        
        # Absence factor (negative impact)
        if data_sources['total_attendance_records'] > 0:
            absence_rate = data_sources['recent_absences'] / data_sources['total_attendance_records']
            mood_score -= absence_rate * 0.6
        
        # Clamp mood score between -1 and 1
        mood_score = max(-1.0, min(1.0, mood_score))
        
        # Determine mood category
        if mood_score >= 0.6:
            mood_category = 'VERY_POSITIVE'
        elif mood_score >= 0.2:
            mood_category = 'POSITIVE'
        elif mood_score >= -0.2:
            mood_category = 'NEUTRAL'
        elif mood_score >= -0.6:
            mood_category = 'NEGATIVE'
        else:
            mood_category = 'VERY_NEGATIVE'
        
        # Calculate detailed metrics
        stress_level = max(0.0, min(1.0, 0.5 + data_sources['overtime_frequency'] * 0.8 - mood_score * 0.3))
        engagement_level = max(0.0, min(1.0, 0.5 + mood_score * 0.4 + data_sources['attendance_consistency'] * 0.3))
        satisfaction_level = max(0.0, min(1.0, 0.5 + mood_score * 0.5))
        
        return {
            'mood_score': mood_score,
            'mood_category': mood_category,
            'stress_level': stress_level,
            'engagement_level': engagement_level,
            'satisfaction_level': satisfaction_level,
            'analysis_factors': data_sources
        }
    
    def _generate_mood_recommendations(self, mood_metrics: Dict) -> str:
        """Generate AI recommendations based on mood analysis"""
        recommendations = []
        
        mood_score = mood_metrics['mood_score']
        stress_level = mood_metrics['stress_level']
        engagement_level = mood_metrics['engagement_level']
        
        if mood_score < -0.3:
            recommendations.append("Consider scheduling a one-on-one meeting to discuss any challenges.")
            
        if stress_level > 0.7:
            recommendations.append("High stress levels detected. Suggest workload review and stress management resources.")
            
        if engagement_level < 0.4:
            recommendations.append("Low engagement detected. Consider career development discussions or role adjustment.")
            
        if mood_metrics['analysis_factors']['overtime_frequency'] > 0.3:
            recommendations.append("Frequent overtime detected. Review workload distribution and consider additional resources.")
            
        if not recommendations:
            if mood_score > 0.5:
                recommendations.append("Employee showing positive indicators. Consider for recognition or leadership opportunities.")
            else:
                recommendations.append("Employee metrics within normal range. Continue regular check-ins.")
        
        return " ".join(recommendations)
    
    def _check_hr_attention_required(self, mood_metrics: Dict) -> Tuple[bool, str]:
        """Check if employee requires HR attention"""
        
        reasons = []
        
        if mood_metrics['mood_score'] < -0.4:
            reasons.append("Very low mood score")
            
        if mood_metrics['stress_level'] > 0.8:
            reasons.append("Extremely high stress levels")
            
        if mood_metrics['engagement_level'] < 0.3:
            reasons.append("Very low engagement")
            
        if mood_metrics['analysis_factors']['overtime_frequency'] > 0.5:
            reasons.append("Excessive overtime")
        
        requires_attention = len(reasons) > 0
        attention_reason = "; ".join(reasons) if requires_attention else ""
        
        return requires_attention, attention_reason
    
    def _generate_default_mood_analysis(self) -> Dict:
        """Generate default mood analysis when analysis fails"""
        return {
            'mood_score': 0.0,
            'mood_category': 'NEUTRAL',
            'stress_level': 0.5,
            'engagement_level': 0.5,
            'satisfaction_level': 0.5,
            'recommendations': 'Unable to analyze mood due to insufficient data.',
            'requires_attention': False,
            'attention_reason': ''
        }
    
    def _save_mood_analysis(self, employee: User, analysis_date: date, mood_metrics: Dict, 
                           data_sources: Dict, recommendations: str, requires_attention: bool, 
                           attention_reason: str):
        """Save mood analysis to database"""
        MoodAnalysis.objects.update_or_create(
            employee=employee,
            analysis_date=analysis_date,
            defaults={
                'mood_score': mood_metrics['mood_score'],
                'mood_category': mood_metrics['mood_category'],
                'stress_level': mood_metrics['stress_level'],
                'engagement_level': mood_metrics['engagement_level'],
                'satisfaction_level': mood_metrics['satisfaction_level'],
                'data_sources': ['attendance_patterns', 'leave_usage', 'overtime_analysis'],
                'analysis_factors': mood_metrics['analysis_factors'],
                'recommendations': recommendations,
                'requires_attention': requires_attention,
                'attention_reason': attention_reason
            }
        )


class LeaveRecommendationService:
    """AI service for smart leave recommendations"""
    
    def __init__(self):
        self.burnout_threshold = 0.7
        self.workload_threshold = 0.8
        
    def generate_leave_recommendation(self, employee: User, analysis_date: date = None) -> Dict:
        """
        Generate smart leave recommendations for an employee
        """
        if analysis_date is None:
            analysis_date = date.today()
        
        try:
            # Analyze current employee state
            employee_state = self._analyze_employee_state(employee, analysis_date)
            
            # Generate recommendations based on analysis
            recommendations = self._generate_recommendations(employee, employee_state, analysis_date)
            
            # Save recommendations to database
            for recommendation in recommendations:
                self._save_leave_recommendation(employee, recommendation)
            
            return {
                'employee_state': employee_state,
                'recommendations': recommendations,
                'total_recommendations': len(recommendations)
            }
            
        except Exception as e:
            logger.error(f"Error generating leave recommendations for {employee.username}: {str(e)}")
            return self._generate_default_recommendations(employee, analysis_date)
    
    def _analyze_employee_state(self, employee: User, analysis_date: date) -> Dict:
        """Analyze current employee state for leave recommendations"""
        cutoff_date = analysis_date - timedelta(days=90)
        
        # Get attendance data
        attendance_records = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=cutoff_date,
            date__lte=analysis_date
        )
        
        # Get leave history
        recent_leaves = LeaveApplication.objects.filter(
            employee=employee,
            end_date__gte=cutoff_date,
            status__in=['APPROVED', 'TAKEN']
        )
        
        # Get current leave balance
        leave_balances = LeaveBalance.objects.filter(employee=employee)
        
        # Calculate metrics
        total_records = attendance_records.count()
        overtime_records = attendance_records.filter(overtime_hours__gt=0).count()
        late_records = attendance_records.filter(is_late=True).count()
        
        # Calculate scores
        workload_score = min(1.0, (overtime_records / max(total_records, 1)) * 2)
        consistency_score = 1.0 - (late_records / max(total_records, 1))
        
        # Days since last leave
        last_leave = recent_leaves.order_by('-end_date').first()
        days_since_last_leave = (analysis_date - last_leave.end_date).days if last_leave else 365
        
        # Burnout risk calculation
        burnout_risk = self._calculate_burnout_risk(workload_score, days_since_last_leave, consistency_score)
        
        return {
            'workload_score': workload_score,
            'consistency_score': consistency_score,
            'burnout_risk': burnout_risk,
            'days_since_last_leave': days_since_last_leave,
            'total_leave_days_used': sum([leave.get_duration() for leave in recent_leaves]),
            'available_leave_balance': self._get_total_leave_balance(leave_balances),
            'overtime_frequency': overtime_records / max(total_records, 1)
        }
    
    def _calculate_burnout_risk(self, workload_score: float, days_since_leave: int, consistency_score: float) -> float:
        """Calculate burnout risk score"""
        # Factors contributing to burnout
        workload_factor = workload_score * 0.4
        time_factor = min(1.0, days_since_leave / 180.0) * 0.4  # 6 months without leave = max factor
        consistency_factor = (1.0 - consistency_score) * 0.2
        
        burnout_risk = workload_factor + time_factor + consistency_factor
        return min(1.0, burnout_risk)
    
    def _get_total_leave_balance(self, leave_balances) -> int:
        """Get total available leave balance"""
        return sum([balance.remaining_days for balance in leave_balances])
    
    def _generate_recommendations(self, employee: User, state: Dict, analysis_date: date) -> List[Dict]:
        """Generate leave recommendations based on employee state"""
        recommendations = []
        
        # High burnout risk recommendation
        if state['burnout_risk'] > self.burnout_threshold:
            recommendations.append(self._create_burnout_prevention_recommendation(employee, state, analysis_date))
        
        # Excessive workload recommendation
        if state['workload_score'] > self.workload_threshold:
            recommendations.append(self._create_workload_balance_recommendation(employee, state, analysis_date))
        
        # Long time without leave
        if state['days_since_last_leave'] > 120:  # 4 months
            recommendations.append(self._create_wellness_recommendation(employee, state, analysis_date))
        
        # Optimal timing recommendations (quarterly breaks)
        if not recommendations:  # Only if no urgent recommendations
            recommendations.extend(self._create_optimal_timing_recommendations(employee, state, analysis_date))
        
        return recommendations
    
    def _create_burnout_prevention_recommendation(self, employee: User, state: Dict, analysis_date: date) -> Dict:
        """Create burnout prevention recommendation"""
        # Recommend immediate leave
        start_date = analysis_date + timedelta(days=7)  # Next week
        duration = min(7, state['available_leave_balance'])  # Up to 1 week
        
        return {
            'type': 'BURNOUT_PREVENTION',
            'priority': 'URGENT' if state['burnout_risk'] > 0.9 else 'HIGH',
            'start_date': start_date,
            'end_date': start_date + timedelta(days=duration - 1),
            'duration': duration,
            'reasoning': f"High burnout risk detected ({state['burnout_risk']:.2f}). Immediate rest recommended to prevent burnout and maintain productivity.",
            'benefits': [
                "Reduce stress and prevent burnout",
                "Improve mental health and well-being",
                "Return with increased productivity and focus",
                "Better work-life balance"
            ],
            'risk_factors': [
                "Continued high stress levels",
                "Potential burnout and decreased performance",
                "Health impacts from prolonged stress"
            ],
            'workload_score': state['workload_score'],
            'burnout_risk_score': state['burnout_risk'],
            'team_impact_score': 0.6,  # Medium impact
            'alternatives': self._generate_alternative_dates(start_date, duration)
        }
    
    def _create_workload_balance_recommendation(self, employee: User, state: Dict, analysis_date: date) -> Dict:
        """Create workload balance recommendation"""
        start_date = analysis_date + timedelta(days=14)  # In 2 weeks
        duration = min(5, state['available_leave_balance'])  # Up to 1 week
        
        return {
            'type': 'WORKLOAD_BALANCE',
            'priority': 'HIGH',
            'start_date': start_date,
            'end_date': start_date + timedelta(days=duration - 1),
            'duration': duration,
            'reasoning': f"High workload intensity detected ({state['workload_score']:.2f}). Short break recommended to restore balance.",
            'benefits': [
                "Reduce workload stress",
                "Prevent overtime fatigue",
                "Maintain consistent performance",
                "Recharge for upcoming challenges"
            ],
            'risk_factors': [
                "Continued excessive overtime",
                "Declining work quality due to fatigue",
                "Increased error rates"
            ],
            'workload_score': state['workload_score'],
            'burnout_risk_score': state['burnout_risk'],
            'team_impact_score': 0.7,
            'alternatives': self._generate_alternative_dates(start_date, duration)
        }
    
    def _create_wellness_recommendation(self, employee: User, state: Dict, analysis_date: date) -> Dict:
        """Create wellness recommendation"""
        start_date = analysis_date + timedelta(days=30)  # In a month
        duration = min(10, state['available_leave_balance'])  # Up to 2 weeks
        
        return {
            'type': 'WELLNESS',
            'priority': 'MEDIUM',
            'start_date': start_date,
            'end_date': start_date + timedelta(days=duration - 1),
            'duration': duration,
            'reasoning': f"It's been {state['days_since_last_leave']} days since last leave. Regular breaks are important for wellness.",
            'benefits': [
                "Maintain work-life balance",
                "Prevent gradual burnout",
                "Personal time for family and hobbies",
                "Return refreshed and motivated"
            ],
            'risk_factors': [
                "Gradual decrease in motivation",
                "Potential for future burnout",
                "Reduced job satisfaction"
            ],
            'workload_score': state['workload_score'],
            'burnout_risk_score': state['burnout_risk'],
            'team_impact_score': 0.4,  # Low impact with advance notice
            'alternatives': self._generate_alternative_dates(start_date, duration)
        }
    
    def _create_optimal_timing_recommendations(self, employee: User, state: Dict, analysis_date: date) -> List[Dict]:
        """Create optimal timing recommendations"""
        recommendations = []
        
        # Quarterly break recommendation
        next_quarter = analysis_date + timedelta(days=90)
        duration = min(5, max(3, state['available_leave_balance'] // 4))  # 3-5 days
        
        recommendations.append({
            'type': 'OPTIMAL_TIMING',
            'priority': 'LOW',
            'start_date': next_quarter,
            'end_date': next_quarter + timedelta(days=duration - 1),
            'duration': duration,
            'reasoning': "Regular quarterly breaks maintain optimal performance and prevent gradual stress accumulation.",
            'benefits': [
                "Maintain consistent high performance",
                "Regular stress relief",
                "Better long-term career sustainability",
                "Improved creativity and problem-solving"
            ],
            'risk_factors': [
                "Gradual stress accumulation",
                "Decreased long-term effectiveness"
            ],
            'workload_score': state['workload_score'],
            'burnout_risk_score': state['burnout_risk'],
            'team_impact_score': 0.3,  # Very low impact
            'alternatives': self._generate_alternative_dates(next_quarter, duration)
        })
        
        return recommendations
    
    def _generate_alternative_dates(self, primary_date: date, duration: int) -> List[Dict]:
        """Generate alternative date options"""
        alternatives = []
        
        # Alternative 1: One week earlier
        alt1_start = primary_date - timedelta(days=7)
        alternatives.append({
            'start_date': alt1_start.isoformat(),
            'end_date': (alt1_start + timedelta(days=duration - 1)).isoformat(),
            'reason': 'Earlier option'
        })
        
        # Alternative 2: One week later
        alt2_start = primary_date + timedelta(days=7)
        alternatives.append({
            'start_date': alt2_start.isoformat(),
            'end_date': (alt2_start + timedelta(days=duration - 1)).isoformat(),
            'reason': 'Later option'
        })
        
        return alternatives
    
    def _generate_default_recommendations(self, employee: User, analysis_date: date) -> Dict:
        """Generate default recommendations when analysis fails"""
        return {
            'employee_state': {
                'workload_score': 0.5,
                'burnout_risk': 0.3,
                'days_since_last_leave': 60
            },
            'recommendations': [],
            'total_recommendations': 0,
            'error': 'Unable to generate recommendations due to insufficient data'
        }
    
    def _save_leave_recommendation(self, employee: User, recommendation: Dict):
        """Save leave recommendation to database"""
        LeaveRecommendation.objects.create(
            employee=employee,
            recommendation_type=recommendation['type'],
            priority=recommendation['priority'],
            recommended_start_date=recommendation['start_date'],
            recommended_end_date=recommendation['end_date'],
            recommended_duration=recommendation['duration'],
            reasoning=recommendation['reasoning'],
            benefits=recommendation['benefits'],
            risk_factors=recommendation['risk_factors'],
            current_workload_score=recommendation['workload_score'],
            burnout_risk_score=recommendation['burnout_risk_score'],
            team_impact_score=recommendation['team_impact_score'],
            alternative_dates=recommendation['alternatives']
        )


# Main AI Service Manager
class AIServiceManager:
    """Central manager for all AI services"""
    
    def __init__(self):
        self.attendance_service = AttendancePredictionService()
        self.mood_service = MoodAnalysisService()
        self.leave_service = LeaveRecommendationService()
    
    def run_daily_analysis(self, employee: User = None):
        """Run daily AI analysis for all or specific employee"""
        if employee:
            employees = [employee]
        else:
            from employees.models import EmployeeProfile
            employees = User.objects.filter(employeeprofile__isnull=False)
        
        results = {
            'attendance_predictions': [],
            'mood_analyses': [],
            'leave_recommendations': [],
            'processed_employees': 0
        }
        
        for employee in employees:
            try:
                # Run attendance prediction
                attendance_result = self.attendance_service.predict_attendance(employee)
                results['attendance_predictions'].append({
                    'employee': employee.username,
                    'result': attendance_result
                })
                
                # Run mood analysis
                mood_result = self.mood_service.analyze_employee_mood(employee)
                results['mood_analyses'].append({
                    'employee': employee.username,
                    'result': mood_result
                })
                
                # Run leave recommendations (weekly basis)
                if date.today().weekday() == 0:  # Monday
                    leave_result = self.leave_service.generate_leave_recommendation(employee)
                    results['leave_recommendations'].append({
                        'employee': employee.username,
                        'result': leave_result
                    })
                
                results['processed_employees'] += 1
                
            except Exception as e:
                logger.error(f"Error processing AI analysis for {employee.username}: {str(e)}")
        
        return results


class SmartLeaveRecommendationService:
    """AI service for generating smart leave recommendations"""
    
    def generate_leave_recommendation(self, employee: User) -> Dict:
        """
        Generate smart leave recommendations for an employee
        """
        try:
            # Analyze current situation
            employee_analysis = self._analyze_employee_situation(employee)
            
            # Generate recommendations based on analysis
            recommendations = self._generate_recommendations(employee, employee_analysis)
            
            # Save recommendations to database
            for recommendation in recommendations:
                self._save_leave_recommendation(employee, recommendation)
            
            return {
                'recommendations_generated': len(recommendations),
                'recommendations': recommendations,
                'analysis': employee_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating leave recommendations for {employee.username}: {str(e)}")
            return {'recommendations_generated': 0, 'recommendations': [], 'analysis': {}}
    
    def _analyze_employee_situation(self, employee: User) -> Dict:
        """Analyze employee's current situation for leave planning"""
        
        # Get recent data
        cutoff_date = date.today() - timedelta(days=90)
        
        # Attendance analysis
        recent_attendance = AttendanceRecord.objects.filter(
            employee=employee,
            date__gte=cutoff_date
        )
        
        total_overtime = sum(record.overtime_hours for record in recent_attendance)
        avg_daily_hours = recent_attendance.aggregate(avg_hours=Avg('actual_hours'))['avg_hours'] or 8.0
        
        # Leave balance analysis
        current_year = date.today().year
        leave_balances = LeaveBalance.objects.filter(
            user=employee,
            year=current_year
        )
        
        total_available_days = sum(balance.available_days for balance in leave_balances)
        
        # Recent leave applications
        recent_leaves = LeaveApplication.objects.filter(
            employee=employee,
            created_at__date__gte=cutoff_date
        )
        
        # Workload indicators
        high_workload_days = recent_attendance.filter(overtime_hours__gt=2).count()
        workload_intensity = high_workload_days / max(recent_attendance.count(), 1)
        
        analysis = {
            'total_overtime_hours': float(total_overtime),
            'avg_daily_hours': float(avg_daily_hours),
            'available_leave_days': float(total_available_days),
            'recent_leave_requests': recent_leaves.count(),
            'workload_intensity': workload_intensity,
            'days_since_last_leave': self._calculate_days_since_last_leave(employee),
            'burnout_risk_score': self._calculate_burnout_risk(employee, recent_attendance)
        }
        
        return analysis
    
    def _calculate_days_since_last_leave(self, employee: User) -> int:
        """Calculate days since employee's last approved leave"""
        last_leave = LeaveApplication.objects.filter(
            employee=employee,
            status='APPROVED'
        ).order_by('-end_date').first()
        
        if last_leave:
            return (date.today() - last_leave.end_date).days
        return 365  # Default to 1 year if no leave found
    
    def _calculate_burnout_risk(self, employee: User, recent_attendance) -> float:
        """Calculate burnout risk score"""
        risk_factors = 0.0
        
        # Overtime frequency
        overtime_records = recent_attendance.filter(overtime_hours__gt=0).count()
        total_records = recent_attendance.count()
        
        if total_records > 0:
            overtime_frequency = overtime_records / total_records
            risk_factors += overtime_frequency * 0.4
        
        # Consecutive work days without break
        # This is simplified - in reality, you'd check for consecutive working days
        risk_factors += min(0.3, total_records / 90.0)  # Working all 90 days would be 0.3 risk
        
        # Average working hours
        avg_hours = recent_attendance.aggregate(avg_hours=Avg('actual_hours'))['avg_hours'] or 8.0
        if avg_hours > 9:
            risk_factors += (avg_hours - 9) * 0.1
        
        return min(1.0, risk_factors)
    
    def _generate_recommendations(self, employee: User, analysis: Dict) -> List[Dict]:
        """Generate specific leave recommendations"""
        recommendations = []
        
        # High burnout risk recommendation
        if analysis['burnout_risk_score'] > 0.6:
            recommendations.append(self._create_burnout_prevention_recommendation(employee, analysis))
        
        # Long-term leave balance recommendation
        if analysis['available_leave_days'] > 15 and analysis['days_since_last_leave'] > 90:
            recommendations.append(self._create_optimal_timing_recommendation(employee, analysis))
        
        # Workload-based recommendation
        if analysis['workload_intensity'] > 0.4:
            recommendations.append(self._create_workload_balance_recommendation(employee, analysis))
        
        # Wellness recommendation for consistent high performers
        if (analysis['total_overtime_hours'] > 40 and 
            analysis['days_since_last_leave'] > 180):
            recommendations.append(self._create_wellness_recommendation(employee, analysis))
        
        return recommendations
    
    def _create_burnout_prevention_recommendation(self, employee: User, analysis: Dict) -> Dict:
        """Create a burnout prevention recommendation"""
        
        # Recommend immediate short break
        recommended_start = date.today() + timedelta(days=7)  # One week notice
        recommended_end = recommended_start + timedelta(days=3)  # 4 days off
        
        return {
            'type': 'BURNOUT_PREVENTION',
            'priority': 'HIGH',
            'start_date': recommended_start,
            'end_date': recommended_end,
            'duration': 4,
            'reasoning': f"High burnout risk detected (score: {analysis['burnout_risk_score']:.2f}). "
                        f"Employee has worked {analysis['total_overtime_hours']} overtime hours recently.",
            'benefits': [
                "Prevent burnout and mental health issues",
                "Restore work-life balance",
                "Improve productivity upon return",
                "Reduce stress levels"
            ],
            'risk_factors': [
                "Continued high-stress work environment",
                "Potential productivity decline",
                "Risk of extended sick leave if burnout occurs"
            ],
            'workload_score': analysis['workload_intensity'],
            'burnout_risk_score': analysis['burnout_risk_score'],
            'team_impact_score': 0.6  # Medium impact
        }
    
    def _create_optimal_timing_recommendation(self, employee: User, analysis: Dict) -> Dict:
        """Create an optimal timing recommendation"""
        
        # Recommend during typically quieter periods
        recommended_start = date.today() + timedelta(days=30)  # Plan ahead
        recommended_end = recommended_start + timedelta(days=7)  # One week
        
        return {
            'type': 'OPTIMAL_TIMING',
            'priority': 'MEDIUM',
            'start_date': recommended_start,
            'end_date': recommended_end,
            'duration': 8,
            'reasoning': f"Employee has {analysis['available_leave_days']} available leave days and "
                        f"hasn't taken leave for {analysis['days_since_last_leave']} days.",
            'benefits': [
                "Utilize available leave balance effectively",
                "Prevent loss of leave days",
                "Maintain regular work-life balance",
                "Plan for optimal team coverage"
            ],
            'risk_factors': [
                "Leave balance may expire if not used",
                "Missing opportunities for rest and recharge"
            ],
            'workload_score': analysis['workload_intensity'],
            'burnout_risk_score': analysis['burnout_risk_score'],
            'team_impact_score': 0.3  # Lower impact with planning
        }
    
    def _create_workload_balance_recommendation(self, employee: User, analysis: Dict) -> Dict:
        """Create a workload balance recommendation"""
        
        recommended_start = date.today() + timedelta(days=14)
        recommended_end = recommended_start + timedelta(days=2)  # Long weekend
        
        return {
            'type': 'WORKLOAD_BALANCE',
            'priority': 'MEDIUM',
            'start_date': recommended_start,
            'end_date': recommended_end,
            'duration': 3,
            'reasoning': f"High workload intensity detected ({analysis['workload_intensity']:.2f}). "
                        f"Regular breaks recommended for sustained performance.",
            'benefits': [
                "Balance heavy workload periods",
                "Maintain consistent performance",
                "Prevent accumulation of stress"
            ],
            'risk_factors': [
                "Workload may continue to intensify",
                "Potential impact on project timelines"
            ],
            'workload_score': analysis['workload_intensity'],
            'burnout_risk_score': analysis['burnout_risk_score'],
            'team_impact_score': 0.4
        }
    
    def _create_wellness_recommendation(self, employee: User, analysis: Dict) -> Dict:
        """Create a wellness-focused recommendation"""
        
        recommended_start = date.today() + timedelta(days=45)
        recommended_end = recommended_start + timedelta(days=10)  # Extended break
        
        return {
            'type': 'WELLNESS',
            'priority': 'LOW',
            'start_date': recommended_start,
            'end_date': recommended_end,
            'duration': 11,
            'reasoning': f"Consistent high performance with {analysis['total_overtime_hours']} overtime hours. "
                        f"Extended break recommended for wellness and motivation.",
            'benefits': [
                "Reward consistent high performance",
                "Complete mental and physical recharge",
                "Prevent long-term burnout",
                "Increase long-term engagement"
            ],
            'risk_factors': [
                "Extended absence may require temporary coverage",
                "Project timeline considerations"
            ],
            'workload_score': analysis['workload_intensity'],
            'burnout_risk_score': analysis['burnout_risk_score'],
            'team_impact_score': 0.7  # Higher impact due to duration
        }
    
    def _save_leave_recommendation(self, employee: User, recommendation: Dict):
        """Save leave recommendation to database"""
        
        LeaveRecommendation.objects.create(
            employee=employee,
            recommendation_type=recommendation['type'],
            priority=recommendation['priority'],
            recommended_start_date=recommendation['start_date'],
            recommended_end_date=recommendation['end_date'],
            recommended_duration=recommendation['duration'],
            reasoning=recommendation['reasoning'],
            benefits=recommendation['benefits'],
            risk_factors=recommendation['risk_factors'],
            current_workload_score=recommendation['workload_score'],
            burnout_risk_score=recommendation['burnout_risk_score'],
            team_impact_score=recommendation['team_impact_score'],
            alternative_dates=[],  # Can be populated later
            expires_at=datetime.now() + timedelta(days=30)
        )