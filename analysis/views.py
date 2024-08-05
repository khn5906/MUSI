from django.shortcuts import render

# Create your views here.
def analysis(request):
    return render(request, 'analysis/analysis.html');

def visualization(request):
    return render(request, 'analysis/visualization.html');
