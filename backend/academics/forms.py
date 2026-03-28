from django import forms
from .models import Backlog

class BacklogRegistrationForm(forms.ModelForm):
    class Meta:
        model = Backlog
        fields = ['subject', 'amount']
        widgets = {
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }
    
    def __init__(self, student, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = self.get_failed_subjects(student)
        self.fields['subject'].label = "Select Failed Subject"
        self.fields['amount'].initial = 500
        self.fields['amount'].label = "Exam Fee (₹)"
    
    def get_failed_subjects(self, student):
        """Get subjects where student has F grade"""
        from .models import Marks
        failed_marks = Marks.objects.filter(
            student=student,
            grade='F'
        ).select_related('subject')
        return [m.subject for m in failed_marks]